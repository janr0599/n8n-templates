# Chat intake agent with human handoff

_Status: documented. Workflow JSON to follow._

## What it does

A chat agent that qualifies and books is useful; one that cannot get out of the way
is a liability. This pattern is an agent with conversation memory and its own tools,
wrapped in two things most demos leave out: a buffer so a burst of short messages
becomes one turn, and a classifier that notices a request for a person and switches
the bot off for that conversation.

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| Webhook | Receives the inbound message | One endpoint per channel, or a channel field |
| Switch: message type | Routes text, audio and image | |
| Transcribe audio | Voice note to text | Only on the audio branch |
| Describe image | Image to a text description | Only on the image branch |
| Redis: buffer | Appends the message, waits briefly for more | Turns three quick messages into one turn |
| If: bot enabled | Reads the per-conversation bot flag | The handoff switch |
| AI Agent | Answers, calls tools, keeps memory | Buffer-window memory keyed by conversation |
| — Tools | Look up contact, create lead, check availability, book | Each is a sub-workflow with its own validation |
| Output parser | Forces the reply into a schema | Auto-fixing parser catches malformed output |
| Text Classifier | Decides whether a person is being asked for | Runs on the user's message, not the reply |
| Set bot flag off | Disables the bot for that conversation | |
| Notify the team | Posts the thread where a person will see it | |
| Send reply | Returns the message to the channel | |

## Credentials you need

- A model provider for the agent, the transcription and the classifier
- Redis for the buffer
- Your CRM or database for the tools
- The channel API you are answering on

## Sample data

`sample/` holds the records the workflow runs on after import.

## Error handling

The agent path runs with `continueRegularOutput` so a tool failure returns a
graceful reply rather than a dead conversation. The classifier runs on every inbound
message, not only the first, because people ask for a human halfway through. If the
model returns unparseable output twice, the conversation is handed to a person.

## Measured result

Rebuilt from a production intake agent that handles first contact in three languages
with twenty turns of memory per conversation.
