<h1>n8n templates</h1>

<p>
  <img alt="Patterns" src="https://img.shields.io/badge/patterns-6-d4702c?style=flat-square&labelColor=131313">
  <img alt="n8n" src="https://img.shields.io/badge/n8n-self--hosted-131313?style=flat-square&labelColor=131313&color=8c8c86">
  <img alt="Credentials" src="https://img.shields.io/badge/credentials-none%20in%20repo-8c8c86?style=flat-square&labelColor=131313">
  <img alt="Client data" src="https://img.shields.io/badge/client%20data-none%2C%20ever-8c8c86?style=flat-square&labelColor=131313">
</p>

Production patterns rebuilt clean and generic, with the error handling left in.
Each folder documents what every node does, which credentials to create and how
failures are handled. Workflow JSON and sample data are added one pattern at a
time: exported from a working instance, stripped of credentials and identifiers,
and generalised out of the vertical they were built for.

Built by **[Javier Noguera Rodríguez](https://javiernoguera.com)**, automation and
AI engineer. Case studies for the production systems these come from are in the
[deck](https://javiernoguera.com).

---

## Patterns

| # | Pattern | What it solves | Docs | JSON |
|---|---|---|:--:|:--:|
| 01 | [Inbound email → CRM conversation](./01-inbound-email-to-crm-thread) | Every email threaded onto the right contact, attachments filed and linked | ✅ | — |
| 02 | [Scheduled reminders with Data Table dedupe](./02-scheduled-reminders-data-table-dedupe) | 48 / 24 / 1 h reminders that never double-send | ✅ | — |
| 03 | [Chat intake agent with human handoff](./03-chat-intake-agent-human-handoff) | Agent, memory, message buffering, tools, and a classifier that hands off to a person | ✅ | — |
| 04 | [Drive folder → vector store, kept current](./04-drive-to-vector-store-upsert) | RAG ingestion where an edited file replaces its own vectors instead of duplicating | ✅ | [✅](./04-drive-to-vector-store-upsert/drive-to-vector-store.json) |
| 05 | [Agent tools over MCP](./05-agent-tools-over-mcp) | Expose workflows as callable tools any MCP client can use | ✅ | [✅](./05-agent-tools-over-mcp) |
| 06 | [Prospect research and first-touch draft](./06-prospect-research-and-draft) | Research a company, score fit, draft the email, and never let the model pick the address unchecked | ✅ | [✅](./06-prospect-research-and-draft/prospect-research-and-draft.json) |

Each folder's README covers the node order, the credentials to create, the error
handling and the measured result from the production build it was rebuilt from.
A dash in the JSON column means the pattern is documented but the workflow file has
not been published yet.

## Conventions

- **No credentials in the JSON.** Every credential node is left empty; the README
  lists what to create.
- **Retries and error branches are part of the template**, not an exercise for the
  reader. `retryOnFail` on every external call, `continueRegularOutput` where one
  failure should not stop the batch.
- **Sample data included** so the workflow runs end to end on import before you
  connect anything real.
- **No client data, ever.** Nothing here is an export of a client-owned workflow,
  and nothing here carries a client's name, record ids, addresses or prompts.
  Every file goes through `tools/clean-export.py` before it lands.

## Publishing a new template

The workflows live in an n8n instance with real credentials attached, because they
are also used for demo recordings. n8n never exports secrets, but it does export
the credential *reference* (id and display name) along with everything written in
node names, notes and sticky text. So exports are sanitised before they land here:

```
cp tools/blocklist.example.txt tools/blocklist.local.txt   # first run only
python3 tools/clean-export.py raw-export.json 0X-pattern/workflow.json
```

It strips every credential block and refuses to write the file if anything
identifying is still in it: an account name, an email address, a record id, a
private hostname. Use `--allow` for strings that are genuinely safe.

The list of names that must never appear lives in `tools/blocklist.local.txt`,
which is gitignored, and the script refuses to run without it. A blocklist
committed to a public repo would publish exactly what it is meant to protect.

## Importing

Once a folder has its `.json`:

```
n8n → Workflows → Import from file → pick the file
```

Then follow that folder's README to attach credentials and run it against the
sample data.

## Licence

MIT. Use them, change them, ship them.
