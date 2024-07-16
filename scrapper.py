from langchain_community.document_loaders import UnstructuredURLLoader
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


    
def scrape_url_1(url):
    # Send a GET request to the website
    response = requests.get(url, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        # Remove leading and trailing whitespace, then split into lines
        lines = [line.strip() for line in text.splitlines()]

        # Filter out empty lines
        clean_lines = [line for line in lines if line]

        # Join the clean lines back into a single string
        clean_text = '\n'.join(clean_lines)

        return clean_text

# print(scrape_url_1("https://kilush.com/"))



