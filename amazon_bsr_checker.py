
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import streamlit as st
import tempfile

def get_bsr_from_amazon(isbn):
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
            bsr_section = product_soup.find(id='detailBulletsWrapper_feature_div')
            if bsr_section:
                text = bsr_section.get_text()
                for line in text.split('\n'):
                    if "Best Sellers Rank" in line:
                        return line.strip()
            return "Not found"
        else:
            return "No link"
    except:
        return "Error"

def main():
    st.title("Amazon BSR Checker")
    st.write("Yüklediğiniz Excel dosyasındaki ISBN'ler için Amazon BSR bilgilerini çeker.")

    uploaded_file = st.file_uploader("Excel dosyanızı yükleyin (ISBN, TITLE, BRN, RETAIL sütunlarını içermelidir):", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        required_columns = {'ISBN', 'TITLE', 'BRN', 'RETAIL'}
        if not required_columns.issubset(df.columns):
            st.error("Excel dosyasında ISBN, TITLE, BRN ve RETAIL sütunları olmalıdır.")
            return

        bsr_list = []
        progress = st.progress(0)
        for i, isbn in enumerate(df['ISBN']):
            bsr = get_bsr_from_amazon(str(isbn))
            bsr_list.append(bsr)
            progress.progress((i + 1) / len(df))
            time.sleep(1.5)

        df['BSR'] = bsr_list

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            df.to_excel(tmp.name, index=False)
            st.success("İşlem tamamlandı. Dosyanız hazır!")
            st.download_button("Excel dosyasını indir", data=open(tmp.name, 'rb').read(), file_name="output_bsr.xlsx")

if __name__ == "__main__":
    main()
