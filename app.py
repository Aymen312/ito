import streamlit as st
import pandas as pd
from io import BytesIO
import numpy as np
import re
import logging

# ═══════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    .data-alert { background: #FEE2E2; border-left: 4px solid #DC2626; padding: 12px; border-radius: 4px; color: #991B1B; }
    .data-complete { background: #DCFCE7; border-left: 4px solid #16A34A; padding: 12px; border-radius: 4px; color: #15803D; }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# ROBUST NUMBER PARSING - French & English formats
# ═══════════════════════════════════════════════════════════════

def parse_french_number(value):
    """
    Parse numbers in French or English format.
    Handles: 1.234,50 | 1,50 | 1234.50 | 1 234,50
    """
    if pd.isna(value):
        return None
    
    s = str(value).strip()
    if not s or s.lower() in ['', 'nan', 'none', '-']:
        return None
    
    s = re.sub(r'[€$]', '', s).strip()
    
    comma_count = s.count(',')
    dot_count = s.count('.')
    space_count = s.count(' ')
    
    try:
        # European: "1.234,50" or "1 234,50"
        if comma_count == 1 and (dot_count == 1 or space_count > 0):
            s = s.replace('.', '').replace(' ', '')
            s = s.replace(',', '.')
            val = float(s)
            return val if val > 0 else None
        
        # European: "1,50"
        elif comma_count == 1 and dot_count == 0:
            s = s.replace(',', '.')
            val = float(s)
            return val if val > 0 else None
        
        # English: "1,234.50"
        elif comma_count > 0 and dot_count == 1:
            s = s.replace(',', '')
            val = float(s)
            return val if val > 0 else None
        
        # Simple: "1234.50" or "1234"
        else:
            val = float(s)
            return val if val > 0 else None
    except:
        return None


def analyze_file_completeness(df):
    """
    Analyze data completeness and determine file type.
    Returns: (data_completeness, has_prices, rows_with_price, rows_without_price)
    """
    total_rows = len(df)
    
    # Check for price column variations
    price_cols = ['Prix Achat', 'Prix d\'achat', 'Prix Achat HT', 'Montant HT', 'Cost', 'Price']
    price_col = None
    
    for col in price_cols:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        # No price column found
        return {
            'completeness': 'NO_PRICES',
            'has_prices': False,
            'price_column': None,
            'rows_with_price': 0,
            'rows_without_price': total_rows,
            'percentage_complete': 0,
            'message': '⚠️ No price column found - Working with quantities only'
        }
    
    # Check how many rows have prices
    rows_with_price = df[price_col].notna().sum()
    rows_without_price = total_rows - rows_with_price
    percentage = (rows_with_price / total_rows * 100) if total_rows > 0 else 0
    
    if rows_with_price == 0:
        completeness = 'NO_DATA'
        message = f'⚠️ Price column "{price_col}" exists but all values are empty'
    elif rows_with_price < total_rows * 0.5:
        completeness = 'INCOMPLETE'
        message = f'⚠️ Only {rows_with_price:,}/{total_rows:,} items have prices ({percentage:.1f}%)'
    elif rows_with_price < total_rows:
        completeness = 'MOSTLY_COMPLETE'
        message = f'⚠️ {rows_without_price:,} items missing prices ({100-percentage:.1f}%)'
    else:
        completeness = 'COMPLETE'
        message = f'✅ All {total_rows:,} items have valid prices'
    
    return {
        'completeness': completeness,
        'has_prices': rows_with_price > 0,
        'price_column': price_col,
        'rows_with_price': rows_with_price,
        'rows_without_price': rows_without_price,
        'percentage_complete': percentage,
        'message': message
    }


def clean_numeric_columns_smart(df, price_column):
    """
    Smart cleaning that handles both complete and incomplete data.
    """
    conversion_failures = {}
    rows_cleaned = 0
    
    # Parse numeric columns
    for col in ['Prix Achat', price_column, 'Qté stock dispo', 'Valeur Stock', 'Montant HT']:
        if col not in df.columns or col is None:
            continue
        
        parsed = []
        failures = 0
        
        for val in df[col]:
            parsed_val = parse_french_number(val)
            if parsed_val is None and pd.notna(val):
                failures += 1
            parsed.append(parsed_val)
        
        df[col] = parsed
        
        if failures > 0:
            conversion_failures[col] = failures
            logger.warning(f"Column '{col}': {failures} failed conversions")
    
    return df, conversion_failures


def clean_size_column(df):
    """Clean size column."""
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df


# ═══════════════════════════════════════════════════════════════
# STOCK ANALYSIS - Handles both complete and incomplete data
# ═══════════════════════════════════════════════════════════════

def calculate_stock_value(df, price_column):
    """
    Calculate stock value by supplier.
    Handles both complete and incomplete price data.
    """
    if price_column not in df.columns:
        return None
    
    df_work = df.copy()
    
    # Parse numeric columns
    df_work['Qté stock dispo'] = pd.to_numeric(df_work['Qté stock dispo'], errors='coerce')
    df_work[price_column] = pd.to_numeric(df_work[price_column], errors='coerce')
    
    # For items WITH prices: calculate value
    df_with_price = df_work[df_work[price_column].notna() & (df_work[price_column] > 0)].copy()
    
    if len(df_with_price) > 0:
        df_with_price['Valeur Totale HT'] = df_with_price['Qté stock dispo'] * df_with_price[price_column]
        df_with_price['fournisseur'] = df_with_price['fournisseur'].fillna('Unknown')
        
        result = df_with_price.groupby('fournisseur', dropna=False).agg({
            'designation': 'count',
            'Qté stock dispo': 'sum',
            'Valeur Totale HT': 'sum'
        }).rename(columns={'designation': 'Items'}).reset_index()
        
        result = result.sort_values('Valeur Totale HT', ascending=False)
        return result
    
    return None


def highlight_row_if_one(row):
    """Highlight rows with quantity = 1."""
    if 'Qté stock dispo' in row.index and row['Qté stock dispo'] == 1:
        return ['background-color: #FEE2E2; color: #991B1B' for _ in row]
    return [''] * len(row)


# ═══════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════

st.title("Ayada TDR - Tableau de Bord Stock ✨")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3081/3081840.png", width=50)
st.sidebar.markdown("### Menu Principal")
st.sidebar.info(
    "✅ **Smart Analysis:**\n"
    "📊 Works with complete prices\n"
    "📊 Works with partial prices\n"
    "📊 Works without prices\n"
    "🔄 Automatic data detection"
)

fichier_telecharge = st.sidebar.file_uploader("📂 Fichier source stock", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        with st.spinner("Chargement et analyse des données..."):
            if extension_fichier == 'csv':
                df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
            elif extension_fichier == 'xlsx':
                df = pd.read_excel(fichier_telecharge)
            else:
                st.error("Format de fichier non supporté")
                df = None

            if df is not None:
                initial_row_count = len(df)
                
                # ANALYZE DATA COMPLETENESS
                completeness_info = analyze_file_completeness(df)
                price_column = completeness_info['price_column']
                
                # Display data quality alert
                if completeness_info['completeness'] == 'COMPLETE':
                    st.markdown(
                        f"<div class='data-complete'>{completeness_info['message']}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div class='data-alert'>{completeness_info['message']}</div>",
                        unsafe_allow_html=True
                    )
                
                # Clean numeric columns
                df, conv_failures = clean_numeric_columns_smart(df, price_column)
                df = clean_size_column(df)
                
                # Show summary
                st.success(f"✅ Données chargées: {initial_row_count:,} articles")
                
                if completeness_info['has_prices']:
                    with_price = completeness_info['rows_with_price']
                    without_price = completeness_info['rows_without_price']
                    st.info(
                        f"📊 **Stock Summary:**\n"
                        f"- Items with prices: {with_price:,} ✅\n"
                        f"- Items without prices: {without_price:,} ⚠️\n"
                        f"- Data completeness: {completeness_info['percentage_complete']:.1f}%"
                    )

                # CREATE TABS
                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                    "🏢 Fournisseur", "🔍 Modèle", "⚠️ Stock Négatif",
                    "👙 Anita", "🦶 Sidas", "💰 Valeur Stock",
                    "👟 Catégories", "📊 Tailles"
                ])

                with tab1:
                    st.subheader("Rechercher par Fournisseur")
                    fournisseur = st.text_input("Entrez le nom du fournisseur:")
                    if fournisseur:
                        fournisseur = fournisseur.strip().upper()
                        df['fournisseur'] = df['fournisseur'].fillna('')
                        df_filtered = df[df['fournisseur'].str.upper() == fournisseur]
                        if not df_filtered.empty:
                            st.write(f"**{len(df_filtered)} articles trouvés**")
                            st.dataframe(df_filtered, use_container_width=True)
                        else:
                            st.warning("Aucun article trouvé pour ce fournisseur")

                with tab2:
                    st.subheader("Rechercher par Modèle")
                    designation = st.text_input("Entrez le modèle/désignation:")
                    if designation:
                        designation = designation.strip().upper()
                        df['designation'] = df['designation'].fillna('')
                        df_filtered = df[df['designation'].str.upper().str.contains(designation)]
                        if not df_filtered.empty:
                            st.write(f"**{len(df_filtered)} articles trouvés**")
                            st.dataframe(df_filtered, use_container_width=True)
                        else:
                            st.warning("Aucun article trouvé pour ce modèle")

                with tab3:
                    st.subheader("⚠️ Stock Négatif")
                    df['Qté stock dispo'] = pd.to_numeric(df['Qté stock dispo'], errors='coerce').fillna(0)
                    df_negative = df[df['Qté stock dispo'] < 0]
                    if not df_negative.empty:
                        st.dataframe(df_negative, use_container_width=True)
                    else:
                        st.success("✅ Aucun stock négatif")

                with tab6:
                    st.subheader("💰 Valorisation Stock")
                    
                    if completeness_info['has_prices']:
                        df_tv = calculate_stock_value(df, price_column)
                        if df_tv is not None and not df_tv.empty:
                            total_value = df_tv['Valeur Totale HT'].sum()
                            st.metric("Valeur Totale Stock", f"€{total_value:,.2f}".replace(',', ' '))
                            
                            # Display by supplier
                            st.dataframe(df_tv, use_container_width=True)
                            
                            # Export option
                            csv = df_tv.to_csv(index=False, sep=';')
                            st.download_button(
                                "📥 Télécharger valorisation CSV",
                                data=csv,
                                file_name="stock_value_by_supplier.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("Aucune donnée de prix disponible pour cette analyse")
                    else:
                        st.warning("⚠️ Pas de colonne prix trouvée - impossible de calculer la valorisation")
                        st.info("Conseil: Vérifiez que votre fichier contient une colonne 'Prix Achat'")

                with tab7:
                    st.subheader("👟 Catégories de Produits")
                    if 'famille' in df.columns:
                        families = df['famille'].fillna('Autres').unique()
                        selected_family = st.selectbox("Sélectionnez une catégorie:", families)
                        
                        df['famille'] = df['famille'].fillna('Autres')
                        df_family = df[df['famille'] == selected_family]
                        
                        st.write(f"**{len(df_family)} articles dans {selected_family}**")
                        st.dataframe(df_family, use_container_width=True)
                    else:
                        st.info("Colonne 'famille' non trouvée")

                with tab8:
                    st.subheader("📊 Analyse des Tailles")
                    if 'taille' in df.columns:
                        sizes = df['taille'].value_counts().head(20)
                        st.bar_chart(sizes)
                        st.dataframe(sizes.reset_index(), use_container_width=True)
                    else:
                        st.info("Colonne 'taille' non trouvée")

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
        logger.exception("Critical error in file processing")

else:
    st.info("📂 Chargez votre fichier stock pour commencer l'analyse")
    st.markdown("---")
    st.markdown("""
    ## 🎯 Utilisation
    
    1. **Préparation du fichier:**
       - Format: CSV ou Excel
       - Encodage: UTF-8 ou ISO-8859-1
       - Séparateur: Point-virgule (;) pour CSV
    
    2. **Colonnes requises (minimum):**
       - `fournisseur` - Nom du fournisseur
       - `designation` - Nom du produit
       - `Qté stock dispo` - Quantité en stock
       - `taille` - Taille (optionnel)
    
    3. **Colonnes optionnelles (pour valorisation):**
       - `Prix Achat` - Prix unitaire
       - `famille` - Catégorie produit
    
    4. **Fonctionnalités:**
       - ✅ Recherche par fournisseur
       - ✅ Recherche par modèle
       - ✅ Détection stock négatif
       - ✅ Valorisation par fournisseur (si prix disponibles)
       - ✅ Analyse par catégorie
       - ✅ Distribution des tailles
    """)
