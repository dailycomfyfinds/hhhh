# DCF Launch HQ operations

## Approval invariant

Every social `content_versions` row has a version number. An approval is valid only when `approval_status = APPROVED` and `approval_version = content_versions.version_no`. The `publish-approved` Edge Function checks this with the service-role client immediately before claiming a job. It also checks QA, channel connection, existing provider IDs, and an atomic `READY` claim. The client dashboard is not a security boundary.

## Buffer

Buffer is integrated through its GraphQL endpoint (`BUFFER_API_URL`, default `https://api.buffer.com`) with a server-side bearer token. Configure one `platform_channels` row per market/channel and set `connection_status = CONNECTED` only after the real Buffer channel ID is verified. A disconnected channel is blocked; it is never represented as published.

Set Edge Function secrets:

```bash
supabase secrets set SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... BUFFER_API_TOKEN=... PUBLISH_FUNCTION_SECRET=...
```

The exact Buffer channel/account permissions and media capabilities depend on the connected Buffer account. The adapter sends text and the scheduled time; media must be represented in the content version and should only be scheduled when the connected channel capability supports it.

## Scheduling

A trusted scheduler selects due `READY` jobs and invokes the function with `x-publish-secret`. It should pass one job ID per request, record the HTTP response, and use the database status as truth. Do not invoke the function from browser code. A Supabase `pg_cron` + `pg_net` setup can call the function after the project URL and function secret are configured; those deployment-specific values are intentionally not committed.

## Markets and affiliate routing

Markets and destinations are rows, not code branches. Add a market, product-market availability, and an active destination with a validated HTTPS URL. Destination selection must be exact-market first, then `INTL`, ordered by priority. Credentials never belong in destination URLs or frontend code.

## QA and lifecycle

Content is generated into `GENERATED`, receives a version and QA result, then moves to `READY_FOR_APPROVAL`. An operator may edit, hold, reject, or approve. Only approval creates a `READY` publishing job. Audit events should accompany transitions. `BLOCKED`, `FAILED`, `HELD`, and `REJECTED` are terminal/exception states until an explicit operator action changes them.

## Deployment checklist

1. Apply `supabase/migrations/202609230001_dcf_launch_hq.sql`.
2. Create authenticated operator accounts and verify RLS policies for the project’s auth model.
3. Configure Buffer channels and insert only their external IDs/statuses.
4. Deploy the Edge Function and secrets.
5. Configure the trusted scheduler/cron; verify it cannot call without the secret.
6. Run `pytest -q` and a staging approval test: an unapproved job must return `409 BLOCKED`, while an approved job with a connected test channel must reach the real Buffer API.
7. Replace `dcf_website/ads.txt` with the exact Google-provided publisher line only after AdSense supplies it. AdSense approval is external and is not claimed here.

## Security notes

The existing Flask bundle is preserved as the public-site compatibility layer. Before production deployment, replace its legacy hard-coded secret/default bootstrap credentials with environment-managed credentials and migrate public/admin data to Supabase. The new HQ schema and Edge Function do not expose service-role or Buffer secrets. Review RLS policies with the project’s operator roles before launch; service-role access bypasses RLS by design and is restricted to the Edge Function.
