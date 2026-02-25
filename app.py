import streamlit as st
import pandas as pd
from io import BytesIO
import numpy as np
import re

#### --- Configuration de l'application Streamlit ---
st.set_page_config(
    page_title="Ayada TDR",
    layout="wide",
    initial_sidebar_state="expanded"
)

#### --- CSS Personnalisé (Style SaaS Moderne) ---
st.markdown(
    """
    <style>
    /* --- Importation de la police Inter --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* --- Styles globaux --- */
    html, body,[class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #F8FAFC; /* Gris très clair/bleuté façon Tailwind */
    }

    /* --- Titres --- */
    h1, h2, h3 {
        color: #0F172A;
        font-weight: 700;
        letter-spacing: -0.025em;
    }

    /* --- Sidebar --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
        box-shadow: 2px 0 8px rgba(0,0,0,0.02);
    }

    /* --- Onglets (Tabs) --- */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #FFFFFF;
        padding: 4px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 16px;
        border-radius: 8px !important;
        border: none !important;
        color: #64748B;
        font-weight: 500;
        background-color: transparent;
        transition: all 0.2s ease-in-out;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #0F172A;
        background-color: #F1F5F9;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3B82F6 !important; /* Bleu moderne */
        color: #FFFFFF !important;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }

    /* --- Boutons globaux --- */
    .stButton>button {
        background-color: #0F172A;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #334155;
        transform: translateY(-1px);
        box-shadow: 0 6px 8px -1px rgba(0, 0, 0, 0.15);
        color: white !important;
    }

    /* --- Inputs et Selectboxes --- */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
        padding: 8px 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }

    /* --- Expanders --- */
    [data-testid="stExpander"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* --- File Uploader --- */[data-testid="stFileUploadDropzone"] {
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        background-color: #FFFFFF;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #3B82F6;
        background-color: #EFF6FF;
    }
    
    /* --- Tableaux HTML (ex: markdown) --- */
    table {
        border-collapse: collapse;
        width: 100%;
        background-color: white;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
        overflow: hidden;
    }
    th { background-color: #0F172A; color: white; }
    th, td { padding: 12px 16px; border-bottom: 1px solid #E2E8F0; }
    </style>
    """,
    unsafe_allow_html=True
)

