# Inbound email → CRM conversation, with attachments

_Status: documented. Workflow JSON to follow._

## What it does

Email about a customer lives in somebody's inbox, so nobody can see the whole
conversation in one place and attachments get re-downloaded by hand. This pattern
puts an Outlook trigger on inbound and outbound mail, matches each message to an
existing conversation record or opens a new one, matches the sender to a contact,
tells direct mail apart from forwarded mail, extracts attachments to Drive and
links them on the record, then deletes the temporary copies.

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| Outlook Trigger | Fires on a new message in the mailbox | One trigger per direction; the outbound copy reads the Sent folder |
| Set: normalise | Pulls subject, from, to, conversation id, received time into flat fields | Keeps every later node off raw Graph payloads |
| Code: strip HTML | Turns the HTML body into plain text | Removes signatures and quoted replies before storage |
| Search: find thread | Looks for a conversation record by the mail conversation id | The id is stable across replies, the subject is not |
| If: thread exists | Branches to update or create | |
| Create / Update record | Writes the message onto the conversation | Both branches converge afterwards |
| Search: match contact | Matches the counterparty address to a contact | Falls through to an unmatched queue rather than guessing |
| If: has attachments | Skips the file branch when there are none | |
| Download attachment | Pulls each attachment as binary | Runs per item |
| Upload to Drive | Stores it in a per-contact folder | |
| Update record: links | Writes the share links back onto the conversation | |
| Delete temp files | Removes the binaries from the run | Keeps execution data small |

## Credentials you need

- Microsoft Outlook (Graph) with `Mail.Read`, and `Mail.ReadWrite` if you mark messages
- A CRM or database connection for the conversation and contact tables
- Google Drive, or swap the two file nodes for your own storage

## Sample data

`sample/` holds the records the workflow runs on after import.

## Error handling

Every external call has `retryOnFail` on. The attachment branch runs with
`continueRegularOutput` so one bad file does not lose the message that carried it.
The contact match deliberately has no fuzzy fallback: an unmatched sender goes to a
queue for a person rather than onto the wrong record.

## Measured result

The production version this is rebuilt from is the highest-volume workflow on that
instance, around 214 runs on a normal weekday, replacing about five minutes of
filing per message.
