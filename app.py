import streamlit as st
import pandas as pd
from io import StringIO

# Titre de l'application
st.title("Visualisation et Filtrage des Données")

# 1. Permettre à l'utilisateur de télécharger un fichier CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Lire le fichier CSV dans un DataFrame avec encodage adaptatif
        data = pd.read_csv(uploaded_file, encoding_errors='ignore')
        
        # Afficher les premières lignes du fichier
        st.write("Aperçu des données :")
        st.write(data.head())
        
        # 2. Ajouter un champ pour saisir une date de livraison
        date_livraison = st.text_input("Entrez la date de livraison (format JJ/MM/AAAA):")
        
        if date_livraison:
            try:
                # Filtrer les données pour afficher celles correspondant à la date
                filtered_data = data[data['datelivraison'] == date_livraison]
                
                if not filtered_data.empty:
                    st.write("Données correspondantes :")
                    st.write(filtered_data)
                else:
                    st.warning("Aucune donnée trouvée pour cette date de livraison.")
            except KeyError:
                st.error("La colonne 'datelivraison' n'existe pas dans le fichier.")
            except Exception as e:
                st.error(f"Erreur : {e}")
    except Exception as e:
        st.error(f"Impossible de lire le fichier : {e}")
else:
    st.info("Veuillez télécharger un fichier CSV pour commencer.")
