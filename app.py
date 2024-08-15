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
    df['taille'] = pd.Categorical(df['taille'], 
                                  categories=sorted(df['taille'].unique(), 
                                                    key=lambda x: (int(x[:-1]), x[-1]) if x[:-1].isdigit() else (float('inf'), x)), 
                                  ordered=True)
    df = df.sort_values('taille')
    return df

# Function to filter by family and rayon, and display stock quantities
def display_stock_by_family(df):
    familles = ["CHAUSSURES RANDO", "CHAUSSURES RUNN", "CHAUSSURE TRAIL"]

    for famille in familles:
        st.subheader(f"Stock pour {famille}")

        df_family = df[df['famille'].str.upper() == famille]

        # Calculate and display the total stock for the family
        total_stock = df_family['Qté stock dispo'].sum()
        st.write(f"**Qté dispo totale pour {famille} : {total_stock}**") 

        # Get unique rayons for the selected family 
        rayons = df_family['rayon'].str.upper().unique()

        # Options for rayon filter
        rayon_options = ['Tous', 'Homme', 'Femme', 'Autre']

        # Create the rayon filter selectbox
        rayon_filter = st.selectbox(f"Filtrer par Rayon pour {famille}:", 
                                    options=rayon_options, 
                                    key=f"rayon_{famille}")
        
        # Apply filtering based on selected rayon
        if rayon_filter == 'Tous':
            # Show all rayons
            pass 
        elif rayon_filter in ['Homme', 'Femme']:
            df_family = df_family[df_family['rayon'].str.upper() == rayon_filter.upper()]
        else:  # rayon_filter == 'Autre'
            df_family = df_family[~df_family['rayon'].str.upper().isin(['HOMME', 'FEMME'])]

        # Display the filtered DataFrame
        if not df_family.empty:
            df_family = sort_sizes(df_family.copy())
            st.dataframe(df_family[['fournisseur', 'couleur', 'taille', 'designation', 'marque', 'ssfamille']])

            # Calculate and display the total stock for the filtered rayon
            total_stock_filtered = df_family['Qté stock dispo'].sum()
            st.write(f"**Qté dispo totale pour {rayon_filter} : {total_stock_filtered}**")
        else:
            st.write(f"Aucune information disponible pour {famille} "
                     f"dans la catégorie {rayon_filter}.")

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
            outline: none.
        }
        .stMultiSelect>div>div {
            border: 2px solid #007BFF;
            border-radius: 5px;
            background-color: #1E1E1E;
            color: #F5F5F5.
        }
        .stMultiSelect>div>div>div>div {
            color: #F5F5F5.
        }
        .stExpander>div>div {
            background-color: #2D2D2D;
            color: #F5F5F5;
            border-radius: 5px;
            padding: 10px.
        }
        .stExpander>div>div>div {
            color: #F5F5F5.
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

            st.success("Données chargées avec succès!")

            # Tabs for different analyses
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Filtrer par Fournisseur", 
                                                          "Filtrer par Désignation", 
                                                          "Stock Négatif", 
                                                          "Anita Tailles", 
                                                          "Sidas Niveaux", 
                                                          "Valeur Totale du Stock par Fournisseur"])

            # Filter by Supplier Tab
            with tab1:
                fournisseur = st.text_input("Entrez le nom du fournisseur:")
                df_filtered = display_supplier_info(df, fournisseur)
                if not df_filtered.empty:
                    st.dataframe(df_filtered)
                else:
                    st.write("Aucune information disponible pour ce fournisseur.")

            # Filter by Designation Tab
            with tab2:
                designation = st.text_input("Entrez la désignation du produit:")
                df_filtered = display_designation_info(df, designation)
                if not df_filtered.empty:
                    st.dataframe(df_filtered)
                else:
                    st.write("Aucune information disponible pour cette désignation.")

            # Negative Stock Tab
            with tab3:
                df_negative_stock = filter_negative_stock(df)
                if not df_negative_stock.empty:
                    st.dataframe(df_negative_stock)
                else:
                    st.write("Aucun stock négatif trouvé.")

            # Anita Sizes Tab
            with tab4:
                df_anita_sizes = display_anita_sizes(df)
                st.write("Quantités disponibles pour Anita par taille:")
                st.dataframe(df_anita_sizes)

            # Sidas Levels Tab
            with tab5:
                sidas_results = display_sidas_levels(df)
                for level, df_level in sidas_results.items():
                    st.write(f"Quantités disponibles pour SIDAS niveau {level}:")
                    st.dataframe(df_level)

            # Total Stock Value by Supplier Tab
            with tab6:
                st.subheader("Valeur Totale du Stock par Fournisseur")
                df_total_value_by_supplier = total_stock_value_by_supplier(df)

                # Display the sorted table
                st.dataframe(df_total_value_by_supplier)

                # Calculate and display the total sum of all suppliers
                total_value = df_total_value_by_supplier['Valeur Totale HT'].sum()
                st.write(f"**Valeur Totale du Stock pour tous les fournisseurs : {total_value:.2f}**")
            
            # Stock by Family Section
            st.header("Stock par Famille")
            display_stock_by_family(df)

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
