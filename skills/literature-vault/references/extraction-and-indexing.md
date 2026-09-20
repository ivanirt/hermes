# Extraction, splitting, merging and verifying

Scripted pipeline. Everything runs from a scratch work dir (never the vault), invoked with `terminal`,
re-runnable after every wave.

```
<work>/
  split.py               source PDF/EPUB -> page-ranged .txt with page markers
  CONVENTIONS.md         the child contract
  extract_terms.py       vault notes -> merged term JSON
  build_indexes.py       glossary roster + index tables + full list
  build_topics.py        tag index
  verify.py              per-note structural check
```

## 1. Extract and split

One per-page JSON per source, then one `.txt` per chapter group with explicit page markers:

```python
import pdfplumber, json
out = []
with pdfplumber.open(src) as pdf:
    for i, p in enumerate(pdf.pages, 1):
        out.append({'page': i, 'text': p.extract_text() or ''})
with open(dest, 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False)
```

Before this, run the `pdf` skill's `pdf_read.py --meta` and check `encrypted` and `likely_scanned_pages`. Report
empty extracted text as *scanned, needs OCR* — never as "no content".

Then a `RANGES` table drives the split, emitting `--- [<abbrev> p.N] ---` before each non-empty page. Print the
byte size of every file: a suspiciously small one means the range is wrong.

## 2. Structure detection

Find chapter starts by regexing the extracted text for heading shapes and near-start-of-page positions:

- explicit markers (`CHAPTER 7`, `Chapter VII`) at the start of a page;
- running-head repeats at the top of many pages — these give reliable page ranges for the *body*, not the start;
- the printed contents page(s) give titles and count, and must be cross-checked against the body (they can be
  out of numeric order, miss a chapter, or list figures rather than chapters — figure captions appear on their own
  pages and will fool a naive detector).

Build the chapter → range table by hand from that output before spawning anyone, and print it for the record.

## 3. Merge the terms tables into a glossary roster

For each note: take everything after `## Terms introduced`, keep lines starting `|`, drop separator and header rows,
normalise the term (lowercase, collapse whitespace, strip emphasis markers) and accumulate:

- `senses` — a list, deduped, order preserved; join with `·` on output (a term defined in several chapters has
  several working senses, and all of them are worth showing);
- `where` — the notes that defined it, as wikilinks.

Exclude the terms already in the hand-written core table (parse the bolded term from each core row, and split
`Foo / Bar` and `Foo · Bar` cells into separate keys). Report `unique terms`, `roster size` and `core size` —
if `roster` is 0, the section heading or the table shape changed.

## 4. Merge correspondence tables into one index

The same data arrives in two shapes, and they have different strengths:

| Shape | Where | Strength |
|---|---|---|
| one row, N columns (`Kabbalistic \| Taoist \| Indian \| Acupuncture`) | canonical subject notes | the doctrine column |
| N rows, 2 columns (`Aspect \| Correspondence`) | chapter notes | cleanly separated tradition columns |

Parse both into separate stores, then assign **one preferred source per column** and fall back to the other only
for gaps. Do not concatenate both stores into the same cell — you get every value twice with page cites attached.

Classify 2-column rows by **keyword**, because children label freely:

```python
def classify(label):
    l = label.lower()
    if 'tamil' in l: return 'tamil'                      # before 'indian'
    if 'taoist' in l or 'chinese yoga' in l: return 'taoist'
    if 'acupun' in l or 'chinese' in l or 'medicine' in l: return 'acupuncture'
    if 'sanskrit' in l or 'indian' in l: return 'sanskrit'
    if 'kabbal' in l or 'sephir' in l: return 'kabbalah'
    return None
```

Then strip leaked label prefixes from merged cells (`^<label>\s*·\s*`) in a loop until stable, and print a
coverage line such as `subjects with >=3 columns: 12/12`. That line is the only cheap signal that the parser
matched something.

Two failures to expect here, both silent: a **slug-key mismatch** between chapter files (`02-subject`) and
canonical files (`subject`), and an **em-dash row** where a parser matched nothing. Both look like "the sources
did not give this", so verify coverage before trusting an empty cell.

## 5. Generate the rest

- **Full list** — every note, grouped by layer, in reading order (a fixed order table, not filesystem order),
  with counts per layer and a total. The total is asserted in the note, so recompute it from disk each run.
- **Tag index** — group by tag family. Do **not** expand the admin tags (`source/…`, `status/…`): listing all N
  notes under "status/draft" triples the file size and helps nobody. Give those as counts on one line.
- **Themes** — hand-write a short "through-lines" table linking the ideas that run across the whole corpus.

## 6. Verify

`scripts/verify_vault.py` checks, per note: frontmatter present and parseable, mandatory tag, terms table present
with row count, byte size, wikilink count, citation count. It prints the notes without a terms table as
`PROBLEMS` — the hand-written front matter (README, MOC, MAP, indexes, sources) is expected to be on that list, so
read the list rather than assuming it is all bad.

Then reconcile counts: planned notes vs `find <vault> -name '*.md' | wc -l`. Announce the vault as complete only
when the counts match, and state the real numbers in the reply.
