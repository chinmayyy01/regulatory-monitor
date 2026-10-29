from dotenv import load_dotenv
load_dotenv()
from app.fetchers.rbi import fetch_rbi_circulars
from app.chains.summarizer import summarize_circular
from app.chains.impact_scorer import score_impact

print('Fetching 1 RBI circular...')
circulars = fetch_rbi_circulars(limit=1)
if not circulars:
    print('No circulars found')
    exit()
c = circulars[0]
print(f'\nTesting: {c.title}')
print('-' * 60)
print('\nGenerating summary...\n')
summary = summarize_circular(
    c.title,
    c.full_text
)
print(summary)
print('\nGenerating impact score...\n')
impact = score_impact(
    c.title,
    summary,
    c.full_text
)
print(f'Impact:   {impact["impact_level"]}')
print(f'Affects:  {impact["affected_entities"]}')
print(f'Deadline: {impact["deadline"]}')
print(f'Reason:   {impact["reason"]}')
print(f'Action:   {impact["action_required"]}')