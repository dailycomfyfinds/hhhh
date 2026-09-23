import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
const BUFFER_URL = Deno.env.get("BUFFER_API_URL") || "https://api.buffer.com";
const MAX_RETRIES = 3;

async function bufferMutation(text: string, channelId: string, dueAt: string | null) {
  const token = Deno.env.get("BUFFER_API_TOKEN");
  if (!token) throw new Error("Buffer is not configured");
  const query = `mutation CreatePost($input: CreatePostInput!) { createPost(input: $input) { ... on Post { id dueAt sentAt channelId text } ... on Error { message } } }`;
  const input: Record<string, unknown> = { channelId, content: { text } };
  if (dueAt) input.dueAt = dueAt;
  const response = await fetch(BUFFER_URL, { method: "POST", headers: { authorization: `Bearer ${token}`, "content-type": "application/json" }, body: JSON.stringify({ query, variables: { input } }) });
  const body = await response.json();
  if (!response.ok || body.errors?.length) throw new Error(`Buffer request failed: ${JSON.stringify(body.errors || body)}`);
  const result = body.data?.createPost;
  if (!result?.id) throw new Error(result?.message || "Buffer returned no post id");
  return result;
}

Deno.serve(async (request) => {
  try {
    if (request.headers.get("x-publish-secret") !== Deno.env.get("PUBLISH_FUNCTION_SECRET")) return json({ error: "unauthorized" }, 401);
    const { job_id } = await request.json();
    if (!job_id) return json({ error: "job_id is required" }, 400);
    const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
    const { data: job, error } = await supabase.from("publishing_jobs").select("*, content_versions!inner(*), platform_channels!inner(*)").eq("id", job_id).single();
    if (error || !job) return json({ error: "publishing job not found" }, 404);
    if (["SUBMITTED", "PUBLISHED"].includes(job.status) || job.external_post_id) return json({ status: job.status, external_post_id: job.external_post_id, idempotent: true });
    const version = job.content_versions;
    const { data: approval } = await supabase.from("approvals").select("approval_status, approval_version").eq("content_version_id", version.id).order("approval_version", { ascending: false }).limit(1).maybeSingle();
    if (!approval || approval.approval_status !== "APPROVED" || approval.approval_version !== version.version_no) {
      await supabase.from("publishing_jobs").update({ status: "BLOCKED", last_error: "Explicit human approval is required for this content version" }).eq("id", job_id);
      return json({ status: "BLOCKED", reason: "explicit human approval is required" }, 409);
    }
    if (version.qa_status === "BLOCKED") return json({ status: "BLOCKED", reason: "QA blocked content" }, 409);
    const channel = job.platform_channels;
    if (channel.connection_status !== "CONNECTED" || !channel.external_channel_id) {
      await supabase.from("publishing_jobs").update({ status: "BLOCKED", last_error: "Buffer channel is disconnected or missing external channel id" }).eq("id", job_id);
      return json({ status: "BLOCKED", reason: "channel is not connected" }, 409);
    }
    const { data: claimed } = await supabase.from("publishing_jobs").update({ status: "SUBMITTED", retry_count: job.retry_count + 1, submitted_at: new Date().toISOString(), last_error: null }).eq("id", job_id).eq("status", "READY").select().maybeSingle();
    if (!claimed) return json({ status: "SUBMITTED", idempotent: true });
    try {
      const post = await bufferMutation(version.caption || version.body || "", channel.external_channel_id, job.scheduled_at);
      await supabase.from("publishing_jobs").update({ status: "PUBLISHED", external_post_id: post.id, provider_job_id: post.id, published_at: post.sentAt || null }).eq("id", job_id);
      await supabase.from("audit_log").insert({ entity_type: "publishing_job", entity_id: job_id, event: "PUBLISHED", actor: "buffer-edge-function", previous_state: "SUBMITTED", new_state: "PUBLISHED", metadata: { provider: "BUFFER", external_post_id: post.id } });
      return json({ status: "PUBLISHED", external_post_id: post.id });
    } catch (publishError) {
      const message = publishError instanceof Error ? publishError.message : "provider failure";
      const nextStatus = job.retry_count + 1 >= MAX_RETRIES ? "FAILED" : "READY";
      await supabase.from("publishing_jobs").update({ status: nextStatus, last_error: message }).eq("id", job_id);
      await supabase.from("audit_log").insert({ entity_type: "publishing_job", entity_id: job_id, event: "PUBLISH_FAILED", actor: "buffer-edge-function", previous_state: "SUBMITTED", new_state: nextStatus, metadata: { error: message } });
      return json({ status: nextStatus, error: message }, 502);
    }
  } catch (error) { return json({ error: error instanceof Error ? error.message : "unexpected error" }, 500); }
});
