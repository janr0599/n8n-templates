# n8n templates, public repo

Public patterns at github.com/janr0599/n8n-templates, linked from the portfolio deck.
Personal project of Javier Noguera Rodríguez. The n8n instance it draws from is a
production one carrying both agency and client work, so what may be published is
decided by where a workflow came from, not by whether it is interesting.

This file is public. Keep client names, workflow inventories and instance detail
out of it; the blocklist in `tools/blocklist.local.txt` holds the names, and that
file is gitignored.

## Origin decides what may be published

| Origin | Modify the original? | Publish here? |
|---|---|---|
| Own agency work, published and live | No. Export a copy and work on the file | Yes, after export, clean and generalise |
| Already published to this repo (Drive to vector store) | No, leave it | Done |
| Client-derived, copied to the instance | Yes, they are his copies | **No.** Asked and answered 2026-09-24. See below |
| Built clean for this repo (Examples folder) | Yes | Yes |

Never publish a workflow the client owns, however generalised. Describing the work
is fine, publishing it is not.

**The sanitiser does not decide this.** It removes identifiers: names, emails,
record ids, credentials. It cannot remove the client's business, which lives in node
names, branch conditions and document templates. The onboarding workflow is the worked
example: forced through the script it still carries RFE 42 times, NIW 20, I-130 19,
plus beneficiary, petition, USCIS and priority date. Every name gone, the practice
still obvious. A clean scan means the file is free of identifiers, not that it is
free to publish.

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

**One copy per workflow.** A copy of a live workflow goes in `Demos` and serves both
jobs: it is what gets recorded, and it is what gets exported to this repo. There is
no separate clean-room build. `clean-export.py` is the gate between the two, so a
second copy would only be a second thing to keep in sync.

- `Demos` — every copy. Recorded against, and exported from. Publishable only when
  the origin table above says so, which is not true of everything in here
- `Examples` — unrelated scratch, nothing in this repo comes from it
- Everything else is live agency work. Do not activate, deactivate or save it

Copies are made with n8n's own **Duplicate**, in the UI, which clones the credential
bindings exactly. A duplicated webhook workflow needs a new path before it can be
activated.

Point the copy at demo resources: a demo Chatwoot inbox, a demo Airtable table, a
demo Pinecone namespace. That is for the recording, not the export, because the
screen is visible in the video and the ids are not visible after the script has run.
It also keeps a bad take off a live channel.

## Repo conventions

- No credentials in any JSON. The README lists what to create
- Retries and error branches ship as part of the template
- Every README: what it does, import and placeholders, node table, credentials,
  error handling, why the non-obvious choices were made, measured result
- No em dashes in copy
- Git identity: `gh auth switch --user janr0599` before pushing, back to
  `javiern0599` afterwards. Commit as `Javier Noguera <javiernr0599@gmail.com>`
