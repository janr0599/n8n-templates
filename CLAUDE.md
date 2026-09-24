# n8n templates, public repo

Public patterns at github.com/janr0599/n8n-templates, linked from the portfolio deck.
Personal project of Javier Noguera Rodríguez. The n8n instance it draws from is the
example production instance, so what may be published is decided by where a
workflow came from, not by whether it is interesting.

## Origin decides what may be published

| Origin | Modify the original? | Publish here? |
|---|---|---|
| example, published and live (Cold Outreach A-E, AI Voice Receptionist, AI Chat Customer Support, Social Media) | No. Export a copy and work on the file | Yes, after export, clean and generalise |
| Already published to this repo (Drive to vector store) | No, leave it | Done |
| Client-derived, copied to the instance (Demos folder: client onboarding, attorney email, intake agent) | Yes, they are his copies | **Ask first.** Client-owned logic is the TAA risk, and "generalised" is hardest to defend here |
| Built clean for this repo (Examples folder) | Yes | Yes |

Never publish a workflow the client owns, however generalised. Describing the work
is fine, publishing it is not.

## Export, clean, generalise. Do not rebuild in the instance

The safe path is a file, not a new workflow:

```
n8n → open the workflow → Download → ~/Downloads/<name>.json
python3 tools/clean-export.py ~/Downloads/<name>.json 0X-pattern/workflow.json
```

`clean-export.py` strips every `credentials` block and refuses to write when an
account name, email address, record id or private hostname is still in the file.
`--allow <string>` for the ones that are genuinely safe.

Then generalise in the file: placeholders for the persona and the offer, and rename
the vertical out of the field names. Keep the connection graph, the `retryOnFail`
and `onError` flags and the code nodes as built.

**Do not rebuild a published workflow inside the instance to get a clean copy.**
n8n auto-attaches the most recently edited credential of each type to a new
workflow, even when the SDK asked for an empty placeholder. That is how a real
Drive and Pinecone credential nearly went into template 04. A file export cannot
do this, because the strip happens before anything is written.

Read the original in full before replicating it. Node order is usually deliberate.

## Folders in the instance

- `Demos` — copies used for recordings. Nothing here is published from directly
- `Examples` — clean reference builds for this repo
- Everything else is live example work. Do not activate, deactivate or save it

Demo copies are made with n8n's own **Duplicate**, in the UI, which clones the
credential bindings exactly. A duplicated webhook workflow needs a new path before
it can be activated, and should point at a demo Chatwoot inbox, a demo Airtable
table and a demo Pinecone namespace, never the live ones.

## Repo conventions

- No credentials in any JSON. The README lists what to create
- Retries and error branches ship as part of the template
- Every README: what it does, import and placeholders, node table, credentials,
  error handling, why the non-obvious choices were made, measured result
- No em dashes in copy
- Git identity: `gh auth switch --user janr0599` before pushing, back to
  `javiern0599` afterwards. Commit as `Javier Noguera <javiernr0599@gmail.com>`
