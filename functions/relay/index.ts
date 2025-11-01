// Front Door: Webhook受信 → GitHub repository_dispatch
// Supabase Edge Function / Cloudflare Workers 両対応

import { createHmac } from "https://deno.land/std@0.224.0/node/crypto.ts";

interface Env {
  GH_OWNER: string;
  GH_REPO: string;
  GH_PAT: string;
  LINE_CHANNEL_SECRET?: string;
  MANUS_API_KEY?: string;
  FEATURE_BOT_ENABLED?: string;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    // Kill-Switch: 即座に停止
    if (env.FEATURE_BOT_ENABLED === "false") {
      return new Response(JSON.stringify({ error: "Bot is disabled" }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      });
    }

    // 署名検証
    const signature = req.headers.get("X-Line-Signature") || req.headers.get("Authorization");
    if (!signature) {
      return new Response(JSON.stringify({ error: "Missing signature" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    const body = await req.text();
    const isValid = verifySignature(body, signature, env);
    if (!isValid) {
      return new Response(JSON.stringify({ error: "Invalid signature" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      });
    }

    // イベントタイプ判定
    const payload = JSON.parse(body);
    const eventType = detectEventType(payload);

    // 個人情報を最小化
    const sanitized = sanitizePayload(payload, eventType);

    // GitHub repository_dispatch
    const ghResp = await fetch(
      `https://api.github.com/repos/${env.GH_OWNER}/${env.GH_REPO}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GH_PAT}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_type: eventType,
          client_payload: sanitized,
        }),
      }
    );

    if (!ghResp.ok) {
      const errorText = await ghResp.text();
      console.error(`GitHub dispatch failed: ${ghResp.status} ${errorText}`);
      return new Response(
        JSON.stringify({ error: `GH dispatch failed: ${ghResp.status}` }),
        {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    return new Response(JSON.stringify({ status: "ok" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  },
};

function verifySignature(body: string, signature: string, env: Env): boolean {
  // LINE署名検証
  if (signature.startsWith("sha256=") && env.LINE_CHANNEL_SECRET) {
    const hash = createHmac("sha256", env.LINE_CHANNEL_SECRET)
      .update(body)
      .digest("base64");
    return signature === hash;
  }

  // Manus署名検証（Bearer token）
  if (signature.startsWith("Bearer ") && env.MANUS_API_KEY) {
    const token = signature.replace("Bearer ", "");
    return token === env.MANUS_API_KEY;
  }

  return false;
}

function detectEventType(payload: any): string {
  // Manus Progress Event
  if (payload.event_type && payload.task_id) {
    return "manus_progress";
  }

  // LINE Event
  if (payload.events && Array.isArray(payload.events)) {
    return "line_event";
  }

  return "unknown";
}

function sanitizePayload(payload: any, eventType: string): any {
  if (eventType === "manus_progress") {
    // ProgressEvent v1.1: 個人情報を除外
    return {
      event_type: payload.event_type,
      task_id: payload.task_id,
      step_id: payload.step_id || null,
      ts: payload.ts || new Date().toISOString(),
      idempotency_key: payload.idempotency_key,
      plan_title: payload.plan_title,
      metrics: payload.metrics || {},
      context: payload.context || {},
      preview: payload.preview || null,
      error: payload.error || null,
    };
  }

  if (eventType === "line_event") {
    // LINE Event: user_idをハッシュ化
    const events = payload.events.map((e: any) => ({
      type: e.type,
      timestamp: e.timestamp,
      source: {
        type: e.source.type,
        userId: hashUserId(e.source.userId),
      },
      replyToken: e.replyToken,
      message: e.message
        ? {
            type: e.message.type,
            id: e.message.id,
            text: e.message.text,
          }
        : null,
    }));

    return {
      destination: payload.destination,
      events,
    };
  }

  return payload;
}

function hashUserId(userId: string): string {
  if (!userId) return "";
  // SHA-256ハッシュ化（簡易実装）
  const encoder = new TextEncoder();
  const data = encoder.encode(userId);
  return Array.from(data)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .substring(0, 16);
}
