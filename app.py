import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Set page configuration to hide Streamlit menu and footer
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

# Custom CSS to hide the Streamlit menu, footer, GitHub button, and "Manage app"
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {visibility: hidden;}
    .viewerBadge_link__1S137 {visibility: hidden;}
    .css-1lsmgbg.egzxvld1 {visibility: hidden;}  /* For Streamlit version < 1.4.0 */
    .css-1rs6os.edgvbvh3 {visibility: hidden;}  /* For Streamlit version >= 1.4.0 */
    .css-1rn8c8m.egzxvld0 {visibility: hidden;}  /* Newer versions may need this */
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Authentication function
def authenticate(username, password):
    return username == st.secrets.credentials.username and password == st.secrets.credentials.password

# Function to perform data analysis
def analyze_data(df):
    # Example analysis
    compte_fournisseurs = df['fournisseur'].value_counts().head(10)
    prix_moyen_par_couleur = df.groupby('couleur')['Prix Achat'].mean().sort_values(ascending=False).head(10)
    analyse_stock = df.groupby('famille').agg({'Qté stock dispo': 'sum', 'Valeur Stock': 'sum'}).sort_values(by='Qté stock dispo', ascending=False).head(10)
    return compte_fournisseurs, prix_moyen_par_couleur, analyse_stock

# Function to create PDF report
def create_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Write PDF content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Fichier")
    c.setFont("Helvetica", 12)

    # Write analysis sections
    y_position = 720
    for idx, (title, data) in enumerate(zip(["Analyse des Fournisseurs", "Prix Moyen par Couleur", "Analyse des Stocks"],
                                            [compte_fournisseurs, prix_moyen_par_couleur, analyse_stock])):
        c.drawString(50, y_position, title + ":")
        y_position -= 20
        for i, (key, value) in enumerate(data.items(), start=1):
            c.drawString(70, y_position - i * 20, f"{i}. {key}: {value}")
        y_position -= len(data) * 20 + 20

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# Streamlit application
st.title("Application d'Analyse de Fichier")

# Authentication section
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.header("Veuillez vous authentifier")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if authenticate(username, password):
            st.session_state.authenticated = True
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect")
else:
    st.header("Bienvenue!")

    # File upload and data analysis
    uploaded_file = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)  # Adjust for different file types if necessary

            # Perform data analysis
            compte_fournisseurs, prix_moyen_par_couleur, analyse_stock = analyze_data(df)

            # Display analyses
            st.subheader("Analyse des Fournisseurs")
            st.write(compte_fournisseurs)

            st.subheader("Prix Moyen par Couleur")
            st.write(prix_moyen_par_couleur)

            st.subheader("Analyse des Stocks")
            st.write(analyse_stock)

            # Generate and download PDF report
            if st.button("Générer et Télécharger le PDF"):
                pdf_bytes = create_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock)
                st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name="rapport_analyse.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")

    else:
        st.info("Veuillez télécharger un fichier pour commencer.")

# Footer or logout option
if st.session_state.authenticated:
    if st.button("Se déconnecter"):
        st.session_state.authenticated = False
