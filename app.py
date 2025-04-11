import streamlit as st
import pandas as pd
from io import BytesIO

#### --- Fonctions pour le traitement des données ---
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
    """Met en surbrillance la ligne en rouge si 'Qté stock dispo' est égale à 1."""
    if row['Qté stock dispo'] == 1:
        return ['background-color: red' for _ in row]
    else:
        return [''] * len(row)

#### --- Fonction pour les désignations Brooks manquantes ---
def display_missing_brooks_designations(df):
    # Désignations attendues pour Brooks
    expected_designations = [
        'GHOST 16', 'GHOST 16 W', 
        'CASCADIA 18', 'CASCADIA 18 W'
    ]
    
    # Filtrer seulement les produits Brooks disponibles
    df_brooks = df[df['marque'].str.upper() == 'BROOKS']
    available_designations = df_brooks['designation'].str.upper().unique()
    
    # Trouver les désignations manquantes
    missing_designations = [
        desig for desig in expected_designations 
        if desig.upper() not in available_designations
    ]
    
    # Créer un DataFrame pour l'affichage
    if missing_designations:
        df_missing = pd.DataFrame({
            'Désignation manquante': missing_designations,
            'Statut': 'Indisponible'
        })
        
        # Afficher le tableau avec style
        st.subheader("Désignations Brooks indisponibles")
        st.dataframe(
            df_missing.style.applymap(
                lambda x: 'color: red', 
                subset=['Statut']
            )
        )
        
        # Afficher un résumé
        st.warning(f"{len(missing_designations)} désignations Brooks manquantes sur {len(expected_designations)} attendues")
    else:
        st.success("Toutes les désignations Brooks sont disponibles en stock!")
    
    return df_missing

#### --- Fonctions modifiées pour afficher les colonnes spécifiques ---
def display_supplier_info(df, fournisseur):
    colonnes_affichier = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    fournisseur = fournisseur.strip().upper()
    df['fournisseur'] = df['fournisseur'].fillna('')
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame(columns=colonnes_affichier)
    return df_filtered[colonnes_affichier]

def display_designation_info(df, designation):
    colonnes_a_afficher = ['barcode', 'taille', 'rayon', 'designation', 'Qté stock dispo']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    df_filtered = df[df['designation'].str.upper() == designation] if designation else pd.DataFrame(columns=colonnes_a_afficher)

    def normalize_size(size):
        if pd.isna(size):
            return ''
        size_str = str(size).strip()
        if '.' in size_str:
            int_part, dec_part = size_str.split('.', 1)
            int_part = int_part.lstrip('0') or '0'
            size_str = f"{int_part}.{dec_part}"
        else:
            size_str = size_str.lstrip('0') or '0'
        return size_str

    if 'taille' in df_filtered.columns:
        df_filtered['taille_normalisee'] = df_filtered['taille'].apply(normalize_size)

    sum_by_size = pd.DataFrame()
    if not df_filtered.empty and 'taille_normalisee' in df_filtered.columns:
        df_filtered['taille_num'] = pd.to_numeric(df_filtered['taille_normalisee'], errors='coerce')
        sum_by_size = df_filtered.groupby(['taille_normalisee', 'rayon'])['Qté stock dispo'].sum().reset_index()
        sum_by_size.columns = ['Taille', 'Rayon', 'Total Qté dispo']
        sum_by_size['taille_num'] = pd.to_numeric(sum_by_size['Taille'], errors='coerce')
        sum_by_size = sum_by_size.sort_values('taille_num')
        sum_by_size = sum_by_size.drop(columns=['taille_num'])

    def highlight_row_if_one(row):
        if 'taille_normalisee' in row and row['taille_normalisee'] in sum_by_size['Taille'].values:
            mask = (sum_by_size['Taille'] == row['taille_normalisee']) 
            if 'rayon' in sum_by_size.columns:
                mask &= (sum_by_size['Rayon'] == row['rayon'])
            total = sum_by_size.loc[mask, 'Total Qté dispo'].values[0] if any(mask) else 0
            if total == 1:
                return ['background-color: red'] * len(row)
        return [''] * len(row)

    if not df_filtered.empty and 'taille_num' in df_filtered.columns:
        df_filtered = df_filtered.sort_values('taille_num')
    st.dataframe(df_filtered[colonnes_a_afficher].style.apply(highlight_row_if_one, axis=1))

    if not sum_by_size.empty:
        sum_homme = sum_by_size[sum_by_size['Rayon'] == 'HOMME']
        sum_femme = sum_by_size[sum_by_size['Rayon'] == 'FEMME']

        def highlight_total_if_one(val):
            color = 'red' if val == 1 else ''
            return f'background-color: {color}'

        if not sum_homme.empty:
            st.subheader("Somme des quantités disponibles par taille - Rayon HOMME")
            styled_homme = sum_homme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo'])
            st.dataframe(styled_homme)

        if not sum_femme.empty:
            st.subheader("Somme des quantités disponibles par taille - Rayon FEMME")
            styled_femme = sum_femme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo'])
            st.dataframe(styled_femme)

