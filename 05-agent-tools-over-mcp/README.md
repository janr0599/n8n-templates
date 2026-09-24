# Agent tools over MCP

_Status: documented. Workflow JSON not yet published._

## What it does

An assistant that can only talk is a demo. This pattern exposes a set of n8n
workflows as callable tools over MCP, so any MCP-speaking client — a voice agent, a
chat agent, an IDE — can look something up, check availability and write a record,
while each tool stays a small workflow you can test and version on its own.

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| MCP Server Trigger | Publishes the tool surface and handles the protocol | One endpoint; the client discovers the tools |
| Tool: get contact details | Reads a contact by id or phone | Read-only, safe to call often |
| Tool: create lead record | Creates a record from a conversation | Validates before writing |
| Tool: check availability | Returns free slots in a window | Keep the response small; models pay for every token |
| Tool: book event | Writes the appointment | |
| Tool: update appointment | Moves or edits one | |
| Tool: delete appointment | Cancels one | Destructive, so it confirms the id exists first |

Each tool is a separate sub-workflow. The trigger exposes them; it does not
implement them.

## Credentials you need

- Whatever each tool talks to: a CRM or database, and a calendar
- An MCP-capable client to call it (a voice platform, a chat agent, or any MCP host)

## Sample data

`sample/` will hold a contacts table and an availability window so every tool
returns something on import.

## Error handling

Each tool validates its own input and returns a structured error the model can read
and recover from, rather than throwing. A tool that fails silently teaches the model
to keep calling it; one that returns "no contact with that id" gets asked a better
question next time.

## Measured result

Rebuilt from a production voice agent that books appointments and creates records
from a phone call, with every tool call logged as its own execution.
