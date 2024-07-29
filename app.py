import streamlit as st
import pandas as pd
from io import BytesIO

# Function to create an Excel file from DataFrame
def create_excel_file(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    return output.getvalue()

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
                df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
            elif extension_fichier == 'xlsx':
                df = pd.read_excel(fichier_telecharge)
            else:
                st.error("Format de fichier non supporté")
                df = None

        if df is not None:
            # Clean data
            df = clean_numeric_columns(df)
            df = clean_size_column(df)

            # Separate data by gender
            df_homme = df[df['rayon'].str.upper() == 'HOMME']
            df_femme = df[df['rayon'].str.upper() == 'FEMME']

            # Tab selection
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "Analyse ANITA",
                "Analyse par Fournisseur",
                "Analyse par Désignation",
                "Stock Négatif",
                "Analyse SIDAS",
                "Valeur Totale du Stock par Fournisseur",
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

    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {e}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
