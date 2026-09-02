# Read-only connection contract

This is one guided action. Do not make the user remember separate create, list, or revoke
commands.

## Start

After the compulsory freshness check, run this read-only preflight before asking for a name:

```text
python skills/3rdbrain-connect/scripts/connect.py doctor --base "<base>"
```

- `PUBLIC`: return the public API address and its reading instructions. A key and this skill
  are optional for public content. Leave all Cloudflare settings unchanged and skip the key menu.
- `SETUP_REQUIRED`: read `cloudflare-setup.md` and guide the owner through the missing setup.
  Begin its next guided step immediately, keeping the pending request. Stop failed mutations,
  not assistance: a permission failure is a cue to guide setup, not to hand off a checklist.
- `UNVERIFIED`: explain the publishing/network issue; do not infer privacy or change access.
- `PREFLIGHT_OK`: read permissions work; this alone does not prove key creation works.

For a protected API, ask what they want to do unless their request already specifies it:

1. Create a read-only connection
2. View existing connections
3. Revoke a connection

Use `scripts/connect.py` for every Cloudflare operation. Never recreate its requests by hand.
It reads `THIRDBRAIN_CONNECT_API_TOKEN`, falling back to `CLOUDFLARE_API_TOKEN`, plus
`CLOUDFLARE_ACCOUNT_ID` from the environment or the base's ignored `_site/.env` file.

The management token needs these narrow Cloudflare permissions:

- Access: Service Tokens Write
- Access: Apps and Policies Write

If either permission is missing, stop further mutations and follow `cloudflare-setup.md`.
Guide local credential storage there; do not assume the user knows tokens or `.env` files.
Never display, commit, copy into a prompt, or record that management token.

## Create

Ask for missing details together with the access explanation:

- A connection name, such as the person, app, or agent receiving access
- Expiry: 30 days, 90 days, one year, a custom duration, or no expiry

Read the published address from `_site/mkdocs.yml`. Ask for it only when it is absent or still a
placeholder. Example: "What name and expiry? This grants read-only access to the whole published
API of <site>." A clear reply such as "Agent, 90 days" authorizes creation. Do not ask for a
second confirmation. If all details are already supplied and scope is understood, proceed.
Clarify only an ambiguous site, recipient, expiry or access scope.

Run:

```text
python skills/3rdbrain-connect/scripts/connect.py create --name "<name>" --duration "<duration>" --base "<base>"
```

If Cloudflare rejects creation, stop and follow `cloudflare-setup.md`. A successful read preflight
does not establish write permission. Do not repeat mutations with the same rejected credential.
Start the guided recovery in your response and retain the supplied name, expiry and site.

The helper creates or reuses a path-specific Cloudflare Access application for `/api/*`, creates
one service credential, attaches one Service Auth policy, and checks the live manifest. The
credential grants access only to the published read API. It grants no repository, inbox,
curation, deployment, or Cloudflare management access.

Show the returned connection bundle once and tell the user to store it in the receiving agent's
secret settings. Never save the Client Secret in the base, shell profile, skill, chat summary, or
Git. Cloudflare does not show the same secret again.

Report `VERIFIED` only when the authenticated manifest succeeds, an unauthenticated request is
blocked, and an authenticated write request is rejected. If the site has not yet published the
read API, report `CREATED, NOT YET VERIFIED` and offer to run the normal publish workflow with
explicit consent.

## View

Run:

```text
python skills/3rdbrain-connect/scripts/connect.py list --base "<base>"
```

Show each connection's name, creation time, expiry, and enabled state. Secrets are intentionally
absent because Cloudflare returns them only at creation or rotation.

## Revoke

List connections first. Ask the user to choose one visible connection and confirm the exact
name. Then run:

```text
python skills/3rdbrain-connect/scripts/connect.py revoke --token-id "<id>" --base "<base>" --confirm
```

Revocation deletes its matching Service Auth policy and service credential. Report any cleanup
warning, but treat the connection as revoked only after Cloudflare confirms deletion of the
credential.

## Boundaries

- A connection covers the whole published read API. Never claim page-level or section-level scope.
- The API is read-only because it contains static `GET` resources and its Access application has
  no write route. The service credential itself is an authentication credential, not a content
  permission system.
- A public API remains public. Never create an Access application just because Connect was
  invoked. A public website may have a separately protected API; inspect the API itself.
- Existing email policies, approved users and browser sessions are outside a routine key request.
- An unchanged verified framework uses the freshness fast path. Connection actions do not
  independently require a full site build. Reconciliation still requires its normal checks.
- Never create a connection for an unpublished local-only base. Explain that a network address is
  required and offer the publish workflow separately.