#### --- Fonctions pour le traitement des données ---
def clean_numeric_columns(df):
    numeric_columns =['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def highlight_row_if_one(row):
    """Met en surbrillance la ligne en rouge si 'Qté stock dispo' est égale à 1."""
    if row['Qté stock dispo'] == 1:
        return['background-color: #FEE2E2; color: #991B1B' for _ in row] # Rouge doux
    else:
        return[''] * len(row)

#### --- Fonctions modifiées pour afficher les colonnes spécifiques ---
def display_supplier_info(df, fournisseur):
    colonnes_afficher =['fournisseur', 'barcode', 'couleur', 'taille', 'designation',
                         'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    fournisseur = fournisseur.strip().upper()
    df['fournisseur'] = df['fournisseur'].fillna('')
    
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame(columns=colonnes_afficher)
    
    if not df_filtered.empty:
        designations_rayons = df_filtered.groupby(['designation', 'rayon']).size().reset_index(name='Nombre de références')
        designations_rayons = designations_rayons.sort_values(['designation', 'rayon'])
        
        with st.expander(f"Désignations disponibles pour {fournisseur}", expanded=True):
            designations_rayons['selection'] = designations_rayons.apply(
                lambda x: f"{x['designation']} ({x['rayon']})", axis=1)
            
            selected = st.selectbox(
                "Sélectionnez une désignation pour voir les tailles manquantes",
                designations_rayons['selection']
            )
            
            selected_design, selected_rayon = selected.split(" (")
            selected_rayon = selected_rayon[:-1]
            
            filtered = df_filtered[
                (df_filtered['designation'] == selected_design) & 
                (df_filtered['rayon'] == selected_rayon)
            ]
            
            if selected_rayon.upper() == 'FEMME':
                expected_sizes =[round(x*0.5, 1) for x in range(10, 21)]
            elif selected_rayon.upper() == 'HOMME':
                expected_sizes =[round(x*0.5, 1) for x in range(14, 29)]
            else:
                existing_sizes = filtered['taille'].unique()
                expected_sizes = sorted([float(x.replace(',', '.')) for x in existing_sizes if str(x).replace('.', '').isdigit()])
            
            def extract_size_value(size_str):
                try:
                    cleaned = str(size_str).upper().replace('US', '').strip()
                    cleaned = cleaned.replace(',', '.')
                    if '.' in cleaned:
                        int_part, dec_part = cleaned.split('.', 1)
                        int_part = int_part.lstrip('0') or '0'
                        cleaned = f"{int_part}.{dec_part}"
                    else:
                        cleaned = cleaned.lstrip('0') or '0'
                    return float(cleaned)
                except:
                    return None
            
            size_qtys = {}
            size_mapping = {}
            
            for _, row in filtered.iterrows():
                size = row['taille']
                qty = row['Qté stock dispo']
                size_value = extract_size_value(size)
                
                if size_value is not None:
                    if size_value not in size_qtys:
                        size_qtys[size_value] = 0
                        size_mapping[size_value] = str(size)
                    size_qtys[size_value] += qty
                else:
                    if size not in size_qtys:
                        size_qtys[size] = 0
                    size_qtys[size] += qty
            
            if selected_rayon.upper() in ['FEMME', 'HOMME']:
                missing_sizes =[]
                for expected in expected_sizes:
                    expected_float = float(expected)
                    if expected_float not in[s for s in size_qtys.keys() if isinstance(s, float)]:
                        missing_sizes.append(str(expected))
            else:
                missing_sizes =[]
            
            st.markdown(f"**Tailles disponibles pour {selected_design} ({selected_rayon}):**")
            
            display_sizes =[]
            for size in sorted(size_qtys.keys()):
                qty = size_qtys[size]
                display_size = size_mapping.get(size, str(size))
                display_text = f"{display_size} ({qty})"
                
                if qty == 1:
                    display_text = f"<span style='color:#DC2626; font-weight:bold;'>{display_text}</span>"
                display_sizes.append(display_text)
            
            st.markdown(", ".join(display_sizes), unsafe_allow_html=True)
            
            if missing_sizes:
                st.markdown(f"**Tailles manquantes ({selected_rayon}):**")
                st.info(", ".join(missing_sizes))
            else:
                st.success("Toutes les tailles attendues sont disponibles.")
    
    return df_filtered[colonnes_afficher]

def display_designation_info(df, designation):
    colonnes_a_afficher =['barcode', 'taille', 'rayon', 'couleur', 'designation', 'Qté stock dispo']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    
    df_filtered = df[df['designation'].str.upper() == designation] if designation else pd.DataFrame(columns=colonnes_a_afficher)

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

    if 'taille' in df_filtered.columns:
        df_filtered['taille_normalisee'] = df_filtered['taille'].apply(normalize_size)

    sum_by_size = pd.DataFrame()
    if not df_filtered.empty and 'taille_normalisee' in df_filtered.columns:
        df_filtered['taille_num'] = pd.to_numeric(df_filtered['taille_normalisee'], errors='coerce')
        sum_by_size = df_filtered.groupby(['taille_normalisee', 'rayon'])['Qté stock dispo'].sum().reset_index()
        sum_by_size.columns = ['Taille', 'Rayon', 'Total Qté dispo']
        sum_by_size['taille_num'] = pd.to_numeric(sum_by_size['Taille'], errors='coerce')
        sum_by_size = sum_by_size.sort_values('taille_num').drop(columns=['taille_num'])

    def highlight_row_if_one_cond(row):
        if 'taille_normalisee' in row and row['taille_normalisee'] in sum_by_size['Taille'].values:
            mask = (sum_by_size['Taille'] == row['taille_normalisee']) 
            if 'rayon' in sum_by_size.columns:
                mask &= (sum_by_size['Rayon'] == row['rayon'])
            total = sum_by_size.loc[mask, 'Total Qté dispo'].values[0] if any(mask) else 0
            if total == 1:
                return['background-color: #FEE2E2; color: #991B1B'] * len(row)
        return [''] * len(row)

    if not df_filtered.empty and 'taille_num' in df_filtered.columns:
        df_filtered = df_filtered.sort_values('taille_num')
    st.dataframe(df_filtered[colonnes_a_afficher].style.apply(highlight_row_if_one_cond, axis=1), use_container_width=True)

    if not sum_by_size.empty:
        sum_homme = sum_by_size[sum_by_size['Rayon'] == 'HOMME']
        sum_femme = sum_by_size[sum_by_size['Rayon'] == 'FEMME']

        def highlight_total_if_one(val):
            return 'background-color: #FEE2E2; color: #991B1B' if val == 1 else ''

        col1, col2 = st.columns(2)
        if not sum_homme.empty:
            with col1:
                st.subheader("Somme par taille - HOMME")
                styled_homme = sum_homme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo'])
                st.dataframe(styled_homme, use_container_width=True)

        if not sum_femme.empty:
            with col2:
                st.subheader("Somme par taille - FEMME")
                styled_femme = sum_femme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo'])
                st.dataframe(styled_femme, use_container_width=True)

def filter_negative_stock(df):
    colonnes_affichier =['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0)
    df_filtered = df[df['Qté stock dispo'] < 0]
    return df_filtered[colonnes_affichier]

def display_anita_sizes(df):
    df_anita = df[df['fournisseur'].str.upper() == "ANITA"]
    tailles =[f"{num}{letter}" for num in[85, 90, 95, 100, 105, 110] for letter in 'ABCDEF']
    df_anita_sizes = df_anita[df_anita['taille'].isin(tailles)]
    df_anita_sizes = df_anita_sizes.groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)
    df_anita_sizes = df_anita_sizes.replace(0, "Nul")
    return df_anita_sizes

def display_sidas_levels(df):
    df['fournisseur'] = df['fournisseur'].fillna('')
    df = df.dropna(subset=['couleur', 'taille'])
    df_sidas = df[df['fournisseur'].str.upper().str.contains("SIDAS")]
    levels = ['LOW', 'MID', 'HIGH']
    sizes =['XS', 'S', 'M', 'L', 'XL', 'XXL']
    results = {}
    for level in levels:
        df_sidas_level = df_sidas[df_sidas['couleur'].str.upper() == level]
        df_sizes = df_sidas_level[df_sidas_level['taille'].isin(sizes)]
        df_sizes_grouped = df_sizes.groupby(['taille', 'designation'])['Qté stock dispo'].sum().unstack(fill_value=0)
        df_sizes_grouped = df_sizes_grouped.replace(0, "Nul")
        df_sizes_with_designation = df_sizes_grouped.stack().reset_index().rename(columns={0: 'Qté stock dispo'})
        results[level] = df_sizes_with_designation

        available_sizes = df_sidas_level['taille'].unique()
        unavailable_sizes =[size for size in sizes if size not in available_sizes]
        if unavailable_sizes:
            st.warning(f"Tailles indisponibles pour SIDAS niveau {level}: {', '.join(unavailable_sizes)}")
        else:
            st.success(f"Toutes les tailles SIDAS niveau {level} sont en stock.")

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
                                                       key=lambda x: (int(x[:-1]), x[-1]) if str(x)[:-1].isdigit() else (
                                                           float('inf'), x)),
                                     ordered=True)
    df = df.sort_values('taille')
    return df

