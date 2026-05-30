import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import Circular

RBI_URL = 'https://www.rbi.org.in/scripts/NotificationUser.aspx'

def fetch_rbi_circulars(limit: int = 10) -> list[Circular]:
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(RBI_URL, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.content, 'lxml')
    table = soup.find('table')
    if not table:
        print('[RBI] No table found')
        return []
    rows = table.find_all('tr')
    circulars = []
    count = 0
    for row in rows:
        link = row.find('a')
        if not link:
            continue
        href = link.get('href')
        if not href:
            continue
        if 'NotificationUser.aspx' not in href:
            continue
        title = link.get_text(strip=True)
        if len(title) < 10:
            continue
        url = urljoin(RBI_URL, href)
        try:
            doc = requests.get(url, headers=headers, timeout=10)
            doc_soup = BeautifulSoup(doc.content, 'lxml')
            content_div = (
                doc_soup.find('div', class_='content')
                or doc_soup.find('div', id='content')
                or doc_soup.find('table')
            )
            if content_div:
                full_text = content_div.get_text(separator=' ', strip=True)
                full_text = ' '.join(full_text.split())
                full_text = full_text[:8000]
            else:
                full_text = title
        except Exception as e:
            print(f'[RBI DOC ERROR] {e}')
            full_text = title
        circulars.append(
            Circular(
                id=url,
                title=title,
                source='RBI',
                url=url,
                published_date=datetime.now(),
                full_text=full_text,
            )
        )
        count += 1
        if count >= limit:
            break
    return circulars