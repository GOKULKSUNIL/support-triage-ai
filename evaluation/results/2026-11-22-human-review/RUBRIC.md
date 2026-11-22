# Human review rubric

Score every reply on your own; do not compare answers with the other assessor
until both sheets are finished. Read the ticket first, then the reply. Ignore
the standard first line ("This reply was drafted automatically ...").

## sentences_<you>.csv: one row per sentence

- **cited_supports**: does the passage in `cited_passage_text` say what the
  sentence says? `Y` if it does (wording may differ), `N` if the sentence adds
  anything the passage does not say: a fact, a number, a condition, advice.
- **any_passage_supports**: only when cited_supports is `N`. Look at the other
  passages listed for the same sentence (`other_passages`). `Y` if one of them
  says it, `N` if none does. Leave blank when cited_supports is `Y`.

## replies_<you>.csv: one row per reply

- **satisfaction** (1-5): as the customer who wrote this ticket, how satisfied
  would you be with this reply?
  - 5: answers the question correctly and clearly; I could act on it without writing back
  - 4: answers the question; a small gap or awkward wording, but I probably would not write back
  - 3: partly answers; useful, but a step is missing or it is generic; I might write back
  - 2: mostly misses my question or is confusing; I would write back
  - 1: wrong, irrelevant or misleading
- **comment** (optional): one line on why, especially for 1-3.

Save the files as CSV with the same names when you finish.
