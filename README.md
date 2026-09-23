# DCF Launch HQ

Daily Comfy Finds is a consumer product-discovery brand. `dcf_website/` preserves the existing Flask public site; `supabase/` is the operational system of record for products, content, approval, publishing, and analytics.

## Current implementation

- Supabase migration with markets, categories, products, configurable evaluation criteria, affiliate destinations, master/platform content, QA, approvals, audit history, publishing jobs, analytics, feedback, configuration, and automation logs.
- Server-side human approval gate: the publishing Edge Function rejects every job without an approved content version and matching approval version.
- Real Buffer GraphQL adapter in `supabase/functions/publish-approved`; it makes no request when Buffer credentials/channel configuration is absent and records failures instead of claiming success.
- Pure Python domain services in `dcf_hq/` for scoring, routing, platform formatting, QA, and idempotency; these are deterministic and provider-independent.
- Tests for the approval gate, scoring, routing, formatting, QA, duplicate prevention, retries, and lifecycle transitions.

## Local verification

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r dcf_website/requirements.txt
pip install pytest
pytest -q
python -m py_compile dcf_website/app.py dcf_hq/*.py
```

Apply the database with the Supabase CLI:

```bash
supabase db push
supabase functions deploy publish-approved --no-verify-jwt
```

The function is intended to be invoked by a protected cron/pg_net request using `PUBLISH_FUNCTION_SECRET`; it uses the Supabase service-role key only inside the Edge Function. Set secrets with `supabase secrets set`, never in Git.

## Required production configuration

Copy `.env.example` for local development. Production requires a Supabase project, a Buffer API token, configured Buffer channel IDs, and a connected account for each channel that should publish. No channel is considered connected merely because a platform is listed in configuration.

See `docs/architecture.md` and `docs/operations.md` for migration, approval, Buffer, scheduling, security, and launch procedures.
