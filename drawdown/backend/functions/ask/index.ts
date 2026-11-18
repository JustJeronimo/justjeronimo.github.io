// drawdown `ask` — Supabase Edge Function. Holds the Anthropic key and asks Claude for the signed-in user.
// Deploy with verify_jwt on. Secrets: ANTHROPIC_API_KEY (required), ANTHROPIC_MODELS (optional, comma list).
// Order: CORS → POST only from allowed origins → key present → user token → allow-list → validate → quota → Claude (failed calls still count; a browser-callable refund would let anyone reset their quota).
import { createClient } from 'npm:@supabase/supabase-js@2.49.4';

const ORIGINS = ['https://justjeronimo.github.io'];
const MODELS = (Deno.env.get('ANTHROPIC_MODELS') || 'claude-haiku-5-5,claude-sonnet-5-5').split(',').map(s => s.trim()).filter(Boolean);
const MAX_PROMPT = 8000, MAX_IMAGE = 2_000_000; // characters of base64

function cors(origin: string) {
  return {
    'Access-Control-Allow-Origin': ORIGINS.includes(origin) ? origin : ORIGINS[0],
    'Access-Control-Allow-Headers': 'authorization, apikey, content-type, x-client-info',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Vary': 'Origin',
  };
}

Deno.serve(async (req) => {
  const origin = req.headers.get('origin') || '';
  const out = (status: number, body: Record<string, unknown>) =>
    new Response(JSON.stringify(body), { status, headers: { ...cors(origin), 'Content-Type': 'application/json' } });

  if (req.method === 'OPTIONS') return new Response(null, { headers: cors(origin) });
  if (req.method !== 'POST' || !ORIGINS.includes(origin)) return out(403, { error: 'forbidden' });

  const key = Deno.env.get('ANTHROPIC_API_KEY');
  if (!key) return out(503, { error: 'not_configured' });

  const auth = req.headers.get('Authorization') || '';
  const sb = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_ANON_KEY')!, { global: { headers: { Authorization: auth } } });
  const { data: { user } } = await sb.auth.getUser();
  if (!user) return out(401, { error: 'signed_out' });
  const { data: allowed } = await sb.rpc('am_i_allowed');
  if (allowed !== true) return out(403, { error: 'not_on_list' });

  let body: { prompt?: unknown; images?: unknown };
  try { body = await req.json(); } catch { return out(400, { error: 'bad_json' }); }
  const prompt = typeof body.prompt === 'string' ? body.prompt.trim() : '';
  const images = Array.isArray(body.images) ? body.images : [];
  if (!prompt || prompt.length > MAX_PROMPT) return out(400, { error: 'bad_prompt' });
  if (images.length > 1 || images.some(i => typeof i !== 'string' || i.length > MAX_IMAGE || !/^[A-Za-z0-9+/=]+$/.test(i))) return out(400, { error: 'bad_image' });

  const { data: slot } = await sb.rpc('ai_take_quota');
  if (slot !== true) return out(429, { error: 'quota' });

  const content = [
    ...images.map(data => ({ type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data } })),
    { type: 'text', text: prompt },
  ];
  for (const model of MODELS) {
    try {
      const r = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        signal: AbortSignal.timeout(30_000),
        headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
        body: JSON.stringify({ model, max_tokens: 900, messages: [{ role: 'user', content }] }),
      });
      if (r.status === 404 || r.status === 400) continue; // model name not available: try the next
      if (!r.ok) throw new Error('upstream ' + r.status);
      const j = await r.json();
      const text = (j.content || []).filter((c: { type: string }) => c.type === 'text').map((c: { text: string }) => c.text).join('');
      return out(200, { text, model });
    } catch (_) { /* try the next model */ }
  }
  return out(502, { error: 'upstream' });
});
