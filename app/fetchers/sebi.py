import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import Circular

SEBI_URL = (
    'https://www.sebi.gov.in/'
    'sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0'
)
def fetch_sebi_circulars(limit: int = 10) -> list[Circular]:
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(SEBI_URL, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.content, 'lxml')
    circulars = []
    links = soup.find_all('a')
    count = 0
    for link in links:
        href = link.get('href')
        if not href:
            continue
        href_lower = href.lower()
        if (
            'circular' not in href_lower
            and 'master' not in href_lower
            and '.pdf' not in href_lower
        ):
            continue
        title = link.get_text(strip=True)
        if len(title) < 10:
            continue
        url = urljoin(SEBI_URL, href)
        try:
            doc = requests.get(
                url,
                headers=headers,
                timeout=10
            )
            doc_soup = BeautifulSoup(doc.content, 'lxml')
            content_div = (
                doc_soup.find('div', class_='main-content')
                or doc_soup.find('div', class_='inner_cont')
                or doc_soup.find('body')
            )
            if content_div:
                full_text = content_div.get_text(separator='\n', strip=True)[:8000]
            else:
                full_text = title
        except Exception as e:
            print(f'[SEBI DOC ERROR] {e}')
            full_text = title
        circulars.append(
            Circular(
                id=url,
                title=title,
                source='SEBI',
                url=url,
                published_date=datetime.now(),
                full_text=full_text,
            )
        )
        count += 1
        if count >= limit:
            break
    return circulars