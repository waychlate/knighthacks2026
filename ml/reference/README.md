# Local ML format references

`predictions.example.json` is the user-provided example of the local prediction
format. It is explicitly synthetic and retained for schema/reference work while
Supabase is unavailable. It is historical example data, not current model output.

Current locally generated predictions continue to go to
`ml/out/predictions.json`, which is gitignored and can be regenerated with:

```powershell
cd ml
.\.venv\Scripts\python.exe predict.py --park katmai --local-only --no-sample
```
