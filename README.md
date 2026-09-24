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
time, rebuilt from scratch rather than exported.

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
| 05 | [Agent tools over MCP](./05-agent-tools-over-mcp) | Expose workflows as callable tools any MCP client can use | ✅ | — |
| 06 | [Prospect research and first-touch draft](./06-prospect-research-and-draft) | Research a company, score fit, draft the email, and never let the model pick the address unchecked | ✅ | — |

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
- **No client data, ever.** These are rebuilt from scratch. Nothing here is an
  export of a client workflow, and nothing here carries a client's name, record
  ids, addresses or prompts.

## Importing

Once a folder has its `.json`:

```
n8n → Workflows → Import from file → pick the file
```

Then follow that folder's README to attach credentials and run it against the
sample data.

## Licence

MIT. Use them, change them, ship them.
