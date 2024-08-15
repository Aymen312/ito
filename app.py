import streamlit as st
import pandas as pd
from io import BytesIO

# --- Fonctions pour le traitement des données ---

def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def display_supplier_info(df, fournisseur):
    fournisseur = fournisseur.strip().upper() 
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame()
    return df_filtered

def display_designation_info(df, designation):
    designation = designation.strip().upper()  
    df_filtered = df[df['designation'].str.upper().str.contains(designation)] if designation else pd.DataFrame()
    return df_filtered

def filter_negative_stock(df):
    rayons = df['rayon'].str.upper().unique()
    selected_rayon = st.selectbox("Filtrer par Rayon:", ['Tous'] + list(rayons))
    if selected_rayon == 'Tous':
        df_filtered = df[df['Qté stock dispo'] < 0]
    else:
        df_filtered = df[(df['rayon'].str.upper() == selected_rayon) & (df['Qté stock dispo'] < 0)]
    return df_filtered

def display_anita_sizes(df):
    df_anita = df[df['fournisseur'].str.upper() == "ANITA"]
    tailles = [f"{num}{letter}" for num in [85, 90, 95, 100, 105, 110] for letter in 'ABCDEF']
    df_anita_sizes = df_anita[df_anita['taille'].isin(tailles)]
    df_anita_sizes = df_anita_sizes.groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)
    df_anita_sizes = df_anita_sizes.replace(0, "Nul")
    return df_anita_sizes

def display_sidas_levels(df):
    df_sidas = df[df['fournisseur'].str.upper().str.contains("SIDAS", na=False)]
    df_sidas = df_sidas.dropna(subset=['couleur', 'taille'])
    levels = ['LOW', 'MID', 'HIGH']
    sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    results = {}
    for level in levels:
        df_sidas_level = df_sidas[df_sidas['couleur'].str.upper() == level]
        df_sizes = df_sidas_level[df_sidas_level['taille'].isin(sizes)]
        df_sizes_grouped = df_sizes.groupby(['taille', 'designation'])['Qté stock dispo'].sum().unstack(fill_value=0)
        df_sizes_grouped = df_sizes_grouped.replace(0, "Nul")
        df_sizes_with_designation = df_sizes_grouped.stack().reset_index().rename(columns={0: 'Qté stock dispo'})
        results[level] = df_sizes_with_designation
    return results

def total_stock_value_by_supplier(df):
    df['Valeur Totale HT'] = df['Qté stock dispo'] * df['Prix Achat']
    total_value_by_supplier = df.groupby('fournisseur')['Valeur Totale HT'].sum().reset_index()
    total_value_by_supplier = total_value_by_supplier.sort_values(by='Valeur Totale HT', ascending=False) 
    return total_value_by_supplier

def sort_sizes(df):
    df['taille'] = pd.Categorical(df['taille'], 
                                  categories=sorted(df['taille'].unique(), 
                                                    key=lambda x: (int(x[:-1]), x[-1]) if x[:-1].isdigit() else (float('inf'), x)), 
                                  ordered=True)
    df = df.sort_values('taille')
    return df

def display_stock_by_family(df):
    familles = ["CHAUSSURES RANDO", "CHAUSSURES RUNN", "CHAUSSURE TRAIL"]
    for famille in familles:
        st.subheader(f"Stock pour {famille}")
        df_family = df[df['famille'].str.upper() == famille]
        total_stock = df_family['Qté stock dispo'].sum()
        st.write(f"**Qté dispo totale pour {famille} : {total_stock}**") 

        rayon_options = ['Tous', 'Homme', 'Femme', 'Autre']
        rayon_filter = st.selectbox(f"Filtrer par Rayon pour {famille}:", 
                                    options=rayon_options, 
                                    key=f"rayon_{famille}")
        
        if rayon_filter == 'Tous':
            pass 
        elif rayon_filter in ['Homme', 'Femme']:
            df_family = df_family[df_family['rayon'].str.upper() == rayon_filter.upper()]
        else: 
            df_family = df_family[~df_family['rayon'].str.upper().isin(['HOMME', 'FEMME'])]

        if not df_family.empty:
            df_family = sort_sizes(df_family.copy())
            st.dataframe(df_family[['fournisseur', 'couleur', 'taille', 'designation', 'marque', 'ssfamille']])

            total_stock_filtered = df_family['Qté stock dispo'].sum()
            st.write(f"**Qté dispo totale pour {rayon_filter} : {total_stock_filtered}**")
        else:
            st.write(f"Aucune information disponible pour {famille} "
                     f"dans la catégorie {rayon_filter}.")

