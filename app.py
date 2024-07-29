import streamlit as st
import pandas as pd
from io import BytesIO
import PyPDF2

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with PyPDF2.PdfReader(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du texte du PDF: {e}")
    return text

# Function to process extracted text and convert it into a DataFrame
def process_text_to_dataframe(text):
    # Example: Split text into lines and create a DataFrame
    lines = text.splitlines()
    data = [line.split(';') for line in lines if line.strip()]
    columns = data[0]  # Assuming the first line contains column headers
    df = pd.DataFrame(data[1:], columns=columns)
    return df

# Function to clean numeric columns
def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

# Function to strip leading and trailing spaces from sizes
def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse TDR", layout="wide")

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

st.title("Application d'Analyse TDR")

st.sidebar.markdown("### Menu")
st.sidebar.info("Téléchargez un fichier CSV, Excel ou PDF pour commencer l'analyse.")

# File upload
fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV, Excel ou PDF", type=['csv', 'xlsx', 'pdf'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    
    try:
        if extension_fichier == 'csv':
            df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
        elif extension_fichier == 'xlsx':
            df = pd.read_excel(fichier_telecharge)
        elif extension_fichier == 'pdf':
            text = extract_text_from_pdf(fichier_telecharge)
            df = process_text_to_dataframe(text)
        else:
            st.error("Format de fichier non supporté")
            df = None

        if df is not None:
            # Clean data
            df = clean_numeric_columns(df)
            df = clean_size_column(df)  # Clean size column

            # Tab selection
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Analyse ANITA", "Analyse par Fournisseur", "Analyse par Désignation", "Stock Négatif", "Analyse SIDAS", "Valeur Totale du Stock par Fournisseur", "Exporter les Données"])

            with tab1:
                st.subheader("Quantités Disponibles pour chaque Taille - Fournisseur ANITA")
                # Example of functionality, modify as needed
                st.write(df.head())  # Display the first few rows of the DataFrame as an example

            with tab2:
                fournisseur = st.text_input("Entrez le nom du fournisseur:")
                
                if fournisseur:
                    # Filter DataFrame based on user input
                    df_filtered = df[df['fournisseur'].str.upper() == fournisseur.strip().upper()]
                    st.dataframe(df_filtered)

            with tab3:
                designation = st.text_input("Entrez la désignation:")

                if designation:
                    # Filter DataFrame based on user input
                    df_filtered = df[df['designation'].str.upper().str.contains(designation.strip().upper())]
                    st.dataframe(df_filtered)

            with tab4:
                st.subheader("Stock Négatif et Sa Valeur")
                df_negative_stock = df[df['Qté stock dispo'] < 0]
                st.dataframe(df_negative_stock)

            with tab5:
                st.subheader("Analyse des Tailles de Chaussures SIDAS")
                # Example of functionality, modify as needed
                st.write(df.head())  # Display the first few rows of the DataFrame as an example

            with tab6:
                st.subheader("Valeur Totale du Stock par Fournisseur")
                # Example of functionality, modify as needed
                st.write(df.head())  # Display the first few rows of the DataFrame as an example

            with tab7:
                st.subheader("Exporter les Données au Format Excel")
                try:
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Données')
                    excel_buffer.seek(0)

                    st.download_button(
                        label="Télécharger le fichier Excel",
                        data=excel_buffer,
                        file_name='donnees_analyse.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                except Exception as e:
                    st.error(f"Erreur lors de l'exportation des données au format Excel: {e}")

    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {e}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
