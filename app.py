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

# ... (Your other functions remain the same)

# Function to filter by family and rayon, and display stock quantities 
# with additional columns for Homme, Femme, and Autres
def display_stock_by_family(df):
    familles = ["CHAUSSURES RANDO", "CHAUSSURES RUNN", "CHAUSSURE TRAIL"]
    additional_columns = ['couleur', 'taille', 'designation', 'ssfamille', 'marque', 'rayon']
    
    # Filter the DataFrame for the specified families
    df_filtered = df[df['famille'].str.upper().isin(familles)]

    # Create separate DataFrames for Homme, Femme, and Autres
    df_homme = df_filtered[df_filtered['rayon'].str.upper() == 'HOMME']
    df_femme = df_filtered[df_filtered['rayon'].str.upper() == 'FEMME']
    df_autres = df_filtered[~df_filtered['rayon'].str.upper().isin(['HOMME', 'FEMME'])]

    # Group each DataFrame by 'famille' and the additional columns, 
    # then sum the stock quantities
    df_homme_grouped = df_homme.groupby(['famille'] + additional_columns)['Qté stock dispo'].sum().reset_index()
    df_femme_grouped = df_femme.groupby(['famille'] + additional_columns)['Qté stock dispo'].sum().reset_index()
    df_autres_grouped = df_autres.groupby(['famille'] + additional_columns)['Qté stock dispo'].sum().reset_index()
    
    return df_homme_grouped, df_femme_grouped, df_autres_grouped

# ... (Rest of your Streamlit application code)

            with tab7:
                st.subheader("Quantité de Stock par Famille")
                try:
                    df_homme_grouped, df_femme_grouped, df_autres_grouped = display_stock_by_family(df)

                    if not df_homme_grouped.empty:
                        st.write("**Stock Homme:**")
                        st.dataframe(df_homme_grouped)
                    else:
                        st.write("Aucune information disponible pour le rayon Homme.")

                    if not df_femme_grouped.empty:
                        st.write("**Stock Femme:**")
                        st.dataframe(df_femme_grouped)
                    else:
                        st.write("Aucune information disponible pour le rayon Femme.")

                    if not df_autres_grouped.empty:
                        st.write("**Stock Autres Rayons:**")
                        st.dataframe(df_autres_grouped)
                    else:
                        st.write("Aucune information disponible pour les autres rayons.")

                except Exception as e:
                    st.error(f"Erreur lors de l'affichage du stock par famille: {e}")
