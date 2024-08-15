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

# Function to calculate total trail and running shoes
def count_shoes_by_type(df):
    # Convert the designation column to uppercase for consistency
    df['designation'] = df['designation'].str.upper()
    
    # Filter for trail and running shoes
    df_trail = df[df['designation'].str.contains('TRAIL')]
    df_running = df[df['designation'].str.contains('RUNNING')]
    
    # Calculate totals for men and women
    trail_homme = df_trail[df_trail['rayon'].str.upper() == 'HOMME']['Qté stock dispo'].sum()
    trail_femme = df_trail[df_trail['rayon'].str.upper() == 'FEMME']['Qté stock dispo'].sum()
    running_homme = df_running[df_running['rayon'].str.upper() == 'HOMME']['Qté stock dispo'].sum()
    running_femme = df_running[df_running['rayon'].str.upper() == 'FEMME']['Qté stock dispo'].sum()
    
    return {
        'trail_homme': trail_homme,
        'trail_femme': trail_femme,
        'running_homme': running_homme,
        'running_femme': running_femme
    }

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
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "Analyse ANITA", 
                "Analyse par Fournisseur", 
                "Analyse par Désignation", 
                "Stock Négatif", 
                "Analyse SIDAS", 
                "Valeur Totale du Stock par Fournisseur", 
                "Total Chaussures Trail et Running"
            ])
            
            with tab1:
                st.subheader("Quantités Disponibles pour chaque Taille - Fournisseur ANITA")
                try:
                    df_anita_sizes = display_anita_sizes(df)
                    if not df_anita_sizes.empty:
                        df_anita_sizes = sort_sizes(df_anita_sizes)
                        st.write(df_anita_sizes)
                    else:
                        st.warning("Aucune donnée trouvée pour le fournisseur ANITA")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse des tailles pour ANITA: {e}")

            with tab2:
                st.subheader("Analyse par Fournisseur")
                fournisseur = st.text_input("Entrez le nom du fournisseur")
                try:
                    df_filtered = display_supplier_info(df, fournisseur)
                    if not df_filtered.empty:
                        st.write(df_filtered)
                    else:
                        st.warning("Aucune donnée trouvée pour ce fournisseur")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse par fournisseur: {e}")

            with tab3:
                st.subheader("Analyse par Désignation")
                designation = st.text_input("Entrez une désignation (ex: Soutien-gorge)")
                try:
                    df_filtered_designation = display_designation_info(df, designation)
                    if not df_filtered_designation.empty:
                        st.write(df_filtered_designation)
                    else:
                        st.warning("Aucune donnée trouvée pour cette désignation")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse par désignation: {e}")

            with tab4:
                st.subheader("Produits en Stock Négatif")
                try:
                    df_negative_stock = filter_negative_stock(df)
                    if not df_negative_stock.empty:
                        st.write(df_negative_stock)
                    else:
                        st.warning("Aucun produit trouvé avec un stock négatif")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse des stocks négatifs: {e}")

            with tab5:
                st.subheader("Quantités Disponibles pour chaque Taille - Fournisseur SIDAS")
                try:
                    df_sidas_levels = display_sidas_levels(df)
                    if df_sidas_levels:
                        for level, df_level in df_sidas_levels.items():
                            with st.expander(f"Niveau {level}"):
                                st.write(df_level)
                    else:
                        st.warning("Aucune donnée trouvée pour le fournisseur SIDAS")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse des niveaux pour SIDAS: {e}")

            with tab6:
                st.subheader("Valeur Totale du Stock par Fournisseur")
                try:
                    df_total_value = total_stock_value_by_supplier(df)
                    st.write(df_total_value)
                except Exception as e:
                    st.error(f"Erreur lors du calcul de la valeur totale du stock: {e}")

            with tab7:
                st.subheader("Nombre Total des Chaussures Trail et Running")
                try:
                    shoe_counts = count_shoes_by_type(df)
                    
                    st.write(f"**Trail Homme :** {shoe_counts['trail_homme']}")
                    st.write(f"**Trail Femme :** {shoe_counts['trail_femme']}")
                    st.write(f"**Running Homme :** {shoe_counts['running_homme']}")
                    st.write(f"**Running Femme :** {shoe_counts['running_femme']}")
                except Exception as e:
                    st.error(f"Erreur lors du calcul des totaux pour les chaussures Trail et Running: {e}")

    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
