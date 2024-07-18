import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import plotly.express as px

# Authentication function
def authenticate(username, password):
    return username == "ayada" and password == "123"

# Function to perform analyses
def analyser_donnees(df):
    compte_fournisseurs = df['fournisseur'].value_counts().head(10)
    df['Prix Achat'] = df['Prix Achat'].astype(str).str.replace(',', '.').astype(float)
    prix_moyen_par_couleur = df.groupby('couleur')['Prix Achat'].mean().sort_values(ascending=False).head(10)
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0).astype(int)
    df['Valeur Stock'] = df['Valeur Stock'].astype(str).str.replace(',', '.').astype(float)
    analyse_stock = df.groupby('famille').agg({'Qté stock dispo': 'sum', 'Valeur Stock': 'sum'}).sort_values(by='Qté stock dispo', ascending=False).head(10)
    return compte_fournisseurs, prix_moyen_par_couleur, analyse_stock

# Function to create PDF report
def creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Start writing PDF content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Fichier")
    c.setFont("Helvetica", 12)
    
    # Add fournisseur analysis
    c.drawString(50, 720, "Analyse des Fournisseurs:")
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
    
    # Save PDF to buffer
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

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
                    df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
                elif extension_fichier == 'xlsx':
                    df = pd.read_excel(fichier_telecharge)
                else:
                    st.error("Format de fichier non supporté")
                    df = None

            if df is not None:
                # User selects analyses
                st.sidebar.header("Sélectionnez les Analyses à Effectuer")
                analyse_fournisseurs = st.sidebar.checkbox("Analyse des Fournisseurs")
                analyse_couleur = st.sidebar.checkbox("Prix Moyen par Couleur")
                analyse_stock = st.sidebar.checkbox("Analyse des Stocks")

                if analyse_fournisseurs or analyse_couleur or analyse_stock:
                    compte_fournisseurs, prix_moyen_par_couleur, analyse_stock_res = analyser_donnees(df)

                    if analyse_fournisseurs:
                        st.subheader("Analyse des Fournisseurs")
                        st.write(compte_fournisseurs)
                        fig1 = px.bar(compte_fournisseurs, x=compte_fournisseurs.index, y=compte_fournisseurs.values, title="Top 10 des Fournisseurs")
                        st.plotly_chart(fig1)

                    if analyse_couleur:
                        st.subheader("Prix Moyen par Couleur")
                        st.write(prix_moyen_par_couleur)
                        fig2 = px.bar(prix_moyen_par_couleur, x=prix_moyen_par_couleur.index, y=prix_moyen_par_couleur.values, title="Prix Moyen par Couleur")
                        st.plotly_chart(fig2)

                    if analyse_stock:
                        st.subheader("Analyse des Stocks")
                        st.write(analyse_stock_res)
                        fig3 = px.bar(analyse_stock_res, x=analyse_stock_res.index, y='Qté stock dispo', title="Quantité de Stock Disponible par Famille")
                        st.plotly_chart(fig3)
                        fig4 = px.bar(analyse_stock_res, x=analyse_stock_res.index, y='Valeur Stock', title="Valeur de Stock par Famille")
                        st.plotly_chart(fig4)

                # Filter data for stock quantities from 1 to 5
                filtered_df = df[df['Qté stock dispo'].isin([1, 2, 3, 4, 5])][['Magasin', 'fournisseur', 'barcode', 'couleur', 'Qté stock dispo']]
                
                # Display filtered results
                with st.expander("Détails des Stocks avec Qté de 1 à 5"):
                    st.write(filtered_df)

                # PDF Generation and Download
                st.markdown("## Générer un Rapport PDF")
                if st.button("Télécharger le rapport en PDF"):
                    pdf_bytes = creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock_res, filtered_df)
                    st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name="rapport_analyse.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"Une erreur s'est produite lors de l'analyse des données : {e}")
    else:
        st.info("Veuillez télécharger un fichier à analyser.")
