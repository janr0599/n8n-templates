# Prospect research and first-touch draft

_Status: documented. Workflow JSON not yet published._

## What it does

Research a company from its website, decide whether it is worth contacting, and
draft a first email that refers to something real about them. The pattern's point is
the part after the model: code checks the model's choice of contact address and
overrules it when it fails validation, so a confident wrong answer never becomes a
sent email.

## Nodes, in order

| Node | Does | Notes |
|---|---|---|
| Schedule Trigger | Runs the research pass daily | Rate is set by how many prospects you can act on |
| Get new prospects | Reads unresearched rows | `retryOnFail` |
| Fetch site | Pulls the home page | `retryOnFail`, `continueRegularOutput` |
| Find contact page | Picks likely contact and team URLs from the anchors | Pure function |
| Fetch sitemap | Falls back to `sitemap.xml` when the navigation hides them | The fallback that makes this work on real sites |
| Fetch contact page / team page | Pulls the pages that actually carry people and addresses | Both continue on error |
| Build context | Strips HTML and assembles one compact prompt input | Keeps the token bill predictable |
| Research and draft | One model call: fit score, best contact, personalisation hooks, draft email | Structured output parser enforces the schema |
| Verify the address | Code validates the model's pick, falls back to a priority list, blocks generic and no-reply inboxes | **The node that matters** |
| If: fit score over threshold | Splits ready drafts from disqualified | |
| Save draft / Save disqualified | Writes the outcome and the reason back | `retryOnFail` |

## Credentials you need

- A model provider
- A CRM or database for the prospect table
- Optionally a scraping source for finding prospects in the first place

## Sample data

`sample/` will hold a handful of prospect rows pointing at real public sites so the
research pass has something to read.

## Error handling

Every outbound fetch retries and continues on error, because a site being down
should cost one prospect, not the run. The model call retries once. The address
verification has no model fallback by design: if validation fails, deterministic
code decides, and if that finds nothing usable the row is disqualified with a reason
rather than guessed at.

## Measured result

Rebuilt from the research stage of a six-workflow outbound system that sources,
researches, sequences and handles replies without a sales team.
