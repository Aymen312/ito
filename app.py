import streamlit as st
import pandas as pd

# --- Fonctions pour le traitement des données ---
def cleannumericcolumns(df):
    numeric_columns = ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']
    for col in numeric_columns:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def cleansizecolumn(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def highlightrowif_one(row):
    """Met en surbrillance la ligne en rouge si 'Qté stock dispo' est égale à 1."""
    if row['Qté stock dispo'] == 1:
        return ['background-color: red' for _ in row]
    else:
        return [''] * len(row)

# --- Affichage des tailles indisponibles SIDAS ---
def displaysidas_levels(df):
    sidas_levels = {
        "XS": ["XS", "34", "36"],
        "S": ["S", "38", "40"],
        "M": ["M", "42", "44"],
        "L": ["L", "46", "48"],
        "XL": ["XL", "50", "52"],
        "XXL": ["XXL", "54", "56"]
    }
    
    result = {}
    
    for level, sizes in sidas_levels.items():
        # Filtrer le dataframe pour le niveau SIDAS spécifique
        dflevel = df[df['taille'].isin(sizes)]
        
        # Trouver les tailles indisponibles pour ce niveau
        available_sizes = dflevel['taille'].unique()
        unavailable_sizes = [size for size in sizes if size not in available_sizes]
        
        result[level] = {
            'data': dflevel,
            'unavailable_sizes': unavailable_sizes
        }
    
    return result

# --- Interface principale de l'application ---
st.title("Application d'Analyse TDR")
st.sidebar.markdown("###### Menu")
fichiertelecharge = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])

if fichiertelecharge is not None:
    extension_fichier = fichiertelecharge.name.split('.')[-1]
    try:
        if extension_fichier == 'csv':
            df = pd.read_csv(fichiertelecharge, encoding='ISO-8859-1', sep=';')
        elif extension_fichier == 'xlsx':
            df = pd.read_excel(fichiertelecharge)
        
        # Nettoyage des colonnes
        df = cleannumericcolumns(df)
        df = cleansizecolumn(df)
        st.success("Données chargées avec succès!")

        # --- Onglet Niveaux SIDAS ---
        sidasresults = displaysidas_levels(df)
        for level, result in sidasresults.items():
            st.write(f"Quantités disponibles pour SIDAS niveau {level}:")
            st.dataframe(result['data'].style.apply(highlightrowif_one, axis=1))  # Appliquer le style ici
            
            # Afficher les tailles indisponibles
            st.write(f"Tailles indisponibles pour SIDAS niveau {level}: {', '.join(result['unavailable_sizes'])}")

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
else:
    st.warning("Veuillez télécharger un fichier pour commencer l'analyse.")
