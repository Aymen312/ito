import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
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

# Function to extract text from PDF
def extract_text_from_pdf(file):
    document = fitz.open(file)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text

# Function to convert extracted text to DataFrame (customize as needed)
def text_to_dataframe(text):
    # Custom parsing logic depending on PDF content
    data = {
        'Column1': [],
        'Column2': [],
        'Column3': []
    }
    for line in text.splitlines():
        columns = line.split()
        if len(columns) == 3:
            data['Column1'].append(columns[0])
            data['Column2'].append(columns[1])
            data['Column3'].append(columns[2])
    return pd.DataFrame(data)

# Function to create Excel file from DataFrame
def create_excel_file(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    buffer.seek(0)
    return buffer

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
st.sidebar.info("Téléchargez un fichier CSV, Excel ou PDF pour commencer l'analyse.")

# File upload
uploaded_file = st.file_uploader("Téléchargez un fichier CSV, Excel ou PDF", type=['csv', 'xlsx', 'pdf'])

if uploaded_file is not None:
    extension_fichier = uploaded_file.name.split('.')[-1]
    try:
        with st.spinner("Chargement des données..."):
            if extension_fichier == 'csv':
                # Read CSV with proper encoding and separator
                df = pd.read_csv(uploaded_file, encoding='ISO-8859-1', sep=';')
            elif extension_fichier == 'xlsx':
                df = pd.read_excel(uploaded_file)
            elif extension_fichier == 'pdf':
                # Extract text from PDF
                text = extract_text_from_pdf(uploaded_file)
                # Convert text to DataFrame
                df = text_to_dataframe(text)
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
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "Analyse ANITA", "Analyse par Fournisseur", "Analyse par Désignation", 
                "Stock Négatif", "Analyse SIDAS", "Valeur Totale du Stock par Fournisseur", 
                "Téléchargement de Fichier Excel"
            ])
            
            with tab1:
                st.subheader("Quantités Disponibles pour chaque Taille - Fournisseur ANITA")
                try:
                    df_anita_sizes = display_anita_sizes(df)
                    if not df_anita_sizes.empty:
                        st.dataframe(df_anita_sizes)
                    else:
                        st.write("Aucune donnée disponible pour le fournisseur ANITA.")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse des tailles ANITA : {e}")

            with tab2:
                st.subheader("Analyse par Fournisseur")
                fournisseur = st.text_input("Entrez le nom du fournisseur")
                df_supplier = display_supplier_info(df, fournisseur)
                if not df_supplier.empty:
                    st.dataframe(df_supplier)
                else:
                    st.write("Aucune donnée disponible pour ce fournisseur.")

            with tab3:
                st.subheader("Analyse par Désignation")
                designation = st.text_input("Entrez la désignation")
                df_designation = display_designation_info(df, designation)
                if not df_designation.empty:
                    st.dataframe(df_designation)
                else:
                    st.write("Aucune donnée disponible pour cette désignation.")

            with tab4:
                st.subheader("Stock Négatif")
                df_negative_stock = filter_negative_stock(df)
                if not df_negative_stock.empty:
                    st.dataframe(df_negative_stock)
                else:
                    st.write("Aucune donnée de stock négatif disponible.")

            with tab5:
                st.subheader("Analyse SIDAS")
                try:
                    sidas_results = display_sidas_levels(df)
                    for level, data in sidas_results.items():
                        st.write(f"**Niveau {level}**")
                        if not data.empty:
                            st.dataframe(data)
                        else:
                            st.write("Aucune donnée disponible pour ce niveau.")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse SIDAS : {e}")

            with tab6:
                st.subheader("Valeur Totale du Stock par Fournisseur")
                try:
                    total_value_by_supplier = total_stock_value_by_supplier(df)
                    if not total_value_by_supplier.empty:
                        st.dataframe(total_value_by_supplier)
                    else:
                        st.write("Aucune donnée disponible pour la valeur totale du stock.")
                except Exception as e:
                    st.error(f"Erreur lors du calcul de la valeur totale du stock : {e}")

         with tab7:
    st.subheader("Téléchargement de Fichier Excel")
    if st.button("Télécharger le fichier Excel"):
        try:
            excel_buffer = create_excel_file(df)
            st.download_button(
                label="Télécharger le fichier Excel",
                data=excel_buffer,
                file_name="data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erreur lors de la création du fichier Excel : {e}")
