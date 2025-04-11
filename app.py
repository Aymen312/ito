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
    # Colonnes à afficher dans le tableau principal
    colonnes_a_afficher = ['barcode', 'taille', 'rayon', 'designation', 'Qté stock dispo']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    
    # Filtre exact sur la désignation
    df_filtered = df[df['designation'].str.upper() == designation] if designation else pd.DataFrame(columns=colonnes_a_afficher)

    # Normalisation des tailles
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

    # Calculer la somme des quantités par taille et rayon
    sum_by_size = pd.DataFrame()
    if not df_filtered.empty and 'taille_normalisee' in df_filtered.columns:
        # Convertir en numérique pour un tri correct
        df_filtered['taille_num'] = pd.to_numeric(df_filtered['taille_normalisee'], errors='coerce')
        # Somme par taille et rayon
        sum_by_size = df_filtered.groupby(['taille_normalisee', 'rayon'])['Qté stock dispo'].sum().reset_index()
        sum_by_size.columns = ['Taille', 'Rayon', 'Total Qté dispo']
        # Trier par taille numérique croissante
        sum_by_size['taille_num'] = pd.to_numeric(sum_by_size['Taille'], errors='coerce')
        sum_by_size = sum_by_size.sort_values('taille_num')
        sum_by_size = sum_by_size.drop(columns=['taille_num'])

    # Fonction de mise en forme conditionnelle
    def highlight_row_if_one(row):
        if 'taille_normalisee' in row and row['taille_normalisee'] in sum_by_size['Taille'].values:
            mask = (sum_by_size['Taille'] == row['taille_normalisee']) 
            if 'rayon' in sum_by_size.columns:
                mask &= (sum_by_size['Rayon'] == row['rayon'])
            total = sum_by_size.loc[mask, 'Total Qté dispo'].values[0] if any(mask) else 0
            if total == 1:
                return ['background-color: red'] * len(row)
        return [''] * len(row)

    # --- Affichage du tableau principal ---
    if not df_filtered.empty and 'taille_num' in df_filtered.columns:
        df_filtered = df_filtered.sort_values('taille_num')
    st.dataframe(df_filtered[colonnes_a_afficher].style.apply(highlight_row_if_one, axis=1))

    # --- Affichage des sommes par taille et rayon ---
    if not sum_by_size.empty:
        # Séparer les données par rayon
        sum_homme = sum_by_size[sum_by_size['Rayon'] == 'HOMME']
        sum_femme = sum_by_size[sum_by_size['Rayon'] == 'FEMME']

        # Fonction de style conditionnel
        def highlight_total_if_one(val):
            color = 'red' if val == 1 else ''
            return f'background-color: {color}'

        # Afficher les tableaux séparés
        if not sum_homme.empty:
            st.subheader("Somme des quantités disponibles par taille - Rayon HOMME")
            styled_homme = sum_homme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo'])
            st.dataframe(styled_homme)

        if not sum_femme.empty:
            st.subheader("Somme des quantités disponibles par taille - Rayon FEMME")
            styled_femme = sum_femme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo'])
            st.dataframe(styled_femme)

    # --- Tailles possibles ---
    specific_designations = [
        'PRODIGIO', 'PRODIGIO WOMAN', 'AKASHA II', 'AKASHA II WOMAN', 'JACKAL',
        'ULTRA RAPTOR II MID LEATHER GTX', 'ULTRA RAPTOR II MID GTX',
        'ULTRA RAPTOR II LEATHER W GTX', 'ULTRA RAPTOR II LEATHER WOMAN',
        'ULTRA RAPTOR II GTX', 'AKASHA'
    ]

    possible_sizes_us = []
    possible_sizes_uk = []

    if any(desig in designation for desig in specific_designations):
        for size in range(36, 48):
            possible_sizes_us.append(f'{size}')
            possible_sizes_us.append(f'0{size}')
            possible_sizes_us.append(f'{size}.0')
            possible_sizes_us.append(f'0{size}.0')
            if size != 47:
                possible_sizes_us.append(f'{size}.5')
                possible_sizes_us.append(f'0{size}.5')
    else:
        # Tailles pour femme (US 4-10, UK 3-10)
        if 'FEMME' in df_filtered['rayon'].unique():
            for size in ['4', '5', '6', '7', '8', '9', '10']:
                possible_sizes_us.append(f'{size}.0US')
                possible_sizes_us.append(f'0{size}.0US')
                possible_sizes_us.append(f'{size}.5US')
                possible_sizes_us.append(f'0{size}.5US')
            for size in ['3', '4', '5', '6', '7', '8', '9', '10']:
                possible_sizes_uk.append(f'{size}.0UK')
                possible_sizes_uk.append(f'0{size}.0UK')
                possible_sizes_uk.append(f'{size}.5UK')
                possible_sizes_uk.append(f'0{size}.5UK')
        
        # Tailles pour homme (US 4-14, UK 4-12)
        if 'HOMME' in df_filtered['rayon'].unique():
            for size in ['4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14']:
                possible_sizes_us.append(f'{size}.0US')
                possible_sizes_us.append(f'0{size}.0US')
                if size != '14':  # Pas de demi-taille pour 14
                    possible_sizes_us.append(f'{size}.5US')
                    possible_sizes_us.append(f'0{size}.5US')
            for size in ['4', '5', '6', '7', '8', '9', '10', '11', '12']:
                possible_sizes_uk.append(f'{size}.0UK')
                possible_sizes_uk.append(f'0{size}.0UK')
                if size != '12':  # Pas de demi-taille pour 12 UK
                    possible_sizes_uk.append(f'{size}.5UK')
                    possible_sizes_uk.append(f'0{size}.5UK')

    # --- Tailles indisponibles par rayon (version simplifiée) ---
    st.subheader("Tailles MAX indisponibles par rayon:")
    
    # Séparer les tailles disponibles par rayon
    available_sizes_homme = df_filtered[df_filtered['rayon'] == 'HOMME']['taille_normalisee'].unique() if 'taille_normalisee' in df_filtered.columns else []
    available_sizes_femme = df_filtered[df_filtered['rayon'] == 'FEMME']['taille_normalisee'].unique() if 'taille_normalisee' in df_filtered.columns else []

    def filter_sizes_by_range(sizes, size_range):
        """Filtre les tailles pour ne garder que celles dans la plage spécifiée"""
        filtered = []
        for size in sizes:
            # Extraire la partie numérique de la taille
            clean_size = size.replace('US', '').replace('UK', '').replace('0', '').strip('.')
            try:
                num_size = float(clean_size)
                if size_range[0] <= num_size <= size_range[1]:
                    filtered.append(size)
            except ValueError:
                continue
        return filtered

    def find_max_unavailable_size(possible_sizes, available_normalized, size_range):
        # Filtrer les tailles possibles selon la plage
        possible_sizes_filtered = filter_sizes_by_range(possible_sizes, size_range)
        
        # Identifier les tailles canoniques (sans doublons de format)
        canonical_sizes = set()
        for size in possible_sizes_filtered:
            # Nettoyer la taille pour la comparaison
            clean_size = size.replace('US', '').replace('UK', '').replace('0', '').strip('.')
            canonical_sizes.add(clean_size)
        
        # Convertir en numérique et trouver le max des tailles indisponibles
        numeric_unavailable = []
        for size in canonical_sizes:
            normalized = normalize_size(size)
            if normalized not in available_normalized:
                try:
                    numeric_unavailable.append(float(size))
                except:
                    continue
        
        return max(numeric_unavailable) if numeric_unavailable else None

    # Calcul des tailles max indisponibles
    max_unavailable = {
        'HOMME': {
            'US': find_max_unavailable_size(possible_sizes_us, available_sizes_homme, (4, 14)),
            'UK': find_max_unavailable_size(possible_sizes_uk, available_sizes_homme, (4, 12))
        },
        'FEMME': {
            'US': find_max_unavailable_size(possible_sizes_us, available_sizes_femme, (4, 10)),
            'UK': find_max_unavailable_size(possible_sizes_uk, available_sizes_femme, (3, 10))
        }
    }

    # Affichage des résultats
    tab1, tab2 = st.tabs(["HOMME", "FEMME"])
    
    with tab1:
        st.subheader("Rayon HOMME")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Taille US max indisponible (4-14):")
            st.write(max_unavailable['HOMME']['US'] or "Toutes disponibles")
        with col2:
            st.write("Taille UK max indisponible (4-12):")
            st.write(max_unavailable['HOMME']['UK'] or "Toutes disponibles")
    
    with tab2:
        st.subheader("Rayon FEMME")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Taille US max indisponible (4-10):")
            st.write(max_unavailable['FEMME']['US'] or "Toutes disponibles")
        with col2:
            st.write("Taille UK max indisponible (3-10):")
            st.write(max_unavailable['FEMME']['UK'] or "Toutes disponibles")
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

