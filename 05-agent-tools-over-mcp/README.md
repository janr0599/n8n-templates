# Agent tools over MCP

_Status: **published**. [`mcp-server.json`](./mcp-server.json) plus six tools in
[`tools/`](./tools). 7 workflows, 33 nodes._

## What it does

An assistant that can only talk is a demo. This exposes a set of n8n workflows as
callable tools over MCP, so any MCP-speaking client, a voice agent, a chat agent, an
IDE, can look a contact up, check a calendar and write a record.

The MCP server itself holds no logic. It is one trigger and six references. Each
tool is a separate sub-workflow you can open, run and version on its own, and a
failing tool shows up as its own execution rather than a branch buried inside a
50-node agent.

## Import

Import the six tools **first**, then the server, because the server has to point at
workflows that already exist:

```
n8n → Import from file → tools/*.json          (six files)
n8n → Import from file → mcp-server.json
```

Then open `mcp-server.json`'s six tool nodes and pick the imported workflow in each.
They ship as named placeholders (`YOUR_BOOK_EVENT_WORKFLOW_ID` and so on) because a
workflow id means nothing in someone else's instance.

| Placeholder | Where | What to put |
|---|---|---|
| `YOUR_AIRTABLE_BASE_ID` | five tools | Your base id, `app...` |
| `YOUR_LEADS_TABLE_ID` | get client details, create lead, book event | `tbl...` |
| `YOUR_COMPANIES_TABLE_ID` | create lead record | `tbl...` |
| `YOUR_MEETINGS_TABLE_ID` | get client details, book, update, delete | `tbl...` |
| `YOUR_EMAIL` | calendar id in four tools, and the record Owner | Your calendar id, which for a primary calendar is the account address |
| `YOUR_RESEND_AUDIENCE_ID` | create lead record | Your Resend audience, or delete that node |

## The tools

| Tool | Does | Notes |
|---|---|---|
| `get-client-details` | Looks the email up in Leads, then finds their scheduled meetings | 8 nodes. The one that feeds the others |
| `check-availability` | Lists calendar events between two times | Read only |
| `create-lead-record` | Creates a Lead, then a Company linked to it, then a Resend contact | Three writes in order; the Company links back to the Lead's id |
| `book-event` | Creates the calendar event, finds the Lead, writes a Meetings row | Stores the calendar event id, which is what makes the next two possible |
| `update-appointment` | Moves the event, updates the Meetings row | Matches on `Calendar Event ID` |
| `delete-appointment` | Deletes the event, marks the Meetings row Cancelled | Destructive. See below |

Each tool node carries a one-line `description`. That description is the only thing
the model reads when deciding whether to call it, so it is part of the prompt, not
documentation. Arguments are bound with `$fromAI()`, which maps the model's chosen
values onto the sub-workflow's typed inputs.

## Credentials you need

- Airtable, or whatever you swap the table nodes for
- Google Calendar
- Resend, only if you keep the contact-creation node
- An MCP-capable client to call the server

## The empty-result problem

A tool that returns nothing is indistinguishable, to a model, from a tool that
broke. It will retry, or it will invent an answer.

Both read tools handle this explicitly rather than returning an empty array:

- `get-client-details` sets `alwaysOutputData` on both Airtable searches, then
  branches. No Lead returns the sentence *"This is a new client, they don't exist in
  the CRM."* A Lead with no meetings returns its own sentence. Only the case with
  real meetings returns fields.
- `check-availability` does the same in reverse. If the calendar returns events they
  pass straight through; if it returns nothing the false branch sets *"the entire day
  is available."*

Writing the empty case as a sentence the model can read is the whole trick. It costs
one Set node per tool and removes an entire class of hallucination.

## Destructive tools take an id the model supplies

`update-appointment` and `delete-appointment` act on whatever `eventID` the model
passes. Nothing in these workflows checks that the id belongs to the caller, or that
it exists, before the calendar call runs.

In the original that is acceptable, because the id only ever reaches the model
through `get-client-details`, which returns the meetings for one looked-up email. If
you expose these tools to a client where a caller can influence the id more directly,
add the ownership check before the calendar node. It is not in here, and the template
should not pretend otherwise.

All three calendar write tools use `sendUpdates: all`, so booking, moving or
cancelling emails the attendee. That is correct in production and worth turning off
before you test.

## Error handling

`retryOnFail` is set on the Airtable reads and writes and on the Resend call, so a
rate limit or a blip is absorbed before it reaches the model. `alwaysOutputData` on
the two searches is what makes the empty-result branches above possible.

There are no error-output branches. A genuine failure surfaces to the MCP client as a
failed tool call, which is the behaviour you want: the model is told the tool failed
rather than handed an empty success.

## Measured result

Rebuilt from a production voice agent that books appointments and creates CRM records
from a phone call, with every tool call logged as its own execution.
