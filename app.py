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

# Function to filter by shoe size and display corresponding data
def display_shoe_size_info(df, taille_utilisateur):
    taille_utilisateur_converted = convert_to_eu_size(taille_utilisateur)
    
    if taille_utilisateur_converted is not None:
        df_filtered = df[df['taille_eu'] == taille_utilisateur_converted]
        df_women_filtered = filter_womens_shoes(df[df['taille_eu'] == taille_utilisateur_converted])
    else:
        df_filtered = pd.DataFrame()
        df_women_filtered = pd.DataFrame()
    
    return df_filtered, df_women_filtered

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
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille EU = {row['taille_eu']}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(df_filtered) * 20 + 20
    
    if not df_women_filtered.empty:
        # Add women's shoes analysis
        c.drawString(50, y_position, f"Chaussures pour Femmes à Taille {taille_utilisateur}:")
        y_position -= 20
        for idx, (_, row) in enumerate(df_women_filtered.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille EU = {row['taille_eu']}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(df_women_filtered) * 20 + 20
    
    # Save PDF to buffer
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Taille de Chaussure", layout="wide")

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
            # Clean and convert data
            df = clean_numeric_columns(df)
            df = convert_dataframe_to_eu(df)
            
            # Ask for user shoe size
            taille_utilisateur = st.text_input("Entrez votre taille de chaussure (ex: 10.0US, 9.5UK, 40):")
            
            if taille_utilisateur:
                # Filter DataFrame based on user input
                df_filtered, df_women_filtered = display_shoe_size_info(df, taille_utilisateur)
                
                # Display filtered information
                st.subheader(f"Information pour la Taille {taille_utilisateur}")
                st.write(df_filtered)
                
                # Display women's shoe information if available
                if not df_women_filtered.empty:
                    st.subheader(f"Chaussures pour Femmes à Taille {taille_utilisateur}")
                    st.write(df_women_filtered)
                
                # PDF Generation and Download
                st.markdown("## Générer un Rapport PDF")

                if st.button("Télécharger le rapport en PDF"):
                    pdf_bytes = creer_pdf(df_filtered, df_women_filtered, taille_utilisateur)
                    st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name="rapport_analyse_taille.pdf")

    except Exception as e:
        st.error(f"Une erreur s'est produite : {e}")
