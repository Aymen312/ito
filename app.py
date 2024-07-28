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

# Function to filter by shoe size and display corresponding data
def display_shoe_size_info(df, taille_utilisateur):
    taille_utilisateur = taille_utilisateur.strip().upper()  # Convert user input size to uppercase
    df_filtered = df[df['taille'].str.upper() == taille_utilisateur] if taille_utilisateur else pd.DataFrame()
    df_women_filtered = filter_womens_shoes(df_filtered) if not df_filtered.empty else pd.DataFrame()
    df_filtered = df_filtered[~(df_filtered['designation'].str.contains('WOMAN', na=False, case=False) | df_filtered['designation'].str.contains('W', na=False, case=False))]  # Exclude women's shoes
    return df_filtered, df_women_filtered

# Function to filter by supplier and display corresponding data
def display_supplier_info(df, fournisseur):
    fournisseur = fournisseur.strip().upper()  # Convert user input supplier to uppercase
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame()
    return df_filtered

# Function to filter by shoe designation
def filter_by_designation(df, keyword):
    keyword = keyword.strip().lower()  # Convert keyword to lowercase for case insensitive search
    return df[df['designation'].str.lower().str.contains(keyword, na=False)]

# Function to create PDF report
def creer_pdf(df_filtered, df_women_filtered, taille_utilisateur):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Start writing PDF content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Taille de Chaussure")
    c.setFont("Helvetica", 12)
    
    y_position = 720
    
    if not df_filtered.empty:
        # Add shoe size analysis
        c.drawString(50, y_position, f"Analyse pour la Taille {taille_utilisateur}:")
        y_position -= 20
        for idx, (_, row) in enumerate(df_filtered.iterrows(), start=1):
            taille = f"{row['taille']} ({row['taille_originale']})" if row['taille_originale'] else row['taille']
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille = {taille}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(df_filtered) * 20 + 20
    
    if not df_women_filtered.empty:
        # Add women's shoes analysis
        c.drawString(50, y_position, f"Chaussures pour Femmes à Taille {taille_utilisateur}:")
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

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Taille de Chaussure", layout="wide")

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

st.title("Application d'Analyse de Taille de Chaussure")

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
            
            # Tab selection
            tab1, tab2, tab3 = st.tabs(["Analyse de Taille de Chaussure", "Analyse par Fournisseur", "Stock Négatif"])
            
            with tab1:
                # Ask for user shoe size
                taille_utilisateur = st.text_input("Entrez votre taille de chaussure (ex: 40, 41, 42):")
                
                # Ask for shoe designation keyword
                keyword_designation = st.text_input("Entrez un mot-clé de désignation de chaussure (optionnel):")
                
                if taille_utilisateur:
                    try:
                        taille_utilisateur = str(taille_utilisateur).strip().upper()  # Convert user input size to uppercase
                        
                        # Filter DataFrame based on user input
                        df_filtered, df_women_filtered = display_shoe_size_info(df, taille_utilisateur)
                        
                        # Filter by shoe designation if keyword provided
                        if keyword_designation:
                            df_filtered = filter_by_designation(df_filtered, keyword_designation)
                            df_women_filtered = filter_by_designation(df_women_filtered, keyword_designation)
                        
                        # Display filtered information
                        st.subheader("Chaussures Disponibles")
                        if not df_filtered.empty:
                            st.dataframe(df_filtered)
                        else:
                            st.write("Aucune chaussure disponible pour la taille spécifiée et le mot-clé de désignation.")
                        
                        st.subheader("Chaussures pour Femmes Disponibles")
                        if not df_women_filtered.empty:
                            st.dataframe(df_women_filtered)
                        else:
                            st.write("Aucune chaussure pour femmes disponible pour la taille spécifiée et le mot-clé de désignation.")
                        
                        # Create PDF report
                        if st.button("Créer un rapport PDF"):
                            pdf_bytes = creer_pdf(df_filtered, df_women_filtered, taille_utilisateur)
                            st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name=f"rapport_taille_{taille_utilisateur}.pdf", mime="application/pdf")
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse de la taille de chaussure: {e}")
            
            with tab2:
                # Ask for supplier name
                fournisseur = st.text_input("Entrez le nom du fournisseur:")
                
                if fournisseur:
                    try:
                        fournisseur = str(fournisseur).strip().upper()  # Convert user input supplier to uppercase
                        
                        # Filter DataFrame based on user input
                        df_filtered = display_supplier_info(df, fournisseur)
                        
                        # Display filtered information
                        st.subheader("Informations du Fournisseur")
                        if not df_filtered.empty:
                            st.dataframe(df_filtered)
                        else:
                            st.write("Aucune information disponible pour le fournisseur spécifié.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse du fournisseur: {e}")
            
            with tab3:
                # Display negative stock
                st.subheader("Stock Négatif et Valeur Correspondante")
                df_negative_stock = filter_negative_stock(df)
                
                if not df_negative_stock.empty:
                    st.dataframe(df_negative_stock)
                else:
                    st.write("Aucun stock négatif trouvé.")

    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {e}")
