import streamlit as st
import pandas as pd
from io import BytesIO
import numpy as np
import re

#### --- Configuration de l'application Streamlit ---
# Doit être la première commande Streamlit
st.set_page_config(
    page_title="Terre de Running - Ayada",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        return['background-color: #ffcccc' for _ in row]
    else:
        return [''] * len(row)

#### --- Fonctions modifiées pour afficher les colonnes spécifiques ---
def display_supplier_info(df, fournisseur):
    colonnes_afficher =['fournisseur', 'barcode', 'couleur', 'taille', 'designation',
                         'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    fournisseur = fournisseur.strip().upper()
    df['fournisseur'] = df['fournisseur'].fillna('')
    
    # Filtrer par fournisseur
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame(columns=colonnes_afficher)
    
    # Si des résultats sont trouvés
    if not df_filtered.empty:
        # Créer un DataFrame avec les désignations et rayons
        designations_rayons = df_filtered.groupby(['designation', 'rayon']).size().reset_index(name='Nombre de références')
        designations_rayons = designations_rayons.sort_values(['designation', 'rayon'])
        
        # Afficher les désignations et rayons dans un expander
        with st.expander(f"Désignations disponibles pour {fournisseur}"):
            # Créer une colonne cliquable avec designation + rayon
            designations_rayons['selection'] = designations_rayons.apply(
                lambda x: f"{x['designation']} ({x['rayon']})", axis=1)
            
            selected = st.selectbox(
                "Sélectionnez une désignation pour voir les tailles manquantes",
                designations_rayons['selection']
            )
            
            # Récupérer la désignation et le rayon sélectionnés
            selected_design, selected_rayon = selected.split(" (")
            selected_rayon = selected_rayon[:-1]  # Enlever la parenthèse fermante
            
            # Filtrer le dataframe pour la désignation et rayon sélectionnés
            filtered = df_filtered[
                (df_filtered['designation'] == selected_design) & 
                (df_filtered['rayon'] == selected_rayon)
            ]
            
            # Définir les plages de tailles attendues selon le rayon
            if selected_rayon.upper() == 'FEMME':
                expected_sizes =[round(x*0.5, 1) for x in range(10, 21)]  # 5.0 à 10.0 par pas de 0.5
            elif selected_rayon.upper() == 'HOMME':
                expected_sizes =[round(x*0.5, 1) for x in range(14, 29)]  # 7.0 à 14.0 par pas de 0.5
            else:  # UNISEX ou autres
                existing_sizes = filtered['taille'].unique()
                expected_sizes = sorted([float(x.replace(',', '.')) for x in existing_sizes if str(x).replace('.', '').isdigit()])
            
            # Fonction pour extraire la valeur numérique de la taille
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
            
            # Trouver les tailles manquantes
            if selected_rayon.upper() in ['FEMME', 'HOMME']:
                missing_sizes =[]
                for expected in expected_sizes:
                    expected_float = float(expected)
                    if expected_float not in[s for s in size_qtys.keys() if isinstance(s, float)]:
                        missing_sizes.append(str(expected))
            else:
                missing_sizes =[]
            
            st.write(f"Tailles disponibles pour {selected_design} ({selected_rayon}):")
            
            display_sizes =[]
            for size in sorted(size_qtys.keys()):
                qty = size_qtys[size]
                display_size = size_mapping.get(size, str(size))
                display_text = f"{display_size} ({qty})"
                
                if qty == 1:
                    display_text = f"<span style='color:red; font-weight:bold;'>{display_text}</span>"
                display_sizes.append(display_text)
            
            st.markdown(", ".join(display_sizes), unsafe_allow_html=True)
            
            if missing_sizes:
                st.write(f"Tailles manquantes ({selected_rayon}):")
                st.write(", ".join(missing_sizes))
            else:
                st.write("Toutes les tailles attendues sont disponibles.")
    
    return df_filtered[colonnes_afficher]

def display_designation_info(df, designation):
    colonnes_a_afficher =['barcode', 'taille', 'rayon', 'couleur', 'designation', 'Qté stock dispo']
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

    def highlight_row_if_one_designation(row):
        if 'taille_normalisee' in row and row['taille_normalisee'] in sum_by_size['Taille'].values:
            mask = (sum_by_size['Taille'] == row['taille_normalisee']) 
            if 'rayon' in sum_by_size.columns:
                mask &= (sum_by_size['Rayon'] == row['rayon'])
            total = sum_by_size.loc[mask, 'Total Qté dispo'].values[0] if any(mask) else 0
            if total == 1:
                return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)

    if not df_filtered.empty and 'taille_num' in df_filtered.columns:
        df_filtered = df_filtered.sort_values('taille_num')
    st.dataframe(df_filtered[colonnes_a_afficher].style.apply(highlight_row_if_one_designation, axis=1))

    if not sum_by_size.empty:
        sum_homme = sum_by_size[sum_by_size['Rayon'] == 'HOMME']
        sum_femme = sum_by_size[sum_by_size['Rayon'] == 'FEMME']

        def highlight_total_if_one(val):
            color = '#ffcccc' if val == 1 else ''
            return f'background-color: {color}'

        if not sum_homme.empty:
            st.subheader("Somme des quantités disponibles par taille - Rayon HOMME")
            styled_homme = sum_homme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo'])
            st.dataframe(styled_homme)

        if not sum_femme.empty:
            st.subheader("Somme des quantités disponibles par taille - Rayon FEMME")
            styled_femme = sum_femme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo'])
            st.dataframe(styled_femme)

def filter_negative_stock(df):
    colonnes_affichier =['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0)
    df_filtered = df[df['Qté stock dispo'] < 0]
    return df_filtered[colonnes_affichier]

def display_anita_sizes(df):
    df_anita = df[df['fournisseur'].str.upper() == "ANITA"]
    tailles = [f"{num}{letter}" for num in[85, 90, 95, 100, 105, 110] for letter in 'ABCDEF']
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
        st.markdown(f"Qté dispo totale pour **{famille}** : **{total_stock}**")
        st.markdown(f"Valeur totale du stock pour **{famille}** : **{total_stock_value:.2f} €**")

        rayon_options =['Tous', 'Homme', 'Femme', 'Autre']
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
            st.dataframe(df_family[['rayon', 'fournisseur', 'couleur', 'taille', 'designation', 'marque', 'ssfamille',
                              'Qté stock dispo', 'Valeur Stock']].style.apply(highlight_row_if_one, axis=1))
        else:
            st.write(f"Aucune information disponible pour {famille} dans la catégorie {rayon_filter}.")

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

    # Normalisation FORCÉE À .0 OU .5
    def normalize_size(size):
        if pd.isna(size):
            return ""

        s = str(size).upper().strip()
        s = s.replace(",", ".")
        s = re.sub(r"\b(US|UK|EU)\b", "", s).strip()
        s = re.sub(r"\s+", " ", s)

        if re.fullmatch(r"\d+[A-Z]", s):
            return s

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

    st.markdown("## VUE DÉTAILLÉE DES MARQUES")

    cols = st.columns(3)
    for i, supplier in enumerate(sorted(suppliers.keys())):
        with cols[i % 3]:
            if st.button(supplier, key=f"btn_{supplier}"):
                st.session_state.selected_supplier = supplier

    if 'selected_supplier' in st.session_state:
        supplier = st.session_state.selected_supplier
        designations = suppliers[supplier]
        df_filtered = df[df['designation'].str.upper().isin([d.upper() for d in designations])].copy()
        
        if not df_filtered.empty:
            df_filtered['taille_normalisee'] = df_filtered['taille'].apply(normalize_size)

            results = []
            for designation in sorted(designations):
                df_design = df_filtered[df_filtered['designation'].str.upper() == designation.upper()]
                is_woman = " W" in designation.upper() or "WOMAN" in designation.upper()
                expected_sizes =[]

                if supplier == "SALOMON":
                    if "AERO GLIDE 3 GRVL" in designation.upper():
                        sizes = list(range(4, 10)) if is_woman else list(range(6, 14))
                    else:
                        sizes = list(range(6, 14)) if is_woman else list(range(4, 10))
                    expected_sizes =[f"{x}.0" for x in sizes] +[f"{x}.5" for x in sizes if x != sizes[-1]]
                
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
                        expected_sizes =[f"{x}.0" for x in sizes] +[f"{x}.5" for x in sizes if x != sizes[-1] and x < 13]
                
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
            
            st.markdown(f"### 📦 Stock disponible pour : **{supplier}**")
            st.table(
                results_df.style
                .set_properties(**{
                    'text-align': 'left',
                    'border': '1px solid #e0e0e0',
                    'padding': '10px'
                })
                .set_table_styles([{
                    'selector': 'th',
                    'props':[('background-color', '#ff5722'), ('color', 'white'), ('font-size', '16px')]
                }])
            )
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Exporter en Excel (XLSX)", key=f"export_excel_{supplier}"):
                    try:
                        import io
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            results_df.to_excel(writer, sheet_name=f"{supplier}_Stock", index=False)
                        st.download_button(label="⬇ Télécharger le fichier Excel", data=output.getvalue(), file_name=f"{supplier}_stock.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    except Exception as e:
                        st.error(f"Erreur Excel: {str(e)}. Pensez à installer xlsxwriter.")
            
            with col2:
                if st.button("📄 Exporter en CSV", key=f"export_csv_{supplier}"):
                    try:
                        csv = results_df.to_csv(index=False, sep=';')
                        st.download_button(label="⬇ Télécharger le fichier CSV", data=csv, file_name=f"{supplier}_stock.csv", mime="text/csv")
                    except Exception as e:
                        st.error(f"Erreur CSV: {str(e)}")


#### --- CSS Personnalisé Globale ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');

    body {
        font-family: 'Roboto', sans-serif;
        background-color: #f8f9fa;
    }
    
    /* Hero Banner CSS */
    .hero-container {
        position: relative;
        text-align: center;
        color: white;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        margin-bottom: 40px;
        background-color: #000;
    }
    .hero-image {
        width: 100%;
        height: 400px;
        object-fit: cover;
        opacity: 0.6;
        display: block;
    }
    .hero-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 90%;
    }
    .hero-title {
        font-size: 4.5rem;
        font-weight: 900;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 3px;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.8);
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 10px 0;
        color: #ff5722; /* Orange Terre de Running */
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }
    .hero-desc {
        font-size: 1.3rem;
        margin-top: 15px;
        font-weight: 400;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    
    /* Feature Cards CSS */
    .feature-box {
        background-color: white;
        padding: 25px 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        height: 100%;
        border-top: 5px solid #ff5722;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .feature-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 15px;
    }
    .feature-title {
        color: #212529;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .feature-text {
        color: #6c757d;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* Tabs Style */
    .stTabs[data-baseweb="tab-list"] {
        border-bottom: 2px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab-list"] button {
        color: #6c757d;
        font-size: 16px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #ff5722;
        border-bottom: 3px solid #ff5722;
    }

    /* Buttons */
    div.stButton > button:first-child {
        background-color: #212529;
        color: #FFFFFF;
        border: 2px solid #212529;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #ff5722 !important;
        color: #FFFFFF !important;
        border: 2px solid #ff5722 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#### --- Menu Latéral ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Running_icon_-_Noun_Project_17825.svg/512px-Running_icon_-_Noun_Project_17825.svg.png", width=80)
st.sidebar.markdown("## ⚙️ Menu Principal")
st.sidebar.info("Veuillez importer votre base de données (CSV/Excel) pour activer l'application.")
fichier_telecharge = st.file_uploader("📂 Charger le fichier d'inventaire", type=['csv', 'xlsx'])

#### --- Logique d'affichage Principale ---

# Si AUCUN fichier n'est chargé, on affiche la belle page d'accueil
if fichier_telecharge is None:
    st.markdown("""
    <div class="hero-container">
        <img class="hero-image" src="https://images.unsplash.com/photo-1515248137880-45e105b710e0?q=80&w=2000&auto=format&fit=crop" alt="Trail Running Shoes">
        <div class="hero-text">
            <h1 class="hero-title">Terre de Running</h1>
            <h2 class="hero-subtitle">Magasin Ayada</h2>
            <p class="hero-desc">L'outil professionnel pour piloter, analyser et optimiser vos stocks de chaussures et équipements.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Section des fonctionnalités
    st.markdown("<h3 style='text-align: center; color: #424242; margin-bottom: 30px;'>🚀 Fonctionnalités Principales</h3>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="feature-box">
            <div class="feature-icon">👟</div>
            <div class="feature-title">Analyse par Marque</div>
            <div class="feature-text">Filtrez vos modèles Asics, Brooks, Salomon, Hoka et visualisez vos stocks en un clin d'œil.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-box">
            <div class="feature-icon">📏</div>
            <div class="feature-title">Ruptures de Tailles</div>
            <div class="feature-text">Détectez automatiquement les tailles manquantes ou en faible quantité pour anticiper vos commandes.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="feature-box">
            <div class="feature-icon">💶</div>
            <div class="feature-title">Valorisation Financière</div>
            <div class="feature-text">Calculez instantanément la valeur totale de votre inventaire, globalement ou par fournisseur.</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="feature-box">
            <div class="feature-icon">⚠️</div>
            <div class="feature-title">Alertes Stocks</div>
            <div class="feature-text">Repérez facilement les stocks négatifs ou les dernières paires pour corriger les anomalies.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.success("👈 **Prêt à commencer ? Utilisez le menu à gauche pour importer votre fichier.**")

# Si le fichier EST chargé, on lance l'application normalement
else:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        with st.spinner("🔄 Traitement des données en cours..."):
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
                
                # Petit Header pour rappeler où on est une fois l'appli lancée
                st.markdown("""
                <div style='background-color: #212529; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;'>
                    <h2 style='color: white; margin:0;'>Terre de Running - Ayada 🏃‍♂️</h2>
                </div>
                """, unsafe_allow_html=True)

                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                    "🏢 Par Fournisseur",
                    "🔍 Par Désignation",
                    "⚠️ Stock Négatif",
                    "👙 Anita",
                    "🦶 Sidas",
                    "💰 Valorisation",
                    "📦 Par Famille",
                    "🎯 Tailles Manquantes"
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
                    st.markdown(f"### 💶 Valeur globale : **{total_value:,.2f} €**")

                with tab7:
                    display_stock_by_family(df)
                    
                with tab8:
                    display_specific_designations(df.copy())

    except Exception as e:
        st.error(f"❌ Erreur lors du traitement du fichier: {str(e)}")
