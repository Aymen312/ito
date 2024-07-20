import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Authentication function
def authenticate(username, password):
    return username == "ayada" and password == "123"

# Function to perform analyses
def analyser_donnees(df):
    compte_fournisseurs = df['fournisseur'].value_counts().head(10)
    df['Prix Achat'] = df['Prix Achat'].astype(str).str.replace(',', '.').astype(float)
    prix_moyen_par_couleur = df.groupby('couleur')['Prix Achat'].mean().sort_values(ascending=False).head(10)
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0).astype(int)
    df['Valeur Stock'] = df['Valeur Stock'].astype(str).str.replace(',', '.').astype(float)
    analyse_stock = df.groupby('famille').agg({'Qté stock dispo': 'sum', 'Valeur Stock': 'sum'}).sort_values(by='Qté stock dispo', ascending=False).head(10)
    return compte_fournisseurs, prix_moyen_par_couleur, analyse_stock

# Function to create PDF report
def creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df, selections):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Start writing PDF content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Rapport d'Analyse de Fichier")
    c.setFont("Helvetica", 12)
    
    y_position = 720
    
    if 'Analyse des Fournisseurs' in selections:
        # Add fournisseur analysis
        c.drawString(50, y_position, "Analyse des Fournisseurs:")
        y_position -= 20
        for idx, (fournisseur, count) in enumerate(compte_fournisseurs.items(), start=1):
            c.drawString(70, y_position - idx * 20, f"{idx}. {fournisseur}: {count}")
        y_position -= len(compte_fournisseurs) * 20 + 20
    
    if 'Prix Moyen par Couleur' in selections:
        # Add average price by color
        c.drawString(50, y_position, "Prix Moyen par Couleur:")
        y_position -= 20
        for idx, (couleur, prix) in enumerate(prix_moyen_par_couleur.items(), start=1):
            c.drawString(70, y_position - idx * 20, f"{idx}. {couleur}: {prix:.2f}")
        y_position -= len(prix_moyen_par_couleur) * 20 + 20
    
    if 'Analyse des Stocks' in selections:
        # Add stock analysis
        c.drawString(50, y_position, "Analyse des Stocks:")
        y_position -= 20
        for idx, (famille, row) in enumerate(analyse_stock.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{idx}. {famille}: Qté stock dispo = {row['Qté stock dispo']}, Valeur Stock = {row['Valeur Stock']:.2f}")
        y_position -= len(analyse_stock) * 20 + 20
    
    if 'Détails des Stocks avec Qté de 1 à 5' in selections:
        # Add filtered stock details
        c.drawString(50, y_position, "Détails des Stocks avec Qté de 1 à 5:")
        y_position -= 20
        for idx, (_, row) in enumerate(filtered_df.iterrows(), start=1):
            c.drawString(70, y_position - idx * 20,
                         f"{row['Magasin']}, {row['fournisseur']}, {row['barcode']}, {row['couleur']}, Qté stock dispo = {row['Qté stock dispo']}")
        y_position -= len(filtered_df) * 20 + 20
    
    # Save PDF to buffer
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes, True

# Function to send email
def send_email(pdf_bytes):
    fromaddr = "your_email@gmail.com"  # Replace with your email address
    toaddr = "aymenskateboard@gmail.com"  # Recipient's email address

    # Setup the MIME
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Rapport d'Analyse"

    # Attach the PDF to the email
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename=rapport_analyse.pdf")

    msg.attach(part)

    # Connect to Gmail's SMTP server and send the email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "your_password")  # Replace with your email password
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

# Streamlit Application
st.set_page_config(page_title="Application d'Analyse de Fichier", layout="wide")

# Custom CSS for futuristic design (not changed)
# ... CSS code remains the same as provided in the question ...

st.title("Application d'Analyse de Fichier")

# User authentication (not changed)
# ... Authentication code remains the same as provided in the question ...

# File upload and analysis (not changed)
# ... File upload and analysis code remains the same as provided in the question ...

# PDF Generation and Download (slightly modified)
# ... PDF generation code remains mostly the same as provided in the question ...

if st.button("Télécharger le rapport en PDF"):
    if selections:
        pdf_bytes, success = creer_pdf(compte_fournisseurs, prix_moyen_par_couleur, analyse_stock, filtered_df, selections)
        if success:
            st.download_button(label="Télécharger le PDF", data=pdf_bytes, file_name="rapport_analyse.pdf", mime="application/pdf")
            
            # Option to send the PDF via email
            if st.checkbox("Envoyer par Email"):
                send_email(pdf_bytes)
                st.success("Le rapport a été envoyé par email à aymenskateboard@gmail.com.")
    else:
        st.error("Veuillez sélectionner au moins une section à inclure dans le rapport.")
