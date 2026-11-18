-- drawdown backend (Supabase). Sign-in with Google, per-person sync, AI through the `ask` function.
-- Run once in the SQL editor (or apply as a migration). Safe to re-run.
-- Access is enforced three times: the sign-up guard below, RLS + the `ask` function on every request, and the page.

create schema if not exists private;

-- who may sign in ---------------------------------------------------------
create table if not exists public.allowed_emails (
  email text primary key check (email = lower(email)),
  note text,
  added_at timestamptz not null default now()
);
alter table public.allowed_emails enable row level security;   -- no policies: not readable from the browser

create or replace function private.is_allowed() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.allowed_emails a where a.email = lower(coalesce(auth.jwt() ->> 'email', '')));
$$;
grant usage on schema private to authenticated;
grant execute on function private.is_allowed() to authenticated;

-- the page and the function ask this to show "Not on the list."
create or replace function public.am_i_allowed() returns boolean
language sql stable security definer set search_path = '' as $$ select private.is_allowed(); $$;
revoke execute on function public.am_i_allowed() from anon, public;
grant execute on function public.am_i_allowed() to authenticated;

-- no account for addresses that aren't on the list
create or replace function private.guard_signup() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if not exists (select 1 from public.allowed_emails a where a.email = lower(coalesce(new.email, ''))) then
    raise exception 'Not on the list.';
  end if;
  return new;
end $$;
drop trigger if exists guard_signup on auth.users;
create trigger guard_signup before insert on auth.users for each row execute function private.guard_signup();

-- the app's documents: setups, beans, brews, prefs ------------------------
create table if not exists public.docs (
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  id text not null check (length(id) between 1 and 80),
  kind text not null check (kind in ('setup', 'bean', 'brew', 'prefs')),
  data jsonb not null check (pg_column_size(data) < 400000),
  updated_at timestamptz not null default now(),
  primary key (user_id, id)
);
alter table public.docs enable row level security;

drop policy if exists docs_select on public.docs;
drop policy if exists docs_insert on public.docs;
drop policy if exists docs_update on public.docs;
drop policy if exists docs_delete on public.docs;
create policy docs_select on public.docs for select to authenticated using (user_id = auth.uid() and private.is_allowed());
create policy docs_insert on public.docs for insert to authenticated with check (user_id = auth.uid() and private.is_allowed());
create policy docs_update on public.docs for update to authenticated using (user_id = auth.uid() and private.is_allowed()) with check (user_id = auth.uid());
create policy docs_delete on public.docs for delete to authenticated using (user_id = auth.uid() and private.is_allowed());

-- at most 3000 documents per person (a few years of daily brews)
create or replace function private.docs_enforce_cap() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  perform pg_advisory_xact_lock(hashtext(new.user_id::text));
  if (select count(*) from public.docs d where d.user_id = new.user_id) >= 3000 then
    raise exception 'Row limit reached.';
  end if;
  return new;
end $$;
drop trigger if exists docs_cap on public.docs;
create trigger docs_cap before insert on public.docs for each row execute function private.docs_enforce_cap();

create or replace function private.touch() returns trigger language plpgsql as $$ begin new.updated_at = now(); return new; end $$;
drop trigger if exists docs_touch on public.docs;
create trigger docs_touch before update on public.docs for each row execute function private.touch();

-- AI quota: 30 requests per person per UTC day, 300 for the whole site -----
create table if not exists public.ai_usage (
  user_id uuid not null references auth.users (id) on delete cascade,
  day date not null default (now() at time zone 'utc')::date,
  n int not null default 0,
  primary key (user_id, day)
);
alter table public.ai_usage enable row level security;   -- no policies: only the functions below touch it

create or replace function public.ai_take_quota() returns boolean
language plpgsql security definer set search_path = '' as $$
declare today date := (now() at time zone 'utc')::date; mine int; site int;
begin
  if auth.uid() is null or not private.is_allowed() then return false; end if;
  perform pg_advisory_xact_lock(hashtext('ai_usage:' || today::text));
  select coalesce(sum(n), 0) into site from public.ai_usage where day = today;
  select coalesce(n, 0) into mine from public.ai_usage where user_id = auth.uid() and day = today;
  if coalesce(mine, 0) >= 30 or site >= 300 then return false; end if;
  insert into public.ai_usage (user_id, day, n) values (auth.uid(), today, 1)
    on conflict (user_id, day) do update set n = public.ai_usage.n + 1;
  return true;
end $$;

-- no refund function: one the browser can call would let anyone reset their own quota. Failed calls count.
revoke execute on function public.ai_take_quota() from anon, public;
grant execute on function public.ai_take_quota() to authenticated;

-- seed: the owner (replace before running), then friends the same way
-- insert into public.allowed_emails (email, note) values ('you@example.com', 'owner') on conflict do nothing;
