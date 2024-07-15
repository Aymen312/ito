import streamlit as st
import pandas as pd

## Fonction pour effectuer des analyses
def analyser_donnees(df):
    compte_fournisseurs = df['fournisseur'].value_counts().head(10)
    df['Prix Achat'] = df['Prix Achat'].astype(str).str.replace(',', '.').astype(float)
    prix_moyen_par_couleur = df.groupby('couleur')['Prix Achat'].mean().sort_values(ascending=False).head(10)
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0).astype(int)
    df['Valeur Stock'] = df['Valeur Stock'].astype(str).str.replace(',', '.').astype(float)
    analyse_stock = df.groupby('famille').agg({'Qté stock dispo': 'sum', 'Valeur Stock': 'sum'}).sort_values(by='Qté stock dispo', ascending=False).head(10)
    return compte_fournisseurs, prix_moyen_par_couleur, analyse_stock

## Application Streamlit
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

## CSS personnalisé
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

## Téléchargement du fichier
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

        # Afficher un résumé des données
        st.subheader("Résumé des Données")
        st.write(df.describe())

        # Analyse des données
        compte_fournisseurs, prix_moyen_par_couleur, analyse_stock = analyser_donnees(df)

        # Affichage des résultats
        st.subheader("Analyse des Fournisseurs")
        st.write(compte_fournisseurs)

        st.subheader("Prix Moyen par Couleur")
        st.write(prix_moyen_par_couleur)

        st.subheader("Analyse des Stocks")
        st.write(analyse_stock)

        # Filtrer les données pour Qté stock dispo de 1 à 5
        filtered_df = df[df['Qté stock dispo'].isin([1, 2, 3, 4, 5])][['Magasin', 'fournisseur', 'barcode', 'couleur', 'Qté stock dispo']]
        
        # Afficher les résultats filtrés
        st.subheader("Détails des Stocks avec Qté de 1 à 5")
        st.write(filtered_df)

    except Exception as e:
        st.error(f"Une erreur s'est produite lors de l'analyse des données : {e}")
else:
    st.info("Veuillez télécharger un fichier à analyser.")
