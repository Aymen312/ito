import streamlit as st
import pandas as pd
import altair as alt
from fpdf import FPDF

## Function to perform analyses
def analyser_donnees(df):
    compte_fournisseurs = df['fournisseur'].value_counts().head(10)
    df['Prix Achat'] = df['Prix Achat'].astype(str).str.replace(',', '.').astype(float)
    prix_moyen_par_couleur = df.groupby('couleur')['Prix Achat'].mean().sort_values(ascending=False).head(10)
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0).astype(int)
    df['Valeur Stock'] = df['Valeur Stock'].astype(str).str.replace(',', '.').astype(float)
    analyse_stock = df.groupby('famille').agg({'Qté stock dispo': 'sum', 'Valeur Stock': 'sum'}).sort_values(by='Qté stock dispo', ascending=False).head(10)
    return compte_fournisseurs, prix_moyen_par_couleur, analyse_stock

## Function to create PDF report
def creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)

    # Add title
    pdf.cell(200, 10, txt = "Rapport d'Analyse de Fichier", ln = True, align = 'C')
    
    # Add fournisseur analysis
    pdf.cell(200, 10, txt = "Analyse des Fournisseurs", ln = True)
    for idx, (fournisseur, count) in enumerate(compte_fournisseurs.items(), start=1):
        pdf.cell(200, 10, txt = f"{idx}. {fournisseur}: {count}", ln = True)

    # Add average price by color
    pdf.cell(200, 10, txt = "Prix Moyen par Couleur", ln = True)
    for idx, (couleur, prix) in enumerate(prix_moyen_par_couleur.items(), start=1):
        pdf.cell(200, 10, txt = f"{idx}. {couleur}: {prix:.2f}", ln = True)

    # Add stock analysis
    pdf.cell(200, 10, txt = "Analyse des Stocks", ln = True)
    for idx, (famille, row) in enumerate(analyse_stock.iterrows(), start=1):
        pdf.cell(200, 10, txt = f"{idx}. {famille}: Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}", ln = True)

    # Add filtered stock details
    pdf.cell(200, 10, txt = "Détails des Stocks avec Qté de 1 à 5", ln = True)
    for idx, row in filtered_df.iterrows():
        pdf.cell(200, 10, txt = f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Qté stock dispo = {row['Qté stock dispo']}", ln = True)

    return pdf.output(dest="S").encode("latin1")

## Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

## Custom CSS
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

## File upload
fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        if extension_fichier == 'csv':
            df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=',', on_bad_lines='skip')
        elif extension_fichier == 'xlsx':
            df = pd.read_excel(fichier_telecharge)
        else:
            st.error("Format de fichier non supporté")

        # Show a summary of the data
        st.subheader("Résumé des Données")
        st.write(df.describe())

        # Data analysis
        compte_fournisseurs, prix_moyen_par_couleur, analyse_stock = analyser_donnees(df)

        # Display results in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Analyse des Fournisseurs")
            st.write(compte_fournisseurs)
        
        with col2:
            st.subheader("Prix Moyen par Couleur")
            st.write(prix_moyen_par_couleur)
            # Visualize average price by color
            chart = alt.Chart(df).mark_bar().encode(
                x='couleur',
                y='Prix Achat',
                color='couleur'
            )
            st.altair_chart(chart, use_container_width=True)

        with col3:
            st.subheader("Analyse des Stocks")
            st.write(analyse_stock)

        # Filter data for stock quantities from 1 to 5
        filtered_df = df[df['Qté stock dispo'].isin([1, 2, 3, 4, 5])][['Magasin', 'fournisseur', 'barcode', 'couleur', 'Qté stock dispo']]
        
        # Display filtered results
        st.subheader("Détails des Stocks avec Qté de 1 à 5")
        st.write(filtered_df)

        # PDF Generation and Download
        if st.button("Télécharger le rapport en PDF"):
            pdf = creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df)
            st.download_button(label="Télécharger le PDF", data=pdf, file_name="rapport_analyse.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Une erreur s'est produite lors de l'analyse des données : {e}")
else:
    st.info("Veuillez télécharger un fichier à analyser.")
