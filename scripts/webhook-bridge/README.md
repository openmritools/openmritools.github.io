# Webhook bridge: Formspree → GitHub Issues

Cloudflare Worker that receives Formspree form submissions and triggers
the `formspree-to-issue.yml` GitHub Actions workflow, which creates a
GitHub Issue for each submission.

## Flow

```
openmritools.com/contribute
  → Formspree (form host)
  → this Worker (auth + format bridge)
  → GitHub repository_dispatch
  → GitHub Actions workflow
  → GitHub Issue created
```

## One-time setup

### 1. Create a GitHub fine-grained PAT

Go to **GitHub → Settings → Developer settings → Personal access tokens →
Fine-grained tokens → Generate new token**.

- Resource owner: `openmritools`
- Repository access: only `openmritools.github.io`
- Permissions:
  - Repository permissions → **Contents: Read and write** (required for repository_dispatch)
  - Repository permissions → **Metadata: Read-only**

Copy the token — you'll need it in step 3.

### 2. Deploy the Worker

```bash
npm install -g wrangler
wrangler login
cd scripts/webhook-bridge
wrangler deploy
```

Copy the Worker URL printed at the end (e.g. `https://openmritools-webhook-bridge.your-subdomain.workers.dev`).

### 3. Add Worker secrets

```bash
wrangler secret put GITHUB_TOKEN
# paste the PAT from step 1

wrangler secret put GITHUB_REPO
# enter: openmritools/openmritools.github.io

wrangler secret put FORMSPREE_SECRET
# paste the signing secret from step 4
```

### 4. Configure Formspree webhook

1. Go to **Formspree dashboard → your form (mwvjjkay) → Integrations → Webhooks**
2. Add a new webhook:
   - **URL:** the Worker URL from step 2
   - **Events:** New submission
3. Copy the **Signing Secret** shown and use it in `wrangler secret put FORMSPREE_SECRET` above

### 5. Test

Submit a test entry via `openmritools.com/contribute` and verify:
- A GitHub Actions run appears under the **Actions** tab
- A GitHub Issue is created with the correct title and label

## Updating the issue format

Edit `.github/workflows/formspree-to-issue.yml`. No Worker redeploy needed.
The Worker only forwards data — all issue logic lives in the workflow.
