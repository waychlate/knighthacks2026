-- Animal Logger schema. Run in the Supabase SQL editor (or `supabase db push`).

create table if not exists cameras (
  id          uuid primary key default gen_random_uuid(),
  name        text not null unique,
  location    text,
  lat         double precision,
  lng         double precision,
  status      text not null default 'active' check (status in ('active', 'offline'))
);

create table if not exists species (
  id               uuid primary key default gen_random_uuid(),
  common_name      text not null,
  scientific_name  text not null unique,
  image_url        text
);

-- Append-only log of sightings.
create table if not exists sightings (
  id           uuid primary key default gen_random_uuid(),
  species_id   uuid not null references species(id),
  camera_id    uuid not null references cameras(id),
  seen_at      timestamptz not null default now(),   -- stored in UTC
  confidence   real not null check (confidence >= 0 and confidence <= 1),
  snapshot_url text
);

create index if not exists sightings_seen_at_idx on sightings (seen_at desc);
create index if not exists sightings_species_idx on sightings (species_id, seen_at);

-- Row-level security: anyone can read; only the service-role key (worker) can write.
alter table cameras   enable row level security;
alter table species   enable row level security;
alter table sightings enable row level security;

create policy "public read cameras"   on cameras   for select using (true);
create policy "public read species"   on species   for select using (true);
create policy "public read sightings" on sightings for select using (true);

-- Live feed: let the frontend subscribe to new sightings.
alter publication supabase_realtime add table sightings;

-- Snapshots bucket (public read). Create in the dashboard: Storage -> New bucket
-- named "snapshots", public. Or:
insert into storage.buckets (id, name, public)
values ('snapshots', 'snapshots', true)
on conflict (id) do nothing;

-- Predictions written by the ML job (/ml). The frontend shows upcoming ones.
create table if not exists predictions (
  id             uuid primary key default gen_random_uuid(),
  species_id     uuid not null references species(id),
  camera_id      uuid references cameras(id),          -- null = anywhere in the park
  predicted_for  timestamptz not null,                 -- when we expect to see it (UTC)
  probability    real not null check (probability >= 0 and probability <= 1),
  created_at     timestamptz not null default now()
);

create index if not exists predictions_for_idx on predictions (predicted_for);

alter table predictions enable row level security;
create policy "public read predictions" on predictions for select using (true);
