# Prepare private agent connections

Use during email-restricted publishing or to upgrade an existing protected base. The same
procedure serves both. Keep the existing hostname, email allowlist and working browser login.
Local-only setup and public publishing skip this procedure.

## Guide the person, one step at a time

Assume no Cloudflare or file-editing knowledge. Keep the pending action, site, name and expiry
in the conversation without secrets. Start at the first unfinished step; skip confirmed steps.
Give one short, actionable instruction, then wait only when the person must act. Offer the full
checklist only if requested. Never end with only "set this variable and tell me when done."

1. **Sign in.** Start with: "Your Cloudflare setup needs one extra permission step. I'll walk
   you through it, then continue your pending connection. Open [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
   and sign in. Tell me when you see the API Tokens page."
   With available, authorized browser tools, open the page and assist with navigation. Let the
   user handle login and MFA. Without browser tools, the link and guided steps still work.
2. **Create the management token.** Guide **Create Token > Create Custom Token**. Suggest the
   label "3rdBrain connection management". Walk through the two permission rows below, then
   select only the account hosting this base under Account Resources. Help identify the account
   using its configured ID without exposing secrets. If labels differ, ask what the user sees
   or request a screenshot with all secrets hidden. Do not guess a permission selection.
3. **Review and authorize.** Explain that this credential manages agent connections and stays
   on the owner's machine. Obtain any still-needed authorization for setup and its temporary
   test. Guide the review/create screen. Never request token-creation privileges for the agent.
4. **Save locally.** Resolve the actual base path and verify `_site/.env` is ignored by Git.
   Provide its clickable local path or open it in an authorized local editor. Explain: "This
   is the private settings file. Add a new line starting with
   `THIRDBRAIN_CONNECT_API_TOKEN=`, then paste the new token immediately after the equals sign
   and save. Keep the existing lines. Tell me when saved; keep the token out of chat."
   Help create the file safely if absent and supply the account ID separately when needed.
   Never capture the screen while a secret is visible or print file contents to check it.
5. **Verify and resume.** After "saved", run the preflight and authorized temporary trial below.
   On `READY`, resume the pending request in the same task using its existing details and consent.
   Ask only for genuinely missing details. If the check still fails, explain the specific failure
   and guide the next corrective step. If the user pauses, retain a secret-free pending summary.

## One owner authorization

Explain during protected publishing: "We will protect your site for the approved emails and
prepare read-only agent connections. Cloudflare needs your authorization once. Setup includes
a temporary connection test; its key is removed afterwards."

Use the owner's existing account. For a new account, guide them through Cloudflare One / Zero
Trust enrollment and preview protection. Let the owner complete login, MFA, plan selection and
any billing or consent screens. Never claim that entering email addresses alone completes this.

During that same setup visit, guide them to **My Profile > API Tokens > Create Token > Custom
token**, scoped to the selected account, with these Account permissions:

- **Access: Apps and Policies: Edit** (API name: `Access: Apps and Policies Write`)
- **Access: Service Tokens: Edit** (API name: `Access: Service Tokens Write`)

Keep the Pages deployment credential separate. Save the new management credential locally as
`THIRDBRAIN_CONNECT_API_TOKEN` and the account ID as `CLOUDFLARE_ACCOUNT_ID` in the base's ignored
`_site/.env`. Check Git ignores the file first. Never ask for the secret in chat or give it to a
receiving agent. A configured credential with both permissions can be reused. Signing into the
dashboard does not grant these permissions to a deployment token.

The owner can revoke the management credential in Cloudflare. Its expiry or permission removal
will require reauthorization for future key management. Avoid requesting account-wide token
creation privileges or changing unrelated permissions.

## Preflight and live proof

Run `scripts/connect.py doctor --base "<base>"`. `SETUP_REQUIRED` means stop and explain the
missing permission or account configuration, then continue the guided steps above. Successful
read calls only prove read access.
If the owner chose private publishing but the probe returns `PUBLIC`, stop: privacy protection
is incomplete. Fix and verify the gate before proceeding. Do not report private setup ready.

After owner authorization, run:

```text
python skills/3rdbrain-connect/scripts/connect.py prepare --base "<base>" --confirm
```

This creates or reuses a 3rdBrain-owned `/api/*` Access application, creates a temporary service
credential and its Service Auth policy, checks authenticated reading and blocked anonymous and
write requests, deletes the temporary credential/policy, and checks revoked access. The temporary
secret stays in memory. The API application stays protected for future connections. An unrelated
application on that path requires review; do not replace it automatically.

Report **Connect ready** only on `READY`. `PREFLIGHT_OK` is not a readiness receipt. If a check
fails, report the failed check and cleanup state. Allow for Cloudflare propagation by offering
a later explicit retry, without repeatedly creating credentials. If cleanup fails, identify the
temporary connection from the managed list and finish cleanup before trying again.

Verify normal email login with the owner and recheck protected alternate/preview URLs as part
of publishing. The API trial does not prove that every website URL is protected. Keep private
content out of deployment until the publishing protection checks pass.

For an existing base, perform only these access-readiness steps. Preserve content, deployment
configuration, email policies and user sessions. Rebuild only if the API is missing or framework
reconciliation requires it. Never automatically remove an existing API gate on a public website.

References: [Cloudflare API token permissions](https://developers.cloudflare.com/fundamentals/api/reference/permissions/),
[service credentials](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/).
