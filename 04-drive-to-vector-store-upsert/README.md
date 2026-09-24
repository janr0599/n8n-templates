# Drive folder → vector store, kept current

_Status: **published**. [`drive-to-vector-store.json`](./drive-to-vector-store.json), 11 nodes._

## What it does

Most RAG demos index a folder once. The interesting part is the second run: what
happens when a file is edited, or when nothing has changed. This pattern walks a
Drive folder on a schedule and, for every readable document, deletes that file's
previous passages before writing the new ones, so an edited document replaces its
own vectors instead of sitting alongside a stale copy of itself.

## Import

```
n8n → Workflows → Import from file → drive-to-vector-store.json
```

Then fill in three placeholders and attach three credentials:

| Placeholder | Where | What to put |
|---|---|---|
| `YOUR_DRIVE_FOLDER_ID` | List folder files | The folder id from its Drive URL |
| `YOUR_INDEX_NAME` | Index the passages | Your Pinecone index name |
| `YOUR_INDEX_HOST` | Delete previous chunks | Your index host, e.g. `my-index-abc123.svc.us-east-1-aws.pinecone.io` |

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| Every hour | Runs the pass on a schedule | Hourly by default; the interval is the only thing tying this to "how fresh" |
| List folder files | Lists every file in the folder with its full metadata | `returnAll`, `fields: *`, so `modifiedTime` and `mimeType` come back |
| Readable document? | Splits documents the loader can read from everything else | PDF, Google Doc, .docx and plain text on the true branch |
| Skip unreadable file | Absorbs the rest | A spreadsheet or image ends the run for that item, not the batch |
| Download file | Fetches the binary | Google Docs are exported as plain text on the way out |
| Delete previous chunks | Deletes this file's existing vectors by `fileId` | **The node that matters.** Continues on error, because a first-time file has nothing to delete |
| Index the passages | Embeds and writes the new passages | `insert` mode into the `documents` namespace |
| Embeddings | Turns each passage into a vector | `text-embedding-3-small` |
| Read the document | Reads the binary and attaches `fileId` and `fileName` as metadata | The metadata is what the delete step filters on next run |
| Split into passages | 1000 characters, 200 overlap | Overlap keeps sentences from being cut mid-thought |

## Credentials you need

- Google Drive (read access to one folder is enough)
- An embeddings provider
- A vector database (Pinecone in the original; any supported store works)

## Sample data

Point it at any Drive folder with a few documents in it. There is nothing to seed:
the workflow discovers whatever is in the folder.

## Error handling

The download and extraction calls retry, and extraction continues on error so one
unreadable file does not abandon the rest of the batch. The upsert does **not**
continue on error: a passage that fails to write should fail loudly, because a
partial index is the failure mode nobody notices.

## Why the delete step exists

Most published RAG ingestion flows index a folder once. The interesting run is the
second one. Without the delete, editing a document leaves its old passages in the
index next to the new ones, and the assistant starts answering from a version of
the document that no longer exists. Deleting by `fileId` first is what makes an
edit a replacement.

## Measured result

Rebuilt from a production pipeline where documents dropped into a shared folder are
answerable within minutes, and editing a file changes the answers rather than adding
a competing version.
