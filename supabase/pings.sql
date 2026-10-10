-- User pings: "I saw something here". Run in the Supabase SQL editor after social.sql. Safe to re-run.
-- Anonymous: anyone can read and post, nobody can edit or delete. To moderate, set is_hidden = true.
-- USER-REPORTED, not camera detections: pings never go into `sightings` and /ml never reads them.
-- Privacy: coordinates are rounded to about 500 m here, so even a modified client cannot store an exact spot.

create table if not exists pings (
  id            uuid primary key default gen_random_uuid(),
  lat           double precision not null check (lat between -90 and 90),
  lng           double precision not null check (lng between -180 and 180),
  species_name  text check (species_name is null or char_length(species_name) <= 60),
  note          text check (note is null or char_length(note) <= 140),
  created_at    timestamptz not null default now(),
  is_hidden     boolean not null default false
);
create index if not exists pings_created_idx on pings (created_at desc);

create or replace function pings_before_insert() returns trigger language plpgsql as $$
begin
  new.created_at := now();
  new.is_hidden := false;
  new.lat := round(new.lat / 0.005) * 0.005;
  new.lng := round(new.lng / 0.005) * 0.005;
  new.species_name := nullif(btrim(new.species_name), '');
  new.note := nullif(btrim(new.note), '');
  return new;
end $$;

drop trigger if exists pings_before_insert on pings;
create trigger pings_before_insert before insert on pings
  for each row execute function pings_before_insert();

alter table pings enable row level security;
drop policy if exists "public read pings" on pings;
drop policy if exists "public post pings" on pings;
create policy "public read pings" on pings for select using (not is_hidden);
create policy "public post pings" on pings for insert with check (true);

do $$ begin
  alter publication supabase_realtime add table pings;
exception when duplicate_object then null;
end $$;
