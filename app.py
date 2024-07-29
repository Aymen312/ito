import streamlit as st
import pandas as pd
from io import BytesIO

# Function to clean numeric columns
def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

# Function to strip leading and trailing spaces from sizes
def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

# Function to filter by supplier and display corresponding data
def display_supplier_info(df, fournisseur):
    fournisseur = fournisseur.strip().upper()  # Convert user input supplier to uppercase
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame()
    return df_filtered

# Function to filter by designation and display corresponding data
def display_designation_info(df, designation):
    designation = designation.strip().upper()  # Convert user input designation to uppercase
    df_filtered = df[df['designation'].str.upper().str.contains(designation)] if designation else pd.DataFrame()
    return df_filtered

# Function to filter negative stock
def filter_negative_stock(df):
    return df[df['Qté stock dispo'] < 0]

# Function to filter by supplier "ANITA" and display quantities available for each size
def display_anita_sizes(df):
    df_anita = df[df['fournisseur'].str.upper() == "ANITA"]
    tailles = [f"{num}{letter}" for num in [85, 90, 95, 100, 105, 110] for letter in 'ABCDEF']
    df_anita_sizes = df_anita[df_anita['taille'].isin(tailles)]
    df_anita_sizes = df_anita_sizes.groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)
    df_anita_sizes = df_anita_sizes.replace(0, "Nul")
    return df_anita_sizes

# Function to filter by SIDAS levels and display quantities available for each size
def display_sidas_levels(df):
    # Drop rows where 'couleur' or 'taille' are NaN
    df_sidas = df[df['fournisseur'].str.upper().str.contains("SIDAS", na=False)]
    df_sidas = df_sidas.dropna(subset=['couleur', 'taille'])
    
    levels = ['LOW', 'MID', 'HIGH']
    sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    results = {}
    for level in levels:
        df_sidas_level = df_sidas[df_sidas['couleur'].str.upper() == level]
        df_sizes = df_sidas_level[df_sidas_level['taille'].isin(sizes)]
        df_sizes_grouped = df_sizes.groupby(['taille', 'designation'])['Qté stock dispo'].sum().unstack(fill_value=0)
        df_sizes_grouped = df_sizes_grouped.replace(0, "Nul")
        df_sizes_with_designation = df_sizes_grouped.stack().reset_index().rename(columns={0: 'Qté stock dispo'})
        results[level] = df_sizes_with_designation
    return results

# Function to calculate total stock value by supplier
def total_stock_value_by_supplier(df):
    df['Valeur Totale HT'] = df['Qté stock dispo'] * df['Prix Achat']
    total_value_by_supplier = df.groupby('fournisseur')['Valeur Totale HT'].sum().reset_index()
    total_value_by_supplier = total_value_by_supplier.sort_values(by='Valeur Totale HT', ascending=False)
    return total_value_by_supplier

# Function to sort sizes numerically
def sort_sizes(df):
    df['taille'] = pd.Categorical(df['taille'], categories=sorted(df['taille'].unique(), key=lambda x: (int(x[:-1]), x[-1]) if x[:-1].isdigit() else (float('inf'), x)), ordered=True)
    df = df.sort_values('taille')
    return df

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
                        
                        # Sort sizes numerically
                        df_homme_filtered = sort_sizes(df_homme_filtered)
                        df_femme_filtered = sort_sizes(df_femme_filtered)
                        
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
                    except Exception as e:
                        st.error(f"Erreur lors de l'affichage des informations du fournisseur: {e}")
            
            with tab3:
                # Ask for designation input
                designation = st.text_input("Entrez la désignation:")

                if designation:
                    try:
                        designation = str(designation).strip().upper()  # Convert user input designation to uppercase

                        # Filter DataFrame based on user input
                        df_homme_filtered = display_designation_info(df_homme, designation)
                        df_femme_filtered = display_designation_info(df_femme, designation)

                        # Sort sizes numerically
                        df_homme_filtered = sort_sizes(df_homme_filtered)
                        df_femme_filtered = sort_sizes(df_femme_filtered)
                        
                        # Display filtered information
                        st.subheader("Informations par Désignation pour Hommes")
                        if not df_homme_filtered.empty:
                            st.dataframe(df_homme_filtered)
                        else:
                            st.write("Aucune information disponible pour la désignation spécifiée pour les hommes.")
                        
                        st.subheader("Informations par Désignation pour Femmes")
                        if not df_femme_filtered.empty:
                            st.dataframe(df_femme_filtered)
                        else:
                            st.write("Aucune information disponible pour la désignation spécifiée pour les femmes.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'affichage des informations par désignation: {e}")

            with tab4:
                st.subheader("Stock Négatif et Sa Valeur")
                try:
                    df_negative_stock = filter_negative_stock(df)
                    
                    if not df_negative_stock.empty:
                        # Display selected columns by default
                        columns_to_display = ['fournisseur', 'barcode', 'couleur', 'taille', 'Qté stock dispo']
                        
                        # Allow user to select additional columns to display
                        additional_columns = st.multiselect("Sélectionnez des colonnes supplémentaires à afficher", df.columns.difference(columns_to_display))
                        
                        columns_to_display.extend(additional_columns)
                        st.dataframe(df_negative_stock[columns_to_display])
                    else:
                        st.write("Aucun stock négatif trouvé.")
                except Exception as e:
                    st.error(f"Erreur lors de l'affichage du stock négatif: {e}")
            
            with tab5:
                st.subheader("Analyse des Tailles de Chaussures SIDAS")
                try:
                    sidas_results = display_sidas_levels(df)
                    if sidas_results:
                        for level, data in sidas_results.items():
                            st.write(f"Niveau: {level}")
                            st.dataframe(data)
                    else:
                        st.write("Aucune information disponible pour les niveaux SIDAS.")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse des niveaux SIDAS: {e}")

            with tab6:
                st.subheader("Valeur Totale du Stock par Fournisseur")
                try:
                    total_value_by_supplier = total_stock_value_by_supplier(df)
                    st.dataframe(total_value_by_supplier)
                except Exception as e:
                    st.error(f"Erreur lors du calcul de la valeur totale du stock par fournisseur: {e}")

            # Option to download the cleaned data
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                writer.save()

            download_file = st.download_button(
                label="Télécharger les données nettoyées",
                data=buffer,
                file_name="donnees_nettoyees.xlsx",
                mime="application/vnd.ms-excel"
            )

    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {e}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
