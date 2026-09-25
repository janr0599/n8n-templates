# Drive folder → vector store, kept current

_Status: **published**. [`drive-to-vector-store.json`](./drive-to-vector-store.json) (16 nodes) and [`ask-the-knowledge-base.json`](./ask-the-knowledge-base.json) (7 nodes)._

## What it does

Most RAG demos index a folder once. The interesting part is the second run: what
happens when a file is edited, or when nothing has changed. This pattern walks a
Drive folder on a schedule and, for each file, looks it up in the index by
`file_id`. No entry means the file is new. An entry means comparing Drive's
`modifiedTime` against the `last_modified` written when it was indexed, and doing
nothing unless the file is genuinely newer. Only then are the old passages deleted
and the file re-indexed.

## Import

```
n8n → Workflows → Import from file → drive-to-vector-store.json
n8n → Workflows → Import from file → ask-the-knowledge-base.json
```

The first keeps the index current. The second is how you actually see it work:
a chat window that answers from whatever is in the index right now. Ingestion on
its own is only testable by staring at Pinecone.

Then fill in three placeholders and attach three credentials:

| Placeholder | Where | What to put |
|---|---|---|
| `YOUR_DRIVE_FOLDER_ID` | List folder files | The folder id from its Drive URL |
| `YOUR_INDEX_NAME` | Index the passages | Your Pinecone index name |
| `YOUR_INDEX_HOST` | Delete previous chunks | Your index host, e.g. `my-index-abc123.svc.us-east-1-aws.pinecone.io` |

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| Every hour | Runs the pass on a schedule | Drive has no reliable per-folder change event, so this polls and filters |
| List folder files | Lists every file with full metadata | `returnAll`, `fields: *`, so `modifiedTime` comes back |
| Look up this file in the index | Asks the store whether this `file_id` is already there | Metadata filter does the lookup; `topK: 1`; continues on error so an empty index is not a failure |
| Pair file with index entry | Left-joins the Drive file to its index entry | `id` ↔ `document.metadata.file_id`, `keepEverything` |
| Never indexed? | Empty `document` means the file is new | New files go straight to download |
| Changed since it was indexed? | `modifiedTime` later than `last_modified` | **The node that saves the money.** False means stop |
| Nothing to do | Ends the run for an unchanged file | No download, no embedding, no write, no cost |
| Download file | Fetches the binary, before anything is deleted | A failure here leaves the existing passages untouched |
| Delete previous chunks | Deletes this file's vectors by `file_id` | Harmless for a new file: the filter matches nothing |
| Wait for the delete | Holds the file until the delete finishes, then passes it through | `chooseBranch`, so the insert cannot race the delete |
| Read the document | Reads the binary, attaches `file_id`, `file_name`, `last_modified` | `last_modified` is what the next run compares against |
| Split into passages | 1000 characters, 200 overlap | |
| Index the passages | Embeds and writes | `embeddingBatchSize: 1` |

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

## Why the two checks exist

Most published RAG ingestion flows index a folder once, and the naive scheduled
version re-indexes everything on every pass. That works, and it is wrong: you pay
for embeddings on files nobody touched, burn Drive and vector-store quota, and
leave a window on each pass where a document is deleted and not yet rewritten.

The two checks are the whole point:

1. **Never indexed?** An empty join result means the file is new. Index it.
2. **Changed since it was indexed?** Compare Drive's `modifiedTime` against the
   `last_modified` stored on the file's own passages. If it is not newer, stop.

Which is why `last_modified` has to be written as metadata at index time. Without
it there is nothing to compare against on the next pass, and you are back to
re-indexing everything.

Drive has no straightforward per-folder "file added or modified" event, which is
why this polls on a schedule and filters, rather than triggering on change.

## Why the download comes first

The order is deliberate. Downloading before deleting means a failed download costs
nothing: the old passages are still in the index and the next pass tries again.
Deleting first would leave a window where the document is gone from the index and
its replacement never arrives.

The `Wait for the delete` merge closes the other half of that race. It waits for
both the download and the delete, then passes the downloaded file through, so the
insert can only start once the old passages are actually gone.

## The two halves have to agree

The chat side and the ingestion side are separate workflows pointed at the same
place, and three things must match or retrieval silently returns nothing:

| | Both workflows use |
|---|---|
| Index | `YOUR_INDEX_NAME` |
| Namespace | `documents` |
| Embedding model | `text-embedding-3-small` |

The embedding model is the one that bites. Query with a different model from the
one used at index time and the vectors are not comparable, so you get results
back, they are just meaningless. No error, no warning, only bad answers.

## The assistant will answer from memory if you let it

`Simple Memory` keeps the last 10 turns, and a vector store attached as a tool is
optional: the agent decides per turn whether to call it. With the answer already in
the conversation it usually will not bother, so it can keep answering from a
document you deleted ten minutes ago and never notice.

This is worth knowing because it looks exactly like a broken index. It is not. Open
the execution and check whether the vector store node ran at all.

Two things keep it honest here. The system prompt requires a fresh lookup on every
document question and forbids repeating an earlier answer as though it had just been
retrieved. And when you are testing deletions, start a new chat session rather than
continuing the old one.

## Chat access

The chat trigger ships with `public` enabled, which gives you a hosted chat URL you
can open without the n8n editor. Turn it off if you would rather only reach it from
inside n8n.

## Measured result

Rebuilt from a production pipeline where documents dropped into a shared folder are
answerable within minutes, and editing a file changes the answers rather than adding
a competing version.
