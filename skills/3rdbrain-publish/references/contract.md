---
description: Put your 3rdBrain base online, free, with a login wall or an open link. Warns before anything uploads and verifies the result from outside.
---

# 3rdBrain publishing contract

Before publishing, load `3rdbrain-curator` and follow its
`references/framework-freshness.md`.

The base already runs on the user's computer. This command puts it on the internet so they
can read it from a phone or share it with one other person.

Hosting is **Cloudflare Pages**, free tier, no card. The build is the same one that runs
locally, so what they see online matches what they see at home.

## 0. Consent, before anything else

State this plainly, in the user's own words, and wait for a clear yes:

> This puts your knowledge base on the internet. Anyone with the address can reach it
> unless we add a login. Your notes include everything you have filed so far.

If they hesitate, stop. The local site keeps working.

Then ask the one question that decides the whole setup:

| Ask | Meaning |
| --- | --- |
| **"Only my email address, through a sign in screen?"** | Cloudflare Access, allowlist |
| **"Anyone who has the link?"** | Open, no sign in |

Do not choose for them. Do not treat silence as consent to publish openly.

## 1. Credentials

One token, from the user's own Cloudflare account:

- **Cloudflare API token**: dash.cloudflare.com → My Profile → API Tokens → Create Token →
  template **Edit Cloudflare Workers**. Revoke on that same page at any time.
- **Account ID**: the long value in their dashboard URL.

Store both in the site folder's `.env`, which is gitignored. State that the file stays on
their machine.

## 2. Project name

Ask what the address should be. Default `3rdbrain`. The published address becomes
`https://main.<name>.pages.dev`.

Names are global to Cloudflare, so be ready for a clash and ask for a second choice.

## 3. Create the project

```bash
wrangler pages project create <name> --production-branch unused-production
```

`unused-production` is a branch that never exists, and that is the point. Cloudflare cannot
put a login wall on a project's **production** address. It can put one on **preview**
addresses. Setting production to a branch nobody pushes leaves the public address empty and
sends every deploy to `main`, which is treated as a preview and therefore can be protected.

Verify afterwards that `https://<name>.pages.dev` (without `main.`) returns nothing.

## 4. Deploy

```bash
wrangler pages deploy site --project-name <name> --branch main --commit-dirty=true
```

Uploads are incremental. The first run sends everything; later runs send only what changed,
usually in a few seconds.

## 5. The lock, when they chose an allowlist

Cloudflare Access needs a Zero Trust team on the account. Many accounts have never created
one, and the API cannot create it with a Pages-scoped token, so this part is done in the
dashboard. Walk the user through it, one click per line:

1. Pages project → **Settings → General → Preview access → Restrict previews**.
2. Add their email address to the policy.
3. For an owner only area, add a second Access application on the same hostname with the
   path `admin`, allowing only the owner's address.

Sign in uses a one time PIN by default, which needs no further setup. Google sign in is
available if they want one click.

## 6. Verify from outside, always

Never report success from the dashboard alone. Fetch the live address with no cookies and
no credentials, and read the result:

- **Allowlist chosen**: expect a redirect to a Cloudflare Access login. Report the status
  code and confirm no page content came back.
- **Open link chosen**: expect the site. Say clearly that anyone with the address can read
  it, and remind them a login can be added later.

Also fetch the production address and confirm it is empty.

Report what a stranger sees, in one sentence, with the evidence. A base that leaks quietly
is the worst outcome this command can produce, so the check is part of the job.

## 7. Keeping it current

Offer to install the post-commit hook so every filing run republishes automatically:

```bash
bash install-hook.sh
```

The hook runs the build and the upload in the background, and never blocks a commit.
Output goes to `deploy.log`. Removing it is one line: `rm .git/hooks/post-commit`.

## Reporting back

Give them: the address, who can reach it, what a stranger sees right now, and whether
automatic updates are on. Remind them the token is revokable and the local base keeps
working whatever happens online.
