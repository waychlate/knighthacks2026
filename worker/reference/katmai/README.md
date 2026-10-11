# Katmai species reference

`npspecies_full.csv` is the user-provided NPSpecies export for park code `KATM`,
downloaded on 2026-10-10. It is the complete inventory reference: 1,050 rows.

`approved_present_summary.json` filters the export to `Record Status=Approved`
and `Occurrence=Present`. It contains category counts and the 35 mammals in that
subset. There are 762 approved/present species across all categories.

This inventory must not be passed directly to BioCLIP. Presence in Katmai does
not mean an animal is likely to appear at Brooks Falls Low, and a very long
candidate list makes zero-shot classification less reliable. The camera-specific
working shortlist remains `worker/species_katmai.json`.

Regenerate these files and the prediction-format reference from the repository
root with:

```powershell
.\worker\.venv\Scripts\python.exe scripts\import-katmai-reference.py `
  --species-csv "C:\Users\andre\Downloads\NPSpecies_FullList_KATM_20261010_130954.csv" `
  --predictions-example "C:\Users\andre\Downloads\message.txt"
```
