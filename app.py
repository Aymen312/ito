import streamlit as st
import pandas as pd
from io import BytesIO

# Function definitions as before ...

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse TDR", layout="wide")

# Custom CSS for futuristic design
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
st.sidebar.info("Téléchargez un fichier CSV ou Excel pour commencer l'analyse.")

# File upload
fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        with st.spinner("Chargement des données..."):
            if extension_fichier == 'csv':
                # Read CSV with proper encoding and separator
                df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
            elif extension_fichier == 'xlsx':
                df = pd.read_excel(fichier_telecharge)
            else:
                st.error("Format de fichier non supporté")
                df = None

        if df is not None:
            # Clean data
            df = clean_numeric_columns(df)
            df = clean_size_column(df)  # Clean size column

            # Separate data by gender
            df_homme = df[df['rayon'].str.upper() == 'HOMME']
            df_femme = df[df['rayon'].str.upper() == 'FEMME']
            df_unisexe = df[df['rayon'].str.upper() == 'UNISEXE']
            
            # Tab selection
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Analyse ANITA", "Analyse par Fournisseur", "Analyse par Désignation", "Stock Négatif", "Analyse SIDAS", "Valeur Totale du Stock par Fournisseur"])
            
            with tab1:
                st.subheader("Quantités Disponibles pour chaque Taille - Fournisseur ANITA")
                try:
                    df_anita_sizes = display_anita_sizes(df)
                    if not df_anita_sizes.empty:
                        st.table(df_anita_sizes)
                    else:
                        st.write("Aucune information disponible pour le fournisseur ANITA.")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse des tailles pour ANITA: {e}")
            
            with tab2:
                # Ask for supplier name
                fournisseur = st.text_input("Entrez le nom du fournisseur:")
                
                if fournisseur:
                    try:
                        fournisseur = str(fournisseur).strip().upper()  # Convert user input supplier to uppercase
                        
                        # Filter DataFrame based on user input
                        df_homme_filtered = display_supplier_info(df_homme, fournisseur)
                        df_femme_filtered = display_supplier_info(df_femme, fournisseur)
                        df_unisexe_filtered = display_supplier_info(df_unisexe, fournisseur)
                        
                        # Sort sizes numerically
                        df_homme_filtered = sort_sizes(df_homme_filtered)
                        df_femme_filtered = sort_sizes(df_femme_filtered)
                        df_unisexe_filtered = sort_sizes(df_unisexe_filtered)
                        
                        # Display filtered information
                        st.subheader("Informations sur le Fournisseur pour Hommes")
                        if not df_homme_filtered.empty:
                            st.dataframe(df_homme_filtered)
                        else:
                            st.write("Aucune information disponible pour le fournisseur spécifié pour les hommes.")
                        
                        st.subheader("Informations sur le Fournisseur pour Femmes")
                        if not df_femme_filtered.empty:
                            st.dataframe(df_femme_filtered)
                        else:
                            st.write("Aucune information disponible pour le fournisseur spécifié pour les femmes.")
                        
                        st.subheader("Informations sur le Fournisseur pour Unisexe")
                        if not df_unisexe_filtered.empty:
                            st.dataframe(df_unisexe_filtered)
                        else:
                            st.write("Aucune information disponible pour le fournisseur spécifié pour unisexe.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse par fournisseur: {e}")
            
            with tab3:
                st.subheader("Analyse par Désignation")
                
                # Rayon selection
                rayon = st.selectbox("Sélectionnez le rayon", ['Tous', 'Homme', 'Femme', 'Unisexe'])
                
                # Désignation input
                designation = st.text_input("Entrez la désignation à rechercher:")
                
                if designation:
                    try:
                        # Filter by rayon
                        if rayon == 'Tous':
                            df_filtered = df
                        elif rayon == 'Homme':
                            df_filtered = df_homme
                        elif rayon == 'Femme':
                            df_filtered = df_femme
                        else:  # Unisexe
                            df_filtered = df_unisexe
                        
                        # Filter by designation
                        df_designation_filtered = display_designation_info(df_filtered, designation)
                        df_designation_filtered = sort_sizes(df_designation_filtered)
                        
                        st.subheader("Informations par Désignation")
                        if not df_designation_filtered.empty:
                            st.dataframe(df_designation_filtered)
                        else:
                            st.write("Aucune information disponible pour la désignation spécifiée.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse par désignation: {e}")

            with tab4:
                st.subheader("Stock Négatif")
                try:
                    df_negative_stock = filter_negative_stock(df)
                    if not df_negative_stock.empty:
                        st.dataframe(df_negative_stock[['fournisseur', 'barcode', 'couleur', 'taille', 'Qté stock dispo']])
                    else:
                        st.write("Aucun stock négatif trouvé.")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse du stock négatif: {e}")
            
            with tab5:
                st.subheader("Analyse SIDAS")
                try:
                    sidas_results = display_sidas_levels(df)
                    for level, data in sidas_results.items():
                        st.subheader(f"Niveaux {level}")
                        if not data.empty:
                            st.dataframe(data)
                        else:
                            st.write(f"Aucune information disponible pour le niveau {level}.")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse SIDAS: {e}")
            
            with tab6:
                st.subheader("Valeur Totale du Stock par Fournisseur")
                try:
                    stock_value_by_supplier = total_stock_value_by_supplier(df)
                    if not stock_value_by_supplier.empty:
                        st.dataframe(stock_value_by_supplier)
                    else:
                        st.write("Aucune valeur totale disponible.")
                except Exception as e:
                    st.error(f"Erreur lors du calcul de la valeur totale du stock: {e}")

    else:
        st.info("Veuillez télécharger un fichier pour commencer l'analyse.")
