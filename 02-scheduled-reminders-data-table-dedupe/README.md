# Scheduled reminders with Data Table dedupe

_Status: documented. Workflow JSON to follow._

## What it does

Appointment reminders at 48 hours, 24 hours and 1 hour are easy to send and hard to
send *once*. A schedule that runs every fifteen minutes will happily send the same
48-hour reminder four times. This pattern uses an n8n Data Table as an idempotency
ledger: before sending, it checks whether this appointment has already had this
reminder, and only writes the ledger row after the send succeeds.

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| Schedule Trigger | Runs every 15 minutes | Interval is independent of the reminder offsets |
| Get upcoming appointments | Reads appointments in the next 49 hours | One query covers all three windows |
| Code: which window | Tags each row `48h`, `24h`, `1h` or none | Pure function, easy to unit test |
| Filter | Drops rows with no window | |
| Data Table: get row | Looks for `appointmentId + window` | The dedupe key |
| If: already sent | Skips anything already in the ledger | |
| Send reminder | Email or message to the attendee | `retryOnFail` |
| Data Table: insert row | Records `appointmentId + window + sentAt` | Written **after** the send, never before |

## Credentials you need

- Your calendar or appointments source
- A mail or messaging credential for the send step
- No credential for the Data Table; it is built into n8n

## Sample data

`sample/` holds the records the workflow runs on after import.

## Error handling

The ledger row is written only after a successful send, so a failed send is retried
on the next tick instead of being silently marked as done. The send node retries;
the ledger insert does not continue on error, because a send without a ledger row is
the one state that causes a duplicate.

## Measured result

Rebuilt from a production reminder workflow that has not double-sent since it was
switched to this pattern.
