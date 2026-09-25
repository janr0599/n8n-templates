# Drive folder → vector store, kept in sync

_Status: **published**. [`drive-to-vector-store.json`](./drive-to-vector-store.json) (19 nodes)
and [`ask-the-knowledge-base.json`](./ask-the-knowledge-base.json) (7 nodes)._

## What it does

Most RAG demos index a folder once. The interesting part is every run after that:
what happens when a file is edited, when nothing has changed, and when a file is
deleted.

This walks a Drive folder on a schedule and makes the index match it. New files are
indexed. Edited files replace their own passages. Unchanged files cost nothing. And
files that are no longer in the folder have their passages removed, which is the half
most ingestion pipelines skip, because they iterate over what exists and a deletion is
the absence of a thing.

The second workflow is how you see it work: a chat window that answers from whatever
is in the index right now. Delete a file, run the sync, ask again, and the answer is
gone.

## Import

```
n8n → Workflows → Import from file → drive-to-vector-store.json
n8n → Workflows → Import from file → ask-the-knowledge-base.json
```

| Placeholder | Where | What to put |
|---|---|---|
| `YOUR_SHARED_DRIVE_ID` | List folder files | Your shared drive, or switch the filter to My Drive |
| `YOUR_DRIVE_FOLDER_ID` | List folder files | The folder id from its Drive URL |
| `YOUR_INDEX_NAME` | both Pinecone nodes, both workflows | Your index name |
| `YOUR_INDEX_HOST` | the three delete calls | `my-index-abc123.svc.us-east-1-aws.pinecone.io` |

Credentials: Google Drive (read on one folder), OpenAI, Pinecone.

## The shape of it

```
On a schedule → List folder files ─┬─> Only real files ─> Look up this file in the index ─┐
                                   │                                                      ├─> Pair file with index entry
                                   │                                                      │
                                   │   ┌──────────────────────────────────────────────────┘
                                   │   └─> Never indexed? ─true──────────────> Download file
                                   │         └─false─> Changed since indexed? ─true─> Download file
                                   │                     └─false─> Nothing to do
                                   │
                                   └─> Collect current file ids → Any files in the folder?
                                            ├─ yes → Delete files no longer in the folder   ($nin)
                                            └─ no  → Clear the namespace                    (deleteAll)

Download file → Index the passages → Delete the old version → Time Saved
```

## Three decisions worth copying

### Index first, then delete

The obvious order is delete the old passages, then write the new ones. This does the
opposite, and filters the delete on `file_id` **and** `last_modified != the new value`.

Two things fall out of that. The document is never absent from the index, where
deleting first leaves a window when it is. And Pinecone's delete returns before it is
fully applied, so a late-landing delete would otherwise match the passages just
written and wipe the file entirely; filtering on `last_modified` makes that
impossible.

The failure modes invert too. A failed delete now leaves duplicates, which are
visible and recoverable. Deleting first meant a failed insert lost the document
silently, which is worse.

`Delete the old version` is `executeOnce`, because the insert emits one item per
chunk and without it a nine-chunk document fires nine identical deletes.

### The sweep is the same pass, not a second workflow

A separate deletion workflow would need its own folder listing, so it inherits the
same risk and adds a second schedule that can disagree with the first. One listing,
one pass.

`Collect current file ids` aggregates the listing into a single item, and one call
deletes every passage whose `file_id` is not in it. That is what handles a file being
deleted, renamed out, or moved out of the folder, none of which the per-file path ever
sees.

### The empty folder is a branch, not an accident

`Any files in the folder?` splits because `$nin` against an empty list is not a valid
Pinecone filter. An empty folder clears the namespace with `deleteAll` instead.

This is safe because `alwaysOutputData` only emits its placeholder item when the Drive
call **succeeded** and found nothing. A failed call errors the run rather than
returning zero items, so an empty listing genuinely means an empty folder.

`Only real files` exists to keep that placeholder out of the per-file branch, where it
would reach the embedding as `undefined` and fail the run.

## The two halves have to agree

| | Both workflows use |
|---|---|
| Index | `YOUR_INDEX_NAME` |
| Namespace | `documents` |
| Embedding model | `text-embedding-3-small` |

The embedding model is the one that bites. Query with a different model from the one
used at index time and the vectors are not comparable, so you get results back, they
are just meaningless. No error, no warning, only bad answers.

## Errors you will see, and which ones matter

**`Namespace not found` on a sweep node is normal.** Pinecone does not keep empty
namespaces, so once the index is emptied the namespace ceases to exist, and the next
run's sweep runs before anything has been indexed. Deleting from a namespace that does
not exist and deleting nothing are the same outcome, which is why both sweep nodes
continue on error rather than branching around it. It resolves itself the moment
something is indexed.

**`Delete the old version` fails loudly on purpose.** With the new ordering a failed
delete leaves duplicate passages rather than losing the document, and duplicates are
worth being told about.

Both sweep deletes retry twice; a 404 will never succeed on retry, so more attempts
only add dead time. The per-file delete retries three times because it is a real
operation worth insisting on.

## The assistant will answer from memory if you let it

`Simple Memory` keeps the last 10 turns, and a vector store attached as a tool is
optional: the agent decides per turn whether to call it. With the answer already in
the conversation it usually will not bother, so it can keep answering from a document
you deleted ten minutes ago.

This looks exactly like a broken index and is not one. Open the execution and check
whether the vector store node ran at all.

Two things keep it honest. The system prompt requires a fresh lookup on every document
question and forbids repeating an earlier answer as though it had just been retrieved.
And when testing deletions, start a new chat session rather than continuing the old one.

## Chat access

The chat trigger ships with `public` enabled, which gives you a hosted chat URL you can
open without the n8n editor. Turn it off if you would rather only reach it from inside
n8n.

## Measured result

Rebuilt from a production pipeline where documents dropped into a shared folder are
answerable within minutes, editing a file changes the answers rather than adding a
competing version, and deleting one removes it from the answers.
