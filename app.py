import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from passlib.hash import pbkdf2_sha256

# Secure user passwords
VALID_USERS = {
    "ayada": pbkdf2_sha256.hash("123"),
    "username2": pbkdf2_sha256.hash("password2")
}

# Authentication function
def authenticate(username, password):
    if username in VALID_USERS and pbkdf2_sha256.verify(password, VALID_USERS[username]):
        return True
    return False

# Function to perform analyses
def analyser_donnees(df):
    compte_fournisseurs = df['fournisseur'].value_counts().head(10)
    df['Prix Achat'] = df['Prix Achat'].astype(str).str.replace(',', '.').astype(float)
    prix_moyen_par_couleur = df.groupby('couleur')['Prix Achat'].mean().sort_values(ascending=False).head(10)
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0).astype(int)
    df['Valeur Stock'] = df['Valeur Stock'].astype(str).str.replace(',', '.').astype(float)
    analyse_stock = df.groupby('famille').agg({'Qté stock dispo': 'sum', 'Valeur Stock': 'sum'}).sort_values(by='Qté stock dispo', ascending=False).head(10)
    return compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, df

# Function to create PDF report
def creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add title
    pdf.cell(200, 10, txt="Rapport d'Analyse de Fichier", ln=True, align='C')
    
    # Add fournisseur analysis
    pdf.cell(200, 10, txt="Analyse des Fournisseurs", ln=True)
    for idx, (fournisseur, count) in enumerate(compte_fournisseurs.items(), start=1):
        pdf.cell(200, 10, txt=f"{idx}. {fournisseur}: {count}", ln=True)

    # Add average price by color
    pdf.cell(200, 10, txt="Prix Moyen par Couleur", ln=True)
    for idx, (couleur, prix) in enumerate(prix_moyen_par_couleur.items(), start=1):
        pdf.cell(200, 10, txt=f"{idx}. {couleur}: {prix:.2f}", ln=True)

    # Add stock analysis
    pdf.cell(200, 10, txt="Analyse des Stocks", ln=True)
    for idx, (famille, row) in enumerate(analyse_stock.iterrows(), start=1):
        pdf.cell(200, 10, txt=f"{idx}. {famille}: Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}", ln=True)

    # Add filtered stock details
    pdf.cell(200, 10, txt="Détails des Stocks avec Qté de 1 à 5", ln=True)
    for idx, row in filtered_df.iterrows():
        pdf.cell(200, 10, txt=f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Qté stock dispo = {row['Qté stock dispo']}", ln=True)

    return pdf.output(dest="S").encode("latin1")

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .main {
            background-color: #f0f2f6;
        }
        .stButton>button {
            background-color: #101E50;
            color: white;
        }
        .stHeader {
            color: #101E50;
        }
        .stTextInput > div > div > input {
            width: 100%;
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
                    # Try different separators
                    try:
                        df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
                    except Exception:
                        df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=',')
                elif extension_fichier == 'xlsx':
                    df = pd.read_excel(fichier_telecharge)
                else:
                    st.error("Format de fichier non supporté")
                    df = None

            if df is not None:
                # Show a summary of the data
                st.subheader("Résumé des Données")
                st.write(df.describe())

                # Data analysis
                compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, full_df = analyser_donnees(df)

                # Display analyses with scrollable sections and filters
                with st.expander("Analyse des Fournisseurs"):
                    st.write(compte_fournisseurs)

                with st.expander("Prix Moyen par Couleur"):
                    st.write(prix_moyen_par_couleur)

                with st.expander("Analyse des Stocks"):
                    st.write(analyse_stock)

                # Filtering options
                filter_options = st.sidebar.selectbox("Filtrer par", ["Fournisseur", "Couleur"])
                if filter_options == "Fournisseur":
                    selected_fournisseur = st.sidebar.selectbox("Sélectionnez un fournisseur", full_df['fournisseur'].unique())
                    filtered_df = full_df[full_df['fournisseur'] == selected_fournisseur]
                elif filter_options == "Couleur":
                    selected_couleur = st.sidebar.selectbox("Sélectionnez une couleur", full_df['couleur'].unique())
                    filtered_df = full_df[full_df['couleur'] == selected_couleur]
                else:
                    filtered_df = full_df

                # Display filtered data
                st.subheader("Détails des Stocks filtrés")
                st.write(filtered_df)

                # Export to PDF
                if st.button("Générer PDF"):
                    pdf_data = creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df)
                    st.download_button("Télécharger PDF", pdf_data, file_name="rapport_analyse.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")
