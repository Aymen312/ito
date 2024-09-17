import streamlit as st
import pandas as pd
from io import BytesIO

# --- Fonctions pour le traitement des données ---
def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def highlight_row_if_one(row):
    """Met en surbrillance la ligne en rouge si 'Qté stock dispo' est égale à 1."""
    if row['Qté stock dispo'] == 1:
        return ['background-color: red' for _ in row]
    else:
        return [''] * len(row)

# --- Fonctions modifiées pour afficher les colonnes spécifiques ---
def display_supplier_info(df, fournisseur):
    colonnes_affichier = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    fournisseur = fournisseur.strip().upper()
    df['fournisseur'] = df['fournisseur'].fillna('')
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame(columns=colonnes_affichier)
    return df_filtered[colonnes_affichier]

def display_designation_info(df, designation):
    colonnes_affichier = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    df_filtered = df[df['designation'].str.upper().str.contains(designation)] if designation else pd.DataFrame(columns=colonnes_affichier)

    # --- Filtrage par rayon ---
    df_homme = df_filtered[df_filtered['rayon'].str.upper() == 'HOMME']
    df_femme = df_filtered[df_filtered['rayon'].str.upper() == 'FEMME']
    df_autre = df_filtered[~df_filtered['rayon'].str.upper().isin(['HOMME', 'FEMME'])]

    # --- Affichage des tableaux ---
    st.subheader("Rayon Homme:")
    st.dataframe(df_homme[colonnes_affichier].style.apply(highlight_row_if_one, axis=1))

    st.subheader("Rayon Femme:")
    st.dataframe(df_femme[colonnes_affichier].style.apply(highlight_row_if_one, axis=1))

    st.subheader("Autres Rayons:")
    st.dataframe(df_autre[colonnes_affichier].style.apply(highlight_row_if_one, axis=1))

    # --- Affichage des tailles indisponibles ---
    st.subheader("Tailles indisponibles pour la désignation sélectionnée:")
    unavailable_sizes = df_filtered[df_filtered['Qté stock dispo'] == 0]
    unavailable_sizes = unavailable_sizes[['fournisseur', 'couleur', 'taille', 'designation', 'rayon']]

    if not unavailable_sizes.empty:
        st.dataframe(unavailable_sizes)
    else:
        st.write("Toutes les tailles sont disponibles pour cette désignation.")

# --- Fonction modifiée pour "Stock Négatif" ---
def filter_negative_stock(df):
    colonnes_affichier = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0)
    df_filtered = df[df['Qté stock dispo'] < 0]
    return df_filtered[colonnes_affichier]

def display_anita_sizes(df):
    df_anita = df[df['fournisseur'].str.upper() == "ANITA"]
    tailles = [f"{num}{letter}" for num in [85, 90, 95, 100, 105, 110] for letter in 'ABCDEF']
    df_anita_sizes = df_anita[df_anita['taille'].isin(tailles)]
    df_anita_sizes = df_anita_sizes.groupby('taille')['Qté stock dispo'].sum().reindex(tailles, fill_value=0)
    df_anita_sizes = df_anita_sizes.replace(0, "Nul")
    return df_anita_sizes

def display_sidas_levels(df):
    df['fournisseur'] = df['fournisseur'].fillna('')
    df = df.dropna(subset=['couleur', 'taille'])
    df_sidas = df[df['fournisseur'].str.upper().str.contains("SIDAS")]
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

def total_stock_value_by_supplier(df):
    df['Qté stock dispo'] = pd.to_numeric(df['Qté stock dispo'], errors='coerce').fillna(0)
    df['Prix Achat'] = pd.to_numeric(df['Prix Achat'], errors='coerce').fillna(0)
    df['Valeur Totale HT'] = df['Qté stock dispo'] * df['Prix Achat']
    total_value_by_supplier = df.groupby('fournisseur')['Valeur Totale HT'].sum().reset_index()
    total_value_by_supplier = total_value_by_supplier.sort_values(by='Valeur Totale HT', ascending=False)
    return total_value_by_supplier

def sort_sizes(df):
    df['taille'] = pd.Categorical(df['taille'],
                                 categories=sorted(df['taille'].unique(),
                                                   key=lambda x: (int(x[:-1]), x[-1]) if x[:-1].isdigit() else (
                                                       float('inf'), x)),
                                 ordered=True)
    df = df.sort_values('taille')
    return df

