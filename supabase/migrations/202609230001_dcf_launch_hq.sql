create extension if not exists pgcrypto;

create table if not exists public.markets (
  code text primary key check (code = upper(code)), name text not null, currency text, active boolean not null default true,
  created_at timestamptz not null default now()
);
create table if not exists public.categories (id uuid primary key default gen_random_uuid(), name text unique not null, active boolean not null default true);
create table if not exists public.products (
  id uuid primary key default gen_random_uuid(), title text not null, slug text unique not null, description text, category_id uuid references public.categories(id), subcategory text, brand text,
  source text, source_product_id text, original_url text, image_urls jsonb not null default '[]', video_urls jsonb not null default '[]', price numeric, currency text, availability text,
  product_score numeric check (product_score between 0 and 1), dcf_score numeric check (dcf_score between 0 and 1), status text not null default 'DISCOVERED' check (status in ('DISCOVERED','EVALUATED','REJECTED','ACTIVE','ARCHIVED')),
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), unique(source, source_product_id)
);
create table if not exists public.product_markets (product_id uuid references public.products(id) on delete cascade, market_code text references public.markets(code), available boolean not null default true, price numeric, currency text, availability text, primary key(product_id, market_code));
create table if not exists public.evaluation_criteria (key text primary key, label text not null, weight numeric not null check (weight >= 0), active boolean not null default true);
create table if not exists public.product_evaluations (
  id uuid primary key default gen_random_uuid(), product_id uuid not null references public.products(id) on delete cascade, criterion_scores jsonb not null, score numeric not null check (score between 0 and 1), decision text not null check (decision in ('PASS','REVIEW','REJECT')), evaluated_by text not null, created_at timestamptz not null default now()
);
create table if not exists public.affiliate_destinations (
  id uuid primary key default gen_random_uuid(), product_id uuid not null references public.products(id) on delete cascade, market_code text not null references public.markets(code), network text not null, url text not null, priority int not null default 0, active boolean not null default true, last_checked_at timestamptz, last_check_status text
);
create table if not exists public.content_pillars (id uuid primary key default gen_random_uuid(), name text unique not null, mix_percent numeric not null default 0 check (mix_percent between 0 and 100), active boolean not null default true);
create table if not exists public.platforms (code text primary key, display_name text not null, active boolean not null default true, capabilities jsonb not null default '{}');
create table if not exists public.platform_channels (id uuid primary key default gen_random_uuid(), platform_code text references public.platforms(code), market_code text references public.markets(code), provider text not null default 'BUFFER', external_channel_id text, connection_status text not null default 'DISCONNECTED' check (connection_status in ('CONNECTED','DISCONNECTED','UNSUPPORTED','BLOCKED')), metadata jsonb not null default '{}', unique(platform_code, market_code));
create table if not exists public.content (
  id uuid primary key default gen_random_uuid(), product_id uuid references public.products(id), pillar_id uuid references public.content_pillars(id), content_type text not null, status text not null default 'GENERATED', market_code text references public.markets(code), master_idea jsonb not null default '{}', created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.content_versions (
  id uuid primary key default gen_random_uuid(), content_id uuid not null references public.content(id) on delete cascade, version_no int not null, platform_code text references public.platforms(code), hook text, title text, caption text, body text, cta text, hashtags jsonb not null default '[]', keywords jsonb not null default '[]', media_reference jsonb not null default '{}', affiliate_destination_id uuid references public.affiliate_destinations(id), disclosure_required boolean not null default true, disclosure text, fingerprint text not null, qa_status text not null default 'PENDING' check (qa_status in ('PENDING','PASS','WARNING','BLOCKED')), created_at timestamptz not null default now(), unique(content_id, version_no, platform_code)
);
create unique index if not exists content_versions_fingerprint_idx on public.content_versions(fingerprint);
create table if not exists public.qa_results (id uuid primary key default gen_random_uuid(), content_version_id uuid not null references public.content_versions(id) on delete cascade, status text not null check(status in ('PASS','WARNING','BLOCKED')), checks jsonb not null, created_at timestamptz not null default now());
create table if not exists public.approvals (
  id uuid primary key default gen_random_uuid(), content_version_id uuid not null references public.content_versions(id) on delete cascade, approval_status text not null default 'PENDING' check(approval_status in ('PENDING','APPROVED','REJECTED','HELD')), approved_by uuid references auth.users(id), approved_at timestamptz, approval_version int not null, notes text, unique(content_version_id, approval_version)
);
create table if not exists public.publishing_jobs (
  id uuid primary key default gen_random_uuid(), content_version_id uuid not null references public.content_versions(id), channel_id uuid references public.platform_channels(id), platform_code text references public.platforms(code), market_code text references public.markets(code), scheduled_at timestamptz, payload jsonb not null default '{}', provider text not null default 'BUFFER', provider_job_id text, external_post_id text, status text not null default 'READY' check(status in ('READY','SUBMITTED','PUBLISHED','FAILED','BLOCKED','CANCELLED')), retry_count int not null default 0, last_error text, idempotency_key text not null unique, submitted_at timestamptz, published_at timestamptz, created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.analytics_metrics (id uuid primary key default gen_random_uuid(), content_version_id uuid references public.content_versions(id), product_id uuid references public.products(id), platform_code text, market_code text, metric_name text not null, metric_value numeric, source_type text not null check(source_type in ('PLATFORM','PROVIDER','AFFILIATE_NETWORK','CALCULATED','UNAVAILABLE')), observed_at timestamptz not null default now(), metadata jsonb not null default '{}');
create table if not exists public.feedback_insights (id uuid primary key default gen_random_uuid(), scope jsonb not null, insight text not null, confidence numeric, threshold numeric, status text not null default 'PROPOSED', created_at timestamptz not null default now());
create table if not exists public.system_config (key text primary key, value jsonb not null, updated_at timestamptz not null default now());
create table if not exists public.automation_jobs (id uuid primary key default gen_random_uuid(), job_type text not null, status text not null default 'RUNNING', idempotency_key text unique not null, attempts int not null default 0, last_error text, started_at timestamptz not null default now(), finished_at timestamptz);
create table if not exists public.audit_log (id uuid primary key default gen_random_uuid(), entity_type text not null, entity_id uuid, event text not null, actor text not null, previous_state text, new_state text, metadata jsonb not null default '{}', created_at timestamptz not null default now());

insert into public.markets(code,name,currency) values ('US','United States','USD'),('EG','Egypt','EGP'),('SA','Saudi Arabia','SAR'),('AE','United Arab Emirates','AED'),('INTL','International',null) on conflict do nothing;
insert into public.platforms(code,display_name,capabilities) values ('FACEBOOK','Facebook','{"image":true,"video":true}'),('INSTAGRAM','Instagram','{"image":true,"video":true}'),('TIKTOK','TikTok','{"video":true}'),('YOUTUBE','YouTube','{"video":true}'),('PINTEREST','Pinterest','{"image":true}'),('THREADS','Threads','{"text":true}'),('X','X / Twitter','{"text":true,"thread":true}') on conflict do nothing;
insert into public.content_pillars(name,mix_percent) values ('Smart Finds',25),('Problem → Solution',15),('Useful Tips / Educational',20),('Product Comparisons',15),('Lifestyle Finds',10),('Giftable / Seasonal',10),('Promotional',5) on conflict do nothing;
insert into public.evaluation_criteria(key,label,weight) values ('usefulness','Usefulness',.12),('practicality','Practicality',.10),('value','Value',.10),('quality_signals','Quality signals',.08),('uniqueness','Uniqueness',.08),('problem_solving','Problem solving',.12),('visual_potential','Visual potential',.08),('content_potential','Content potential',.10),('audience_relevance','Audience relevance',.08),('purchase_intent','Purchase intent',.05),('availability','Availability',.05),('affiliate_viability','Affiliate viability',.04) on conflict do nothing;
insert into public.system_config(key,value) values ('approval_mode','"MANUAL"'),('publishing_rules','{"max_retries":3,"product_cooldown_hours":48,"duplicate_cooldown_hours":168}') on conflict do nothing;

create index if not exists publishing_jobs_due_idx on public.publishing_jobs(status, scheduled_at);
create index if not exists content_status_idx on public.content(status);
create index if not exists audit_entity_idx on public.audit_log(entity_type, entity_id, created_at desc);

alter table public.markets enable row level security; alter table public.categories enable row level security; alter table public.products enable row level security; alter table public.product_markets enable row level security; alter table public.content enable row level security; alter table public.content_versions enable row level security; alter table public.approvals enable row level security; alter table public.publishing_jobs enable row level security; alter table public.analytics_metrics enable row level security;
create policy "public can read active products" on public.products for select using (status = 'ACTIVE');
create policy "authenticated operators manage HQ" on public.products for all to authenticated using (true) with check (true);
create policy "authenticated operators manage content" on public.content for all to authenticated using (true) with check (true);
create policy "authenticated operators manage versions" on public.content_versions for all to authenticated using (true) with check (true);
create policy "authenticated operators manage approvals" on public.approvals for all to authenticated using (true) with check (true);
create policy "authenticated operators read jobs" on public.publishing_jobs for select to authenticated using (true);
create policy "authenticated operators read analytics" on public.analytics_metrics for select to authenticated using (true);

create or replace function public.touch_updated_at() returns trigger language plpgsql as $$ begin new.updated_at = now(); return new; end $$;
drop trigger if exists products_touch on public.products; create trigger products_touch before update on public.products for each row execute function public.touch_updated_at();
drop trigger if exists content_touch on public.content; create trigger content_touch before update on public.content for each row execute function public.touch_updated_at();
drop trigger if exists jobs_touch on public.publishing_jobs; create trigger jobs_touch before update on public.publishing_jobs for each row execute function public.touch_updated_at();
