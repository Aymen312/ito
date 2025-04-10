import streamlit as st
import pandas as pd
from io import BytesIO

#### --- Fonctions pour le traitement des données ---
def clean_numeric_columns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def normalize_size(size):
    """Supprimer les zéros non significatifs en début et convertir en chaîne uniforme."""
    try:
        if size.endswith('US') or size.endswith('UK'):
            num, suffix = size[:-2], size[-2:]
            return f"{str(float(num))}{suffix}"
        return str(float(size))
    except:
        return size

def highlight_row_if_one(row):
    if row['Qté stock dispo'] == 1:
        return ['background-color: red' for _ in row]
    else:
        return [''] * len(row)

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

    df_filtered['taille_normalized'] = df_filtered['taille'].apply(normalize_size)

    df_homme = df_filtered[df_filtered['rayon'].str.upper() == 'HOMME']
    df_femme = df_filtered[df_filtered['rayon'].str.upper() == 'FEMME']
    df_autre = df_filtered[~df_filtered['rayon'].str.upper().isin(['HOMME', 'FEMME'])]

    st.subheader("Rayon Homme:")
    st.dataframe(df_homme[colonnes_affichier].style.apply(highlight_row_if_one, axis=1))

    st.subheader("Rayon Femme:")
    st.dataframe(df_femme[colonnes_affichier].style.apply(highlight_row_if_one, axis=1))

    st.subheader("Autres Rayons:")
    st.dataframe(df_autre[colonnes_affichier].style.apply(highlight_row_if_one, axis=1))

    specific_designations = [
        'PRODIGIO', 'PRODIGIO WOMAN', 'AKASHA II', 'AKASHA II WOMAN', 'JACKAL',
        'ULTRA RAPTOR II MID LEATHER GTX', 'ULTRA RAPTOR II MID GTX',
        'ULTRA RAPTOR II LEATHER W GTX', 'ULTRA RAPTOR II LEATHER WOMAN',
        'ULTRA RAPTOR II GTX', 'AKASHA'
    ]

    possible_sizes_us = []
    possible_sizes_uk = []

    if any(desig in designation for desig in specific_designations):
        for size in range(36, 48):
            possible_sizes_us.append(f'{size}')
            if size != 47:
                possible_sizes_us.append(f'{size}.5')
    else:
        for size in ['4', '5', '6', '7', '8', '9', '10', '11', '12']:
            possible_sizes_us.append(f'{size}.0US')
            possible_sizes_us.append(f'{size}.5US')
            possible_sizes_uk.append(f'{size}.0UK')
            possible_sizes_uk.append(f'{size}.5UK')

    # Normaliser les tailles disponibles
    available_sizes_normalized = df_filtered['taille_normalized'].unique()

    # Normaliser les tailles possibles
    possible_sizes_us_normalized = [normalize_size(s) for s in possible_sizes_us]
    possible_sizes_uk_normalized = [normalize_size(s) for s in possible_sizes_uk]

    unavailable_sizes_us = [s for s, s_norm in zip(possible_sizes_us, possible_sizes_us_normalized) if s_norm not in available_sizes_normalized]
    unavailable_sizes_uk = [s for s, s_norm in zip(possible_sizes_uk, possible_sizes_uk_normalized) if s_norm not in available_sizes_normalized]

    st.subheader("Tailles indisponibles pour la désignation sélectionnée:")

    col1, col2 = st.columns(2)
    with col1:
        st.write("Tailles US indisponibles :")
        if unavailable_sizes_us:
            st.write(unavailable_sizes_us)
        else:
            st.write("Toutes les tailles US sont disponibles pour cette désignation.")

    with col2:
        st.write("Tailles UK indisponibles :")
        if unavailable_sizes_uk:
            st.write(unavailable_sizes_uk)
        else:
            st.write("Toutes les tailles UK sont disponibles pour cette désignation.")

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

        available_sizes = df_sidas_level['taille'].unique()
        unavailable_sizes = [size for size in sizes if size not in available_sizes]
        st.write(f"Tailles indisponibles pour SIDAS niveau {level}: {', '.join(unavailable_sizes) if unavailable_sizes else 'Aucune'}")

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
        st.markdown(f"Qté dispo totale pour {famille} : {total_stock}")
        st.markdown(f"Valeur totale du stock pour {famille} : {total_stock_value:.2f}")

        rayon_options = ['Tous', 'Homme', 'Femme', 'Autre']
        rayon_filter = st.selectbox(f"Filtrer par Rayon pour {famille}:",
                                    options=rayon_options,
                                    key=f"rayon_{famille}")

        if rayon_filter == 'Tous':
            pass
        elif rayon_filter in ['Homme', 'Femme']:
            df_family['rayon'] = df_family['rayon'].fillna('')
            df_family = df_family[df_family['rayon'].str.upper() == rayon_filter.upper()]