def display_stock_by_family(df):
    familles =["CHAUSSURES RANDO", "CHAUSSURES RUNN", "CHAUSSURE TRAIL"]
    for famille in familles:
        st.subheader(f"Catégorie : {famille}")
        df['famille'] = df['famille'].fillna('')
        df_family = df[df['famille'].str.upper() == famille]
        
        if 'Valeur Stock' not in df_family.columns or df_family['Valeur Stock'].isnull().all():
             df_family['Valeur Stock'] = df_family['Qté stock dispo'] * df_family.get('Prix Achat', 0)

        total_stock = df_family['Qté stock dispo'].sum()
        total_stock_value = df_family['Valeur Stock'].sum()
        
        # --- Utilisation des KPIs modernes ---
        col1, col2 = st.columns(2)
        col1.metric("Qté dispo totale", f"{int(total_stock)}")
        col2.metric("Valeur totale du stock HT", f"{total_stock_value:,.2f} €".replace(',', ' '))

        rayon_options = ['Tous', 'Homme', 'Femme', 'Autre']
        rayon_filter = st.selectbox(f"Filtrer par Rayon pour {famille}:", options=rayon_options, key=f"rayon_{famille}")

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
            st.dataframe(df_family[['rayon', 'fournisseur', 'couleur', 'taille', 'designation', 'marque', 'ssfamille',
                              'Qté stock dispo', 'Valeur Stock']].style.apply(highlight_row_if_one, axis=1), use_container_width=True)
        else:
            st.info(f"Aucune information disponible pour {famille} dans le rayon {rayon_filter}.")
        
        st.markdown("---")