#### --- Fonction modifiée pour "Stock Négatif" ---
def filter_negative_stock(df):
    colonnes_affichier = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0)
    df_filtered = df[df['Qté stock dispo'] < 0]
    return df_filtered[colonnes_affichier]

def display_anita_sizes(df):
    df_anita = df[df['fournisseur'].str.upper() == "ANITA"]
    tailles = [f"{num}{letter}" for num in [85, 90, 95, 100, 105, 110] for letter in 'ABCDEF']
    df_anita_sizes = df_anita[df_anita['taille'].isin(tailles)]
    df_anita_sizes = df_anita_sizes.groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)
    df_anita_sizes = df_anita_sizes.replace(0, "Nul")
    return df_anita_sizes

def display_sidas_levels(df):
    df['fournisseur'] = df['fournisseur'].fillna('')
    df = df.dropna(subset=['couleur', 'taille'])
    df_sidas = df[df['fournisseur'].str.upper().str.contains("SIDAS")]
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

        available_sizes = df_sidas_level['taille'].unique()
        unavailable_sizes = [size for size in sizes if size not in available_sizes]
        st.write(f"Tailles indisponibles pour SIDAS niveau {level}: {', '.join(unavailable_sizes) if unavailable_sizes else 'Aucune'}")

    return results

def total_stock_value_by_supplier(df):
    df['Qté stock dispo'] = pd.to_numeric(df['Qté stock dispo'], errors='coerce').fillna(0)
    df['Prix Achat'] = pd.to_numeric(df['Prix Achat'], errors='coerce').fillna(0)
    df['Valeur Totale HT'] = df['Qté stock dispo'] * df['Prix Achat']
    total_value_by_supplier = df.groupby('fournisseur')['Valeur Totale HT'].sum().reset_index()
    total_value_by_supplier = total_value_by_supplier.sort_values(by='Valeur Totale HT', ascending=False)
    return total_value_by_supplier

def sort_sizes(df):
    df['taille'] = pd.Categorical(df['taille'],
                                 categories=sorted(df['taille'].unique(),
                                                   key=lambda x: (int(x[:-1]), x[-1]) if x[:-1].isdigit() else (
                                                       float('inf'), x)),
                                 ordered=True)
    df = df.sort_values('taille')
    return df

def display_stock_by_family(df):
    familles = ["CHAUSSURES RANDO", "CHAUSSURES RUNN", "CHAUSSURE TRAIL"]
    for famille in familles:
        st.subheader(f"Stock pour {famille}")
        df['famille'] = df['famille'].fillna('')
        df_family = df[df['famille'].str.upper() == famille]
        df_family['Valeur Stock'] = df_family['Qté stock dispo'] * df_family['Prix Achat']

        total_stock = df_family['Qté stock dispo'].sum()
        total_stock_value = df_family['Valeur Stock'].sum()
        st.markdown(f"Qté dispo totale pour {famille} : {total_stock}")
        st.markdown(f"Valeur totale du stock pour {famille} : {total_stock_value:.2f}")

        rayon_options = ['Tous', 'Homme', 'Femme', 'Autre']
        rayon_filter = st.selectbox(f"Filtrer par Rayon pour {famille}:",
                                    options=rayon_options,
                                    key=f"rayon_{famille}")

        if rayon_filter == 'Tous':
            pass
        elif rayon_filter in ['Homme', 'Femme']:
            df_family['rayon'] = df_family['rayon'].fillna('')
            df_family = df_family[df_family['rayon'].str.upper() == rayon_filter.upper()]
        else:
            df_family['rayon'] = df_family['rayon'].fillna('')
            df_family = df_family[~df_family['rayon'].str.upper().isin(['HOMME', 'FEMME'])]

        if not df_family.empty:
            df_family = sort_sizes(df_family.copy())
            st.dataframe(df_family[
                             ['rayon', 'fournisseur', 'couleur', 'taille', 'designation', 'marque', 'ssfamille',
                              'Qté stock dispo', 'Valeur Stock']].style.apply(highlight_row_if_one, axis=1))

            total_stock_filtered = df_family['Qté stock dispo'].sum()
            total_stock_value_filtered = df_family['Valeur Stock'].sum()
            st.markdown(f"Qté dispo totale pour {rayon_filter} : {total_stock_filtered}")
            st.markdown(f"Valeur totale du stock pour {rayon_filter} : {total_stock_value_filtered:.2f}")
        else:
            st.write(f"Aucune information disponible pour {famille} "
                     f"dans la catégorie {rayon_filter}.")