# --- CONFIGURATION (DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT) ---
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
    table { width: 100%; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    th, td { padding: 12px 16px; border-bottom: 1px solid #EEE; }
    .stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #EEE; }
    .stButton>button { background-color: #2196f3; color: white; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS DE BASE ---
def clean_numeric_columns(df):
    numeric_cols = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def highlight_row_if_one(row):
    return ['background-color: red' if row['Qté stock dispo'] == 1 else '' for _ in row]

# --- FONCTIONS D'AFFICHAGE ---
def display_supplier_info(df, fournisseur):
    cols = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 
            'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    df['fournisseur'] = df['fournisseur'].fillna('')
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur.strip().upper()]
    return df_filtered[cols] if not df_filtered.empty else pd.DataFrame(columns=cols)

def normalize_size(size):
    if pd.isna(size): return ''
    size_str = str(size).strip()
    if '.' in size_str:
        int_part, dec_part = size_str.split('.', 1)
        return f"{int_part.lstrip('0') or '0'}.{dec_part}"
    return size_str.lstrip('0') or '0'

def display_designation_info(df, designation):
    main_cols = ['barcode', 'taille', 'rayon', 'designation', 'Qté stock dispo']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    df_filtered = df[df['designation'].str.upper() == designation] if designation else pd.DataFrame()
    
    if not df_filtered.empty and 'taille' in df_filtered.columns:
        df_filtered['taille_normalisee'] = df_filtered['taille'].apply(normalize_size)
        df_filtered['taille_num'] = pd.to_numeric(df_filtered['taille_normalisee'], errors='coerce')
        sum_by_size = df_filtered.groupby(['taille_normalisee', 'rayon'])['Qté stock dispo'].sum().reset_index()
        sum_by_size.columns = ['Taille', 'Rayon', 'Total Qté dispo']
        
        # Affichage principal
        st.dataframe(df_filtered[main_cols].style.apply(highlight_row_if_one, axis=1))
        
        # Affichage des sommes par rayon
        for rayon in ['HOMME', 'FEMME']:
            rayon_sum = sum_by_size[sum_by_size['Rayon'] == rayon]
            if not rayon_sum.empty:
                st.subheader(f"Stock total - Rayon {rayon}")
                st.dataframe(rayon_sum[['Taille', 'Total Qté dispo']].style.applymap(
                    lambda x: 'background-color: red' if x == 1 else '', subset=['Total Qté dispo']))

def filter_negative_stock(df):
    cols = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 
            'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0)
    return df[df['Qté stock dispo'] < 0][cols]

def display_anita_sizes(df):
    df_anita = df[df['fournisseur'].str.upper() == "ANITA"]
    tailles = [f"{num}{letter}" for num in [85, 90, 95, 100, 105, 110] for letter in 'ABCDEF']
    return df_anita[df_anita['taille'].isin(tailles)].groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)

def display_sidas_levels(df):
    df_sidas = df[df['fournisseur'].str.upper().str.contains("SIDAS")].dropna(subset=['couleur', 'taille'])
    results = {}
    for level in ['LOW', 'MID', 'HIGH']:
        df_level = df_sidas[df_sidas['couleur'].str.upper() == level]
        results[level] = df_level[df_level['taille'].isin(['XS', 'S', 'M', 'L', 'XL', 'XXL']]
    return results

def total_stock_value_by_supplier(df):
    df['Valeur Totale HT'] = df['Qté stock dispo'] * df['Prix Achat']
    return df.groupby('fournisseur')['Valeur Totale HT'].sum().sort_values(ascending=False).reset_index()

# --- INTERFACE PRINCIPALE ---
st.title("📊 Application d'Analyse TDR")
st.sidebar.header("Menu")

uploaded_file = st.sidebar.file_uploader("Télécharger fichier", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        with st.spinner("Traitement en cours..."):
            df = pd.read_csv(uploaded_file, encoding='ISO-8859-1', sep=';') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            df = clean_numeric_columns(clean_size_column(df))
            
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "🔍 Fournisseur", 
                "📝 Désignation", 
                "⚠ Stock Négatif", 
                "👙 Anita", 
                "🧦 Sidas", 
                "💰 Valeur Stock"
            ])

            with tab1:
                supplier = st.text_input("Nom du fournisseur:")
                st.dataframe(display_supplier_info(df, supplier).style.apply(highlight_row_if_one, axis=1))

            with tab2:
                product = st.text_input("Désignation produit:")
                display_designation_info(df, product)

            with tab3:
                st.dataframe(filter_negative_stock(df).style.apply(highlight_row_if_one, axis=1))

            with tab4:
                st.dataframe(display_anita_sizes(df))

            with tab5:
                for level, data in display_sidas_levels(df).items():
                    st.subheader(f"Niveau {level}")
                    st.dataframe(data)

            with tab6:
                st.dataframe(total_stock_value_by_supplier(df))
                st.metric("Valeur totale du stock", f"{total_stock_value_by_supplier(df)['Valeur Totale HT'].sum():,.2f} €")

    except Exception as e:
        st.error(f"Erreur: {str(e)}")
else:
    st.info("Veuillez télécharger un fichier pour commencer l'analyse")
