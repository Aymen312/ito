import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Authentication function
def authenticate(username, password):
    return username == "ayada" and password == "123"

# Function to clean numeric columns
def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

# Function to convert shoe size to standard format
def convert_shoe_size(size):
    try:
        size = str(size).strip().upper()  # Ensure size is a string, remove spaces and convert to uppercase
        if size.endswith("US"):
            return float(size.replace("US", "").strip())
        elif size.endswith("UK"):
            return float(size.replace("UK", "").strip())
        else:
            return float(size)  # Convert directly if it's already a number
    except ValueError:
        return None  # Return None if conversion fails

# Function to perform analyses
def analyser_donnees(df, taille_utilisateur=None):
    # Clean numeric columns
    df = clean_numeric_columns(df)
    
    # Convert user shoe size
    taille_utilisateur_converted = convert_shoe_size(taille_utilisateur)
    
    # Filter DataFrame based on converted shoe size
    if taille_utilisateur_converted is not None:
        df = df[df['taille'].apply(convert_shoe_size) == taille_utilisateur_converted]
    
    # Select relevant columns for analysis
    analyse_tailles = df[['Magasin', 'fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'Qté stock dispo', 'Valeur Stock']]
    
    return analyse_tailles

# Function to create PDF report
def creer_pdf(analyse_tailles, selections):
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
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille = {row['taille']}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(analyse_tailles) * 20 + 20
    
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

# User authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.header("Veuillez vous authentifier")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect")
else:
    st.sidebar.button("Se déconnecter", on_click=lambda: st.session_state.update(authenticated=False))
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

                # Data analysis with user shoe size
                analyse_tailles = analyser_donnees(df, taille_utilisateur=taille_utilisateur)

                # Display shoe size analysis
                st.subheader("Analyse des Tailles de Chaussures")
                st.write(analyse_tailles)

                # PDF Generation and Download
                st.markdown("## Générer un Rapport PDF")

                # Add checkboxes for PDF content selection
                selections = st.multiselect("Sélectionnez les sections à inclure dans le rapport PDF:",
                                            ['Analyse des Tailles de Chaussures'])

                if st.button("Télécharger le rapport en PDF"):
                    if selections:
                        pdf_bytes = creer_pdf(analyse_tailles, selections)
                        st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name="rapport_analyse.pdf")

        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")