#### --- Configuration de l'application Streamlit ---
st.set_page_config(
    page_title="Application d'Analyse TDR",
    layout="wide",
    initial_sidebar_state="expanded"
)

#### --- CSS Personnalisé ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #f5f5f5;
    }
    h1, h2, h3 {
        color: #212121;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        background-color: white;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
    }
    th, td {
        text-align: left;
        padding: 12px 16px;
        border-bottom: 1px solid #EEEEEE;
    }
    th {
        font-weight: bold;
    }
    .st-success {
        color: #448a50;
    }
    .st-warning {
        color: #f0ad4e;
    }
    .st-error {
        color: #d9534f;
    }
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid #EEEEEE;
    }
    .stTabs [data-baseweb="tab-list"] button {
        background-color: transparent;
        border: none;
        color: #757575;
        font-size: 16px;
        margin-right: 32px;
        padding: 12px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        color: #212121;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #2196f3;
        border-bottom: 2px solid #2196f3;
    }
    .stButton>button {
        background-color: #2196f3;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #1976d2;
    }
    .stSelectbox [data-baseweb="select"] {
        padding: 8px 12px;
        border-radius: 4px;
        border: 1px solid #bdbdbd;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#### --- Interface principale ---
st.title("Application d'Analyse TDR")
st.sidebar.markdown("############ Menu")
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

                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                    "Filtrer par Fournisseur",
                    "Filtrer par Désignation", 
                    "Stock Négatif",
                    "Anita Tailles",
                    "Sidas Niveaux",
                    "Valeur Totale par Fournisseur",
                    "Stock par Famille",
                    "Brooks - Manquants"
                ])

                with tab1:
                    fournisseur = st.text_input("Entrez le nom du fournisseur:")
                    df_filtered = display_supplier_info(df.copy(), fournisseur)
                    if not df_filtered.empty:
                        st.dataframe(df_filtered.style.apply(highlight_row_if_one, axis=1))
                    else:
                        st.write("Aucune information disponible pour ce fournisseur.")

                with tab2:
                    designation = st.text_input("Entrez la désignation du produit:")
                    display_designation_info(df.copy(), designation)

                with tab3:
                    st.dataframe(filter_negative_stock(df.copy()).style.apply(highlight_row_if_one, axis=1))

                with tab4:
                    df_anita_sizes = display_anita_sizes(df)
                    st.write("Quantités disponibles pour Anita par taille:")
                    st.dataframe(df_anita_sizes)

                with tab5:
                    sidas_results = display_sidas_levels(df)
                    for level, df_level in sidas_results.items():
                        st.write(f"Quantités disponibles pour SIDAS niveau {level}:")
                        st.dataframe(df_level.style.apply(highlight_row_if_one, axis=1))

                with tab6:
                    st.subheader("Valeur Totale du Stock par Fournisseur")
                    df_total_value_by_supplier = total_stock_value_by_supplier(df)
                    st.dataframe(df_total_value_by_supplier)
                    total_value = df_total_value_by_supplier['Valeur Totale HT'].sum()
                    st.markdown(f"Valeur Totale du Stock pour tous les fournisseurs : {total_value:.2f}")

                with tab7:
                    st.header("Stock par Famille")
                    display_stock_by_family(df)

                with tab8:
                    st.header("Désignations Brooks manquantes en stock")
                    missing_designations = display_missing_brooks_designations(df.copy())
                    
                    if not missing_designations.empty:
                        csv = missing_designations.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Exporter la liste des manquants",
                            csv,
                            "brooks_manquants.csv",
                            "text/csv",
                            key='download-missing-brooks'
                        )

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
