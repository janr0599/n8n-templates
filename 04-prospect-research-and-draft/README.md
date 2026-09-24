# Prospect research and first-touch draft

_Status: **published**. [`prospect-research-and-draft.json`](./prospect-research-and-draft.json), 16 nodes._

## What it does

Research a company from its own website, score whether it is worth contacting, and
draft a first email that refers to something real about them.

The interesting part is not the model call. It is what happens either side of it.
Before: finding the pages that actually carry people and addresses, which the
navigation often hides, with the sitemap as a fallback. After: deterministic code
re-checks the address the model picked and overrules it when it fails validation, so
a confident wrong answer never becomes a sent email.

## Import

```
n8n → Workflows → Import from file → prospect-research-and-draft.json
```

Then fill in the placeholders and attach two credentials.

| Placeholder | Where | What to put |
|---|---|---|
| `YOUR_AIRTABLE_BASE_ID` | all three Airtable nodes | The base id from its URL, `app...` |
| `YOUR_AIRTABLE_TABLE_ID` | all three Airtable nodes | The table id, `tbl...` |
| `YOUR_NAME` | Research & Draft Email | Who the email is from |
| `YOUR_COMPANY` | Research & Draft Email | Your company name |
| `YOUR_DOMAIN` | Research & Draft Email | Your website |
| `YOUR_TARGET` | Research & Draft Email | The kind of company you sell to, e.g. "dental practice" |
| `WHAT_YOU_SELL` | Research & Draft Email | One sentence on what you do for them |

### The prompt ships short on purpose

The prompt in the JSON is a skeleton: the tasks, the output contract and the hard
rules. The version this was built from is roughly twice as long, and almost all of
that extra length is negative constraints earned from real sends, things the model
did once that you never want it to do again. Those are specific to a market and to
a sender, so copying them would not help you.

Grow yours the same way: send, read what comes out, and add the constraint. The
structure here is the part that transfers.

The `Find Contact Page` node carries a note worth reading: put the words your own
market uses at the front of `teamPats`. The list ships generic (`our team`,
`leadership`, `about`); a vertical usually has a better word (`attorneys`,
`clinicians`, `agents`) and the first pattern that matches wins.

## The prospect table

Airtable in the original, but nothing here needs Airtable specifically. Any store
that can filter by a status column and update a row by id will do. The columns:

| Column | Type | Read or written |
|---|---|---|
| Company Name, Website, City, State, Focus Areas, Search Query | text | read |
| Google Rating, Reviews Count | number | read |
| Email, Contact Name | text | read, then written |
| Prospect Status | single select: `New`, `Draft Ready`, `Disqualified` | read, then written |
| Company Size | single select: `Solo`, `2-5`, `6-10`, `11-25`, `26-50`, `Unknown` | written |
| Fit Score | number | written |
| Research Notes, Personalization Hooks, Draft Subject, Draft Body | long text | written |

`Get New Prospects` pulls rows where `Prospect Status` is `New`, 20 at a time.
Rows are seeded by whatever sources prospects for you; that stage is not part of
this template.

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| Daily Draft Trigger | Runs the research pass once a day | Rate is set by how many drafts you can actually review |
| Get New Prospects | Reads rows with status `New` | `retryOnFail`, 20 per pass |
| Fetch Company Website | Pulls the home page | Retries, then continues on error |
| Fetch Sitemap | Pulls `sitemap.xml` | Retries, continues on error. Most sites 404 here and that is fine |
| Find Contact Page | Reads the home page anchors, picks the likeliest contact and team URLs, falls back to the sitemap | Pure function, no network |
| Fetch Contact Page / Fetch Team Page | Pull the two pages that carry addresses and people | Both continue on error |
| Build AI Context | Strips HTML, caps each page, harvests every email on the page | Caps are 4k home, 3k contact, 10k team |
| Research & Draft Email | One model call: fit score, size, best contact, hooks, subject, body | `retryOnFail` |
| Draft JSON Parser | Enforces the output schema | Attached as the chain's output parser |
| Prepare Update | **Re-checks the model's email, then normalises the copy** | The node that matters. See below |
| Fit Score >= 60? | Splits ready from disqualified | Threshold is a literal, change it here |
| Save Draft (Ready) | Writes the draft and sets status `Draft Ready` | `retryOnFail` |
| Save (Disqualified) | Writes the score and notes, sets status `Disqualified` | `retryOnFail`. No draft is written |

## Credentials you need

- An OpenAI-compatible model provider (GPT-5 mini in the original)
- Airtable, or whatever you swap the three Airtable nodes for

The HTTP fetches are unauthenticated: they read public pages.

## Finding the pages: anchors first, sitemap second

Scraping a home page and handing it to a model is the version everyone builds, and
it mostly returns nothing useful, because the home page rarely carries an address or
a named person. Those live on `/contact` and `/our-team`, and the link to them is
often in a hamburger menu, a footer, or rendered by JavaScript.

So `Find Contact Page` does two passes. First it reads every `<a href>` out of the
home page HTML, scores them against an ordered pattern list, and takes the first
same-origin match. If either page is still missing it parses `sitemap.xml` and
matches the same patterns against the URLs there. Only if both fail does it guess
`/contact/` and `/team/`, and even then the fetch continues on error.

## Why the email is checked in code, not by the model

The model is told the priority order and mostly gets it right. Mostly is not good
enough when the output is an email that gets sent.

`Prepare Update` runs the check again, in code:

1. Validate the model's choice. It has to look like an address and must not match
   the blocklist: `marketing@`, `pr@`, `press@`, `media@`, `devteam@`, `no-reply@`,
   anything Cloudflare-obfuscated, and the free-mail domains.
2. If it fails, ignore it and pick from the addresses actually harvested off the
   page, scored `intake@` 3, `info@ contact@ hello@ office@ admin@` 2, anything else 1.
3. If that finds nothing, fall back to the address already on the record.
4. If there is still nothing, the row saves with an empty email and a score, and a
   human decides.

At no point does the model get a second attempt. A validation failure hands the
decision to code, and code either finds something defensible or admits it did not.

The same node runs `clean()` over the subject and body: en and em dashes become
commas or the word "to", smart quotes become straight ones, runs of blank lines
collapse. The prompt already forbids dashes. The prompt being ignored is why the
function exists.

## Error handling

Every outbound fetch retries and then continues on error, because a site being down
should cost one prospect, not the pass. The model call retries but does **not**
continue on error: a failed draft should fail loudly rather than write an empty
record.

Both writes retry. Neither branch is a dead end; a disqualified prospect gets its
score and its reason written back so the pass is not repeated on it.

## Sample data

Seed the table with a handful of rows pointing at real public company sites, status
`New`, and leave everything else blank. The research pass fills the rest.

## Measured result

Rebuilt from the research stage of a six-workflow outbound system that sources,
researches, sequences and handles replies without a sales team.
