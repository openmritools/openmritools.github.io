/**
 * Cloudflare Worker: Formspree → GitHub repository_dispatch bridge
 *
 * Receives Formspree webhook POSTs, validates the HMAC-SHA256 signature,
 * and forwards the payload to GitHub's repository_dispatch API so the
 * formspree-to-issue.yml workflow can create a GitHub Issue.
 *
 * Required Worker secrets (set with `wrangler secret put`):
 *   GITHUB_TOKEN      — fine-grained PAT (Contents: Read on the repo)
 *   GITHUB_REPO       — "openmritools/openmritools.github.io"
 *   FORMSPREE_SECRET  — webhook signing secret from Formspree dashboard
 */

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    const rawBody = await request.text();

    // Validate Formspree HMAC-SHA256 signature
    const signature = request.headers.get('X-Formspree-Signature');
    if (env.FORMSPREE_SECRET) {
      if (!signature) {
        return new Response('Missing signature', { status: 401 });
      }
      const expected = await hmacSHA256Hex(env.FORMSPREE_SECRET, rawBody);
      // Formspree sends the hex digest directly (no "sha256=" prefix)
      if (!timingSafeEqual(signature, expected)) {
        return new Response('Invalid signature', { status: 401 });
      }
    }

    let submission;
    try {
      submission = JSON.parse(rawBody);
    } catch {
      return new Response('Bad Request: invalid JSON', { status: 400 });
    }

    // Formspree nests form fields under `data`
    const data = submission.data || submission;

    const dispatch = {
      event_type: 'formspree-submission',
      client_payload: {
        type:        String(data.type        || '').trim(),
        tool_name:   String(data.tool_name   || '').trim(),
        tool_url:    String(data.tool_url    || '').trim(),
        description: String(data.description || '').trim(),
        contact:     String(data.contact     || '').trim(),
      },
    };

    const resp = await fetch(
      `https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`,
      {
        method: 'POST',
        headers: {
          'Authorization':        `Bearer ${env.GITHUB_TOKEN}`,
          'Content-Type':         'application/json',
          'Accept':               'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent':           'openmritools-webhook-bridge',
        },
        body: JSON.stringify(dispatch),
      }
    );

    if (!resp.ok) {
      const text = await resp.text();
      console.error('GitHub dispatch failed:', resp.status, text);
      return new Response('Upstream error', { status: 502 });
    }

    return new Response('OK', { status: 200 });
  },
};

async function hmacSHA256Hex(secret, message) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(message));
  return Array.from(new Uint8Array(sig))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

// Constant-time string comparison to prevent timing attacks
function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}
