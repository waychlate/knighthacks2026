# TEAM: three people, 24 hours

Read this first, then your own file: **A** = `TASKS-A.md`, **B** = `TASKS-B.md`, **C** = `TASKS-C.md`.

| | Owns | Works in | Language |
|---|---|---|---|
| **A** | Make the detector see small animals (tiling), keep the worker healthy | `worker/` | Python |
| **B** | Other parks' species lists, QA, Devpost, slides, demo script | `docs/`, `worker/species_*.json` | Python (a little) + writing |
| **C** | Merge, Supabase, Vercel, web app, reviews, the live demo (the only GPU laptop) | `supabase/`, `web/`, everything else | everything |

## The one big rule
**Nobody pushes to `main`.** Work on your own branch, push the branch, open a Pull Request on GitHub, and C merges it after running the tests. This protects the demo from a bad push at 3 AM.

## Git in five commands
```bash
git checkout main && git pull              # start from the latest
git checkout -b a/tiling                   # your branch: a/..., b/..., c/...
# ... edit files ...
git add <the files you changed>            # not `git add .` if you are unsure what changed
git commit -m "Say what you did in one line"
git push -u origin a/tiling                # then open the Pull Request on GitHub
```
If git says something scary, **stop and ask C** instead of trying `--force` or `reset --hard`.

## Never commit
- `.env` (it holds the database keys; it is already gitignored, keep it that way)
- Model files (`*.pt`), big videos, the `sample_videos/` folder
- Anything you did not look at. Run `git status` before every commit.

## Keys
C creates the Supabase project and Vercel site. If you need a key, C sends it privately (not in the repo, not in a public chat). Until then, everything works on mock data.

## Honesty rules (these are judged)
- Synthetic or mock data is always labelled as such. Never call it real.
- Don't say the AI is better than we measured. Our numbers are in `ml/README.md` and `docs/PROGRESS.md`.

## Rough clock (H0 = now; C: write the real deadline here: __________)
| Hours from now | What |
|---|---|
| 0-2 | C runs `scripts/setup-supabase-vercel.sh`; A and B set up their laptops and start |
| 2-14 | A: tiling experiment (3 h cap). B: QA, species lists, drafts |
| 14-18 | Integration: everything merged, deployed site checked on a phone |
| **18** | **FREEZE: only bug fixes after this** |
| 18-24 | Demo rehearsal (3 times), Devpost submitted early, not at the last minute |

## Stuck for more than 20 minutes?
Ask C. Say what you ran, what you expected, and the exact error text.
