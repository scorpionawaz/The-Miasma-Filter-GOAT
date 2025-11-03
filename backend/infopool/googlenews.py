import requests
from bs4 import BeautifulSoup
import json
import re

def get_google_news_json():
    """Fetch and return Google News results for a given location in JSON format."""
    
    URL = "https://news.google.com/home?hl=en-IN&gl=IN&ceid=IN:enn"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
    }

    def parse_time_to_minutes(timestamp):
        if not timestamp or timestamp == 'N/A':
            return float('inf')
        timestamp = timestamp.lower().strip()
        match = re.match(r'(\d+)\s*(minute|hour|day)', timestamp)
        if not match:
            return float('inf')
        value, unit = int(match.group(1)), match.group(2)
        return value if unit == 'minute' else value * 60 if unit == 'hour' else value * 1440

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return json.dumps([])

    soup = BeautifulSoup(response.content, 'html.parser')
    article_elements = soup.find_all('article', class_=['IBr9hb', 'UwIKyb', 'IFHyqb'])
    
    news_data = []
    for article in article_elements[:20]:
        headline_tag = article.find('a', class_='gPFEn') or article.find('a', class_='JtKRv iTin5e')
        headline = headline_tag.text.strip() if headline_tag else 'N/A'
        
        if headline == 'N/A':
            headline_anchor = article.find('a', {'data-n-tid': '29'})
            if headline_anchor and 'aria-label' in headline_anchor.attrs:
                headline = headline_anchor['aria-label'].split(' - ')[0].strip()

        source_tag = article.find('div', class_='vr1PYe')
        timestamp_tag = article.find('time', class_='hvbAAd')
        image_tag = article.find('img', class_='Quavad vwBmvb')

        source = source_tag.text.strip() if source_tag else 'N/A'
        timestamp = timestamp_tag.text.strip() if timestamp_tag else 'N/A'
        is_top_trending = bool(image_tag)

        if headline != 'N/A':
            news_data.append({
                "headline": headline,
                "source": source,
                "updated_at": timestamp,
                "minutes_since": parse_time_to_minutes(timestamp),
                "is_top_trending": is_top_trending
            })

    news_data.sort(key=lambda x: (not x["is_top_trending"], x["minutes_since"]))
    return json.dumps(news_data, indent=4, ensure_ascii=False)

