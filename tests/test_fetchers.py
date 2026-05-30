from app.fetchers.rbi import fetch_rbi_circulars 
from app.fetchers.sebi import fetch_sebi_circulars 

print('=== RBI ===') 
rbi = fetch_rbi_circulars(limit=3) 
print(f'Got {len(rbi)} circulars') 
if rbi: 
    print(f'Title:   {rbi[0].title}') 
    print(f'Date:    {rbi[0].published_date}') 
    print(f'Preview: {rbi[0].full_text[:150]}...') 

print() 
print('=== SEBI ===') 
sebi = fetch_sebi_circulars(limit=3) 
print(f'Got {len(sebi)} circulars') 
if sebi: 
    print(f'Title:   {sebi[0].title}') 
    print(f'Date:    {sebi[0].published_date}') 
