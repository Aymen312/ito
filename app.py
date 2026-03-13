import streamlit as st
import pandas as pd
from io import BytesIO
import numpy as np
import re
import pdfplumber
import openpyxl
import io
from datetime import datetime, timedelta
import hashlib
import hashlib

st.set_page_config(page_title="Ayada TDR", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body,[class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    h1, h2, h3 { color: #0F172A; font-weight: 700; letter-spacing: -0.025em; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; box-shadow: 2px 0 8px rgba(0,0,0,0.02); }
    .stTabs [data-baseweb="tab-list"] { background-color: #FFFFFF; padding: 4px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 16px; border-radius: 8px !important; border: none !important; color: #64748B; font-weight: 500; background-color: transparent; transition: all 0.2s ease-in-out; }
    .stTabs [data-baseweb="tab"]:hover { color: #0F172A; background-color: #F1F5F9; }
    .stTabs [aria-selected="true"] { background-color: #3B82F6 !important; color: #FFFFFF !important; box-shadow: 0 2px 4px rgba(59,130,246,0.3); }
    .stButton>button { background-color: #0F172A; color: #FFFFFF; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; transition: all 0.2s ease; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); width: 100%; }
    .stButton>button:hover { background-color: #334155; transform: translateY(-1px); box-shadow: 0 6px 8px -1px rgba(0,0,0,0.15); color: white !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div { border-radius: 8px; border: 1px solid #CBD5E1; padding: 8px 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
    [data-testid="stExpander"] { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    [data-testid="stFileUploadDropzone"] { border: 2px dashed #CBD5E1; border-radius: 12px; background-color: #FFFFFF; }
    [data-testid="stFileUploadDropzone"]:hover { border-color: #3B82F6; background-color: #EFF6FF; }
    table { border-collapse: collapse; width: 100%; background-color: white; box-shadow: 0px 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
    th { background-color: #0F172A; color: white; }
    th, td { padding: 12px 16px; border-bottom: 1px solid #E2E8F0; }
    .invoice-badge { display: inline-block; padding: 4px 10px; border-radius: 99px; font-size: 12px; font-weight: 600; background: #EFF6FF; color: #3B82F6; margin-bottom: 12px; }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# STOCK DASHBOARD FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def clean_numeric_columns(df):
    for col in ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def highlight_row_if_one(row):
    if row['Qté stock dispo'] == 1:
        return ['background-color: #FEE2E2; color: #991B1B' for _ in row]
    return [''] * len(row)

def display_supplier_info(df, fournisseur):
    colonnes_afficher = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    fournisseur = fournisseur.strip().upper()
    df['fournisseur'] = df['fournisseur'].fillna('')
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame(columns=colonnes_afficher)
    if not df_filtered.empty:
        designations_rayons = df_filtered.groupby(['designation', 'rayon']).size().reset_index(name='Nombre de références')
        designations_rayons = designations_rayons.sort_values(['designation', 'rayon'])
        with st.expander(f"Désignations disponibles pour {fournisseur}", expanded=True):
            designations_rayons['selection'] = designations_rayons.apply(lambda x: f"{x['designation']} ({x['rayon']})", axis=1)
            selected = st.selectbox("Sélectionnez une désignation pour voir les tailles manquantes", designations_rayons['selection'])
            selected_design, selected_rayon = selected.split(" (")
            selected_rayon = selected_rayon[:-1]
            filtered = df_filtered[(df_filtered['designation'] == selected_design) & (df_filtered['rayon'] == selected_rayon)]
            if selected_rayon.upper() == 'FEMME':
                expected_sizes = [round(x * 0.5, 1) for x in range(10, 21)]
            elif selected_rayon.upper() == 'HOMME':
                expected_sizes = [round(x * 0.5, 1) for x in range(14, 29)]
            else:
                existing_sizes = filtered['taille'].unique()
                expected_sizes = sorted([float(x.replace(',', '.')) for x in existing_sizes if str(x).replace('.', '').isdigit()])
            def extract_size_value(size_str):
                try:
                    cleaned = str(size_str).upper().replace('US', '').strip().replace(',', '.')
                    if '.' in cleaned:
                        int_part, dec_part = cleaned.split('.', 1)
                        cleaned = f"{int_part.lstrip('0') or '0'}.{dec_part}"
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
                missing_sizes = [str(e) for e in expected_sizes if float(e) not in [s for s in size_qtys.keys() if isinstance(s, float)]]
            else:
                missing_sizes = []
            st.markdown(f"**Tailles disponibles pour {selected_design} ({selected_rayon}):**")
            display_sizes = []
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
    colonnes_a_afficher = ['barcode', 'taille', 'rayon', 'couleur', 'designation', 'Qté stock dispo']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    df_filtered = df[df['designation'].str.upper() == designation] if designation else pd.DataFrame(columns=colonnes_a_afficher)
    def normalize_size(size):
        if pd.isna(size): return ''
        size_str = str(size).strip()
        if '.' in size_str:
            int_part, dec_part = size_str.split('.', 1)
            size_str = f"{int_part.lstrip('0') or '0'}.{dec_part}"
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
                return ['background-color: #FEE2E2; color: #991B1B'] * len(row)
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
                st.dataframe(sum_homme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo']), use_container_width=True)
        if not sum_femme.empty:
            with col2:
                st.subheader("Somme par taille - FEMME")
                st.dataframe(sum_femme[['Taille', 'Total Qté dispo']].style.applymap(highlight_total_if_one, subset=['Total Qté dispo']), use_container_width=True)

def filter_negative_stock(df):
    colonnes_affichier = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0)
    return df[df['Qté stock dispo'] < 0][colonnes_affichier]

def display_anita_sizes(df):
    df_anita = df[df['fournisseur'].str.upper() == "ANITA"]
    tailles = [f"{num}{letter}" for num in [85, 90, 95, 100, 105, 110] for letter in 'ABCDEF']
    df_anita_sizes = df_anita[df_anita['taille'].isin(tailles)]
    df_anita_sizes = df_anita_sizes.groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)
    return df_anita_sizes.replace(0, "Nul")

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
        df_sizes_grouped = df_sizes.groupby(['taille', 'designation'])['Qté stock dispo'].sum().unstack(fill_value=0).replace(0, "Nul")
        df_sizes_with_designation = df_sizes_grouped.stack().reset_index().rename(columns={0: 'Qté stock dispo'})
        results[level] = df_sizes_with_designation
        unavailable = [s for s in sizes if s not in df_sidas_level['taille'].unique()]
        if unavailable:
            st.warning(f"Tailles indisponibles pour SIDAS niveau {level}: {', '.join(unavailable)}")
        else:
            st.success(f"Toutes les tailles SIDAS niveau {level} sont en stock.")
    return results

def total_stock_value_by_supplier(df):
    df['Qté stock dispo'] = pd.to_numeric(df['Qté stock dispo'], errors='coerce').fillna(0)
    df['Prix Achat'] = pd.to_numeric(df['Prix Achat'], errors='coerce').fillna(0)
    df['Valeur Totale HT'] = df['Qté stock dispo'] * df['Prix Achat']
    total_value_by_supplier = df.groupby('fournisseur')['Valeur Totale HT'].sum().reset_index()
    return total_value_by_supplier.sort_values(by='Valeur Totale HT', ascending=False)

def sort_sizes(df):
    df['taille'] = pd.Categorical(df['taille'],
        categories=sorted(df['taille'].unique(),
            key=lambda x: (int(x[:-1]), x[-1]) if str(x)[:-1].isdigit() else (float('inf'), x)),
        ordered=True)
    return df.sort_values('taille')

def display_stock_by_family(df):
    familles = ["CHAUSSURES RANDO", "CHAUSSURES RUNN", "CHAUSSURE TRAIL"]
    for famille in familles:
        st.subheader(f"Catégorie : {famille}")
        df['famille'] = df['famille'].fillna('')
        df_family = df[df['famille'].str.upper() == famille]
        if 'Valeur Stock' not in df_family.columns or df_family['Valeur Stock'].isnull().all():
            df_family['Valeur Stock'] = df_family['Qté stock dispo'] * df_family.get('Prix Achat', 0)
        total_stock = df_family['Qté stock dispo'].sum()
        total_stock_value = df_family['Valeur Stock'].sum()
        col1, col2 = st.columns(2)
        col1.metric("Qté dispo totale", f"{int(total_stock)}")
        col2.metric("Valeur totale du stock HT", f"{total_stock_value:,.2f} €".replace(',', ' '))
        rayon_filter = st.selectbox(f"Filtrer par Rayon pour {famille}:", ['Tous', 'Homme', 'Femme', 'Autre'], key=f"rayon_{famille}")
        if rayon_filter != 'Tous':
            df_family['rayon'] = df_family['rayon'].fillna('')
            if rayon_filter in ['Homme', 'Femme']:
                df_family = df_family[df_family['rayon'].str.upper() == rayon_filter.upper()]
            else:
                df_family = df_family[~df_family['rayon'].str.upper().isin(['HOMME', 'FEMME'])]
        if not df_family.empty:
            df_family = sort_sizes(df_family.copy())
            st.dataframe(df_family[['rayon', 'fournisseur', 'couleur', 'taille', 'designation', 'marque', 'ssfamille', 'Qté stock dispo', 'Valeur Stock']].style.apply(highlight_row_if_one, axis=1), use_container_width=True)
        else:
            st.info(f"Aucune information disponible pour {famille} dans le rayon {rayon_filter}.")
        st.markdown("---")

def display_specific_designations(df):
    brand_col = "marque" if "marque" in df.columns else "fournisseur"
    for c in [brand_col, "designation", "taille", "famille", "ssfamille", "rayon"]:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].fillna("").astype(str)
    shoe_mask = (
        df["famille"].str.upper().str.contains("CHAUSS", na=False) |
        df["ssfamille"].str.upper().str.contains("CHAUSS", na=False) |
        df["designation"].str.upper().str.contains(r"RUN|TRAIL|RANDO|CHAUSS|SHOE", na=False)
    )
    df_shoes = df[shoe_mask].copy() if not df[shoe_mask].empty else df.copy()
    preferred = ["ASICS", "BROOKS", "HOKA", "LA SPORTIVA", "MIZUNO", "NEW BALANCE", "SALOMON", "SAUCONY"]
    brands_series = df_shoes[brand_col].str.upper().str.strip()
    brand_counts = brands_series.value_counts()
    brands = [b for b in preferred if b in brand_counts.index] or brand_counts.head(12).index.tolist()
    suppliers = {b: [d for d in sorted(df_shoes.loc[brands_series == b, "designation"].astype(str).str.strip().unique()) if d] for b in brands}
    def normalize_size(size):
        if pd.isna(size): return ""
        s = str(size).upper().strip().replace(",", ".")
        s = re.sub(r"\b(US|UK|EU)\b", "", s).strip()
        s = re.sub(r"\s+", " ", s)
        if re.fullmatch(r"\d+[A-Z]", s): return s
        def format_half(v): return f"{round(float(v) * 2) / 2:.1f}"
        unicode_frac = {"½": (1,2), "⅓": (1,3), "⅔": (2,3), "¼": (1,4), "¾": (3,4)}
        for symb, (num, den) in unicode_frac.items():
            if symb in s:
                bm = re.search(r"(\d+(\.\d+)?)", s.replace(symb, ""))
                base = float(bm.group(1)) if bm else 0.0
                return format_half(base + num / den)
        m = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)$", s)
        if m:
            return format_half(int(m.group(1)) + int(m.group(2)) / (int(m.group(3)) or 1))
        m = re.search(r"(\d+(\.\d+)?)", s)
        return format_half(float(m.group(1))) if m else s
    cols = st.columns(4)
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
            results = []
            for designation in sorted(designations):
                df_design = df_filtered[df_filtered['designation'].str.upper() == designation.upper()]
                is_woman = " W" in designation.upper() or "WOMAN" in designation.upper()
                if supplier == "SALOMON":
                    sizes = list(range(4, 10)) if is_woman else list(range(6, 14))
                    expected = [f"{x}.0" for x in sizes] + [f"{x}.5" for x in sizes[:-1]]
                elif supplier == "LA SPORTIVA":
                    sizes = list(range(36, 43)) if is_woman else list(range(40, 49))
                    expected = [f"{x/2:.1f}" for x in range(sizes[0]*2, sizes[-1]*2+1)]
                elif supplier == "MIZUNO":
                    raw = [4.0,4.5,5.0,5.5,6.5,7.0,7.5,8.0,9.0] if is_woman else [6.0,6.5,7.0,7.5,8.0,9.0,10.0,10.5,11.0,11.5,12.0]
                    expected = [f"{s:.1f}" for s in raw]
                elif supplier == "NEW BALANCE":
                    sizes = list(range(5, 11)) if is_woman else list(range(7, 15))
                    expected = [f"{x}.0" for x in sizes] + [f"{x}.5" for x in sizes if x < 13]
                else:
                    sizes = list(range(5, 11)) if is_woman else list(range(7, 15))
                    expected = [f"{x}.0" for x in sizes] + [f"{x}.5" for x in sizes if x < 13]
                available = df_design['taille_normalisee'].dropna().unique()
                missing = [s for s in expected if s not in available]
                results.append({'Modèle': designation, 'Tailles disponibles': len(available), 'Tailles manquantes': ", ".join(missing) if missing else "Complet"})
            results_df = pd.DataFrame(results)
            st.markdown(f"### {supplier} - Stock disponible")
            st.dataframe(results_df, use_container_width=True)
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                try:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        results_df.to_excel(writer, sheet_name=f"{supplier}_Stock", index=False)
                    st.download_button("📊 Exporter en Excel (XLSX)", data=output.getvalue(), file_name=f"{supplier}_stock.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception as e:
                    st.error(f"Erreur Excel: {str(e)}")
            with col2:
                try:
                    st.download_button("📄 Exporter en CSV", data=results_df.to_csv(index=False, sep=';'), file_name=f"{supplier}_stock.csv", mime="text/csv")
                except Exception as e:
                    st.error(f"Erreur CSV: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# INVOICE EXTRACTOR FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def parse_french_amount(s):
    """
    Convert French-formatted number to float.
    66,00 → 66.0 | 1.234,56 → 1234.56 | 1 234,56 → 1234.56
    """
    if s is None:
        return None
    s = str(s).strip().replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return None


def parse_date_inv(s):
    """
    Parse date string.
    Supports DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD, DD.MM.YY, DD/MM/YY
    """
    if not s:
        return None
    s = s.strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except:
            pass
    return None


# ── VF France brand prefix map ──────────────────────────────────
# Article code first 2 chars → brand name
_VF_BRAND_PREFIX = {
    "AL": "altra",
    "TM": "timberland",
    "NF": "the north face",
    "VN": "vans",
    "WR": "wrangler",
    "LV": "lee",
    "DK": "dickies",
}

def _vf_brand_from_article(code):
    return _VF_BRAND_PREFIX.get(str(code).strip()[:2].upper(), "vf france")


# ── VF France / ALTRA extractor ─────────────────────────────────
#
# Extracted text patterns from altra79_20.pdf:
#   "Facture 3301194916"
#   "Référence 3040740834"
#   "Date 11.03.26"
#   "No. cmmde.: 0120375559   Votre ref.: ."
#   "AL0A85U74441  W EXPERIENCE FLOW 3 LIGHT BLUE  1  75,00  12,00  66,00  66,00  L1"
#   "Total montant net  66,00"
#   "Total TVA  13,20"
#   "Date facture  11.03.26"
#   "Date d échéance  15.05.26"
#
def extract_invoice_vf_altra(text):
    data = {}

    # N° Facture → "Facture 3301194916"
    m = re.search(r"\bFacture\s+(\d{6,})", text)
    if m:
        data["n_facture"] = m.group(1)

    # Date facture (dedicated summary line at bottom)
    m = re.search(r"Date facture\s+([\d.]+)", text)
    if m:
        data["date_facture"] = parse_date_inv(m.group(1))
    else:
        # Fallback: header line "Date 11.03.26"
        m = re.search(r"\bDate\b\s+(\d{2}\.\d{2}\.\d{2,4})", text)
        if m:
            data["date_facture"] = parse_date_inv(m.group(1))

    # Date d'échéance → "Date d échéance 15.05.26"
    m = re.search(r"Date\s+d\s+[ée]ch[ée]ance\s+([\d.]+)", text)
    if m:
        data["echeance"] = parse_date_inv(m.group(1))

    # N° commande client → "No. cmmde.: 0120375559"
    m = re.search(r"No\.\s*cmmde\.\s*:\s*(\S+)", text)
    if m:
        data["n_commande"] = m.group(1)

    # Product lines: ARTICLE_CODE  DESCRIPTION  QTY  PRICE…
    # VF article codes: 2 alpha + 6+ alphanum (e.g. AL0A85U74441)
    desig_matches = re.findall(
        r"^([A-Z]{2}[A-Z0-9]{6,})\s+([A-Z][A-Z0-9 /\-]+?)\s+\d+\s+[\d,]+",
        text, re.MULTILINE
    )
    if desig_matches:
        data["beneficiaire"] = _vf_brand_from_article(desig_matches[0][0])
        seen = []
        for _, desc in desig_matches:
            d = desc.strip()
            if d not in seen:
                seen.append(d)
        data["designation"] = " / ".join(seen)[:120]
    else:
        data["beneficiaire"] = "vf france"
        # Fallback: known Altra model names
        m = re.search(
            r"(EXPERIENCE FLOW|LONE PEAK|SUPERIOR|OLYMPUS|TIMP|TORIN|ESCALANTE|RIVERA|PARADIGM|PROVISION)[^\n]*",
            text, re.IGNORECASE
        )
        if m:
            data["designation"] = m.group(0).strip()[:120]

    # Montant HT → "Total montant net  66,00"
    m = re.search(r"Total montant net\s+([\d\s.,]+)", text)
    if m:
        data["montant_ht"] = parse_french_amount(m.group(1))

    # TVA → "Total TVA  13,20"
    m = re.search(r"Total TVA\s+([\d\s.,]+)", text)
    if m:
        data["montant_tva"] = parse_french_amount(m.group(1))

    # TTC = HT + TVA — always computed, never read from PDF
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = ht + tva

    data.update({
        "categorie":         "Achats marchandises",
        "statut":            "Attente règlement",
        "moyen_paiement":    "Moyen paiement",
        "date_transmission": "A transmettre",
        "source":            "VF France (Altra / Timberland / TNF / Vans)",
    })
    return data


# ── Saucony / Wolverine ─────────────────────────────────────────
def extract_invoice_saucony(text):
    data = {}
    m = re.search(r"Num[ée]ro de document\s+(\d+)", text)
    if m: data["n_facture"] = m.group(1)
    data["beneficiaire"] = "saucony"
    m = re.search(r"Datum\s+([\d.]+)", text)
    if m: data["date_facture"] = parse_date_inv(m.group(1))
    m = re.search(r"Cond\.\s*paiem\.\s+(\d+)\s+jours", text, re.IGNORECASE)
    if m and data.get("date_facture"):
        data["echeance"] = data["date_facture"] + timedelta(days=int(m.group(1)))
    m = re.search(r"Notre commande N[°º]\s*[:\s]*(\S+)", text)
    if m: data["n_commande"] = m.group(1)
    m = re.search(r"Votre commande N[°º]\s*[:\s]*([^\n]+)", text)
    if m: data["designation"] = m.group(1).strip()
    m = re.search(r"Montant HT\s+[\d]+\s+([\d.,]+)", text)
    if m: data["montant_ht"] = parse_french_amount(m.group(1))
    m = re.search(r"TVA\s+[\d.,]+\s*%\s+[\d.,]+\s+([\d.,]+)", text)
    if m: data["montant_tva"] = parse_french_amount(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = ht + tva
    products = re.findall(r"(XODUS|ENDORPHIN|KINVARA|TRIUMPH|RIDE|TEMPUS|GUIDE)[^\n]+", text)
    if products and not data.get("designation"):
        data["designation"] = " / ".join(set(products))[:100]
    data.update({"categorie": "Achats marchandises", "statut": "Attente règlement",
                 "moyen_paiement": "Moyen paiement", "date_transmission": "A transmettre",
                 "source": "Saucony / Wolverine"})
    return data


# ── HOKA / Deckers ──────────────────────────────────────────────
def extract_invoice_hoka(text):
    data = {}
    m = re.search(r"Num[ée]ro de facture\s*[:\s]*(\d+)", text)
    if m: data["n_facture"] = m.group(1)
    m = re.search(r"Marque\s*[:\s]*([\w]+)", text)
    data["beneficiaire"] = m.group(1).lower() if m else "hoka"
    m = re.search(r"Date de facture\s*[:\s]*([\d/]+)", text)
    if m: data["date_facture"] = parse_date_inv(m.group(1))
    m = re.search(r"Date d'[ée]ch[ée]ance\s*[:\s]*([\d/]+)", text)
    if m: data["echeance"] = parse_date_inv(m.group(1))
    m = re.search(r"(HE-\d+)", text)
    if m: data["n_commande"] = m.group(1)
    m = re.search(r"Sous Total\s+EUR\s+([\d.,]+)", text)
    if m: data["montant_ht"] = float(m.group(1).replace(",", "."))
    m = re.search(r"Total TVA\s+EUR\s+([\d.,]+)", text)
    if m: data["montant_tva"] = float(m.group(1).replace(",", "."))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = ht + tva
    products = re.findall(r"\d{7}-([A-Z0-9 /]+)\n", text)
    if products: data["designation"] = " / ".join(set(products))[:100]
    else:
        m = re.search(r"(CHALLENGER|CLIFTON|BONDI|MAFATE|SPEEDGOAT|RINCON|ARAHI)[^\n]*", text)
        if m: data["designation"] = m.group(0).strip()[:100]
    data.update({"categorie": "Achats marchandises", "statut": "Attente règlement",
                 "moyen_paiement": "Moyen paiement", "date_transmission": "A transmettre",
                 "source": "HOKA / Deckers"})
    return data


# ── Generic fallback ────────────────────────────────────────────
def extract_invoice_generic(text):
    data = {}
    for pat in [r"[Ff]acture\s*N[°º]?\s*[:\s]*([\w\-]+)", r"N[°º]\s+[Ff]acture\s*[:\s]*([\w\-]+)"]:
        m = re.search(pat, text)
        if m: data["n_facture"] = m.group(1).strip(); break
    m = re.search(r"(\d{2}[./]\d{2}[./]\d{2,4})", text)
    if m: data["date_facture"] = parse_date_inv(m.group(1))
    for label, key in [("Montant HT", "montant_ht"), ("TVA", "montant_tva")]:
        m = re.search(label + r"[^\d]*([\d.,]+)", text, re.IGNORECASE)
        if m and key not in data: data[key] = parse_french_amount(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = ht + tva
    data.update({"beneficiaire": "?", "categorie": "Achats marchandises", "statut": "Attente règlement",
                 "moyen_paiement": "Moyen paiement", "date_transmission": "A transmettre",
                 "source": "Format générique"})
    return data


# ── Router ──────────────────────────────────────────────────────
# Cache extraction results — Streamlit re-runs on every widget interaction,
# this ensures we only call pdfplumber once per unique file (180x faster on re-runs)
_pdf_extract_cache = {}

def extract_from_pdf(pdf_bytes):
    cache_key = hashlib.md5(pdf_bytes).hexdigest()
    if cache_key in _pdf_extract_cache:
        return _pdf_extract_cache[cache_key]

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        # Only read page 1 — invoice data is always there.
        # Page 2+ is T&C (23k chars) and takes 3x longer — skip it.
        full_text = pdf.pages[0].extract_text() or ""

    text_upper = full_text.upper()

    # VF France / Altra — signature: company name OR VF article code OR known Altra models
    if ("VF (J) FRANCE" in full_text
            or re.search(r"\bAL[0-9A-Z]{6,}\b", full_text)
            or any(w in text_upper for w in [
                "EXPERIENCE FLOW", "LONE PEAK", "SUPERIOR", "OLYMPUS",
                "TIMP", "TORIN", "ESCALANTE", "ALTRA", "TIMBERLAND",
                "NORTH FACE", "VF FRANCE"
            ])):
        result = extract_invoice_vf_altra(full_text), full_text

    # Saucony / Wolverine
    elif any(w in full_text for w in ["Wolverine", "XODUS", "ENDORPHIN", "KINVARA",
                                       "TRIUMPH", "RIDE", "TEMPUS", "GUIDE"]):
        result = extract_invoice_saucony(full_text), full_text

    # HOKA / Deckers
    elif any(w in full_text for w in ["Deckers", "HOKA", "CHALLENGER", "CLIFTON",
                                       "BONDI", "SPEEDGOAT"]):
        result = extract_invoice_hoka(full_text), full_text

    else:
        result = extract_invoice_generic(full_text), full_text

    _pdf_extract_cache[cache_key] = result
    return result


# ── Excel helpers ───────────────────────────────────────────────
def find_next_empty_row(ws):
    for row in range(2, ws.max_row + 2):
        if ws.cell(row=row, column=1).value is None and ws.cell(row=row, column=5).value is None:
            return row
    return ws.max_row + 1

def write_invoice_to_excel(wb, d):
    ws = wb["Dépenses"]
    row = find_next_empty_row(ws)
    df_date = d.get("date_facture")
    ech     = d.get("echeance")
    ht      = d.get("montant_ht")  or 0
    tva     = d.get("montant_tva") or 0
    ttc     = ht + tva  # Always HT + TVA
    vals = [
        df_date, df_date, ech, None,
        d.get("n_facture", ""),
        d.get("beneficiaire", ""),
        d.get("categorie", "Achats marchandises"),
        d.get("n_commande", ""),
        d.get("designation", ""),
        d.get("moyen_paiement", "Moyen paiement"),
        ht, tva, ttc,
        d.get("date_transmission", "A transmettre"),
        d.get("statut", "Attente règlement"),
        None, None,
        df_date.month        if df_date else None,
        df_date.year         if df_date else None,
        ech.isocalendar()[1] if ech     else None,
        ech.month            if ech     else None,
        ech.year             if ech     else None,
        d.get("commentaire", "")
    ]
    for col, val in enumerate(vals, start=1):
        ws.cell(row=row, column=col).value = val

    # Write dates as DD/MM/YYYY (e.g. 15/05/2026) — no time, no ISO
    import datetime as _dt
    for date_col in [1, 2, 3]:
        cell = ws.cell(row=row, column=date_col)
        if cell.value is not None:
            v = cell.value
            # openpyxl needs datetime (not date) to reliably apply number_format
            if isinstance(v, _dt.date) and not isinstance(v, _dt.datetime):
                cell.value = _dt.datetime(v.year, v.month, v.day)
            cell.number_format = 'DD/MM/YYYY'

    return row


# ═══════════════════════════════════════════════════════════════
# INVOICE TAB UI
# ═══════════════════════════════════════════════════════════════

def render_invoice_tab():
    st.subheader("📄 Extraction de Factures → Excel")
    st.markdown("Importez vos factures PDF et votre fichier Excel. Les données extraites seront ajoutées à l'onglet **Dépenses**.")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("#### 📊 Fichier Excel")
        excel_file = st.file_uploader("Classeur .xlsm / .xlsx", type=["xlsm", "xlsx"], key="inv_excel")
    with col2:
        st.markdown("#### 🧾 Factures PDF")
        pdf_files = st.file_uploader("Une ou plusieurs factures", type=["pdf"], accept_multiple_files=True, key="inv_pdfs")

    if not excel_file and not pdf_files:
        st.info("👆 Importez votre fichier Excel et vos factures PDF pour commencer.")
        return
    if excel_file and not pdf_files:
        st.info("📎 Maintenant importez vos factures PDF.")
        return
    if not excel_file and pdf_files:
        st.info("📊 Maintenant importez votre fichier Excel (.xlsm).")
        return

    st.divider()
    st.markdown("### 📋 Données extraites")

    if ("inv_wb_bytes" not in st.session_state
            or st.session_state.get("inv_excel_name") != excel_file.name):
        st.session_state.inv_wb_bytes   = excel_file.read()
        st.session_state.inv_excel_name = excel_file.name

    wb = openpyxl.load_workbook(io.BytesIO(st.session_state.inv_wb_bytes), keep_vba=True)

    # Cache raw PDF bytes per filename — Streamlit resets file buffers on re-render
    if "inv_pdf_bytes" not in st.session_state:
        st.session_state.inv_pdf_bytes = {}
    for pdf_file in pdf_files:
        if pdf_file.name not in st.session_state.inv_pdf_bytes:
            st.session_state.inv_pdf_bytes[pdf_file.name] = pdf_file.read()

    all_invoice_data = []

    for pdf_file in pdf_files:
        with st.expander(f"📄 {pdf_file.name}", expanded=True):
            try:
                pdf_bytes_cached = st.session_state.inv_pdf_bytes[pdf_file.name]
                invoice_data, _ = extract_from_pdf(pdf_bytes_cached)

                st.markdown(
                    f"<span class='invoice-badge'>🔍 {invoice_data.get('source', '?')}</span>",
                    unsafe_allow_html=True
                )

                df_date  = invoice_data.get("date_facture")
                ech_date = invoice_data.get("echeance")
                ht_disp  = float(invoice_data.get("montant_ht")  or 0.0)
                tva_disp = float(invoice_data.get("montant_tva") or 0.0)
                ttc_disp = ht_disp + tva_disp

                m1, m2, m3 = st.columns(3)
                m1.metric("N° Facture",    invoice_data.get("n_facture", "—"))
                m1.metric("Bénéficiaire",  invoice_data.get("beneficiaire", "—").upper())
                m2.metric("Montant HT",    f"{ht_disp:.2f} €")
                m2.metric("TVA",           f"{tva_disp:.2f} €")
                m2.metric("TTC (HT+TVA)",  f"{ttc_disp:.2f} €")
                m3.metric("Date facture",  df_date.strftime("%d/%m/%Y")  if df_date  else "—")
                m3.metric("Échéance",      ech_date.strftime("%d/%m/%Y") if ech_date else "—")
                m3.metric("N° Commande",   invoice_data.get("n_commande", "—"))
                st.caption(f"Désignation : {invoice_data.get('designation', '—')}")

                with st.form(key=f"form_{pdf_file.name}"):
                    st.markdown("**✏️ Corriger si nécessaire**")
                    fc1, fc2 = st.columns(2)
                    with fc1:
                        invoice_data["n_facture"]    = st.text_input("N° Facture",
                            value=invoice_data.get("n_facture", ""),    key=f"nf_{pdf_file.name}")
                        invoice_data["beneficiaire"] = st.text_input("Bénéficiaire",
                            value=invoice_data.get("beneficiaire", ""), key=f"bn_{pdf_file.name}")
                        invoice_data["n_commande"]   = st.text_input("N° Commande",
                            value=invoice_data.get("n_commande", ""),   key=f"nc_{pdf_file.name}")
                        invoice_data["designation"]  = st.text_input("Désignation",
                            value=invoice_data.get("designation", ""),  key=f"dg_{pdf_file.name}")
                    with fc2:
                        invoice_data["montant_ht"]   = st.number_input("Montant HT (€)",
                            value=ht_disp,  step=0.01, key=f"ht_{pdf_file.name}")
                        invoice_data["montant_tva"]  = st.number_input("Montant TVA (€)",
                            value=tva_disp, step=0.01, key=f"tv_{pdf_file.name}")
                        # TTC read-only, always = HT + TVA
                        st.number_input(
                            "Montant TTC (€)  [= HT + TVA, auto]",
                            value=invoice_data["montant_ht"] + invoice_data["montant_tva"],
                            step=0.01, key=f"tc_{pdf_file.name}", disabled=True
                        )
                        invoice_data["moyen_paiement"] = st.selectbox(
                            "Moyen paiement",
                            ["Moyen paiement", "LCR", "Virement", "CB", "Chèque", "Prélèvement", "Traite", "?"],
                            key=f"mp_{pdf_file.name}"
                        )
                    st.form_submit_button("✅ Confirmer", use_container_width=True)

                all_invoice_data.append((pdf_file.name, invoice_data))

            except Exception as e:
                st.error(f"Erreur lors de l'extraction : {e}")

    st.divider()
    if all_invoice_data:
        if st.button("💾 Écrire dans Excel et télécharger", type="primary", use_container_width=True):
            rows_added = []
            for fname, inv_data in all_invoice_data:
                r = write_invoice_to_excel(wb, inv_data)
                rows_added.append((fname, r))

            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            st.success(f"✅ {len(rows_added)} facture(s) ajoutée(s) :")
            for fname, rnum in rows_added:
                st.write(f"  • **{fname}** → ligne {rnum}")

            orig_name = (excel_file.name
                         .replace(".xlsm", "_updated.xlsm")
                         .replace(".xlsx", "_updated.xlsx"))
            st.download_button(
                "⬇️ Télécharger le fichier Excel mis à jour",
                data=output,
                file_name=orig_name,
                mime="application/vnd.ms-excel.sheet.macroEnabled.12",
                use_container_width=True
            )


# ═══════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════

st.title("Ayada TDR - Tableau de Bord Stock")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3081/3081840.png", width=50)
st.sidebar.markdown("### Menu Principal")
st.sidebar.info("Téléchargez un fichier CSV ou Excel pour commencer l'analyse.")
fichier_telecharge = st.sidebar.file_uploader("📂 Fichier source stock", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        with st.spinner("Chargement et préparation des données..."):
            if extension_fichier == 'csv':
                df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
            elif extension_fichier == 'xlsx':
                df = pd.read_excel(fichier_telecharge)
            else:
                st.error("Format de fichier non supporté"); df = None

            if df is not None:
                df = clean_numeric_columns(df)
                df = clean_size_column(df)
                st.success("Données chargées avec succès!")

                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
                    "🏢 Fournisseur", "🔍 Modèle", "⚠️ Stock Négatif",
                    "👙 Anita", "🦶 Sidas", "💰 Valeur Stock",
                    "👟 Catégories", "📊 Tailles Manquantes", "📄 Factures"
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
                    st.dataframe(display_anita_sizes(df), use_container_width=True)

                with tab5:
                    st.subheader("Disponibilité Semelles Sidas")
                    for level, df_level in display_sidas_levels(df).items():
                        st.markdown(f"**Niveau {level}**")
                        st.dataframe(df_level.style.apply(highlight_row_if_one, axis=1), use_container_width=True)

                with tab6:
                    st.subheader("Valorisation par Fournisseur")
                    df_tv = total_stock_value_by_supplier(df)
                    st.metric("Valeur Totale Globale du Stock", f"{df_tv['Valeur Totale HT'].sum():,.2f} €".replace(',', ' '))
                    st.dataframe(df_tv, use_container_width=True)

                with tab7:
                    display_stock_by_family(df)

                with tab8:
                    st.subheader("Analyse de la profondeur de gamme (Chaussures)")
                    display_specific_designations(df.copy())

                with tab9:
                    render_invoice_tab()

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")

else:
    st.info("Utilisez la barre latérale pour charger un fichier stock, ou utilisez directement l'onglet Factures ci-dessous.")
    st.markdown("---")
    render_invoice_tab()