def display_stock_by_family(df):
    familles = ["CHAUSSURES RANDO", "CHAUSSURES RUNN", "CHAUSSURE TRAIL"]
    for famille in familles:
        st.subheader(f"Stock pour {famille}")
        df['famille'] = df['famille'].fillna('')
        df_family = df[df['famille'].str.upper() == famille]
        df_family['Valeur Stock'] = df_family['Qté stock dispo'] * df_family['Prix Achat']

        total_stock = df_family['Qté stock dispo'].sum()
        total_stock_value = df_family['Valeur Stock'].sum()
        st.markdown(f"**Qté dispo totale pour {famille} : {total_stock}**")
        st.markdown(f"**Valeur totale du stock pour {famille} : {total_stock_value:.2f}**")

        rayon_options = ['Tous', 'Homme', 'Femme', 'Autre']
        rayon_filter = st.selectbox(f"Filtrer par Rayon pour {famille}:",
                                    options=rayon_options,
                                    key=f"rayon_{famille}")

        if rayon_filter == 'Tous':
            pass
        elif rayon_filter in ['Homme', 'Femme']:
            df_family['rayon'] = df_family['rayon'].fillna('')
            df_family = df_family[df_family['rayon'].str.upper() == rayon_filter.upper()]
        else:
            df_family['rayon'] = df_family['rayon'].fillna('')
            df_family = df_family[~df_family['rayon'].str.upper().isin(['HOMME', 'FEMME'])]

        if not df_family.empty:
            df_family = sort_sizes(df_family.copy())
            st.dataframe(df_family[
                             ['rayon', 'fournisseur', 'couleur', 'taille', 'designation', 'marque', 'ssfamille',
                              'Qté stock dispo', 'Valeur Stock']].style.apply(highlight_row_if_one, axis=1))

            total_stock_filtered = df_family['Qté stock dispo'].sum()
            total_stock_value_filtered = df_family['Valeur Stock'].sum()
            st.markdown(f"**Qté dispo totale pour {rayon_filter} : {total_stock_filtered}**")
            st.markdown(f"**Valeur totale du stock pour {rayon_filter} : {total_stock_value_filtered:.2f}**")
        else:
            st.write(f"Aucune information disponible pour {famille} "
                     f"dans la catégorie {rayon_filter}.")

# --- Configuration de l'application Streamlit ---
st.set_page_config(
    page_title="Application d'Analyse TDR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Interface principale de l'application ---
st.title("Application d'Analyse du Stock")

uploaded_file = st.file_uploader("Charger le fichier Excel contenant les données de stock:", type=['xls', 'xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = clean_numeric_columns(df)
    df = clean_size_column(df)

    st.sidebar.subheader("Navigation")
    options = ["Valeur Totale par Fournisseur", "Informations par Désignation", "Stock Négatif", "Stock par Famille", "Tailles ANITA", "Tailles SIDAS"]
    choice = st.sidebar.radio("Sélectionnez une option:", options)

    if choice == "Valeur Totale par Fournisseur":
        total_stock_value = total_stock_value_by_supplier(df)
        st.subheader("Valeur Totale du Stock par Fournisseur:")
        st.dataframe(total_stock_value)

        total_stock_value_sum = total_stock_value['Valeur Totale HT'].sum()
        st.markdown(f"**Valeur Totale du Stock : {total_stock_value_sum:.2f}**")

    elif choice == "Informations par Désignation":
        designation = st.text_input("Entrez la désignation du produit :")
        if designation:
            display_designation_info(df, designation)

    elif choice == "Stock Négatif":
        st.subheader("Produits avec Stock Négatif:")
        df_negative_stock = filter_negative_stock(df)
        st.dataframe(df_negative_stock)

    elif choice == "Stock par Famille":
        display_stock_by_family(df)

    elif choice == "Tailles ANITA":
        st.subheader("Tailles disponibles pour ANITA:")
        df_anita_sizes = display_anita_sizes(df)
        st.dataframe(df_anita_sizes)

    elif choice == "Tailles SIDAS":
        st.subheader("Tailles disponibles pour SIDAS par niveau:")
        df_sidas_levels = display_sidas_levels(df)
        for level, data in df_sidas_levels.items():
            st.subheader(f"Niveau : {level}")
            st.dataframe(data)
else:
    st.info("Veuillez charger un fichier Excel pour commencer.")
