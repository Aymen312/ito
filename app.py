import streamlit as st
import pandas as pd
from io import BytesIO

# --- CONFIGURATION DE L'APPLICATION (DOIT ÊTRE LA PREMIÈRE COMMANDE) ---
st.set_page_config(
    page_title="Application d'Analyse TDR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    body { font-family: 'Roboto', sans-serif; background-color: #f5f5f5; }
    h1, h2, h3 { color: #212121; }
    table { border-collapse: collapse; width: 100%; background-color: white; box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1); }
    th, td { text-align: left; padding: 12px 16px; border-bottom: 1px solid #EEEEEE; }
    th { font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #EEEEEE; }
    .stTabs [data-baseweb="tab-list"] button { 
        background-color: transparent; border: none; color: #757575; 
        font-size: 16px; margin-right: 32px; padding: 12px 16px; 
        border-top-left-radius: 4px; border-top-right-radius: 4px; 
    }
    .stButton>button { background-color: #2196f3; color: white; border: none; padding: 8px 16px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS DE TRAITEMENT ---
def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def highlight_row_if_one(row):
    if row['Qté stock dispo'] == 1:
        return ['background-color: red' for _ in row]
    return [''] * len(row)

def display_supplier_info(df, fournisseur):
    colonnes_affichier = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    fournisseur = fournisseur.strip().upper()
    df['fournisseur'] = df['fournisseur'].fillna('')
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame(columns=colonnes_affichier)
    return df_filtered[colonnes_affichier]

def normalize_size(size):
    if pd.isna(size): return ''
    size_str = str(size).strip()
    if '.' in size_str:
        int_part, dec_part = size_str.split('.', 1)
        int_part = int_part.lstrip('0') or '0'
        size_str = f"{int_part}.{dec_part}"
    else:
        size_str = size_str.lstrip('0') or '0'
    return size_str

def display_designation_info(df, designation):
    colonnes_a_afficher = ['barcode', 'taille', 'rayon', 'designation', 'Qté stock dispo']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    df_filtered = df[df['designation'].str.upper() == designation] if designation else pd.DataFrame(columns=colonnes_a_afficher)

    if 'taille' in df_filtered.columns:
        df_filtered['taille_normalisee'] = df_filtered['taille'].apply(normalize_size)

    sum_by_size = pd.DataFrame()
    if not df_filtered.empty and 'taille_normalisee' in df_filtered.columns:
        df_filtered['taille_num'] = pd.to_numeric(df_filtered['taille_normalisee'], errors='coerce')
        sum_by_size = df_filtered.groupby(['taille_normalisee', 'rayon'])['Qté stock dispo'].sum().reset_index()
        sum_by_size.columns = ['Taille', 'Rayon', 'Total Qté dispo']
        sum_by_size['taille_num'] = pd.to_numeric(sum_by_size['Taille'], errors='coerce')
        sum_by_size = sum_by_size.sort_values('taille_num').drop(columns=['taille_num'])

    if not df_filtered.empty and 'taille_num' in df_filtered.columns:
        df_filtered = df_filtered.sort_values('taille_num')
    
    st.dataframe(df_filtered[colonnes_a_afficher].style.apply(highlight_row_if_one, axis=1))

    if not sum_by_size.empty:
        sum_homme = sum_by_size[sum_by_size['Rayon'] == 'HOMME']
        sum_femme = sum_by_size[sum_by_size['Rayon'] == 'FEMME']

        if not sum_homme.empty:
            st.subheader("Somme des quantités disponibles par taille - Rayon HOMME")
            st.dataframe(sum_homme[['Taille', 'Total Qté dispo']].style.applymap(
                lambda val: 'background-color: red' if val == 1 else '', subset=['Total Qté dispo']))

        if not sum_femme.empty:
            st.subheader("Somme des quantités disponibles par taille - Rayon FEMME")
            st.dataframe(sum_femme[['Taille', 'Total Qté dispo']].style.applymap(
                lambda val: 'background-color: red' if val == 1 else '', subset=['Total Qté dispo']))

# --- INTERFACE UTILISATEUR ---
st.title("Application d'Analyse TDR")
st.sidebar.markdown("### Menu")
fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])

if fichier_telecharge:
    try:
        with st.spinner("Chargement des données..."):
            if fichier_telecharge.name.endswith('.csv'):
                df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
            else:
                df = pd.read_excel(fichier_telecharge)
            
            df = clean_numeric_columns(df)
            df = clean_size_column(df)
            st.success("Données chargées avec succès!")

            tab1, tab2 = st.tabs(["Fournisseur", "Désignation"])
            
            with tab1:
                fournisseur = st.text_input("Entrez le nom du fournisseur:")
                df_filtered = display_supplier_info(df.copy(), fournisseur)
                st.dataframe(df_filtered.style.apply(highlight_row_if_one, axis=1))
            
            with tab2:
                designation = st.text_input("Entrez la désignation du produit:")
                display_designation_info(df.copy(), designation)

    except Exception as e:
        st.error(f"Erreur lors du traitement: {str(e)}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse")
