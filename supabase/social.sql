-- Social tables: one anonymous live chat room per park, plus comments on sightings.
-- Run in the Supabase SQL editor after schema.sql (it does not depend on it). Safe to re-run.
-- Anonymous by design: anyone can read and post, nobody can edit or delete. To moderate, set
-- is_hidden = true on a row in the dashboard; hidden rows disappear from the app.
-- Chat and comments never go into `sightings`: that table is camera detections only.

create table if not exists chat_messages (
  id            uuid primary key default gen_random_uuid(),
  park          text not null,                        -- park slug, e.g. 'yellowstone'
  display_name  text not null check (char_length(btrim(display_name)) between 1 and 40),
  body          text not null check (char_length(btrim(body)) between 1 and 280),
  created_at    timestamptz not null default now(),
  is_hidden     boolean not null default false
);
create index if not exists chat_messages_park_idx on chat_messages (park, created_at desc);

create table if not exists comments (
  id            uuid primary key default gen_random_uuid(),
  sighting_id   uuid not null,                        -- plain uuid, no foreign key, so this file stands alone
  display_name  text not null check (char_length(btrim(display_name)) between 1 and 40),
  body          text not null check (char_length(btrim(body)) between 1 and 280),
  created_at    timestamptz not null default now(),
  is_hidden     boolean not null default false
);
create index if not exists comments_sighting_idx on comments (sighting_id, created_at);

-- Stamp the time on the server (clients cannot backdate) and allow one post per name per 2 seconds.
create or replace function social_before_insert() returns trigger language plpgsql as $$
begin
  new.created_at := now();
  new.is_hidden := false;
  new.display_name := btrim(new.display_name);
  new.body := btrim(new.body);
  if tg_table_name = 'chat_messages' then
    if exists (select 1 from chat_messages
               where lower(display_name) = lower(new.display_name) and created_at > now() - interval '2 seconds') then
      raise exception 'slow down: one message per 2 seconds';
    end if;
  else
    if exists (select 1 from comments
               where lower(display_name) = lower(new.display_name) and created_at > now() - interval '2 seconds') then
      raise exception 'slow down: one comment per 2 seconds';
    end if;
  end if;
  return new;
end $$;

drop trigger if exists chat_messages_before_insert on chat_messages;
create trigger chat_messages_before_insert before insert on chat_messages
  for each row execute function social_before_insert();
drop trigger if exists comments_before_insert on comments;
create trigger comments_before_insert before insert on comments
  for each row execute function social_before_insert();

-- Row-level security: public read of visible rows, public insert, no update/delete policies (so denied).
alter table chat_messages enable row level security;
alter table comments      enable row level security;

drop policy if exists "public read chat"   on chat_messages;
drop policy if exists "public post chat"   on chat_messages;
drop policy if exists "public read comments" on comments;
drop policy if exists "public post comments" on comments;
create policy "public read chat"     on chat_messages for select using (not is_hidden);
create policy "public post chat"     on chat_messages for insert with check (true);
create policy "public read comments" on comments      for select using (not is_hidden);
create policy "public post comments" on comments      for insert with check (true);

-- Live chat: let the frontend subscribe to new messages and comments.
do $$ begin
  alter publication supabase_realtime add table chat_messages;
exception when duplicate_object then null;
end $$;
do $$ begin
  alter publication supabase_realtime add table comments;
exception when duplicate_object then null;
end $$;
