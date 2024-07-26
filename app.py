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

# Function to convert shoe size to EU size
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

# Function to convert the entire dataframe's shoe sizes to EU sizes
def convert_dataframe_to_eu(df):
    df['taille_eu'] = df['taille'].apply(convert_to_eu_size)
    return df

# Function to filter women's shoes
def filter_womens_shoes(df):
    return df[df['designation'].str.endswith('W', na=False)]

# Function to filter by supplier name
def filter_by_supplier(df, supplier_name):
    return df[df['fournisseur'].str.contains(supplier_name, case=False, na=False)]

# Function to perform analyses
def analyser_donnees(df, taille_utilisateur=None, supplier_name=None):
    # Clean numeric columns
    df = clean_numeric_columns(df)
    
    # Convert shoe sizes to EU sizes
    df = convert_dataframe_to_eu(df)
    
    # Filter for women's shoes
    df_women = filter_womens_shoes(df)
    
    # Exclude women's shoes from the main analysis
    df = df[~df.index.isin(df_women.index)]
    
    # Convert user shoe size to EU size
    taille_utilisateur_converted = convert_to_eu_size(taille_utilisateur)
    
    # Filter DataFrame based on converted shoe size
    if taille_utilisateur_converted is not None:
        df = df[df['taille_eu'] == taille_utilisateur_converted]
    
    # Filter DataFrame based on supplier name
    if supplier_name:
        df = filter_by_supplier(df, supplier_name)
    
    # Select relevant columns for analysis
    analyse_tailles = df[['Magasin', 'fournisseur', 'barcode', 'couleur', 'taille_eu', 'designation', 'Qté stock dispo', 'Valeur Stock']]
    analyse_tailles_femmes = df_women[['Magasin', 'fournisseur', 'barcode', 'couleur', 'taille_eu', 'designation', 'Qté stock dispo', 'Valeur Stock']]
    
    return analyse_tailles, analyse_tailles_femmes

# Function to create PDF report
def creer_pdf(analyse_tailles, analyse_tailles_femmes, selections):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Start writing PDF content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Fichier")
    c.setFont("Helvetica", 12)
    
    y_position = 720
    
    if 'Analyse des Tailles de Chaussures' in selections:
        # Add shoe size analysis
        c.drawString(50, y_position, "Analyse des Tailles de Chaussures:")
        y_position -= 20
        for idx, (_, row) in enumerate(analyse_tailles.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille EU = {row['taille_eu']}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(analyse_tailles) * 20 + 20
    
    if 'Analyse des Chaussures pour Femmes' in selections:
        # Add women's shoes analysis
        c.drawString(50, y_position, "Analyse des Chaussures pour Femmes:")
        y_position -= 20
        for idx, (_, row) in enumerate(analyse_tailles_femmes.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille EU = {row['taille_eu']}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(analyse_tailles_femmes) * 20 + 20
    
    # Save PDF to buffer
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

# Custom CSS and JavaScript to hide GitHub icon
st.markdown("""
    <style>
        /* Hide GitHub icon */
        .stApp .github-icon {
            display: none !important;
        }
    </style>
    <script>
        // Remove GitHub icon if CSS doesn't work
        document.addEventListener("DOMContentLoaded", function() {
            var githubIcon = document.querySelector(".stApp .github-icon"); 
            if (githubIcon) {
                githubIcon.style.display = 'none';
            }
        });
    </script>
""", unsafe_allow_html=True)

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

st.title("Application d'Analyse de Fichier")

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
            # Ask for user shoe size
            taille_utilisateur = st.text_input("Entrez votre taille de chaussure (ex: 10.0US, 9.5UK, 40):")
            
            # Ask for supplier name
            supplier_name = st.text_input("Entrez le nom du fournisseur pour afficher ses informations:")

            # Data analysis with user shoe size and supplier name
            analyse_tailles, analyse_tailles_femmes = analyser_donnees(df, taille_utilisateur=taille_utilisateur, supplier_name=supplier_name)

            # Display shoe size analysis
            st.subheader("Analyse des Tailles de Chaussures")
            st.write(analyse_tailles)

            # Display women's shoes analysis
            st.subheader("Analyse des Chaussures pour Femmes")
            st.write(analyse_tailles_femmes)

            # Display supplier information
            if supplier_name:
                st.subheader(f"Informations pour le fournisseur: {supplier_name}")
                st.write(analyse_tailles)

            # PDF Generation and Download
            st.markdown("## Générer un Rapport PDF")

            # Add checkboxes for PDF content selection
            selections = st.multiselect("Sélectionnez les sections à inclure dans le rapport PDF:",
                                        ['Analyse des Tailles de Chaussures', 'Analyse des Chaussures pour Femmes'])

            if st.button("Télécharger le rapport en PDF"):
                if selections:
                    pdf_bytes = creer_pdf(analyse_tailles, analyse_tailles_femmes, selections)
                    st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name="rapport_analyse.pdf")

    except Exception as e:
        st.error(f"Une erreur s'est produite : {e}")
