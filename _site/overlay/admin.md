---
description: Who can reach this site, and how to change it
search:
  exclude: true
---

# Access control

!!! warning "Only the owner can open this page"
    This page sits behind a **second, stricter rule** than the rest of the site.
    Everyone else on the allowlist gets the site but is refused here, and anyone
    not on the allowlist never reaches either.

## Who can get in today

| Email | Role | Can do |
| --- | --- | --- |
| *(your address)* | **Owner** | Read everything, open this page, add and remove people |
| *(none yet)* | Reader | Read everything. Cannot open this page. |

Add your partner by following the steps below.

## Add someone

1. Open **[Cloudflare Zero Trust](https://one.dash.cloudflare.com/)** and sign in
   as `you@example.com`.
2. Go to **Access → Applications → PromptOS**.
3. Open the **Allow** policy.
4. Under **Emails**, add their address.
5. Save. It takes effect on their next sign-in — no rebuild, no deploy.

They will get a sign-in prompt on their first visit and nothing else changes.

## Remove someone

Same path, delete their address from the **Emails** list, then use **Revoke
existing sessions** on the application. Without the revoke they keep their
current session until it expires.

Once removed they cannot load any page. The site is not merely hidden from them.

## Why the buttons are not on this page

Adding and removing people is done in Cloudflare, not here. This site is static
files with no server and no database. Putting an "add user" button here would
mean shipping a Cloudflare API key inside a public JavaScript file, and anyone
who reached the page could then read the key and grant themselves access. The
control therefore stays in the place that already checks identity.

This is the ordinary arrangement: the access layer owns the guest list, and the
site behind it owns nothing.

## How the two rules are set up

| Application | Covers | Allowed |
| --- | --- | --- |
| **PromptOS** | the whole site | everyone on the allowlist |
| **PromptOS Admin** | `/admin` only | `you@example.com` only |

Cloudflare evaluates the more specific path first, so the admin rule wins on
this page. Setup steps for both are in `DEPLOY.md`.

## If you lose access

You own the Cloudflare account, so you can always sign in to the dashboard and
edit the policy — even if the allowlist is emptied by mistake. Deleting the
Access application removes the lock entirely and makes the site public, so do
that only on purpose.
