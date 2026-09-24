# Client onboarding

_Status: **published**. [`client-onboarding.json`](./client-onboarding.json), 25 nodes._

## What it does

A row in your client table gets marked `Ready to onboard`. Fifteen minutes later the
client exists in your time tracker, the project is created with its checklist, the
Drive folder is built with the signed agreement in it, and the contact has a welcome
letter addressed to them by name.

Onboarding is the least glamorous automation anyone builds and the one that pays for
itself fastest, because it is the same twenty minutes of clicking every time and it
is always done by the person you least want doing it.

## Import

```
n8n → Workflows → Import from file → client-onboarding.json
```

| Placeholder | Where | What to put |
|---|---|---|
| `YOUR_AIRTABLE_BASE_ID` | trigger and three Airtable nodes | Your base, `app...` |
| `YOUR_CLIENTS_TABLE_ID` | same | Your clients table, `tbl...` |
| `YOUR_CLOCKIFY_WORKSPACE_ID` | four Clockify nodes | Workspace id |
| `YOUR_TEMPLATE_PROJECT_ID` | Read the task template | The project whose tasks are your checklist |
| `YOUR_CLIENTS_PARENT_FOLDER_ID` | Create the client folder | The Drive folder client folders go under |
| `YOUR_WELCOME_LETTER_TEMPLATE_ID` | Copy the welcome letter template | A Google Doc containing `[[client_name]]`, `[[contact_name]]`, `[[service_plan]]` |
| `YOUR_SENDER_NAME` | Send the welcome email | The name on the email |

The client table needs these fields: `Client Name`, `Contact Name`, `Contact Email`,
`Service Plan`, `Onboarding Status` (single select including `Ready to onboard` and
`Onboarded`), `Onboarded` (checkbox), `Signed Agreement File Id`, `Client Folder Id`,
`Time Tracker Project Id`, and a `Last Modified` field for the trigger to poll on.

Everything is read through one `Client details` node, so if your field names differ
you change them in one place rather than in fifteen.

## The shape of it

```
Client row changed (poll, 15 min) -> Ready to onboard?
  -> Client details -> Find existing client -> Client already onboarded?
        |- yes -> Reuse the existing client ------------------,
        '- no  -> Create client record -> Create tracker client-+-> Client ready
  -> Create the onboarding project -> Read the task template -> For each template task
        |- each -> Copy task onto the project -> back to the loop
        '- done -> Create the client folder -> Agreement on file?
                        |- yes -> File the signed agreement --,
                        '- no  -> Leave a placeholder instead -+-> Agreement handled
  -> Copy the welcome letter template -> Fill in the welcome letter
  -> Send the welcome email -> Mark the row onboarded
```

## Why it is safe to run twice

This is the part worth copying. Onboarding runs once per client in theory and three
times per client in practice, because someone edits the row, or a step fails halfway
and you re-trigger it.

Two things make a re-run harmless:

1. **The lookup comes before the create.** `Find existing client` searches for an
   already-onboarded client with the same email. Only the miss branch creates
   anything. The hit branch carries the existing ids forward.
2. **The status is written last.** `Mark the row onboarded` is the final node. A
   failure anywhere above it leaves the row as `Ready to onboard`, so the next poll
   picks it up and tries again. If the status were written first, a crash would
   silently skip that client forever and nobody would notice until they asked why
   they never got a welcome email.

`Find existing client` sets `alwaysOutputData` precisely because the empty case needs
its own branch. That is the one place that flag is correct.

## The checklist lives outside the workflow

`Read the task template` reads the tasks off a template project in the time tracker
and the loop copies each one onto the new client's project.

The onboarding steps are therefore data, not code. Whoever runs onboarding can add a
step by adding a task to the template project, and the next client gets it. No n8n
edit, no redeploy, no developer. That is the difference between an automation people
keep using and one that rots the first time the process changes.

## The missing agreement

Most onboarding flows assume the paperwork is signed, and fail when it is not, which
means the folder never gets created and somebody does the whole thing by hand.

`Agreement on file?` branches on whether the row carries a file id. If it does, the
agreement is copied into the client folder. If it does not, a file named
`AGREEMENT MISSING.txt` is written into the folder instead, naming the client and the
date. The rest of onboarding completes, and the gap is visible in the place someone
will actually look.

## Credentials you need

- Airtable, a personal access token with read and write on the base
- Clockify, or any time tracker with clients, projects and tasks
- Google Drive and Google Docs, same account
- Gmail

## Error handling

Every external call sets `retryOnFail`, so a rate limit or a blip is absorbed rather
than abandoning a half-onboarded client.

There are no error-output branches, and that is deliberate here. A failure should
stop the run with the row still marked `Ready to onboard`, because the retry is the
recovery. Catching the error and continuing would produce a client who is half set up
and marked done, which is the one outcome worth avoiding.

## Provenance

Built clean from the pattern, not exported from a client system. The production
version it draws on is larger and specific to one firm's document set; nothing of
that firm's process, vocabulary or structure is in this file.
