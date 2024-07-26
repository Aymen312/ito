import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Fonction pour nettoyer les colonnes numériques
def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

# Fonction pour convertir la taille de chaussure en taille EU
def convert_to_eu_size(size):
    try:
        size = str(size).strip().upper()
        if size.endswith("US"):
            us_size = float(size.replace("US", "").strip())
            return us_size + 33  # Exemple de conversion
        elif size.endswith("UK"):
            uk_size = float(size.replace("UK", "").strip())
            return uk_size + 34  # Exemple de conversion
        else:
            return float(size)  # Supposer que c'est déjà en taille EU
    except ValueError:
        return None

# Fonction pour convertir les tailles de chaussure dans le dataframe en tailles EU
def convert_dataframe_to_eu(df):
    df['taille_eu'] = df['taille'].apply(convert_to_eu_size)
    return df

# Fonction pour filtrer les chaussures pour femmes
def filter_womens_shoes(df):
    return df[df['designation'].str.endswith('W', na=False)]

# Fonction pour filtrer par nom de fournisseur
def filter_by_supplier(df, supplier_name):
    return df[df['fournisseur'].str.contains(supplier_name, case=False, na=False)]

# Fonction pour effectuer les analyses
def analyser_donnees(df, taille_utilisateur=None, supplier_name=None):
    # Nettoyer les colonnes numériques
    df = clean_numeric_columns(df)
    
    # Convertir les tailles de chaussure en tailles EU
    df = convert_dataframe_to_eu(df)
    
    # Filtrer pour les chaussures pour femmes
    df_women = filter_womens_shoes(df)
    
    # Exclure les chaussures pour femmes de l'analyse principale
    df = df[~df.index.isin(df_women.index)]
    
    # Convertir la taille de chaussure utilisateur en taille EU
    taille_utilisateur_converted = convert_to_eu_size(taille_utilisateur)
    
    # Filtrer le DataFrame en fonction de la taille de chaussure convertie
    if taille_utilisateur_converted is not None:
        df = df[df['taille_eu'] == taille_utilisateur_converted]
    
    # Filtrer le DataFrame en fonction du nom du fournisseur
    if supplier_name:
        df = filter_by_supplier(df, supplier_name)
    
    # Sélectionner les colonnes pertinentes pour l'analyse
    analyse_tailles = df[['Magasin', 'fournisseur', 'barcode', 'couleur', 'taille_eu', 'designation', 'Qté stock dispo', 'Valeur Stock']]
    analyse_tailles_femmes = df_women[['Magasin', 'fournisseur', 'barcode', 'couleur', 'taille_eu', 'designation', 'Qté stock dispo', 'Valeur Stock']]
    
    return analyse_tailles, analyse_tailles_femmes

# Fonction pour créer un rapport PDF
def creer_pdf(analyse_tailles, analyse_tailles_femmes, selections):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Commencer à écrire le contenu du PDF
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Fichier")
    c.setFont("Helvetica", 12)
    
    y_position = 720
    
    if 'Analyse des Tailles de Chaussures' in selections:
        # Ajouter l'analyse des tailles de chaussures
        c.drawString(50, y_position, "Analyse des Tailles de Chaussures:")
        y_position -= 20
        for idx, (_, row) in enumerate(analyse_tailles.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille EU = {row['taille_eu']}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(analyse_tailles) * 20 + 20
    
    if 'Analyse des Chaussures pour Femmes' in selections:
        # Ajouter l'analyse des chaussures pour femmes
        c.drawString(50, y_position, "Analyse des Chaussures pour Femmes:")
        y_position -= 20
        for idx, (_, row) in enumerate(analyse_tailles_femmes.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Taille EU = {row['taille_eu']}, Désignation = {row['designation']}, Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(analyse_tailles_femmes) * 20 + 20
    
    # Sauvegarder le PDF dans le buffer
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# Application Streamlit
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

# CSS personnalisé et JavaScript pour masquer l'icône GitHub
st.markdown("""
    <style>
        /* Masquer l'icône GitHub */
        .stApp .github-icon {
            display: none !important;
        }
    </style>
    <script>
        // Retirer l'icône GitHub si le CSS ne fonctionne pas
        document.addEventListener("DOMContentLoaded", function() {
            var githubIcon = document.querySelector(".stApp .github-icon"); 
            if (githubIcon) {
                githubIcon.style.display = 'none';
            }
        });
    </script>
""", unsafe_allow_html=True)

# CSS personnalisé pour un design futuriste
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

# Barre latérale pour les saisies utilisateur
st.sidebar.markdown("### Menu")
st.sidebar.info("Téléchargez un fichier CSV ou Excel pour commencer l'analyse.")

# Sélecteur pour choisir la vue
page = st.sidebar.selectbox("Choisissez une option", ["Téléchargement de Fichier", "Analyse", "Générer un Rapport"])

if page == "Téléchargement de Fichier":
    # Téléchargement du fichier
    fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])

    if fichier_telecharge is not None:
        extension_fichier = fichier_telecharge.name.split('.')[-1]
        try:
            with st.spinner("Chargement des données..."):
                if extension_fichier == 'csv':
                    # Lire le CSV avec l'encodage et le séparateur appropriés
                    df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
                elif extension_fichier == 'xlsx':
                    df = pd.read_excel(fichier_telecharge)
                else:
                    st.error("Format de fichier non supporté")
                    df = None

            if df is not None:
                st.sidebar.subheader("Options d'Analyse")

                # Champ pour la taille de chaussure
                taille_utilisateur = st.sidebar.text_input("Entrez votre taille de chaussure (ex: 10.0US, 9.5UK, 40):")

                # Champ pour le nom du fournisseur
                supplier_name = st.sidebar.text_input("Entrez le nom du fournisseur pour afficher ses informations:")

                if page == "Analyse":
                    # Analyse des données avec la taille de chaussure utilisateur et le nom du fournisseur
                    analyse_tailles, analyse_tailles_femmes = analyser_donnees(df, taille_utilisateur=taille_utilisateur, supplier_name=supplier_name)

                    # Afficher l'analyse des tailles de chaussures
                    st.subheader("Analyse des Tailles de Chaussures")
                    st.write(analyse_tailles)

                    # Afficher l'analyse des chaussures pour femmes
                    st.subheader("Analyse des Chaussures pour Femmes")
                    st.write(analyse_tailles_femmes)

                    # Afficher les informations du fournisseur
                    if supplier_name:
                        st.subheader(f"Informations pour le fournisseur: {supplier_name}")
                        st.write(analyse_tailles)

                elif page == "Générer un Rapport":
                    # Génération et téléchargement du PDF
                    if df is not None:
                        # Analyse des données
                        analyse_tailles, analyse_tailles_femmes = analyser_donnees(df, taille_utilisateur=taille_utilisateur, supplier_name=supplier_name)

                        st.markdown("## Générer un Rapport PDF")

                        # Ajouter des cases à cocher pour la sélection du contenu du PDF
                        selections = st.sidebar.multiselect("Sélectionnez les sections à inclure dans le rapport PDF:",
                                                            ['Analyse des Tailles de Chaussures', 'Analyse des Chaussures pour Femmes'])

                        if st.sidebar.button("Télécharger le rapport en PDF"):
                            if selections:
                                pdf_bytes = creer_pdf(analyse_tailles, analyse_tailles_femmes, selections)
                                st.sidebar.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name="rapport_analyse.pdf")

        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")
