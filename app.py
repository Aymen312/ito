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

# Function to filter by supplier and display corresponding data
def display_supplier_info(df, fournisseur):
    fournisseur = fournisseur.strip().upper()  # Convert user input supplier to uppercase
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame()
    df_homme = df_filtered[df_filtered['rayon'].str.upper().str.contains('HOMME', na=False)]
    df_femme = df_filtered[df_filtered['rayon'].str.upper().str.contains('FEMME', na=False)]
    return df_homme, df_femme

# Function to filter by designation and display corresponding data
def display_designation_info(df, designation):
    designation = designation.strip().upper()  # Convert user input designation to uppercase
    df_filtered = df[df['designation'].str.upper().str.contains(designation)] if designation else pd.DataFrame()
    df_homme = df_filtered[df_filtered['rayon'].str.upper().str.contains('HOMME', na=False)]
    df_femme = df_filtered[df_filtered['rayon'].str.upper().str.contains('FEMME', na=False)]
    return df_homme, df_femme

# Function to filter negative stock
def filter_negative_stock(df):
    df_filtered = df[df['Qté stock dispo'] < 0]
    df_homme = df_filtered[df_filtered['rayon'].str.upper().str.contains('HOMME', na=False)]
    df_femme = df_filtered[df_filtered['rayon'].str.upper().str.contains('FEMME', na=False)]
    return df_homme, df_femme

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Chaussure", layout="wide")

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

st.title("Application d'Analyse de Chaussure")

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
            
            # Tab selection
            tab2, tab3, tab4 = st.tabs(["Analyse par Fournisseur", "Analyse par Désignation", "Stock Négatif"])
            
            with tab2:
                # Ask for supplier name
                fournisseur = st.text_input("Entrez le nom du fournisseur:")
                
                if fournisseur:
                    try:
                        fournisseur = str(fournisseur).strip().upper()  # Convert user input supplier to uppercase
                        
                        # Filter DataFrame based on user input
                        df_homme, df_femme = display_supplier_info(df, fournisseur)
                        
                        # Display filtered information
                        st.subheader("Informations du Fournisseur - Hommes")
                        if not df_homme.empty:
                            st.dataframe(df_homme)
                        else:
                            st.write("Aucune information disponible pour le fournisseur spécifié pour les hommes.")
                        
                        st.subheader("Informations du Fournisseur - Femmes")
                        if not df_femme.empty:
                            st.dataframe(df_femme)
                        else:
                            st.write("Aucune information disponible pour le fournisseur spécifié pour les femmes.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse du fournisseur: {e}")
            
            with tab3:
                # Ask for designation
                designation = st.text_input("Entrez la désignation (ex: Sneakers, Running):")
                
                if designation:
                    try:
                        designation = str(designation).strip().upper()  # Convert user input designation to uppercase
                        
                        # Filter DataFrame based on user input
                        df_homme, df_femme = display_designation_info(df, designation)
                        
                        # Display filtered information
                        st.subheader("Informations par Désignation - Hommes")
                        if not df_homme.empty:
                            st.dataframe(df_homme)
                        else:
                            st.write("Aucune information disponible pour la désignation spécifiée pour les hommes.")
                        
                        st.subheader("Informations par Désignation - Femmes")
                        if not df_femme.empty:
                            st.dataframe(df_femme)
                        else:
                            st.write("Aucune information disponible pour la désignation spécifiée pour les femmes.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse de la désignation: {e}")
            
            with tab4:
                # Display negative stock
                st.subheader("Stock Négatif et Valeur Correspondante - Hommes")
                df_homme, df_femme = filter_negative_stock(df)
                
                if not df_homme.empty:
                    st.dataframe(df_homme)
                else:
                    st.write("Aucun stock négatif trouvé pour les hommes.")
                
                st.subheader("Stock Négatif et Valeur Correspondante - Femmes")
                if not df_femme.empty:
                    st.dataframe(df_femme)
                else:
                    st.write("Aucun stock négatif trouvé pour les femmes.")

    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {e}")
