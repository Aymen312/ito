import streamlit as st
import pandas as pd
from io import BytesIO
import PyPDF2

# Fonction pour extraire le texte d'un fichier PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du texte du PDF: {e}")
    return text

# Fonction pour traiter le texte extrait et le convertir en DataFrame
def process_text_to_dataframe(text):
    # Exemple de traitement du texte : séparer les lignes et créer un DataFrame
    lines = text.splitlines()
    data = [line.split(';') for line in lines if line.strip()]
    columns = data[0]  # En supposant que la première ligne contient les en-têtes de colonnes
    df = pd.DataFrame(data[1:], columns=columns)
    return df

# Fonction pour exporter les données au format Excel
def export_to_excel(df):
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Données')
    excel_buffer.seek(0)
    return excel_buffer

# Application Streamlit
st.set_page_config(page_title="Application d'Analyse TDR", layout="wide")

# CSS personnalisé pour le design futuriste
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

# Téléchargement de fichier
fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV, Excel ou PDF", type=['csv', 'xlsx', 'pdf'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]

    if extension_fichier == 'pdf':
        text = extract_text_from_pdf(fichier_telecharge)
        if text:
            df = process_text_to_dataframe(text)
            st.write("Données extraites du PDF:")
            st.dataframe(df)

            # Exporter au format Excel
            st.subheader("Exporter les Données au Format Excel")
            try:
                excel_buffer = export_to_excel(df)
                st.download_button(
                    label="Télécharger le fichier Excel",
                    data=excel_buffer,
                    file_name='donnees_analyse.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            except Exception as e:
                st.error(f"Erreur lors de l'exportation des données au format Excel: {e}")
        else:
            st.error("Aucune donnée extraite du fichier PDF.")

    else:
        st.error("Veuillez télécharger un fichier PDF pour extraire les données.")

else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
