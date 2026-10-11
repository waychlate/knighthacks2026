-- Katmai (Brooks Falls) cameras. Run in the Supabase SQL editor after schema.sql. Safe to re-run.
-- These are explore.org live video streams shown in the app; sightings appear only if the worker is run on them.
insert into cameras (name, location, park, status) values
  ('Brooks Falls Bearcam',  'Brooks Falls, Katmai National Park', 'katmai', 'active'),
  ('Brooks Falls Low Cam',  'Brooks Falls (low camera)',          'katmai', 'active'),
  ('River Watch Cam',       'Brooks River',                       'katmai', 'active')
on conflict (name) do nothing;
