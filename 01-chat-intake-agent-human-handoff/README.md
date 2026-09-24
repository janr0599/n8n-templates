# Chat intake agent with human handoff

_Status: **published**. [`chat-agent.json`](./chat-agent.json) (55 nodes) and
[`notify-human-and-pause-bot.json`](./notify-human-and-pause-bot.json) (4 nodes)._

## What it does

A chat agent on Chatwoot that qualifies a visitor, writes them into a CRM, books a
call, and gets out of the way when a person is needed. It handles text, voice notes
and images on the same webhook.

Most published chat-agent templates are a trigger, an agent and a reply. The parts
worth copying here are the ones around that: a buffer so three quick messages become
one turn instead of three, staggered replies with a typing delay, guardrails on both
sides of the model, and three separate routes to a human.

## Import

Import [template 03](../03-agent-tools-over-mcp) first. This agent calls its six
sub-workflows as tools, and they have to exist before you can point at them.

```
n8n → Import from file → ../03-agent-tools-over-mcp/tools/*.json
n8n → Import from file → notify-human-and-pause-bot.json
n8n → Import from file → chat-agent.json
```

Then open the seven sub-workflow nodes in `chat-agent.json` and select the imported
workflow in each: `get_client_details`, `create_lead_record`, `check_availability`,
`book_event`, `update_appointment`, `delete_appointment`, and the three
`Call 'Send Human Notification & Turn Bot Off'` nodes, which all point at the same
handoff workflow.

| Placeholder | Where | What to put |
|---|---|---|
| `YOUR_CHATWOOT_HOST` | `Send Message`, `update_chatwoot_contact`, handoff | Your Chatwoot host |
| `YOUR_PINECONE_INDEX` / `YOUR_PINECONE_NAMESPACE` | Pinecone Vector Store | The index holding your knowledge base |
| `YOUR_NOTIFICATION_EMAIL` / `YOUR_SENDER_NAME` | handoff | Where a handoff lands, and who it is from |
| `YOUR_ASSISTANT_NAME`, `YOUR_COMPANY`, `YOUR_TARGET_ROLES`, `WHAT_YOU_DO`, `YOUR_BOOKING_LINK`, `YOUR_TIMEZONE` | AI Agent system message | See below |
| `*_WORKFLOW_ID` | the seven sub-workflow nodes | Selected in the UI, not typed |

Point a Chatwoot webhook at the `Webhook` node's production URL.

## The shape of it

```
Webhook -> If (real inbound message?) -> data_extraction -> Message Type
                                                              |- audio -> download -> transcribe -,
                                                              |- image -> download -> describe ----+-> Buffer
                                                              '- text  --------------------------- '
Buffer (Redis) -> Get_buffer_data -> Switch -> Ignore / Wait 30s and re-read / Continue
Continue -> Delete_buffer -> Set Variables -> Input Guardrails
                                                |- pass -> AI Agent -> Output Guardrails
                                                '- trip -> handoff                 |- pass -> strip dashes -> Split into Parts
                                                                                   '- trip -> handoff
Split into Parts -> Create List of Messages -> Loop -> Calculate Delay -> Wait -> Send Message
                                                 '- done -> Human Needed? -> YES -> handoff
```

## The message buffer

Three nodes and a Wait, and it is the difference between an agent that feels human
and one that argues with itself.

People send chat messages in bursts: "hi", "quick question", "do you do X?". Naively
each one is a webhook, so the agent answers three times, and the second answer
arrives before the user finished the thought.

Every inbound message is pushed onto a Redis list keyed by conversation, then
`Get_buffer_data` reads the whole list and the `Switch` decides:

- **Ignore** when the first buffered message belongs to a different session
- **Continue** when the first message is older than 15 seconds, meaning the burst is over
- **Wait** otherwise: sleep 30 seconds and re-read the buffer

Only the Continue branch deletes the buffer and joins the messages into one prompt.
So a burst becomes one turn, and the agent answers the whole thought.

The `If` at the top is the other half of not talking over people. It only proceeds
on `message_created`, only when the sender is a `Contact` rather than an agent, and
only when the contact's `bot_status` is not `OFF`. That last one is what makes the
handoff stick: once a human takes over, the bot stays quiet.

## Staggered replies

The model writes one answer. `Split into Parts` breaks it into up to five
conversational chunks, `Calculate Delay` picks a delay from the length of each chunk,
5 to 7 seconds for something short and 12 to 15 for a paragraph, and the loop sends
them one at a time. The result reads like someone typing rather than a wall of text.

`Strip Out Em Dashes` runs before the split, because the model produces them whatever
the prompt says.

## Guardrails on both sides

- **Input:** jailbreak detection at 0.8, PII detection for card numbers, bank and
  passport and SSN and similar, plus secret keys. A trip routes to the handoff
  instead of the agent, so the model never sees it.
- **Output:** NSFW at 0.8 and secret keys. A trip routes to the handoff instead of
  the visitor, so the message is never sent.

Both failure paths land on the same handoff workflow with a different opening line,
so a person sees what happened and the bot is already off.

## Three routes to a human

1. Input guardrail trips. The visitor sent something sensitive.
2. Output guardrail trips. The agent tried to send something it should not.
3. The visitor asks. After the replies are sent, `Human Needed?` classifies the turn
   with a one-line prompt that must answer exactly YES or NO, and YES calls the handoff.

The handoff workflow emails a person, marks that email unread so it stays visible,
then PUTs `bot_status: OFF` onto the Chatwoot contact. The `If` at the top of the
agent reads that flag, so the bot stops replying in that conversation.

## Credentials you need

OpenAI (chat, transcription, vision, embeddings, both guardrail models), Postgres
for chat memory, Redis for the buffer, Pinecone for the knowledge base, Chatwoot
header auth, Gmail for the handoff email. Plus whatever template 03's tools need.

## The system prompt ships generalised

The persona, the market and the offer are placeholders. Two things were removed
rather than placeholdered: the booking link and the pricing script. The original told
the agent what an audit costs, which is a sentence you want to write yourself before a
model says it to a stranger. The objection section is left as a stub for you to fill.

The operational half is intact, because that is the part worth copying: collect name,
email, company and bottleneck before calling any tool; look the contact up before
creating them; confirm the timezone before checking availability; fetch the event id
via `get_client_details` before rescheduling or cancelling. That ordering is what
stops an agent double-creating records and booking into the past.

One small note: `create_lead_record` in template 03 also accepts a `prospectId`,
which links a new lead back to a cold-outreach prospect row. The chat agent does not
send it, and the sub-workflow handles its absence.

## Error handling

The two downloads and the Chatwoot send retry. The buffer and memory nodes do not,
because a Redis or Postgres failure should stop the turn rather than produce a reply
built on half the conversation.

There are no error-output branches. A genuine failure fails the execution, which is
the right outcome for a conversation: no reply is better than a confident wrong one,
and the visitor sees silence rather than an error string.

## Measured result

Rebuilt from a production agent running on Chatwoot across web chat and social
channels, handling qualification and booking end to end, with a person pulled in only
when the guardrails trip or the visitor asks.
