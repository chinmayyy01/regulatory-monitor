# Agent instructions

## Git

- Never run `git commit`, `git push`, `git rebase`, or change remote state. Stage nothing unless asked.
  The author commits and pushes themselves.
- Show the suggested commit message in chat instead.

## Decisions

- Every non-obvious decision must be appended to `notes/DECISIONS.md` in the same turn it is made:
  what was decided, why, the trade-off, and status.
- `notes/` is gitignored on purpose. Never add it to git, never paste its contents into a public file.
- `notes/PLAN.md` is the current plan, `notes/DECISIONS.md` is the history, `notes/SECURITY.md` are
  binding security rules.

## Verification

- Run `make test` before claiming something works. It must stay offline: no network, no model calls.
- Anything that spends money (LLM calls) must be opt-in, budgeted, and resumable.

## Style

- No comments in code unless the author asks. Explain decisions in chat and in `notes/`.
- Prefer plain code the author can explain line by line over frameworks and abstractions.
