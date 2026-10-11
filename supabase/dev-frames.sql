-- Dev mode: the full camera frame (clean and with the detection box drawn in), plus the detector's numbers.
-- Run after schema.sql. Safe to rerun. Old rows keep nulls and the site falls back to the crop.
alter table sightings add column if not exists frame_url     text;
alter table sightings add column if not exists annotated_url text;
alter table sightings add column if not exists bbox          integer[];
alter table sightings add column if not exists yolo_score    real;

-- The 7 Katmai rows published on 2026-10-11 before the bear-season cutoff moved: some were highlight footage.
update sightings set source_kind = 'replay'
where source_kind = 'live'
  and seen_at < '2026-10-12'
  and camera_id in (select id from cameras where park = 'katmai');
