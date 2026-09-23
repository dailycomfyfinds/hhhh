# DCF Launch HQ architecture

`dcf_website/` remains the consumer-facing Daily Comfy Finds site and preserves its logo, palette, legal/methodology pages, product routes, and retailer directory. The operational control plane is Supabase: it owns normalized records, state transitions, approvals, schedules, jobs, metrics, feedback, and audit history.

The domain services in `dcf_hq/` are provider-independent deterministic helpers. Product evaluation consumes criteria/weights from Supabase. Content generation is expected to call a server-side AI provider and persist the resulting master idea/version; it is never a source of truth. Platform formatting produces distinct payloads and validates configured limits. QA blocks unsafe/incomplete content before approval.

Publishing is an Edge Function, not a browser operation. It reads a job, verifies current QA and approval version, checks a connected Buffer channel, atomically claims the job, and calls Buffer’s GraphQL API. Provider IDs and errors return to Supabase. Retries are finite and each attempt is auditable. The idempotency key and provider ID prevent duplicate submission.

The initial relational model supports US, EG, SA, AE, and INTL plus future rows. Platforms include Facebook, Instagram, TikTok, YouTube, Pinterest, Threads, and X. Content pillars, mix, evaluation criteria, capabilities, cooldowns, and approval mode are data-driven in `system_config` and related tables.
