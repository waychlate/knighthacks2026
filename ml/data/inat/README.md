# iNaturalist observations (REAL, public, not from our cameras)

Downloaded 2026-10-10 with `python ml/inat.py` from the iNaturalist API: research-grade, species-level mammals and birds within 60 km of each park centre (centres in `ml/inat.py`, matching `web/src/lib/parks.js`). One CSV per park, about 2k to 8k rows each (newest observations first, so the data skews recent).

Columns: `park, observation_id, scientific_name, common_name, iconic_taxon, observed_at` (ISO with the observer's UTC offset), `local_hour` (observer's local clock hour, 0 to 23, use this for hour-of-day), `lat, lng, positional_accuracy` (metres, may be empty).

Cleaning already applied: rows before 2005 and rows at exactly local midnight were dropped (placeholder times).

## For the prediction model
- Park-level only. There is no camera information, so predict "species X in park Y around hour H", not per camera.
- Bias: observers are tourists, so daytime, roads and trails dominate. Very few observations at night. Counts are skewed to common, easy-to-photograph species. Hourly counts are a "when people see it" signal, not true activity. Normalise within each species (share of its observations per hour), do not compare raw counts between species.
- Seasonality: the newest observations are mostly from the last few years and from summer and autumn. Month is available in `observed_at` if you want to use it.
- Keep the UI label honest: "based on public iNaturalist observations". Never write these rows into `sightings`, and never mix them with the synthetic data without labelling.
- Credit: iNaturalist observers (CC-licensed photos are not included, only metadata).
