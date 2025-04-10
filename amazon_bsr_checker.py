import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import streamlit as st
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Helper to fetch BSR, price, and BRN from Amazon product page
def get_bsr_price_brn_from_amazon(isbn):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    url = f"https://www.amazon.com/s?k={isbn}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.find('a', {'class': 'a-link-normal s-no-outline'})
        if link:
            product_url = 'https://www.amazon.com' + link['href']
            product_response = requests.get(product_url, headers=headers, timeout=10)
            product_soup = BeautifulSoup(product_response.text, 'html.parser')

            # Fiyat bilgisi
            price_span = product_soup.find('span', {'class': 'a-price-whole'})
            price = price_span.get_text().strip() if price_span else "Not found"

            # BSR bilgisi
            bsr_section = product_soup.find(id='detailBulletsWrapper_feature_div')
            bsr_text = "Not found"
            brn_text = "Not found"
            if bsr_section:
                text = bsr_section.get_text()
                for line in text.split('\n'):
                    if "Best Sellers Rank" in line:
                        bsr_text = line.strip()
                    if "Publisher" in line or "Publication date" in line:
                        brn_text = line.strip()
            return bsr_text, price, brn_text
        else:
            return "No link", "No price", "No BRN"
    except:
        return "Error", "Error", "Error"

# Optional: send email with attachment (you must configure credentials)
def send_email_with_attachment(to_email, subject, body, file_path):
    from_email = "youremail@example.com"
    password = "yourpassword"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    part = MIMEBase('application', "octet-stream")
    with open(file_path, 'rb') as file:
        part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{file_path.split('/')[-1]}"')
    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()

# Web interface using Streamlit
def main():
    st.title("Amazon BSR Checker")
    st.write("Yüklediğiniz Excel dosyasındaki ISBN'ler için Amazon BSR, fiyat ve BRN bilgilerini çeker.")

    uploaded_file = st.file_uploader("Excel dosyanızı yükleyin (ISBN sütunu zorunlu, diğer sütunlar isteğe bağlıdır):", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        if 'ISBN' not in df.columns:
            st.error("Excel dosyasında en azından 'ISBN' sütunu bulunmalıdır.")
            return

        if 'TITLE' not in df.columns:
            df['TITLE'] = ""
        if 'BRN' not in df.columns:
            df['BRN'] = ""
        if 'RETAIL' not in df.columns:
            df['RETAIL'] = ""

        bsr_list = []
        price_list = []
        brn_list = []
        failed_isbns = []
        progress = st.progress(0)

        for i, isbn in enumerate(df['ISBN']):
            bsr, price, brn = get_bsr_price_brn_from_amazon(str(isbn))
            bsr_list.append(bsr)
            price_list.append(price)
            brn_list.append(brn)
            if bsr in ["Not found", "No link", "Error"]:
                failed_isbns.append(isbn)
            progress.progress((i + 1) / len(df))
            time.sleep(1.5)

        df['BSR'] = bsr_list
        df['Amazon Price'] = price_list
        df['Amazon BRN'] = brn_list

        # Save all data to Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_all:
            df.to_excel(tmp_all.name, index=False)
            st.success("İşlem tamamlandı. Dosyanız hazır!")
            st.download_button("Excel dosyasını indir", data=open(tmp_all.name, 'rb').read(), file_name="output_bsr_prices.xlsx")

        # Save failed ISBNs
        if failed_isbns:
            fail_df = pd.DataFrame({'Failed ISBNs': failed_isbns})
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_fail:
                fail_df.to_excel(tmp_fail.name, index=False)
                st.download_button("Hatalı ISBN'leri indir", data=open(tmp_fail.name, 'rb').read(), file_name="failed_isbns.xlsx")

        # Optional: send email
        # send_email_with_attachment("your@email.com", "Amazon BSR Results", "Attached is your BSR file.", tmp_all.name)

if __name__ == "__main__":
    main()
