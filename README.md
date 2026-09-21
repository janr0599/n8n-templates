# n8n templates

Production patterns rebuilt clean and generic, with the error handling left in. Each folder has the workflow JSON, a canvas screenshot, sample data, and a README that says what every node does and where to plug in your own credentials.

Built by [Javier Noguera Rodríguez](https://janr0599.github.io) · automation and AI engineer.

| # | Pattern | What it solves | Status |
|---|---|---|---|
| 01 | [Inbound email → CRM conversation, with attachments](./01-inbound-email-to-crm-thread) | Every email threaded onto the right contact, attachments filed and linked | in progress |
| 02 | [Scheduled reminders with Data Table dedupe](./02-scheduled-reminders-data-table-dedupe) | 48 / 24 / 1 h reminders that never double-send | in progress |
| 03 | [Chat intake agent with human handoff](./03-chat-intake-agent-human-handoff) | Agent, memory, message buffering, tools, and a classifier that hands off to a person | in progress |

## Conventions

- **No credentials in the JSON.** Every credential node is left empty; the README lists what to create.
- **Retries and error branches are part of the template**, not an exercise for the reader. `retryOnFail` on every external call, `continueRegularOutput` where one failure shouldn't stop the batch.
- **Sample data included** so the workflow runs end to end on import before you connect anything real.
- **No client data, ever.** These are rebuilt from scratch; nothing here is an export of a client workflow.

## Importing

n8n → Workflows → Import from file → pick the `.json`. Then follow the folder's README to attach credentials and run it against the sample data.
