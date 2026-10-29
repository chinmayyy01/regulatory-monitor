# Archived v1 pipeline

Snapshot of the original RegIntel v1 (fetch -> summarise -> score -> Slack) kept for reference.
It is **not** imported by the live app and is **not** runnable without changes: the imports here
were written when these modules lived under `app/`.

To run it you would need `pip install -r requirements-legacy.txt` and to rewrite the `app.*`
imports to `legacy.*`. The v2 plan replaces this pipeline entirely.
