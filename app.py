import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Function to clean numeric columns
def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

# Function to strip leading and trailing spaces from sizes
def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

# Function to convert shoe size to EU size (for display purposes only)
def convert_to_eu_size(size):
    try:
        size = str(size).strip().upper()
        if size.endswith("US"):
            us_size = float(size.replace("US", "").strip())
            return us_size + 33  # Example conversion
        elif size.endswith("UK"):
            uk_size = float(size.replace("UK", "").strip())
            return uk_size + 34  # Example conversion
        else:
            return float(size)  # Assuming it's already in EU size
    except ValueError:
        return None

# Function to convert the entire dataframe's shoe sizes to EU sizes for display
def convert_dataframe_to_eu(df):
    df['taille_originale'] = df['taille']
    df['taille_eu'] = df['taille'].apply(convert_to_eu_size)
    return df

# Function to filter women's shoes
def filter_womens_shoes(df):
    return df[df['designation'].str.contains('WOMAN', na=False, case=False) | df['designation'].str.contains('W', na=False, case=False)]

# Function to filter by shoe designation
def filter_by_designation(df, keyword):
    keyword = keyword.strip().lower()  # Convert keyword to lowercase for case insensitive search
    return df[df['designation'].str.lower().str.contains(keyword, na=False)]

# Function to create PDF report
def creer_pdf(df_filtered, df_women_filtered, keyword_designation):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Start writing PDF content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Chaussures par Désignation")
    c.setFont("Helvetica", 12)
    
    y_position = 720
    
    if not df_filtered.empty:
        # Add shoe designation analysis
        c.drawString(50, y_position, f"Analyse pour le Mot-clé de Désignation '{keyword_designation}':")
        y_position -= 20
        for idx, (_, row) in enumerate(df_filtered.iterrows(), start=1):
            taille = f"{row['taille']} ({row['taille_originale']})" if row['taille_originale'] else row['taille']
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille = {taille}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(df_filtered) * 20 + 20
    
    if not df_women_filtered.empty:
        # Add women's shoes analysis
        c.drawString(50, y_position, f"Chaussures pour Femmes avec Désignation '{keyword_designation}':")
        y_position -= 20
        for idx, (_, row) in enumerate(df_women_filtered.iterrows(), start=1):
            taille = f"{row['taille']} ({row['taille_originale']})" if row['taille_originale'] else row['taille']
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille = {taille}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(df_women_filtered) * 20 + 20
    
    # Save PDF to buffer
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# Function to filter negative stock
def filter_negative_stock(df):
    return df[df['Qté stock dispo'] < 0]

# Function to filter by supplier and display corresponding data
def display_supplier_info(df, fournisseur):
    fournisseur = fournisseur.strip().upper()  # Convert user input supplier to uppercase
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame()
    return df_filtered

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Chaussures", layout="wide")

# Custom CSS for futuristic design
st.markdown("""
    <style>
        body {
            background: linear-gradient(135deg, #1E1E1E, #2D2D2D);
            color: #F5F5F5;
            font-family: 'Arial', sans-serif;
        }
        .stButton>button {
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 14px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
        .stTextInput>div>input {
            border: 2px solid #007BFF;
            border-radius: 5px;
            padding: 10px;
            background-color: #1E1E1E;
            color: #F5F5F5;
        }
        .stTextInput>div>input:focus {
            border-color: #0056b3;
            outline: none;
        }
        .stMultiSelect>div>div {
            border: 2px solid #007BFF;
            border-radius: 5px;
            background-color: #1E1E1E;
            color: #F5F5F5;
        }
        .stMultiSelect>div>div>div>div {
            color: #F5F5F5;
        }
        .stExpander>div>div {
            background-color: #2D2D2D;
            color: #F5F5F5;
            border-radius: 5px;
            padding: 10px;
        }
        .stExpander>div>div>div {
            color: #F5F5F5;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("Application d'Analyse de Chaussures")

st.sidebar.markdown("### Menu")
st.sidebar.info("Téléchargez un fichier CSV ou Excel pour commencer l'analyse.")

# File upload
fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        with st.spinner("Chargement des données..."):
            if extension_fichier == 'csv':
                # Read CSV with proper encoding and separator
                df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
            elif extension_fichier == 'xlsx':
                df = pd.read_excel(fichier_telecharge)
            else:
                st.error("Format de fichier non supporté")
                df = None

        if df is not None:
            # Clean data
            df = clean_numeric_columns(df)
            df = clean_size_column(df)  # Clean size column
            
            # Convert sizes to EU sizes for display purposes only
            df = convert_dataframe_to_eu(df)
            
            # Display all data initially
            st.subheader("Visualisation des Données")
            st.dataframe(df)
            
            # Ask for shoe designation keyword
            keyword_designation = st.text_input("Entrez un mot-clé de désignation de chaussure (ex: Running, Sandals, Boots):")
            
            if st.button("Filtrer par Désignation"):
                if keyword_designation:
                    try:
                        keyword_designation = str(keyword_designation).strip()  # Convert input to string
                        
                        # Filter DataFrame based on shoe designation keyword
                        df_filtered = filter_by_designation(df, keyword_designation)
                        df_women_filtered = filter_womens_shoes(df_filtered)
                        
                        # Display filtered information
                        st.subheader(f"Chaussures avec Désignation '{keyword_designation}'")
                        if not df_filtered.empty:
                            st.dataframe(df_filtered)
                            # Create PDF report
                            if st.button("Créer un rapport PDF"):
                                pdf_bytes = creer_pdf(df_filtered, df_women_filtered, keyword_designation)
                                st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name=f"rapport_designation_{keyword_designation}.pdf", mime="application/pdf")
                        else:
                            st.write(f"Aucune chaussure avec la désignation '{keyword_designation}' trouvée.")
                        
                        st.subheader(f"Chaussures pour Femmes avec Désignation '{keyword_designation}'")
                        if not df_women_filtered.empty:
                            st.dataframe(df_women_filtered)
                        else:
                            st.write(f"Aucune chaussure pour femmes avec la désignation '{keyword_designation}' trouvée.")
                    
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse de désignation de chaussure: {e}")

            # Display negative stock
            st.sidebar.subheader("Analyse de Stock Négatif")
            if st.sidebar.button("Afficher Stock Négatif"):
                df_negative_stock = filter_negative_stock(df)
                if not df_negative_stock.empty:
                    st.sidebar.dataframe(df_negative_stock)
                else:
                    st.sidebar.write("Aucun stock négatif trouvé.")

            # Display supplier information
            st.sidebar.subheader("Analyse par Fournisseur")
            fournisseur = st.sidebar.text_input("Entrez le nom du fournisseur:")
            if st.sidebar.button("Rechercher par Fournisseur"):
                if fournisseur:
                    try:
                        df_filtered = display_supplier_info(df, fournisseur)
                        st.sidebar.subheader(f"Informations du Fournisseur '{fournisseur}'")
                        if not df_filtered.empty:
                            st.sidebar.dataframe(df_filtered)
                        else:
                            st.sidebar.write("Aucune information disponible pour le fournisseur spécifié.")
                    except Exception as e:
                        st.sidebar.error(f"Erreur lors de l'analyse du fournisseur: {e}")

    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {e}")
