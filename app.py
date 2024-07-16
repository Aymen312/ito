import streamlit as st
import pandas as pd
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

## Function to perform analyses
def analyser_donnees(df):
    compte_fournisseurs = df['fournisseur'].value_counts().head(10)
    df['Prix Achat'] = df['Prix Achat'].astype(str).str.replace(',', '.').astype(float)
    prix_moyen_par_couleur = df.groupby('couleur')['Prix Achat'].mean().sort_values(ascending=False).head(10)
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0).astype(int)
    df['Valeur Stock'] = df['Valeur Stock'].astype(str).str.replace(',', '.').astype(float)
    analyse_stock = df.groupby('famille').agg({'Qté stock dispo': 'sum', 'Valeur Stock': 'sum'}).sort_values(by='Qté stock dispo', ascending=False).head(10)
    return compte_fournisseurs, prix_moyen_par_couleur, analyse_stock

## Function to generate PDF report
def generate_pdf_report(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Rapport d'Analyse de Fichier", ln=True, align='C')

    pdf.set_font("Arial", size=10)
    
    pdf.cell(200, 10, txt="Analyse des Fournisseurs:", ln=True, align='L')
    for idx, (fournisseur, count) in enumerate(compte_fournisseurs.items(), start=1):
        pdf.cell(200, 10, txt=f"{idx}. {fournisseur}: {count}", ln=True, align='L')
    
    pdf.cell(200, 10, txt="Prix Moyen par Couleur:", ln=True, align='L')
    for idx, (couleur, prix) in enumerate(prix_moyen_par_couleur.items(), start=1):
        pdf.cell(200, 10, txt=f"{idx}. {couleur}: {prix:.2f}", ln=True, align='L')
    
    pdf.cell(200, 10, txt="Analyse des Stocks:", ln=True, align='L')
    for idx, (famille, row) in enumerate(analyse_stock.iterrows(), start=1):
        pdf.cell(200, 10, txt=f"{idx}. {famille}: Qté stock dispo: {row['Qté stock dispo']}, Valeur Stock: {row['Valeur Stock']:.2f}", ln=True, align='L')
    
    pdf.cell(200, 10, txt="Détails des Stocks avec Qté de 1 à 5:", ln=True, align='L')
    for idx, row in enumerate(filtered_df.itertuples(), start=1):
        pdf.cell(200, 10, txt=f"{idx}. Magasin: {row.Magasin}, Fournisseur: {row.fournisseur}, Barcode: {row.barcode}, Couleur: {row.couleur}, Qté stock dispo: {row._5}", ln=True, align='L')
    
    report_path = "rapport_analyse.pdf"
    pdf.output(report_path)
    return report_path

## Function to send email with the report
def send_email(report_path):
    sender_email = "your_email@example.com"
    receiver_email = "aymenskateboard@gmail.com"
    subject = "Rapport d'Analyse de Fichier"
    body = "Veuillez trouver ci-joint le rapport d'analyse de fichier."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    attachment = open(report_path, "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(report_path)}")

    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, "your_password")
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

## Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

## Custom CSS
st.markdown("""
    <style>
        .main {
            background-color: #f0f2f6;
        }
        .stButton>button {
            background-color: #101E50;
            color: white;
        }
        .stHeader {
            color: #101E50;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("Application d'Analyse de Fichier")

## File upload
fichier_telecharge = st.file_uploader("Téléchargez un fichier CSV ou Excel", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    try:
        if extension_fichier == 'csv':
            df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=',', on_bad_lines='skip')
        elif extension_fichier == 'xlsx':
            df = pd.read_excel(fichier_telecharge)
        else:
            st.error("Format de fichier non supporté")

        # Show a summary of the data
        st.subheader("Résumé des Données")
        st.write(df.describe())

        # Data analysis
        compte_fournisseurs, prix_moyen_par_couleur, analyse_stock = analyser_donnees(df)

        # Display results in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Analyse des Fournisseurs")
            st.write(compte_fournisseurs)
        
        with col2:
            st.subheader("Prix Moyen par Couleur")
            st.write(prix_moyen_par_couleur)
        
        with col3:
            st.subheader("Analyse des Stocks")
            st.write(analyse_stock)

        # Filter data for stock quantities from 1 to 5
        filtered_df = df[df['Qté stock dispo'].isin([1, 2, 3, 4, 5])][['Magasin', 'fournisseur', 'barcode', 'couleur', 'Qté stock dispo']]
        
        # Display filtered results
        st.subheader("Détails des Stocks avec Qté de 1 à 5")
        st.write(filtered_df)

        # Generate and send report
        if st.button("Créer et envoyer le rapport"):
            report_path = generate_pdf_report(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df)
            if send_email(report_path):
                st.success("Rapport envoyé avec succès à aymenskateboard@gmail.com")
            else:
                st.error("Échec de l'envoi du rapport")

    except Exception as e:
        st.error(f"Une erreur s'est produite lors de l'analyse des données : {e}")
else:
    st.info("Veuillez télécharger un fichier à analyser.")