def display_specific_designations(df):
    import re
    brand_col = "marque" if "marque" in df.columns else "fournisseur"

    for c in[brand_col, "designation", "taille", "famille", "ssfamille", "rayon"]:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].fillna("").astype(str)

    shoe_mask = (
        df["famille"].str.upper().str.contains("CHAUSS", na=False) |
        df["ssfamille"].str.upper().str.contains("CHAUSS", na=False) |
        df["designation"].str.upper().str.contains(r"RUN|TRAIL|RANDO|CHAUSS|SHOE", na=False)
    )
    df_shoes = df[shoe_mask].copy()
    if df_shoes.empty:
        df_shoes = df.copy()

    preferred =["ASICS", "BROOKS", "HOKA", "LA SPORTIVA", "MIZUNO", "NEW BALANCE", "SALOMON", "SAUCONY"]

    brands_series = df_shoes[brand_col].str.upper().str.strip()
    brand_counts = brands_series.value_counts()

    brands = [b for b in preferred if b in brand_counts.index]
    if not brands:
        brands = brand_counts.head(12).index.tolist()

    suppliers = {}
    for b in brands:
        desigs = df_shoes.loc[brands_series == b, "designation"].astype(str).str.strip()
        desigs =[d for d in sorted(desigs.unique()) if d]
        suppliers[b] = desigs

    def normalize_size(size):
        if pd.isna(size): return ""
        s = str(size).upper().strip()
        s = s.replace(",", ".")
        s = re.sub(r"\b(US|UK|EU)\b", "", s).strip()
        s = re.sub(r"\s+", " ", s)

        if re.fullmatch(r"\d+[A-Z]", s): return s

        def format_half(v):
            rounded = round(float(v) * 2) / 2
            return f"{rounded:.1f}"

        unicode_frac = {
            "½": (1, 2), "⅓": (1, 3), "⅔": (2, 3),
            "¼": (1, 4), "¾": (3, 4), "⅙": (1, 6), "⅚": (5, 6),
        }

        for symb, (num, den) in unicode_frac.items():
            if symb in s:
                base_match = re.search(r"(\d+(\.\d+)?)", s.replace(symb, ""))
                base = float(base_match.group(1)) if base_match else 0.0
                v = base + (num / den)
                return format_half(v)

        m = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)$", s)
        if m:
            whole = int(m.group(1))
            num = int(m.group(2))
            den = int(m.group(3)) if int(m.group(3)) != 0 else 1
            v = whole + (num / den)
            return format_half(v)

        m = re.search(r"(\d+(\.\d+)?)", s)
        if m:
            v = float(m.group(1))
            return format_half(v)

        return s

    cols = st.columns(4) # Changé en 4 colonnes pour un rendu plus compact
    for i, supplier in enumerate(sorted(suppliers.keys())):
        with cols[i % 4]:
            if st.button(supplier, key=f"btn_{supplier}"):
                st.session_state.selected_supplier = supplier

    if 'selected_supplier' in st.session_state:
        supplier = st.session_state.selected_supplier
        designations = suppliers[supplier]
        df_filtered = df[df['designation'].str.upper().isin([d.upper() for d in designations])].copy()
        
        if not df_filtered.empty:
            df_filtered['taille_normalisee'] = df_filtered['taille'].apply(normalize_size)

            results =[]
            for designation in sorted(designations):
                df_design = df_filtered[df_filtered['designation'].str.upper() == designation.upper()]
                is_woman = " W" in designation.upper() or "WOMAN" in designation.upper()
                expected_sizes =[]

                if supplier == "SALOMON":
                    if "AERO GLIDE 3 GRVL" in designation.upper():
                        sizes = list(range(4, 10)) if is_woman else list(range(6, 14))
                    else:
                        sizes = list(range(6, 14)) if is_woman else list(range(4, 10))
                    expected_sizes =[f"{x}.0" for x in sizes] + [f"{x}.5" for x in sizes if x != sizes[-1]]
                
                elif supplier == "LA SPORTIVA":
                    sizes = list(range(36, 43)) if is_woman else list(range(40, 49))
                    expected_sizes = [f"{x/2:.1f}" for x in range(sizes[0]*2, sizes[-1]*2+1)]
                
                elif supplier == "MIZUNO":
                    if is_woman:
                        sizes =[4.0, 4.5, 5.0, 5.5, 6.5, 7.0, 7.5, 8.0, 9.0]
                    else:
                        sizes =[6.0, 6.5, 7.0, 7.5, 8.0, 9.0, 10.0, 10.5, 11.0, 11.5, 12.0]
                    expected_sizes = [f"{s:.1f}" for s in sizes]
                
                elif supplier == "NEW BALANCE":
                    if "FUELCELL REBEL" in designation.upper():
                        sizes = list(range(7, 15))
                        expected_sizes =[f"{x}.0" for x in sizes] + [f"{x}.5" for x in sizes if x != sizes[-1] and x < 13]
                    else:
                        sizes = list(range(5, 11)) if is_woman else list(range(7, 15))
                        expected_sizes =[f"{x}.0" for x in sizes] + [f"{x}.5" for x in sizes if x != sizes[-1] and x < 13]
                
                else:
                    sizes = list(range(5, 11)) if is_woman else list(range(7, 15))
                    expected_sizes = [f"{x}.0" for x in sizes] +[f"{x}.5" for x in sizes if x != sizes[-1] and x < 13]

                available_sizes = df_design['taille_normalisee'].dropna().unique()
                missing_sizes =[size for size in expected_sizes if size not in available_sizes]

                results.append({
                    'Modèle': designation,
                    'Tailles disponibles': len(available_sizes),
                    'Tailles manquantes': ", ".join(missing_sizes) if missing_sizes else "Complet"
                })

            results_df = pd.DataFrame(results)
            
            st.markdown(f"### {supplier} - Stock disponible")
            st.dataframe(results_df, use_container_width=True) # Utilisation de dataframe pleine largeur
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        results_df.to_excel(writer, sheet_name=f"{supplier}_Stock", index=False)
                    st.download_button(
                        label="📊 Exporter en Excel (XLSX)",
                        data=output.getvalue(),
                        file_name=f"{supplier}_stock.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"Erreur Excel: {str(e)}")
            
            with col2:
                try:
                    csv = results_df.to_csv(index=False, sep=';')
                    st.download_button(
                        label="📄 Exporter en CSV",
                        data=csv,
                        file_name=f"{supplier}_stock.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Erreur CSV: {str(e)}")


#### --- Interface principale de l'application ---
st.title("Ayada TDR - Tableau de Bord Stock")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3081/3081840.png", width=50) # Petite icône optionnelle
st.sidebar.markdown("### Menu Principal")
st.sidebar.info("Téléchargez un fichier CSV ou Excel pour commencer l'analyse.")
fichier_telecharge = st.sidebar.file_uploader("📂 Fichier source", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        with st.spinner("Chargement et préparation des données..."):
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
                    "🏢 Fournisseur",
                    "🔍 Modèle",
                    "⚠️ Stock Négatif",
                    "👙 Anita",
                    "🦶 Sidas",
                    "💰 Valeur Stock",
                    "👟 Catégories",
                    "📊 Tailles Manquantes"
                ])

                with tab1:
                    fournisseur = st.text_input("Rechercher un fournisseur:")
                    df_filtered = display_supplier_info(df.copy(), fournisseur)
                    if not df_filtered.empty:
                        st.dataframe(df_filtered.style.apply(highlight_row_if_one, axis=1), use_container_width=True)
                    elif fournisseur:
                        st.warning("Aucune information disponible pour ce fournisseur.")

                with tab2:
                    designation = st.text_input("Rechercher un modèle exact:")
                    display_designation_info(df.copy(), designation)

                with tab3:
                    st.subheader("Produits en stock négatif")
                    st.dataframe(filter_negative_stock(df.copy()).style.apply(highlight_row_if_one, axis=1), use_container_width=True)

                with tab4:
                    st.subheader("Disponibilité Anita")
                    df_anita_sizes = display_anita_sizes(df)
                    st.dataframe(df_anita_sizes, use_container_width=True)

                with tab5:
                    st.subheader("Disponibilité Semelles Sidas")
                    sidas_results = display_sidas_levels(df)
                    for level, df_level in sidas_results.items():
                        st.markdown(f"**Niveau {level}**")
                        st.dataframe(df_level.style.apply(highlight_row_if_one, axis=1), use_container_width=True)

                with tab6:
                    st.subheader("Valorisation par Fournisseur")
                    df_total_value_by_supplier = total_stock_value_by_supplier(df)
                    total_value = df_total_value_by_supplier['Valeur Totale HT'].sum()
                    
                    st.metric(label="Valeur Totale Globale du Stock", value=f"{total_value:,.2f} €".replace(',', ' '))
                    st.dataframe(df_total_value_by_supplier, use_container_width=True)

                with tab7:
                    display_stock_by_family(df)
                    
                with tab8:
                    st.subheader("Analyse de la profondeur de gamme (Chaussures)")
                    display_specific_designations(df.copy())

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
else:
    st.info("Veuillez utiliser la barre latérale pour télécharger un fichier d'inventaire et commencer l'analyse.")
