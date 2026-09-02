# Read-only connection contract

This is one guided action. Do not make the user remember separate create, list, or revoke
commands.

## Start

Ask what they want to do:

1. Create a read-only connection
2. View existing connections
3. Revoke a connection

Use `scripts/connect.py` for every Cloudflare operation. Never recreate its requests by hand.
It reads `THIRDBRAIN_CONNECT_API_TOKEN`, falling back to `CLOUDFLARE_API_TOKEN`, plus
`CLOUDFLARE_ACCOUNT_ID` from the environment or the base's ignored `_site/.env` file.

The management token needs these narrow Cloudflare permissions:

- Access: Service Tokens Write
- Access: Apps and Policies Write

If either permission is missing, stop before mutation. Explain the two permissions and ask the
user to save a suitable token as `THIRDBRAIN_CONNECT_API_TOKEN` in `_site/.env`. Never display,
commit, copy into a prompt, or record that management token.

## Create

Ask only for:

- A connection name, such as the person, app, or agent receiving access
- Expiry: 30 days, 90 days, one year, a custom duration, or no expiry

Read the published address from `_site/mkdocs.yml`. Ask for it only when it is absent or still a
placeholder. Confirm the name, expiry, and site before creating anything.

Run:

```text
python skills/3rdbrain-connect/scripts/connect.py create --name "<name>" --duration "<duration>" --base "<base>"
```

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
- A public 3rdBrain site remains public. The `/api/*` connection path still requires its service
  credential after the first connection is configured.
- Never create a connection for an unpublished local-only base. Explain that a network address is
  required and offer the publish workflow separately.