# --- Configuration de l'application Streamlit ---
st.set_page_config(
    page_title="Application d'Analyse TDR", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- CSS Personnalisé pour un style moderne (Material Design) ---
st.markdown(
    """
    <style>
        /* --- Importation de la police Roboto (Google Fonts) --- */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

        /* --- Styles globaux --- */
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f5f5f5; /* Gris très clair */
        }

        /* --- Titres --- */
        h1, h2, h3 {
            color: #212121; /* Gris foncé */
        }

        /* --- Tableaux de données --- */
        table {
            border-collapse: collapse;
            width: 100%;
            background-color: white;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1); /* Ombre subtile */
        }
        th, td {
            text-align: left;
            padding: 12px 16px;
            border-bottom: 1px solid #EEEEEE; /* Gris très clair */
        }
        th {
            font-weight: bold;
        }

        /* --- Messages d'état --- */
        .st-success {
            color: #448a50; /* Vert */
        }
        .st-warning {
            color: #f0ad4e; /* Orange */
        }
        .st-error {
            color: #d9534f; /* Rouge */
        }

        /* --- Onglets (style Material Design) --- */
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 2px solid #EEEEEE; /* Gris très clair */
        }
        .stTabs [data-baseweb="tab-list"] button {
            background-color: transparent;
            border: none;
            color: #757575; /* Gris moyen */
            font-size: 16px;
            margin-right: 32px;
            padding: 12px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        .stTabs [data-baseweb="tab-list"] button:hover {
            color: #212121; /* Gris foncé */
        }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #2196f3; /* Bleu Material Design */
            border-bottom: 2px solid #2196f3; /* Bleu Material Design */
        }

        /* --- Boutons --- */
        .stButton>button {
            background-color: #2196f3; /* Bleu Material Design */
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        .stButton>button:hover {
            background-color: #1976d2; /* Bleu Material Design plus foncé */
        }

        /* --- Autres éléments --- */
        .stSelectbox [data-baseweb="select"] {
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #bdbdbd; /* Gris clair */
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Interface principale de l'application ---
st.title("Application d'Analyse TDR")

st.sidebar.markdown("### Menu")
st.sidebar.info("Téléchargez un fichier CSV ou Excel pour commencer l'analyse.")

fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        with st.spinner("Chargement des données..."):
            if extension_fichier == 'csv':
                df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
            elif extension_fichier == 'xlsx':
                df = pd.read_excel(fichier_telecharge)
            else:
                st.error("Format de fichier non supporté")
                df = None

        if df is not None:
            df = clean_numeric_columns(df)
            df = clean_size_column(df)  

            st.success("Données chargées avec succès!")

            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Filtrer par Fournisseur", 
                                                              "Filtrer par Désignation", 
                                                              "Stock Négatif", 
                                                              "Anita Tailles", 
                                                              "Sidas Niveaux", 
                                                              "Valeur Totale du Stock par Fournisseur",
                                                              "Stock par Famille"])

            with tab1:
                fournisseur = st.text_input("Entrez le nom du fournisseur:")
                df_filtered = display_supplier_info(df, fournisseur)
                if not df_filtered.empty:
                    st.dataframe(df_filtered)
                else:
                    st.write("Aucune information disponible pour ce fournisseur.")

            with tab2:
                designation = st.text_input("Entrez la désignation du produit:")
                df_filtered = display_designation_info(df, designation)
                if not df_filtered.empty:
                    st.dataframe(df_filtered)
                else:
                    st.write("Aucune information disponible pour cette désignation.")

            with tab3:
                df_negative_stock = filter_negative_stock(df)
                if not df_negative_stock.empty:
                    st.dataframe(df_negative_stock)
                else:
                    st.write("Aucun stock négatif trouvé.")

            with tab4:
                df_anita_sizes = display_anita_sizes(df)
                st.write("Quantités disponibles pour Anita par taille:")
                st.dataframe(df_anita_sizes)

            with tab5:
                sidas_results = display_sidas_levels(df)
                for level, df_level in sidas_results.items():
                    st.write(f"Quantités disponibles pour SIDAS niveau {level}:")
                    st.dataframe(df_level)

            with tab6:
                st.subheader("Valeur Totale du Stock par Fournisseur")
                df_total_value_by_supplier = total_stock_value_by_supplier(df)
                st.dataframe(df_total_value_by_supplier)
                total_value = df_total_value_by_supplier['Valeur Totale HT'].sum()
                st.write(f"**Valeur Totale du Stock pour tous les fournisseurs : {total_value:.2f}**")
            
            with tab7:
                st.header("Stock par Famille")
                display_stock_by_family(df)

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
