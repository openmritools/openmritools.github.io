# Webhook bridge: contribute form → GitHub Issues

Cloudflare Worker that receives direct form POSTs from openmritools.com/contribute
and creates a GitHub Issue for each submission, then redirects the visitor back
to /contribute/?submitted=true.

## Flow

```
openmritools.com/contribute (HTML form POST)
  → this Worker (parses fields, creates issue)
  → GitHub Issues API
  → redirect → /contribute/?submitted=true
```

## One-time setup

### 1. Create a GitHub fine-grained PAT

Go to **GitHub → Settings → Developer settings → Personal access tokens →
Fine-grained tokens → Generate new token**.

- Resource owner: `openmritools`
- Repository access: only `openmritools.github.io`
- Permissions:
  - Repository permissions → **Issues: Read and write**
  - Repository permissions → **Metadata: Read-only**

Copy the token — you'll need it in step 3.

### 2. Deploy the Worker

```bash
npm install -g wrangler
wrangler login
cd scripts/webhook-bridge
wrangler deploy
```

The Worker deploys to `https://openmritools-webhook-bridge.openmritools.workers.dev`.

### 3. Add Worker secrets

```bash
wrangler secret put GITHUB_TOKEN
# paste the PAT from step 1

wrangler secret put GITHUB_REPO
# enter: openmritools/openmritools.github.io
```

### 4. Test

Submit a test entry via `openmritools.com/contribute`. Verify:
- Browser redirects to `/contribute/?submitted=true` with the success message
- A GitHub Issue appears under the Issues tab with the correct title and label

## Updating the issue format

Edit `worker.js` and redeploy with `wrangler deploy`. No GitHub Actions involved —
the Worker talks to the GitHub Issues API directly.
