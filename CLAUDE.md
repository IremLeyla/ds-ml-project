# Project notes for Claude

## Decision log

Team decisions are recorded in `protocol.md` (table with dates). Whenever the user tells us about a team decision, a changed decision or an open question, hand it to the `decision-notetaker` agent so it is written into `protocol.md`. Mention in your reply that it was logged.

## Data

Competition data lives in `data/` and is never committed. Cleaning rules are in `cleaning.py` and are applied to train and test in the same way.
