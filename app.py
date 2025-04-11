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

#### --- Fonctions modifiées pour afficher les colonnes spécifiques ---
def display_supplier_info(df, fournisseur):
    colonnes_affichier = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    fournisseur = fournisseur.strip().upper()
    df['fournisseur'] = df['fournisseur'].fillna('')
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame(columns=colonnes_affichier)
    return df_filtered[colonnes_affichier]


def display_designation_info(df, designation):
    # Colonnes à afficher
    colonnes_a_afficher = ['barcode', 'taille', 'designation', 'Qté stock dispo']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    
    # Filtre sur la désignation
    df_filtered = df[df['designation'].str.upper() == designation] if designation else pd.DataFrame(columns=colonnes_a_afficher)

    # Fonction de normalisation complète
    def normalize_size(size):
        if pd.isna(size):
            return ''
            
        size_str = str(size).strip().upper()
        
        # Détection du type de taille
        is_us = 'US' in size_str
        is_uk = 'UK' in size_str
        suffix = 'US' if is_us else 'UK' if is_uk else ''
        
        # Nettoyage de la chaîne
        clean_size = size_str.replace('US', '').replace('UK', '').strip()
        
        # Gestion des formats complexes
        if clean_size.replace('.', '').isdigit():
            # Cas numérique (5, 05, 5.5, etc.)
            if '.' in clean_size:
                int_part, dec_part = clean_size.split('.')
                int_part = int_part.lstrip('0') or '0'
                clean_size = f"{int_part}.{dec_part}"
            else:
                clean_size = clean_size.lstrip('0') or '0'
        elif '-' in clean_size:
            # Cas des intervalles (ex: 40-41)
            parts = clean_size.split('-')
            normalized_parts = []
            for part in parts:
                part = part.strip().lstrip('0') or '0'
                normalized_parts.append(part)
            clean_size = '-'.join(normalized_parts)
        elif any(x in clean_size for x in ['/', ',']):
            # Cas des tailles multiples (ex: 5/6 ou 5,6)
            separator = '/' if '/' in clean_size else ','
            parts = clean_size.split(separator)
            normalized_parts = []
            for part in parts:
                part = part.strip().lstrip('0') or '0'
                normalized_parts.append(part)
            clean_size = separator.join(normalized_parts)
        else:
            # Autres cas (conservés tels quels)
            clean_size = clean_size.lstrip('0') or clean_size
        
        return f"{clean_size}{suffix}" if suffix else clean_size

    # Application de la normalisation
    if 'taille' in df_filtered.columns:
        df_filtered['taille_normalisee'] = df_filtered['taille'].apply(normalize_size)
        df_filtered['taille_affichage'] = df_filtered['taille'].apply(lambda x: str(x).strip().upper())

    # Affichage du stock actuel
    st.dataframe(df_filtered[colonnes_a_afficher])

    # Tableau récapitulatif par taille
    if not df_filtered.empty:
        sum_by_size = df_filtered.groupby('taille_normalisee')['Qté stock dispo'].sum().reset_index()
        sum_by_size.columns = ['Taille', 'Quantité']
        
        # Tri intelligent
        def sort_key(size):
            try:
                # Extraction numérique
                num_part = ''.join(c for c in size.split()[0] if c.isdigit() or c == '.')
                num = float(num_part) if num_part else 0
                # Type de taille
                suffix = 'US' if 'US' in size else 'UK' if 'UK' in size else 'NUM'
                return (suffix, num)
            except:
                return ('', 0)
        
        sum_by_size['sort_key'] = sum_by_size['Taille'].apply(sort_key)
        sum_by_size = sum_by_size.sort_values('sort_key').drop('sort_key', axis=1)
        
        st.subheader("Résumé par taille")
        st.dataframe(
            sum_by_size.style.applymap(
                lambda x: 'background-color: #FFCDD2' if x == 1 else 
                         'background-color: #C8E6C9' if x > 1 else '',
                subset=['Quantité']
            )
        )

    # Génération des tailles attendues
    def generate_expected_sizes():
        sizes = []
        
        # Tailles numériques simples
        for num in range(1, 50):
            sizes.extend([f"{num}", f"{num}.0", f"{num}.5", f"0{num}", f"0{num}.0"])
        
        # Tailles US/UK
        for num in range(1, 20):
            sizes.extend([
                f"{num}US", f"{num}.0US", f"{num}.5US",
                f"{num}UK", f"{num}.0UK", f"{num}.5UK",
                f"0{num}US", f"0{num}.0US"
            ])
        
        # Tailles spéciales
        special_sizes = [
            'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL',
            '36-37', '38-39', '40-41', '42-43', '44-45',
            '5/6', '7/8', '9/10', '11/12'
        ]
        sizes.extend(special_sizes)
        
        return sorted(list(set(sizes)), key=lambda x: (len(x), x))

    # Détection des tailles manquantes
    expected_sizes = generate_expected_sizes()
    available_sizes = set(df_filtered['taille_normalisee'].unique()) if 'taille_normalisee' in df_filtered.columns else set()
    
    missing_sizes = []
    for size in expected_sizes:
        normalized = normalize_size(size)
        if normalized not in available_sizes:
            # Formatage pour l'affichage
            display_size = size
            if size.endswith('US'):
                display_size = f"{size[:-2]} (US)"
            elif size.endswith('UK'):
                display_size = f"{size[:-2]} (UK)"
            missing_sizes.append(display_size)

    # Affichage unifié des tailles manquantes
    st.subheader("Tailles manquantes")
    
    if missing_sizes:
        # Regroupement par type de taille
        missing_data = []
        for size in missing_sizes:
            if '(US)' in size:
                typ = 'US'
            elif '(UK)' in size:
                typ = 'UK'
            elif any(x in size for x in ['-', '/', ',']):
                typ = 'Spécial'
            elif '.' in size:
                typ = 'Demi-taille'
            else:
                typ = 'Standard'
            
            missing_data.append({'Taille': size, 'Type': typ})
        
        missing_df = pd.DataFrame(missing_data)
        
        # Tri et affichage
        type_order = ['Standard', 'Demi-taille', 'US', 'UK', 'Spécial']
        missing_df['Type'] = pd.Categorical(missing_df['Type'], categories=type_order, ordered=True)
        missing_df = missing_df.sort_values(['Type', 'Taille'])
        
        st.dataframe(
            missing_df,
            column_config={
                "Taille": "Taille manquante",
                "Type": "Catégorie"
            },
            hide_index=True,
            use_container_width=True,
            height=min(600, 35 * len(missing_df))
    else:
        st.success("✔ Toutes les tailles sont disponibles")
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

        # # Affichage des tailles indisponibles
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

#### --- CSS Personnalisé pour un style moderne (Material Design) ---
st.markdown(
    """
    <style>
    /* --- Importation de la police Roboto (Google Fonts) --- */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    /* --- Styles globaux --- */
    body {
        font-family: 'Roboto', sans-serif;
        background-color: # #f5f5f5; /* Gris très clair */
    }

    /* --- Titres --- */
    h1, h2, h3 {
        color: # #212121; /* Gris foncé */
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
        border-bottom: 1px solid # #EEEEEE; /* Gris très clair */
    }
    th {
        font-weight: bold;
    }

    /* --- Messages d'état --- */
    .st-success {
        color: # #448a50; /* Vert */
    }
    .st-warning {
        color: # #f0ad4e; /* Orange */
    }
    .st-error {
        color: # #d9534f; /* Rouge */
    }

    /* --- Onglets (style Material Design) --- */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid # #EEEEEE; /* Gris très clair */
    }
    .stTabs [data-baseweb="tab-list"] button {
        background-color: transparent;
        border: none;
        color: # #757575; /* Gris moyen */
        font-size: 16px;
        margin-right: 32px;
        padding: 12px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        color: # #212121; /* Gris foncé */
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: # #2196f3; /* Bleu Material Design */
        border-bottom: 2px solid # #2196f3; /* Bleu Material Design */
    }

    /* --- Boutons --- */
    .stButton>button {
        background-color: # #2196f3; /* Bleu Material Design */
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: # #1976d2; /* Bleu Material Design plus foncé */
    }

    /* --- Autres éléments --- */
    .stSelectbox [data-baseweb="select"] {
        padding: 8px 12px;
        border-radius: 4px;
        border: 1px solid # #bdbdbd; /* Gris clair */
    }
    </style>
    """,
    unsafe_allow_html=True
)

#### --- Interface principale de l'application ---
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

                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Filtrer par Fournisseur",
                                                                    "Filtrer par Désignation",
                                                                    "Stock Négatif",
                                                                    "Anita Tailles",
                                                                    "Sidas Niveaux",
                                                                    "Valeur Totale du Stock par Fournisseur",
                                                                    "Stock par Famille"])

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
                        st.dataframe(df_level.style.apply(highlight_row_if_one, axis=1))  # # Appliquer le style ici

                with tab6:
                    st.subheader("Valeur Totale du Stock par Fournisseur")
                    df_total_value_by_supplier = total_stock_value_by_supplier(df)
                    st.dataframe(df_total_value_by_supplier)
                    total_value = df_total_value_by_supplier['Valeur Totale HT'].sum()
                    st.markdown(f"Valeur Totale du Stock pour tous les fournisseurs : {total_value:.2f}")

                with tab7:
                    st.header("Stock par Famille")
                    display_stock_by_family(df)

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
