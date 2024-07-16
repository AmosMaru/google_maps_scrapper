from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from playwright.async_api import async_playwright
import asyncio
import csv
import os
from dotenv import load_dotenv
from openai import OpenAI
from scrapper import scrape_url_1
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# # Mount static files and templates
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

async def scrape_google_maps(keyword: str, location: str):
    name_sheet = f'{keyword}_results.csv'
    google_url = f'https://www.google.com/maps/search/{keyword}+{location}/data=!3m1!4b1?authuser=0&hl=en&entry=ttu'
    
    logger.info(f"Starting scraping for keyword: {keyword}, location: {location}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(google_url)
            await page.wait_for_selector('[jstcache="3"]', timeout=60000)
            scrollable = await page.query_selector('xpath=/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]')
            if not scrollable:
                logger.error('Scrollable element not found.')
                await browser.close()
                raise HTTPException(status_code=400, detail='Scrollable element not found')

            end_of_list = False
            while not end_of_list:
                await scrollable.evaluate('node => node.scrollBy(0, 50000)')
                end_of_list = await page.evaluate('() => document.body.innerText.includes("You\'ve reached the end of the list")')

            urls = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                return links.map(link => link.href).filter(href => href.startsWith('https://www.google.com/maps/place/'));
            }''')

            logger.info(f"Found {len(urls)} URLs to scrape")

            async def scrape_page_data(url):
                new_page = await browser.new_page()
                await new_page.goto(url)
                await new_page.wait_for_selector('[jstcache="3"]')
                name_element = await new_page.query_selector('xpath=/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1')
                name = await name_element.text_content() if name_element else ''
                name = f'"{name}"'
                rating_element = await new_page.query_selector('xpath=/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[1]/span[1]')
                rating = await rating_element.text_content() if rating_element else ''
                rating = f'"{rating}"'
                reviews_element = await new_page.query_selector('xpath=/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[2]/span/span')
                reviews = await reviews_element.text_content() if reviews_element else ''
                reviews = reviews.replace('(', '').replace(')', '')
                reviews = f'"{reviews}"'
                category_element = await new_page.query_selector('xpath=/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button')
                category = await category_element.text_content() if category_element else ''
                category = f'"{category}"'
                address_element = await new_page.query_selector('button[data-tooltip="Copy address"]')
                address = await address_element.text_content() if address_element else ''
                address = f'"{address}"'
                website_element = await new_page.query_selector('a[data-tooltip="Open website"]') or await new_page.query_selector('a[data-tooltip="Open menu link"]')
                website = await website_element.get_attribute('href') if website_element else ''
                website = website.strip() if website else ''
                phone_element = await new_page.query_selector('button[data-tooltip="Copy phone number"]')
                phone = await phone_element.text_content() if phone_element else ''
                phone = f'"{phone}"'
                url = f'"{url}"'
                email = await extract_email_from_website(website)
                email = f'"{email}"'
                await new_page.close()
                logger.info(f"Scraped data for: {name}")
                return {
                    'name': name,
                    'rating': rating,
                    'reviews': reviews,
                    'category': category,
                    'address': address,
                    'website': website,
                    'phone': phone,
                    'email': email,
                    'url': url
                }

            async def extract_email_from_website(website_url):
                if not website_url:
                    return 'None'
                try:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You find and output emails from content. Only write the emails you find in the content. If you don't find any emails, write 'None'."},
                            {"role": "user", "content": scrape_url_1(website_url)}
                        ]
                    )
                    logger.info(f"Extracted email for website: {website_url}")
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Error extracting email: {e}")
                    return 'None'

            batch_size = 5
            results = []
            for i in range(0, len(urls), batch_size):
                batch_urls = urls[i:i+batch_size]
                batch_results = await asyncio.gather(*[scrape_page_data(url) for url in batch_urls])
                results.extend(batch_results)

            csv_header = 'Name,Rating,Reviews,Category,Address,Website,Phone,Email,Url\n'
            csv_rows = [f"{r['name']},{r['rating']},{r['reviews']},{r['category']},{r['address']},{r['website']},{r['phone']},{r['email']},{r['url']}" for r in results]
            with open(name_sheet, 'w', newline='', encoding='utf-8') as csvfile:
                csvfile.write(csv_header)
                csvfile.write('\n'.join(csv_rows))

            logger.info(f"Scraping completed. Results saved to {name_sheet}")
            await browser.close()
            return results

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/scrape")
async def scrape(keyword: str = Query(...), location: str = Query(...)):
    if not keyword or not location:
        raise HTTPException(status_code=400, detail='Missing keyword or location parameter')

    try:
        result = await scrape_google_maps(keyword, location)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5522)