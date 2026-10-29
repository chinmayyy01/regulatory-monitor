from dotenv import load_dotenv 
load_dotenv() 
from app.fetchers.rbi import fetch_rbi_circulars 
from app.store.vector_store import CircularStore 

print('Initialising store...') 
print('(First run downloads the embedding model — ~90MB, takes 1-2 minutes)') 
store = CircularStore() 

print('Store ready.') 

print('\nFetching 5 RBI circulars...') 
circulars = fetch_rbi_circulars(limit=5) 
print(f'Fetched: {len(circulars)}')

print('\nFirst run — should flag all as new:') 
new1 = store.filter_new(circulars) 
print(f'New: {len(new1)}') 

print('\nSecond run — should flag none as new (all duplicates):') 
same = fetch_rbi_circulars(limit=5) 
new2 = store.filter_new(same) 
print(f'New: {len(new2)}') 

