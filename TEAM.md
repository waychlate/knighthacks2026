# TEAM: three people, 24 hours

Read this first, then your own guide in `docs/team/`.

| | Owns | Works in | Guide |
|---|---|---|---|
| **Teammate 1: ML** | Tiled detection for small animals, explaining the AI, other parks' species lists | `ml/`, `worker/` | [docs/team/ml.md](docs/team/ml.md) |
| **Teammate 2: frontend** | QA, wording and styling, screenshots, slides visuals | `web/`, `docs/` | [docs/team/frontend.md](docs/team/frontend.md) |
| **Project owner** | Supabase, Vercel, merges, the demo laptop (the only GPU), demo script, README | everything | [docs/team/integrator.md](docs/team/integrator.md) |

## How we work
- Everyone works on their own branch (`ml/...`, `web/...`, `owner/...`), pushes it, and opens a Pull Request. Merge it yourself once the tests pass; no formal review. The one hard rule: **don't push straight to `main`**.
- Stay in your own directory where you can. If you must change someone else's files, tell them.

## Git in five commands
```bash
git checkout main && git pull              # start from the latest
git checkout -b ml/tiling                  # your branch: ml/..., web/..., owner/...
# ... edit files ...
git add <the files you changed>            # not `git add .` if you are unsure what changed
git commit -m "Say what you did in one line"
git push -u origin ml/tiling               # then open the Pull Request on GitHub
```
If git says something scary, **stop and ask** instead of trying `--force` or `reset --hard`.

## Never commit
- `.env` (it holds the database keys; it is already gitignored, keep it that way)
- Model files (`*.pt`), big videos, the `sample_videos/` folder
- Anything you did not look at. Run `git status` before every commit.

## Keys
The project owner creates the Supabase project and Vercel site. If you need a key, they send it privately (not in the repo, not in a public chat). Until then, everything works on mock data.

## Honesty rules (these are judged)
- Synthetic or mock data is always labelled as such. Never call it real.
- Don't say the AI is better than we measured. Our numbers are in `ml/README.md` and `docs/PROGRESS.md`.

## Rough clock (H0 = now; project owner: write the real deadline here: __________)
| Hours from now | What |
|---|---|
| 0-2 | Owner runs `scripts/setup-supabase-vercel.sh`; the teammates set up their laptops and start |
| 2-14 | ML: tiling experiment (3 h cap), AI write-up. Frontend: QA, wording, screenshots |
| 14-18 | Integration: everything merged, deployed site checked on a phone |
| **18** | **FREEZE: only bug fixes after this** |
| 18-24 | Demo rehearsal (3 times), Devpost submitted early, not at the last minute |

## Stuck for more than 20 minutes?
Ask the project owner. Say what you ran, what you expected, and the exact error text.
