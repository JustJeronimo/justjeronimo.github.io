# drawdown backend (Supabase)

This backend adds Google sign-in, per-person sync and AI label reading to the GitHub Pages version. It follows the Bodega pattern (kvendrik.com/bodega): a static page, Supabase Auth, Postgres with RLS, and one Edge Function. There is no server of our own.

## Pieces

- `schema.sql` sets up the database:
  - `allowed_emails` with a sign-up guard (`Not on the list.`)
  - `docs` (user_id, id, kind, data jsonb) with RLS and a cap of 3000 rows per person
  - the AI quota: 30 requests per person and 300 site-wide per UTC day; failed calls still count
- `functions/ask/index.ts` holds `ANTHROPIC_API_KEY` and calls Claude, with an optional image. Set `verify_jwt` on.
- The app side lives in `coffee/index.html` under `account: Supabase sign-in, sync and AI`. It's a no-library client: PKCE sign-in, PostgREST and the function. `SUPA = { url, key }` turns it on. With an empty value, the app runs on this device only, the same as before.

## Setup

1. Create the Supabase project (free tier, region eu-central). Run `schema.sql` with the owner's email seeded.
2. Deploy `ask` and set the `ANTHROPIC_API_KEY` secret. Cap spend in the Anthropic console.
3. In Google Cloud, create an OAuth client of type Web. Its redirect URI is `https://<project>.supabase.co/auth/v1/callback`. Paste the client ID and secret into Supabase under Auth → Providers → Google.
4. In Supabase, set Auth → URL configuration: Site URL `https://justjeronimo.github.io/coffee/`, and the same URL as a Redirect URL.
5. Fill in `SUPA` in `coffee/index.html` with the project URL and the publishable key, bump `APP_VERSION`, and ship.
6. Test the first sign-in. Then add friends with `insert into public.allowed_emails (email) values ('friend@…');`.

## Accepted risks at this size

- Sessions sit in localStorage on the shared github.io origin.
- Google Fonts sees visitor IPs.
- The owner can read all data in the dashboard.
- Free projects pause after a week without use.
