import streamlit as st
import pandas as pd
from io import BytesIO

# Function definitions (same as provided before)

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
                        
                        # Display filtered information
                        st.subheader("Informations du Fournisseur pour Hommes")
                        if not df_homme_filtered.empty:
                            st.dataframe(df_homme_filtered)
                        else:
                            st.write("Aucune information disponible pour le fournisseur spécifié pour les hommes.")
                        
                        st.subheader("Informations du Fournisseur pour Femmes")
                        if not df_femme_filtered.empty:
                            st.dataframe(df_femme_filtered)
                        else:
                            st.write("Aucune information disponible pour le fournisseur spécifié pour les femmes.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse du fournisseur: {e}")
            
            with tab3:
                # Ask for designation
                designation = st.text_input("Entrez la désignation (ex: Sneakers, Running):")
                
                if designation:
                    try:
                        designation = str(designation).strip().upper()  # Convert user input designation to uppercase
                        
                        # Filter DataFrame based on user input
                        df_homme_filtered = display_designation_info(df_homme, designation)
                        df_femme_filtered = display_designation_info(df_femme, designation)
                        
                        # Ask for size system
                        size_system = st.selectbox("Sélectionnez le système de taille", ["EU", "US", "UK"])
                        
                        # Define sizes based on system
                        tailles_us = ['4.5US', '5.0US', '5.5US', '6.0US', '6.5US', '7.0US', '7.5US', '8.0US', '8.5US', '9.0US', '9.5US', '10.0US', '10.5US', '11.0US', '11.5US', '12.0US', '12.5US', '13.0US', '13.5US', '14.0US']
                        tailles_uk = ['4.5UK', '5.0UK', '5.5UK', '6.0UK', '6.5UK', '7.0UK', '7.5UK', '8.0UK', '8.5UK', '9.0UK', '9.5UK', '10.0UK', '10.5UK', '11.0UK', '11.5UK', '12.0UK', '12.5UK', '13.0UK']
                        tailles_eu = [str(size) for size in list(range(30, 51)) + [f'{i}.5' for i in range(30, 50)]]
                        
                        if size_system == "US":
                            tailles = tailles_us
                        elif size_system == "UK":
                            tailles = tailles_uk
                        else:
                            tailles = tailles_eu

                        # Show quantity of stock for each size, excluding zero values
                        st.subheader(f"Quantité de Stock par Taille ({size_system}) pour Hommes")
                        homme_stock_by_size = df_homme_filtered[df_homme_filtered['taille'].isin(tailles)]
                        homme_stock_by_size = homme_stock_by_size.groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)
                        homme_stock_by_size = homme_stock_by_size.replace(0, "Nul")
                        st.table(homme_stock_by_size)
                        
                        st.subheader(f"Quantité de Stock par Taille ({size_system}) pour Femmes")
                        femme_stock_by_size = df_femme_filtered[df_femme_filtered['taille'].isin(tailles)]
                        femme_stock_by_size = femme_stock_by_size.groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)
                        femme_stock_by_size = femme_stock_by_size.replace(0, "Nul")
                        st.table(femme_stock_by_size)

            with tab4:
                # Stock négatif
                st.subheader("Stock Négatif")
                try:
                    negative_stock = df[df['Qté stock dispo'] < 0]
                    if not negative_stock.empty:
                        st.dataframe(negative_stock[['fournisseur', 'barcode', 'couleur', 'taille', 'Qté stock dispo']])
                    else:
                        st.write("Aucun stock négatif trouvé.")
                except Exception as e:
                    st.error(f"Erreur lors de l'affichage du stock négatif: {e}")
            
            with tab5:
                # Analyse SIDAS
                st.subheader("Analyse SIDAS")
                try:
                    sidas_analysis = sidas_analysis_function(df)  # Replace with actual analysis function
                    st.dataframe(sidas_analysis)
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse SIDAS: {e}")
            
            with tab6:
                # Valeur Totale du Stock par Fournisseur
                st.subheader("Valeur Totale du Stock par Fournisseur")
                try:
                    total_value_by_supplier = total_stock_value_by_supplier(df)
                    st.dataframe(total_value_by_supplier)
                except Exception as e:
                    st.error(f"Erreur lors du calcul de la valeur totale du stock: {e}")
