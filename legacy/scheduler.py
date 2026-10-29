from dotenv import load_dotenv
load_dotenv()
from app.fetchers.rbi import fetch_rbi_circulars
from app.fetchers.sebi import fetch_sebi_circulars
from app.store.vector_store import CircularStore
from app.chains.summarizer import summarize_circular
from app.chains.impact_scorer import score_impact
from app.notifier.slack import send_slack_digest

store = CircularStore() #here we Create a single ChromaDB + embedding store loading it again and again is expensive so we initialize once and reuse

def run_pipeline():
    print('\n[Pipeline] Starting regulatory check...\n')
    all_circulars = []
    print('[Pipeline] Fetching RBI circulars...')
    all_circulars.extend(fetch_rbi_circulars(limit=5))
    print('[Pipeline] Fetching SEBI circulars...')
    all_circulars.extend(fetch_sebi_circulars(limit=5))

    print(
        f'[Pipeline] Fetched '
        f'{len(all_circulars)} circulars'
    )

    new_circulars = store.filter_new(all_circulars)

    print(
        f'[Pipeline] '
        f'{len(new_circulars)} new circulars found'
    )

    if not new_circulars:
        print('[Pipeline] No new circulars.')
        return

    results = []
    for circular in new_circulars:
        print(
            f'[Pipeline] Processing: '
            f'{circular.title[:60]}...'
        )
        try:
            summary = summarize_circular(circular.title,circular.full_text)
            impact = score_impact(circular.title, summary, circular.full_text)
            results.append({
                'circular': circular,
                'summary': summary,
                'impact': impact,
            })
        except Exception as e:
            print(
                f'[Pipeline ERROR] '
                f'{circular.title[:40]}'
            )
            print(e)
    send_slack_digest(results)
    print(f'\n[Pipeline] Finished.')

if __name__ == '__main__':
    run_pipeline()