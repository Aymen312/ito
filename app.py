import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

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
def creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df, selections):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Start writing PDF content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Fichier")
    c.setFont("Helvetica", 12)
    
    y_position = 720
    
    if 'Analyse des Fournisseurs' in selections:
        # Add fournisseur analysis
        c.drawString(50, y_position, "Analyse des Fournisseurs:")
        y_position -= 20
        for idx, (fournisseur, count) in enumerate(compte_fournisseurs.items(), start=1):
            c.drawString(70, y_position - idx * 20, f"{idx}. {fournisseur}: {count}")
        y_position -= len(compte_fournisseurs) * 20 + 20
    
    if 'Prix Moyen par Couleur' in selections:
        # Add average price by color
        c.drawString(50, y_position, "Prix Moyen par Couleur:")
        y_position -= 20
        for idx, (couleur, prix) in enumerate(prix_moyen_par_couleur.items(), start=1):
            c.drawString(70, y_position - idx * 20, f"{idx}. {couleur}: {prix:.2f}")
        y_position -= len(prix_moyen_par_couleur) * 20 + 20
    
    if 'Analyse des Stocks' in selections:
        # Add stock analysis
        c.drawString(50, y_position, "Analyse des Stocks:")
        y_position -= 20
        for idx, (famille, row) in enumerate(analyse_stock.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{idx}. {famille}: Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(analyse_stock) * 20 + 20
    
    if 'Détails des Stocks avec Qté de 1 à 5' in selections:
        # Add filtered stock details
        c.drawString(50, y_position, "Détails des Stocks avec Qté de 1 à 5:")
        y_position -= 20
        for idx, (_, row) in enumerate(filtered_df.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Qté stock dispo = {row['Qté stock dispo']}")
        y_position -= len(filtered_df) * 20 + 20
    
    # Save PDF to buffer
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

# Custom CSS for modern design
st.markdown("""
    <style>
        body {
            background: #141414;
            color: #E0E0E0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .main {
            background: #141414;
        }
        .stButton>button {
            background: #333;
            color: #E0E0E0;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: #555;
        }
        .stTextInput>div>input {
            border: 2px solid #333;
            border-radius: 8px;
            padding: 10px;
            background: #222;
            color: #E0E0E0;
        }
        .stTextInput>div>input:focus {
            border-color: #555;
            outline: none;
        }
        .stMultiSelect>div>div {
            border: 2px solid #333;
            border-radius: 8px;
            background: #222;
            color: #E0E0E0;
        }
        .stMultiSelect>div>div>div>div {
            color: #E0E0E0;
        }
        .stExpander>div>div {
            background: rgba(0, 0, 0, 0.6);
            color: #E0E0E0;
            border-radius: 8px;
            padding: 10px;
        }
        .stExpander>div>div>div {
            color: #E0E0E0;
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
                # Show a summary of the data
                st.subheader("Résumé des Données")
                st.write(df.describe())

                # Data analysis
                compte_fournisseurs, prix_moyen_par_couleur, analyse_stock = analyser_donnees(df)

                # Display analyses in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader("Analyse des Fournisseurs")
                    st.write(compte_fournisseurs)
                with col2:
                    st.subheader("Prix Moyen par Couleur")
                    st.write(prix_moyen_par_couleur)
                with col3:
                    st.subheader("Analyse des Stocks")
                    st.write(analyse_stock)

                # Filter data for stock quantities from 1 to 5
                filtered_df = df[df['Qté stock dispo'].isin([1, 2, 3, 4, 5])][['Magasin', 'fournisseur', 'barcode', 'couleur', 'Qté stock dispo']]
                
                # Display filtered results
                with st.expander("Détails des Stocks avec Qté de 1 à 5"):
                    st.write(filtered_df)

                # PDF Generation and Download
                st.markdown("## Générer un Rapport PDF")
                
                # Add checkboxes for PDF content selection
                selections = st.multiselect("Sélectionnez les sections à inclure dans le rapport PDF:",
                                            ['Analyse des Fournisseurs', 'Prix Moyen par Couleur', 'Analyse des Stocks', 'Détails des Stocks avec Qté de 1 à 5'])

                if st.button("Télécharger le rapport en PDF"):
                    if selections:
                        pdf_bytes = creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df, selections)
                        st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name="rapport_analyse.pdf", mime="application/pdf")
                    else:
                        st.error("Veuillez sélectionner au moins une section à inclure dans le rapport.")

        except Exception as e:
            st.error(f"Une erreur s'est produite lors de l'analyse des données : {e}")
    else:
        st.info("Veuillez télécharger un fichier à analyser.")
