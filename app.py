import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Custom CSS for improved design
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
        .stMarkdown>div {
            background-color: #1E1E1E;
            color: #F5F5F5;
            padding: 15px;
            border-radius: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

# Functions and other code remain unchanged

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Taille de Chaussure", layout="wide")

st.title("Application d'Analyse de Taille de Chaussure")

# Sidebar with navigation
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
            
            # Tabs for different functionalities
            tabs = st.tabs(["Analyse de Taille", "Information Fournisseur"])

            with tabs[0]:
                st.subheader("Analyse des Tailles")
                st.markdown("""
                    Entrez votre taille de chaussure pour voir les informations correspondantes.
                    Veuillez entrer la taille au format attendu (ex: 40, 41, 42).
                """)
                
                # Ask for user shoe size
                taille_utilisateur = st.text_input("Entrez votre taille de chaussure (ex: 40, 41, 42):")
                
                if taille_utilisateur:
                    try:
                        taille_utilisateur = str(taille_utilisateur).strip().upper()  # Clean user input size
                        
                        # Convert sizes to EU sizes for display purposes only
                        df = convert_dataframe_to_eu(df)
                        
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
                    except ValueError:
                        st.error("La taille de chaussure entrée est invalide. Veuillez entrer un nombre ou une taille au format attendu.")
            
            with tabs[1]:
                st.subheader("Informations Fournisseur")
                st.markdown("""
                    Entrez le nom du fournisseur pour voir les informations correspondantes.
                    Vous pouvez utiliser le nom du fournisseur en majuscule ou minuscule.
                """)
                
                # Ask for supplier name
                fournisseur_utilisateur = st.text_input("Entrez le nom du fournisseur :")
                
                if fournisseur_utilisateur:
                    try:
                        fournisseur_utilisateur = str(fournisseur_utilisateur).strip().upper()  # Convert user input supplier to uppercase
                        df_fournisseur = display_supplier_info(df, fournisseur_utilisateur)
                        
                        # Display filtered information
                        st.subheader(f"Information pour le Fournisseur {fournisseur_utilisateur}")
                        st.write(df_fournisseur)
                    except Exception as e:
                        st.error(f"Une erreur est survenue : {e}")

    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
