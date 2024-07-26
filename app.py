import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Function definitions (clean_numeric_columns, convert_to_eu_size, etc.) remain the same...

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
            # Add a sidebar option to select the section
            section = st.sidebar.selectbox("Choisissez la section:", ["Taille de Chaussure", "Fournisseur"])

            if section == "Taille de Chaussure":
                taille_utilisateur = st.text_input("Entrez votre taille de chaussure (ex: 10.0US, 9.5UK, 40):")
                st.write("Vous pouvez maintenant entrer votre taille de chaussure.")
            elif section == "Fournisseur":
                supplier_name = st.text_input("Entrez le nom du fournisseur pour afficher ses informations:")
                st.write("Vous pouvez maintenant entrer le nom du fournisseur.")

            # Data analysis with user shoe size and supplier name
            if section == "Taille de Chaussure":
                analyse_tailles, analyse_tailles_femmes = analyser_donnees(df, taille_utilisateur=taille_utilisateur)
            elif section == "Fournisseur":
                analyse_tailles, analyse_tailles_femmes = analyser_donnees(df, supplier_name=supplier_name)

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
