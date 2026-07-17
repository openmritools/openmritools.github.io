/**
 * Cloudflare Worker: openmritools.com contribute form → GitHub Issue
 *
 * Receives a direct HTML form POST, creates a GitHub Issue, then redirects
 * the user back to /contribute/?submitted=true.
 *
 * Required Worker secrets (set with `wrangler secret put`):
 *   GITHUB_TOKEN  — fine-grained PAT with Issues: Read and write
 *   GITHUB_REPO   — "openmritools/openmritools.github.io"
 */

const REDIRECT_BASE = 'https://openmritools.com/contribute/';

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return Response.redirect(REDIRECT_BASE, 302);
    }

    let form;
    try {
      form = await request.formData();
    } catch {
      return Response.redirect(REDIRECT_BASE + '?submitted=true', 302);
    }

    // Honeypot — bots fill hidden fields, real users don't
    if (form.get('_honey')) {
      return Response.redirect(REDIRECT_BASE + '?submitted=true', 302);
    }

    const type        = (form.get('type')        || '').trim();
    const toolName    = (form.get('tool_name')    || '').trim();
    const toolUrl     = (form.get('tool_url')     || '').trim();
    const description = (form.get('description')  || '').trim();
    const contact     = (form.get('contact')      || '').trim();
    const listMe      = form.get('list_contributor') ? 'yes' : 'no';

    if (!toolName) {
      return Response.redirect(REDIRECT_BASE + '?submitted=true', 302);
    }

    const isEdit = type.toLowerCase() === 'flag';
    const prefix = isEdit ? '[Edit]'    : '[Suggest]';
    const label  = isEdit ? 'edit'      : 'suggestion';

    const body = [
      `| Field | Value |`,
      `|---|---|`,
      `| Type | ${isEdit ? 'Flag an edit' : 'Suggest a tool'} |`,
      `| Tool name | ${toolName} |`,
      `| URL | ${toolUrl ? `[${toolUrl}](${toolUrl})` : '—'} |`,
      `| Description | ${description ? description.replace(/\n/g, ' ') : '—'} |`,
      `| Contact | ${contact || '—'} |`,
      `| List as contributor | ${listMe} |`,
      ``,
      `*Submitted via [openmritools.com/contribute](https://openmritools.com/contribute)*`,
    ].join('\n');

    const ghResp = await fetch(
      `https://api.github.com/repos/${env.GITHUB_REPO}/issues`,
      {
        method: 'POST',
        headers: {
          'Authorization':        `Bearer ${env.GITHUB_TOKEN}`,
          'Content-Type':         'application/json',
          'Accept':               'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent':           'openmritools-webhook-bridge',
        },
        body: JSON.stringify({
          title:  `${prefix} ${toolName}`,
          body,
          labels: [label],
        }),
      }
    );

    const ghBody = await ghResp.text();
    console.log('GitHub API status:', ghResp.status);
    console.log('GitHub API response:', ghBody);

    // Always redirect — don't expose GitHub API errors to visitors
    return Response.redirect(REDIRECT_BASE + '?submitted=true', 302);
  },
};
