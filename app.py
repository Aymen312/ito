import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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

# Function to create PDF report using ReportLab
def creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df):
    # Initialize PDF canvas
    pdf_filename = "rapport_analyse.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    
    # Set up styles
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Fichier")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "Analyse des Fournisseurs:")
    
    # Add fournisseur analysis
    y_position = 700
    for idx, (fournisseur, count) in enumerate(compte_fournisseurs.items(), start=1):
        c.drawString(70, y_position - idx * 20, f"{idx}. {fournisseur}: {count}")
    
    # Add average price by color
    c.drawString(50, y_position - len(compte_fournisseurs) * 20 - 40, "Prix Moyen par Couleur:")
    for idx, (couleur, prix) in enumerate(prix_moyen_par_couleur.items(), start=1):
        c.drawString(70, y_position - len(compte_fournisseurs) * 20 - 40 - idx * 20, f"{idx}. {couleur}: {prix:.2f}")
    
    # Add stock analysis
    c.drawString(50, y_position - len(compte_fournisseurs) * 20 - 40 - len(prix_moyen_par_couleur) * 20 - 60, "Analyse des Stocks:")
    for idx, (famille, row) in enumerate(analyse_stock.iterrows(), start=1):
        c.drawString(70, y_position - len(compte_fournisseurs) * 20 - 40 - len(prix_moyen_par_couleur) * 20 - 60 - idx * 20,
                     f"{idx}. {famille}: Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
    
    # Add filtered stock details
    c.drawString(50, y_position - len(compte_fournisseurs) * 20 - 40 - len(prix_moyen_par_couleur) * 20 - 60 - len(analyse_stock) * 20 - 80, "Détails des Stocks avec Qté de 1 à 5:")
    for idx, (_, row) in enumerate(filtered_df.iterrows(), start=1):
        c.drawString(70, y_position - len(compte_fournisseurs) * 20 - 40 - len(prix_moyen_par_couleur) * 20 - 60 - len(analyse_stock) * 20 - 80 - idx * 20,
                     f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Qté stock dispo = {row['Qté stock dispo']}")

    # Save PDF
    c.save()
    return pdf_filename

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

# Title and introduction
st.title("Application d'Analyse de Fichier")
st.markdown("""
    Bienvenue dans l'application d'analyse de fichier. Téléchargez un fichier CSV ou Excel pour commencer.
    """)

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
            st.success("Connecté avec succès!")
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
                st.markdown("## Analyses Principales")
                
                with st.expander("Analyse des Fournisseurs"):
                    st.write(compte_fournisseurs)

                with st.expander("Prix Moyen par Couleur"):
                    st.write(prix_moyen_par_couleur)

                with st.expander("Analyse des Stocks"):
                    st.write(analyse_stock)

                # Filtering options
                st.markdown("## Filtrage des Données")
                filter_options = st.selectbox("Filtrer par", ["Aucun", "Fournisseur", "Couleur"])
                filtered_df = full_df

                if filter_options == "Fournisseur":
                    selected_fournisseur = st.selectbox("Sélectionnez un fournisseur", full_df['fournisseur'].unique())
                    filtered_df = full_df[full_df['fournisseur'] == selected_fournisseur]
                elif filter_options == "Couleur":
                    selected_couleur = st.selectbox("Sélectionnez une couleur", full_df['couleur'].unique())
                    filtered_df = full_df[full_df['couleur'] == selected_couleur]

                # Display filtered data
                st.markdown("## Détails des Stocks")
                st.write(filtered_df)

                # Export to PDF
                st.markdown("## Générer un Rapport PDF")
                if st.button("Générer PDF"):
                    pdf_filename = creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df)
                    st.success(f"Rapport PDF généré avec succès: [Télécharger PDF]({pdf_filename})")

        except Exception as e:
            st.error(f"Une erreur s'est produite lors de l'analyse des données : {e}")
    else:
        st.info("Veuillez télécharger un fichier à analyser.")
