from flask import Flask, request, jsonify,render_template
from playwright.async_api import async_playwright
import asyncio
import csv

app = Flask(__name__)

async def scrape_google_maps(keyword, location):
    name_sheet = f'{keyword}_results.csv'
    google_url = f'https://www.google.com/maps/search/{keyword}+{location}/data=!3m1!4b1?authuser=0&hl=en&entry=ttu'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Change to True for production
        page = await browser.new_page()
        try:
            await page.goto(google_url)
            await page.wait_for_selector('[jstcache="3"]')
            scrollable = await page.query_selector('xpath=/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]')
            if not scrollable:
                print('Scrollable element not found.')
                await browser.close()
                return jsonify({'error': 'Scrollable element not found'}), 400

            end_of_list = False
            while not end_of_list:
                await scrollable.evaluate('node => node.scrollBy(0, 50000)')
                end_of_list = await page.evaluate('() => document.body.innerText.includes("You\'ve reached the end of the list")')

            urls = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                return links.map(link => link.href).filter(href => href.startsWith('https://www.google.com/maps/place/'));
            }''')

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
                website = f'"{website}"'
                phone_element = await new_page.query_selector('button[data-tooltip="Copy phone number"]')
                phone = await phone_element.text_content() if phone_element else ''
                phone = f'"{phone}"'
                url = f'"{url}"'
                await new_page.close()
                return {
                    'name': name,
                    'rating': rating,
                    'reviews': reviews,
                    'category': category,
                    'address': address,
                    'website': website,
                    'phone': phone,
                    'url': url
                }

            batch_size = 5
            results = []
            for i in range(0, len(urls), batch_size):
                batch_urls = urls[i:i+batch_size]
                batch_results = await asyncio.gather(*[scrape_page_data(url) for url in batch_urls])
                results.extend(batch_results)

            csv_header = 'Name,Rating,Reviews,Category,Address,Website,Phone,Url\n'
            csv_rows = [f"{r['name']},{r['rating']},{r['reviews']},{r['category']},{r['address']},{r['website']},{r['phone']},{r['url']}" for r in results]
            with open(name_sheet, 'w', newline='', encoding='utf-8') as csvfile:
                csvfile.write(csv_header)
                csvfile.write('\n'.join(csv_rows))
                
            await browser.close()
            return results

        except Exception as e:
            return jsonify({'error': str(e)}), 500
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['GET'])
def scrape():
    keyword = request.args.get('keyword')
    location = request.args.get('location')
    if not keyword or not location:
        return jsonify({'error': 'Missing keyword or location parameter'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrape_google_maps(keyword, location))
    return result

if __name__ == '__main__':
    app.run(debug=True , port = 5020)


# send a GET request to http://localhost:5020/scrape?keyword=dentist&location=juja