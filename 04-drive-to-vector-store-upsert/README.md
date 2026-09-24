# Drive folder → vector store, kept current

_Status: documented. Workflow JSON not yet published._

## What it does

Most RAG demos index a folder once. The interesting part is the second run: what
happens when a file is edited, or when nothing has changed. This pattern walks a
Drive folder on a schedule, compares what it finds against what the vector store
already holds, and upserts only what is new or changed, so an edited document
replaces its own vectors instead of sitting alongside a stale copy.

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| Schedule Trigger | Runs the pass on an interval | Hourly is usually enough |
| Search files and folders | Lists the folder's files with modified times | The source of truth for "what exists" |
| Vector store: query | Asks what is already indexed | Runs in parallel with the listing |
| Embeddings (query side) | Required by the vector store node | Same model as the write side |
| Merge | Joins the two lists on file id | Left side files, right side index state |
| If: new or changed | Compares modified time against indexed time | Unchanged files stop here |
| If: supported type | Splits documents from anything unreadable | Unsupported types go to a No-Op |
| Download file | Fetches the binary | `retryOnFail` |
| HTTP Request | Extraction or conversion for types Drive will not export directly | `retryOnFail`, `continueRegularOutput` |
| Merge | Rejoins the extracted text with its metadata | |
| Data Loader | Splits the text into overlapping passages | Chunk size and overlap live here |
| Embeddings (write side) | Embeds each passage | |
| Vector store: upsert | Writes passages keyed by file id | The key is what makes an edit replace rather than duplicate |

## Credentials you need

- Google Drive (read access to one folder is enough)
- An embeddings provider
- A vector database (Pinecone in the original; any supported store works)

## Sample data

`sample/` will hold a few public PDFs so the pass runs end to end on import.

## Error handling

The download and extraction calls retry, and extraction continues on error so one
unreadable file does not abandon the rest of the batch. The upsert does **not**
continue on error: a passage that fails to write should fail loudly, because a
partial index is the failure mode nobody notices.

## Measured result

Rebuilt from a production pipeline where documents dropped into a shared folder are
answerable within minutes, and editing a file changes the answers rather than adding
a competing version.
