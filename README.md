# Google Maps Scraper

## Overview

This Python Flask application scrapes Google Maps for places matching a given keyword and location. It utilizes Playwright for browser automation to fetch details such as name, rating, reviews, category, address, website, phone number, and URL of each place. The results are returned as a JSON response.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Setup Instructions

1. **Clone the repository or download the script:**

   ```bash
   git clone https://github.com/AmosMaru/google_maps_scrapper.git
   cd google_maps_scrapper

2. **Install required Python packages:**

    ```
    pip install Flask playwright asyncio
    playwright install
    ```

3. **Run the Flask application:**

    ```
    python app.py
    ```

## Sending Requests

To scrape Google Maps for places, send a GET request to the /scrape endpoint with the following query parameters:

1. keyword: The type of place you're searching for (e.g., dentist).
2. location: The location where you want to search (e.g., Nakuru).

### Example Request
Open your web browser and navigate to:

```bash
 http://localhost:5020/scrape?keyword=dentist&location=Nakuru

```

Or use curl from the command line:

```
curl "http://localhost:5020/scrape?keyword=dentist&location=Nakuru"
```

## Response
The response will be a JSON array containing objects with the following fields:

1. **name**: Name of the place
2. **rating**: Rating of the place
3. **reviews**: Number of reviews
4. **category**: Category of the place
5. **address**: Address of the place
6. **website**: Website URL of the place
7. **phone**: Phone number of the place
8. **url**: Google Maps URL of the place


## Example JSON Response

```[
    {
        "name": "Dentist 1",
        "rating": "4.5",
        "reviews": "123",
        "category": "Dental Clinic",
        "address": "123 Main St, Juja",
        "website": "https://example.com",
        "phone": "+1234567890",
        "url": "https://www.google.com/maps/place/...1"
    },
    {
        "name": "Dentist 2",
        "rating": "4.0",
        "reviews": "98",
        "category": "Dental Office",
        "address": "456 Another St, Juja",
        "website": "https://example.com",
        "phone": "+0987654321",
        "url": "https://www.google.com/maps/place/...2"
    }
    ...
]
```


## Notes
1. The script launches a browser instance in non-headless mode (headless=False). For production use, it's recommended to set headless=True.

2. Ensure that your use of this script complies with the terms of service of the websites you are scraping.

3. Google Maps structure might change, which can break the scraper. Ensure the selectors are up to date.

4. Be cautious with the frequency of requests to avoid IP bans or rate limiting.


# License