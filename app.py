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
import threading
import logging

# ═══════════════════════════════════════════════════════════════
# LOGGING SETUP - Track data issues
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
    .invoice-badge { display: inline-block; padding: 4px 10px; border-radius: 99px; font-size: 12px; font-weight: 600; background: #EFF6FF; color: #3B82F6; margin-bottom: 12px; }
    .iban-box { background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 8px 14px; font-family: monospace; font-size: 13px; color: #166534; margin-top: 6px; }
    .data-quality-warning { background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 12px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# FIX #1: IMPROVED NUMERIC PARSING WITH FRENCH FORMAT SUPPORT
# ═══════════════════════════════════════════════════════════════
def parse_french_number(value):
    """
    Parse French-formatted numbers robustly.
    Handles: 1.234,50 | 1,50 | 1234.50 | 1 234,50 | €1.234,50
    Returns: float or None
    """
    if pd.isna(value):
        return None
    
    s = str(value).strip()
    
    # Remove currency symbols and whitespace
    s = re.sub(r'[€$]', '', s).strip()
    
    # Handle different thousands separators
    # French: 1.234,50 or 1 234,50
    # English: 1,234.50
    
    # Count commas and dots
    comma_count = s.count(',')
    dot_count = s.count('.')
    space_count = s.count(' ')
    
    try:
        # Case 1: European format "1.234,50" or "1 234,50"
        if comma_count == 1 and (dot_count == 1 or space_count > 0):
            # Remove thousands separators (dots and spaces)
            s = s.replace('.', '').replace(' ', '')
            # Replace decimal comma with dot
            s = s.replace(',', '.')
            return float(s)
        
        # Case 2: European format "1,50" (no thousands separator)
        elif comma_count == 1 and dot_count == 0:
            s = s.replace(',', '.')
            return float(s)
        
        # Case 3: English format "1,234.50" (comma as thousands separator)
        elif comma_count > 0 and dot_count == 1:
            s = s.replace(',', '')
            return float(s)
        
        # Case 4: Simple format "1234.50" or "1234"
        else:
            return float(s)
    
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse '{value}' as number: {e}")
        return None


def clean_numeric_columns_fixed(df):
    """
    FIX #1: Improved numeric column cleaning with logging.
    """
    conversion_failures = {}
    
    for col in ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found in dataframe")
            continue
        
        failures = 0
        parsed = []
        
        for idx, val in df[col].items():
            parsed_val = parse_french_number(val)
            if parsed_val is None and pd.notna(val):
                failures += 1
                logger.debug(f"Row {idx}, Col {col}: Failed to parse '{val}'")
            parsed.append(parsed_val)
        
        df[col] = parsed
        
        if failures > 0:
            conversion_failures[col] = failures
            logger.warning(f"Column '{col}': {failures} values could not be converted")
    
    if conversion_failures:
        st.warning(f"⚠️ **Conversion Issues Detected:**\n{conversion_failures}")
    
    return df, conversion_failures


def clean_size_column(df):
    """Clean size column (unchanged)."""
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df


# ═══════════════════════════════════════════════════════════════
# FIX #2: IMPROVED STOCK VALUE CALCULATION
# ═══════════════════════════════════════════════════════════════
def total_stock_value_by_supplier_fixed(df):
    """
    FIX #2: Robust stock value calculation that:
    - Handles missing columns
    - Includes NULL suppliers
    - Logs dropped rows
    """
    # Validate required columns exist
    required_cols = ['fournisseur', 'Qté stock dispo', 'Prix Achat']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"❌ Missing columns: {missing}")
        return pd.DataFrame()
    
    # Create working copy
    df_work = df.copy()
    
    # Safe numeric conversion
    df_work['Qté stock dispo'] = pd.to_numeric(df_work['Qté stock dispo'], errors='coerce')
    df_work['Prix Achat'] = pd.to_numeric(df_work['Prix Achat'], errors='coerce')
    
    # Flag rows with issues
    df_work['has_qty'] = df_work['Qté stock dispo'].notna() & (df_work['Qté stock dispo'] != 0)
    df_work['has_price'] = df_work['Prix Achat'].notna() & (df_work['Prix Achat'] != 0)
    
    rows_no_qty = (~df_work['has_qty']).sum()
    rows_no_price = (~df_work['has_price']).sum()
    rows_no_supplier = df_work['fournisseur'].isna().sum()
    
    if rows_no_qty > 0:
        st.warning(f"⚠️ {rows_no_qty} rows have no quantity")
    if rows_no_price > 0:
        st.warning(f"⚠️ {rows_no_price} rows have no price")
    if rows_no_supplier > 0:
        st.info(f"ℹ️ {rows_no_supplier} rows have NULL supplier (will appear as 'Unknown')")
    
    # Calculate value (NaN × anything = NaN, which is filtered out)
    df_work['Valeur Totale HT'] = df_work['Qté stock dispo'] * df_work['Prix Achat']
    
    # Replace NULL suppliers with 'Unknown' for grouping
    df_work['fournisseur'] = df_work['fournisseur'].fillna('Unknown')
    
    # Group and sum
    result = df_work.groupby('fournisseur', dropna=False)[['Valeur Totale HT']].sum().reset_index()
    result['Valeur Totale HT'] = result['Valeur Totale HT'].fillna(0)
    
    return result.sort_values(by='Valeur Totale HT', ascending=False)


# ═══════════════════════════════════════════════════════════════
# FIX #3: PDF EXTRACTION - SKIP FIRST PAGE
# ═══════════════════════════════════════════════════════════════
_pdf_extract_cache = {}

def extract_from_pdf_fixed(pdf_bytes, skip_first_page=True):
    """
    FIX #3: PDF extraction that skips cover page.
    - skip_first_page=True: Ignores page 0 (cover/header)
    - Returns tuple: (invoice_data, extracted_text)
    """
    cache_key = hashlib.md5(pdf_bytes).hexdigest()
    if cache_key in _pdf_extract_cache:
        return _pdf_extract_cache[cache_key]

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pages_text = []
        total_pages = len(pdf.pages)
        
        # Skip first page if requested
        start_idx = 1 if skip_first_page and total_pages > 1 else 0
        
        logger.info(f"Processing PDF: {total_pages} pages, starting from page {start_idx + 1}")
        
        for i, page in enumerate(pdf.pages):
            if i < start_idx:
                logger.debug(f"Skipping page {i + 1} (cover page)")
                continue
            
            t = page.extract_text()
            if t:
                pages_text.append(t)
            else:
                logger.warning(f"Page {i + 1}: No text extracted (may be image-only)")
        
        full_text = "\n".join(pages_text)
    
    text_upper = full_text.upper()

    # Router logic (unchanged - routes to correct extractor)
    if (
        "NEW BALANCE" in text_upper
        or "NEWBALANCE" in text_upper
        or re.search(r"Num[eé]ro de Facture\s*:\s*0\d{6}", full_text)
    ):
        result = extract_invoice_new_balance(full_text), full_text

    elif (
        "NÄAK" in text_upper
        or "NAAK" in text_upper
        or re.search(r"Facture\s+INV/\d{4}/\d+", full_text)
        or "NÄAK EUROPE" in text_upper
        or "SILLINGY" in text_upper
    ):
        result = extract_invoice_naak(full_text), full_text

    elif (
        "AMER SPORTS" in text_upper
        or "AMERSPORTS" in text_upper
        or "SERVICECLIENTS.FRANCE@AMERSPORTS" in text_upper
        or "VILLEFONTAINE" in text_upper
        or bool(re.search(r"N[°º]\s+de\s+facture\s*/\s*Date", full_text))
    ):
        result = extract_invoice_amer_sports(full_text), full_text

    elif (
        "VF (J) FRANCE" in full_text
        or re.search(r"\bAL[0-9A-Z]{6,}\b", full_text)
        or any(w in text_upper for w in [
            "EXPERIENCE FLOW", "LONE PEAK", "SUPERIOR", "OLYMPUS",
            "TIMP", "TORIN", "ESCALANTE", "ALTRA", "TIMBERLAND",
            "NORTH FACE", "VF FRANCE"
        ])
    ):
        result = extract_invoice_vf_altra(full_text), full_text

    elif any(w in full_text for w in ["Wolverine", "XODUS", "ENDORPHIN", "KINVARA",
                                       "TRIUMPH", "RIDE", "TEMPUS", "GUIDE"]):
        result = extract_invoice_saucony(full_text), full_text

    elif any(w in full_text for w in ["Deckers", "HOKA", "CHALLENGER", "CLIFTON",
                                       "BONDI", "SPEEDGOAT"]):
        result = extract_invoice_hoka(full_text), full_text

    else:
        result = extract_invoice_generic(full_text), full_text

    _pdf_extract_cache[cache_key] = result
    return result


# ═══════════════════════════════════════════════════════════════
# ALL EXTRACTOR FUNCTIONS (unchanged from original)
# ═══════════════════════════════════════════════════════════════

def parse_french_amount(s):
    if s is None:
        return None
    s = str(s).strip()
    s = re.sub(r'\s+', '', s)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return None

def parse_date_inv(s):
    if not s:
        return None
    s = s.strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except:
            pass
    return None

def _clean_iban(raw):
    if not raw:
        return ""
    return re.sub(r'\s+', ' ', raw.strip().upper())

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

def extract_invoice_new_balance(text):
    data = {}
    m = re.search(r"Nu\s*m\s*[eé\xe9]\s*r\s*o\s+de\s+Facture\s*:\s*(\d+)", text, re.IGNORECASE)
    if m:
        data["n_facture"] = m.group(1).strip()
    else:
        m = re.search(r"Facture\s*:\s*(\d{6,})", text)
        if m:
            data["n_facture"] = m.group(1).strip()
    m = re.search(r"Date de la Facture\s*:\s*([\d/]+)", text)
    if m:
        data["date_facture"] = parse_date_inv(m.group(1))
    m = re.search(r"Date d.Ech[eé]ance\s*:\s*([\d/]+)", text)
    if m:
        data["echeance"] = parse_date_inv(m.group(1))
    m = re.search(r"Num[eé]ro de Commande\s*:\s*(\S+)", text)
    if m:
        data["n_commande"] = m.group(1).strip()
    desig_lines = re.findall(r"^([A-Z][A-Z0-9 '/\-]{3,})\n", text, re.MULTILINE)
    _SKIP = {"NEW BALANCE FRANCE SARL", "HSBC FRANCE", "FRANCE", "A SUIVRE",
              "TVA SUR LES DEBITS", "EUR EURO", "VIREMENT BANCAIRE"}
    seen = []
    for line in desig_lines:
        clean = line.strip()
        if clean.upper() not in _SKIP and len(clean) > 3 and clean not in seen:
            seen.append(clean)
    if seen:
        data["designation"] = " / ".join(seen[:6])
    m = re.search(r"Total HT\s+([\d\s.,]+)", text)
    if m:
        data["montant_ht"] = parse_french_amount(m.group(1))
    m = re.search(r"Montant TVA\s+([\d\s.,]+)", text)
    if m:
        data["montant_tva"] = parse_french_amount(m.group(1))
    m = re.search(r"TOTAL TTC\s+([\d\s.,]+)", text)
    if m:
        data["_ttc_pdf"] = parse_french_amount(m.group(1))
    m = re.search(r"IBAN\s*:\s*(FR[\d\s]+\d)", text)
    if m:
        data["iban"] = _clean_iban(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = round(ht + tva, 2)
    data.update({
        "beneficiaire":      "new balance",
        "categorie":         "Achats marchandises",
        "statut":            "Attente règlement",
        "moyen_paiement":    "Virement",
        "date_transmission": "A transmettre",
        "source":            "New Balance France",
    })
    return data

def extract_invoice_naak(text):
    data = {}
    m = re.search(r"Facture\s+(INV/[\d/]+)", text)
    if m:
        data["n_facture"] = m.group(1).strip()
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})\s+\d{4}-\d{2}-\d{2}\s+(\S+)", text)
    if m:
        data["date_facture"] = parse_date_inv(m.group(1))
        data["echeance"]     = parse_date_inv(m.group(2))
        data["n_commande"]   = m.group(3).strip()
    else:
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        if dates:
            data["date_facture"] = parse_date_inv(dates[0])
        if len(dates) >= 2:
            data["echeance"] = parse_date_inv(dates[1])
        m2 = re.search(r"Origine\s*[:\s]+\n?\s*(\S+)", text)
        if m2:
            data["n_commande"] = m2.group(1).strip()
    product_lines = re.findall(r"Energy\s+(?:Puree|Gel|Bar|Waffle|Drink Mix)[^\n]+", text, re.IGNORECASE)
    if product_lines:
        short = []
        seen_labels = set()
        for line in product_lines:
            m2 = re.match(r"(Energy\s+\w+\s*\|?\s*[\w\s]+?)(?:\s*-\s*\d+|\s*\d+\.)", line, re.IGNORECASE)
            label = (m2.group(1) if m2 else line[:50]).strip().rstrip("|").strip()
            if label not in seen_labels:
                seen_labels.add(label)
                short.append(label)
        data["designation"] = " / ".join(short[:4]) + (" / …" if len(short) > 4 else "")
    else:
        data["designation"] = "Nutrition / Compléments sportifs"
    m = re.search(r"Montant hors taxes\s+([\d\s,\.]+)\s*€", text)
    if m:
        data["montant_ht"] = parse_french_amount(m.group(1))
    tva_total = 0.0
    for tva_match in re.finditer(r"TVA\s+[\d,\.]+\s*%\s+on\s+[\d\s,\.]+\s*€\s+([\d\s,\.]+)\s*€", text):
        val = parse_french_amount(tva_match.group(1))
        if val:
            tva_total += val
    if tva_total:
        data["montant_tva"] = round(tva_total, 2)
    m = re.search(r"\bTotal\b\s+([\d\s,\.]+)\s*€", text)
    if m:
        data["_ttc_pdf"] = parse_french_amount(m.group(1))
    m = re.search(r"IBAN\s*:\s*(FR[\d\s]+\d)", text)
    if m:
        data["iban"] = _clean_iban(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = round(ht + tva, 2)
    data.update({
        "beneficiaire":      "näak",
        "categorie":         "Achats marchandises",
        "statut":            "Attente règlement",
        "moyen_paiement":    "Virement",
        "date_transmission": "A transmettre",
        "source":            "Näak Europe",
    })
    return data

def extract_invoice_amer_sports(text):
    data = {}
    lines = text.split('\n')
    values_line  = None
    dates_line   = None
    for i, line in enumerate(lines):
        if re.match(r"^\d{10}\s+\d{10}\s+\S", line):
            values_line = line
            for j in range(i+1, min(i+4, len(lines))):
                if re.match(r"^\d{2}\.\d{2}\.\d{4}", lines[j]):
                    dates_line = lines[j]
                    break
            break
    if values_line:
        m = re.match(r"^(\d{10})\s+(\d{10})\s+(.+?)\s+(\d{6})\s*$", values_line.strip())
        if m:
            data["n_facture"]  = m.group(1)
            data["n_commande"] = m.group(3).strip()
        else:
            m2 = re.match(r"^(\d{7,})", values_line.strip())
            if m2:
                data["n_facture"] = m2.group(1)
    else:
        m = re.search(r"\bFacture\s+(\d{7,})", text)
        if m:
            data["n_facture"] = m.group(1).strip()
    if dates_line:
        m = re.match(r"^(\d{2}\.\d{2}\.\d{4})", dates_line.strip())
        if m:
            data["date_facture"] = parse_date_inv(m.group(1))
    m = re.search(r"Ech[eé]ance\s*:\s*\n?\s*(\d{2}\.\d{2}\.\d{4})", text)
    if m:
        data["echeance"] = parse_date_inv(m.group(1))
    else:
        m = re.search(r"Ech[eé]ance\s*:\s*(\d{2}\.\d{2}\.\d{4})", text)
        if m:
            data["echeance"] = parse_date_inv(m.group(1))
    brands_found = re.findall(r"^(SALOMON|ATOMIC|WILSON|ARC'TERYX|PEAK PERFORMANCE|ARMADA|MAVIC|ENVE|SUUNTO)\s*$", text, re.MULTILINE | re.IGNORECASE)
    if brands_found:
        unique_brands = list(dict.fromkeys(b.title() for b in brands_found))
        data["beneficiaire"] = " / ".join(unique_brands).lower()
    else:
        data["beneficiaire"] = "salomon"
    desig_matches = re.findall(r"^\d+\s+[LC]{1,2}\d{6,8}\s+([A-Z][A-Z0-9 '\-/\.]+?)(?:\s+\d+\s*(?:PR|EA|PC))", text, re.MULTILINE)
    if desig_matches:
        seen = []
        for d in desig_matches:
            clean = d.strip()
            if clean and clean not in seen:
                seen.append(clean)
        data["designation"] = " / ".join(seen[:5]) + (" / …" if len(seen) > 5 else "")
    else:
        m = re.search(r"(AERO GLIDE|ULTRA GLIDE|GENESIS|SPEEDCROSS|SENSE RIDE|PULSAR|TRAIL BLAZER|ADV SKIN|SOFT FLASK|SENSE FLOW|XA PRO)[^\n]*", text, re.IGNORECASE)
        if m:
            data["designation"] = m.group(0).strip()[:120]
    m = re.search(r"TOTAL\s+NET\s+HT\s+([\d\s.,]+)", text)
    if m:
        data["montant_ht"] = parse_french_amount(m.group(1))
    m = re.search(r"TVA\s+[\d,]+\s*%\s+de\s+[\d\s.,]+\s+([\d\s.,]+)", text)
    if m:
        data["montant_tva"] = parse_french_amount(m.group(1))
    m = re.search(r"NET\s+A\s+PAYER\s+EUR\s+([\d\s.,]+)", text)
    if m:
        data["_ttc_pdf"] = parse_french_amount(m.group(1))
    m = re.search(r"IBAN\s*:\s*(FR[\d\s]+\d)", text)
    if m:
        data["iban"] = _clean_iban(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = round(ht + tva, 2)
    data.update({
        "categorie":         "Achats marchandises",
        "statut":            "Attente règlement",
        "moyen_paiement":    "LCR",
        "date_transmission": "A transmettre",
        "source":            "Amer Sports (Salomon / Atomic / Wilson…)",
    })
    return data

def extract_invoice_vf_altra(text):
    data = {}
    m = re.search(r"\bFacture\s+(\d{6,})", text)
    if m:
        data["n_facture"] = m.group(1)
    m = re.search(r"Date facture\s+([\d.]+)", text)
    if m:
        data["date_facture"] = parse_date_inv(m.group(1))
    else:
        m = re.search(r"\bDate\b\s+(\d{2}\.\d{2}\.\d{2,4})", text)
        if m:
            data["date_facture"] = parse_date_inv(m.group(1))
    m = re.search(r"Date\s+d\s+[ée]ch[ée]ance\s+([\d.]+)", text)
    if m:
        data["echeance"] = parse_date_inv(m.group(1))
    m = re.search(r"No\.\s*cmmde\.\s*:\s*(\S+)", text)
    if m:
        data["n_commande"] = m.group(1)
    desig_matches = re.findall(r"^([A-Z]{2}[A-Z0-9]{6,})\s+([A-Z][A-Z0-9 /\-]+?)\s+\d+\s+[\d,]+", text, re.MULTILINE)
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
        m = re.search(r"(EXPERIENCE FLOW|LONE PEAK|SUPERIOR|OLYMPUS|TIMP|TORIN|ESCALANTE|RIVERA|PARADIGM|PROVISION)[^\n]*", text, re.IGNORECASE)
        if m:
            data["designation"] = m.group(0).strip()[:120]
    m = re.search(r"Total montant net\s+([\d\s.,]+)", text)
    if m:
        data["montant_ht"] = parse_french_amount(m.group(1))
    m = re.search(r"Total TVA\s+([\d\s.,]+)", text)
    if m:
        data["montant_tva"] = parse_french_amount(m.group(1))
    m = re.search(r"IBAN\s*:\s*(FR[\d\s]+\d)", text)
    if m:
        data["iban"] = _clean_iban(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = round(ht + tva, 2)
    data.update({
        "categorie":         "Achats marchandises",
        "statut":            "Attente règlement",
        "moyen_paiement":    "Moyen paiement",
        "date_transmission": "A transmettre",
        "source":            "VF France (Altra / Timberland / TNF / Vans)",
    })
    return data

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
    m = re.search(r"IBAN\s*:\s*(FR[\d\s]+\d)", text)
    if m: data["iban"] = _clean_iban(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = round(ht + tva, 2)
    products = re.findall(r"(XODUS|ENDORPHIN|KINVARA|TRIUMPH|RIDE|TEMPUS|GUIDE)[^\n]+", text)
    if products and not data.get("designation"):
        data["designation"] = " / ".join(set(products))[:100]
    data.update({"categorie": "Achats marchandises", "statut": "Attente règlement",
                 "moyen_paiement": "Moyen paiement", "date_transmission": "A transmettre",
                 "source": "Saucony / Wolverine"})
    return data

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
    m = re.search(r"IBAN\s*:\s*(FR[\d\s]+\d)", text)
    if m: data["iban"] = _clean_iban(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = round(ht + tva, 2)
    products = re.findall(r"\d{7}-([A-Z0-9 /]+)\n", text)
    if products: data["designation"] = " / ".join(set(products))[:100]
    else:
        m = re.search(r"(CHALLENGER|CLIFTON|BONDI|MAFATE|SPEEDGOAT|RINCON|ARAHI)[^\n]*", text)
        if m: data["designation"] = m.group(0).strip()[:100]
    data.update({"categorie": "Achats marchandises", "statut": "Attente règlement",
                 "moyen_paiement": "Moyen paiement", "date_transmission": "A transmettre",
                 "source": "HOKA / Deckers"})
    return data

def extract_invoice_generic(text):
    data = {}
    for pat in [r"[Ff]acture\s*N[°º]?\s*[:\s]*([\w\-/]+)", r"N[°º]\s+[Ff]acture\s*[:\s]*([\w\-]+)"]:
        m = re.search(pat, text)
        if m: data["n_facture"] = m.group(1).strip(); break
    m = re.search(r"(\d{1,2}[./]\d{2}[./]\d{2,4})", text)
    if m: data["date_facture"] = parse_date_inv(m.group(1))
    for label, key in [("Montant HT", "montant_ht"), ("TVA", "montant_tva")]:
        m = re.search(label + r"[^\d]*([\d.,]+)", text, re.IGNORECASE)
        if m and key not in data: data[key] = parse_french_amount(m.group(1))
    m = re.search(r"IBAN\s*:\s*(FR[\d\s]+\d)", text)
    if m: data["iban"] = _clean_iban(m.group(1))
    ht  = data.get("montant_ht")  or 0.0
    tva = data.get("montant_tva") or 0.0
    data["montant_ttc"] = round(ht + tva, 2)
    data.update({"beneficiaire": "?", "categorie": "Achats marchandises", "statut": "Attente règlement",
                 "moyen_paiement": "Moyen paiement", "date_transmission": "A transmettre",
                 "source": "Format générique"})
    return data

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (mostly unchanged)
# ═══════════════════════════════════════════════════════════════

def highlight_row_if_one(row):
    if row['Qté stock dispo'] == 1:
        return ['background-color: #FEE2E2; color: #991B1B' for _ in row]
    return [''] * len(row)

def find_next_empty_row(ws):
    return ws.max_row + 1

def write_invoice_to_excel(wb, d):
    ws = wb["Dépenses"]
    row = find_next_empty_row(ws)
    df_date = d.get("date_facture")
    ech     = d.get("echeance")
    ht      = d.get("montant_ht")  or 0
    tva     = d.get("montant_tva") or 0
    ttc     = round(ht + tva, 2)

    iban_str    = d.get("iban", "")
    commentaire = d.get("commentaire", "")
    if iban_str and "IBAN" not in commentaire:
        commentaire = f"IBAN: {iban_str}" + (f" | {commentaire}" if commentaire else "")

    import datetime as _dt
    def _to_datetime(v):
        if v is None:
            return None
        if isinstance(v, _dt.date) and not isinstance(v, _dt.datetime):
            return _dt.datetime(v.year, v.month, v.day)
        return v

    vals = [
        _to_datetime(df_date), _to_datetime(df_date), _to_datetime(ech), None,
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
        commentaire,
    ]

    for col, val in enumerate(vals, start=1):
        ws.cell(row=row, column=col).value = val

    return row

# ═══════════════════════════════════════════════════════════════
# INVOICE TAB (with FIX #3 integrated)
# ═══════════════════════════════════════════════════════════════

def render_invoice_tab():
    st.subheader("📄 Extraction de Factures → Excel")
    st.markdown("Importez vos factures PDF et votre fichier Excel. Les données extraites seront ajoutées à l'onglet **Dépenses**.")
    st.info("✅ **Amélioration:** First page (cover) is now automatically skipped during PDF processing.")

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

    if ("inv_wb_bytes" not in st.session_state or st.session_state.get("inv_excel_name") != excel_file.name):
        st.session_state.inv_wb_bytes   = excel_file.read()
        st.session_state.inv_excel_name = excel_file.name
        st.session_state.inv_wb_object  = None

    if st.session_state.get("inv_wb_object") is None:
        with st.spinner("📂 Chargement du classeur Excel..."):
            st.session_state.inv_wb_object = openpyxl.load_workbook(
                io.BytesIO(st.session_state.inv_wb_bytes), keep_vba=True
            )
    wb = st.session_state.inv_wb_object

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
                # FIX #3: Use improved extract function
                invoice_data, _ = extract_from_pdf_fixed(pdf_bytes_cached, skip_first_page=True)

                st.markdown(f"<span class='invoice-badge'>🔍 {invoice_data.get('source', '?')}</span>", unsafe_allow_html=True)

                df_date  = invoice_data.get("date_facture")
                ech_date = invoice_data.get("echeance")
                ht_disp  = float(invoice_data.get("montant_ht")  or 0.0)
                tva_disp = float(invoice_data.get("montant_tva") or 0.0)
                ttc_disp = round(ht_disp + tva_disp, 2)
                iban_val = invoice_data.get("iban", "")

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

                if iban_val:
                    st.markdown(f"<div class='iban-box'>🏦 IBAN : <b>{iban_val}</b></div>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ IBAN non détecté dans ce PDF.")

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
                        invoice_data["iban"]         = st.text_input("IBAN",
                            value=iban_val,                              key=f"ib_{pdf_file.name}")
                    with fc2:
                        invoice_data["montant_ht"]   = st.number_input("Montant HT (€)",
                            value=ht_disp,  step=0.01, key=f"ht_{pdf_file.name}")
                        invoice_data["montant_tva"]  = st.number_input("Montant TVA (€)",
                            value=tva_disp, step=0.01, key=f"tv_{pdf_file.name}")
                        st.number_input("Montant TTC (€)  [= HT + TVA, auto]",
                            value=invoice_data["montant_ht"] + invoice_data["montant_tva"],
                            step=0.01, key=f"tc_{pdf_file.name}", disabled=True)
                        invoice_data["moyen_paiement"] = st.selectbox(
                            "Moyen paiement",
                            ["Virement", "Moyen paiement", "LCR", "CB", "Chèque", "Prélèvement", "Traite", "?"],
                            index=0 if invoice_data.get("moyen_paiement") == "Virement" else 1,
                            key=f"mp_{pdf_file.name}")
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

            save_result = {}
            def _do_save(wb, holder):
                out = io.BytesIO()
                wb.save(out)
                holder['bytes'] = out.getvalue()

            t = threading.Thread(target=_do_save, args=(wb, save_result))
            t.start()
            with st.spinner("💾 Génération du fichier Excel..."):
                t.join()

            output = io.BytesIO(save_result['bytes'])
            output.seek(0)
            st.session_state.inv_wb_object = None

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

st.title("Ayada TDR - Tableau de Bord Stock ✅ FIXED")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3081/3081840.png", width=50)
st.sidebar.markdown("### Menu Principal")
st.sidebar.info("✅ **Corrections appliquées:**\n- Meilleure gestion des nombres français\n- Valeurs stock plus précises\n- Première page PDF ignorée\n- Rapports d'erreurs détaillés")
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
                # FIX #1: Use improved numeric cleaning
                df, conv_failures = clean_numeric_columns_fixed(df)
                df = clean_size_column(df)
                st.success("✅ Données chargées avec succès!")

                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
                    "🏢 Fournisseur", "🔍 Modèle", "⚠️ Stock Négatif",
                    "👙 Anita", "🦶 Sidas", "💰 Valeur Stock",
                    "👟 Catégories", "📊 Tailles Manquantes", "📄 Factures"
                ])

                with tab6:
                    st.subheader("Valorisation par Fournisseur")
                    # FIX #2: Use improved stock value function
                    df_tv = total_stock_value_by_supplier_fixed(df)
                    if not df_tv.empty:
                        st.metric("Valeur Totale Globale du Stock", 
                                 f"{df_tv['Valeur Totale HT'].sum():,.2f} €".replace(',', ' '))
                        st.dataframe(df_tv, use_container_width=True)

                with tab9:
                    render_invoice_tab()

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
        logger.exception("Critical error in file processing")

else:
    st.info("Utilisez la barre latérale pour charger un fichier stock.")
    st.markdown("---")
    render_invoice_tab()
