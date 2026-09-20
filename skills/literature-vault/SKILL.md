---
name: literature-vault
description: "Map source books into a linked Obsidian vault."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Obsidian, literature, book-map, glossary, wikilinks, subagents, pipeline]
    category: note-taking
    related_skills: [obsidian, pdf, grounded-citations]
---

# Literature vault — source documents into a linked Obsidian vault

Turning one or more books/documents into a browsable, cross-linked vault: metadata per source, notes per
chapter, canonical notes per subject, a vocabulary layer, a glossary, tag indexes and correspondence tables —
all wired together with wikilinks.

**This is a delegation-shaped task.** A 200-page book is ~200k characters; three books will not fit in one
context alongside the writing work. The pipeline below splits extraction, note-writing and index-building so
that no single context has to hold the whole corpus.

## When to use

Triggering requests, in the user's own vocabulary: "review the main concepts that <author> covers", "create the
md files with metadata of the source", "categorize the info and add as tags in the metadata", "create a glossary
and a list of concepts", "save them in an Obsidian-like structure and connect the concepts and files".

Also use it when the user hands you a book with no instructions beyond "file this" — the deliverable shape below
is what this user expects by default.

## Deliverable shape

Produce all of these. Anything missing is a partially-finished job:

| Layer | Contents |
|---|---|
| `sources/` | One note per source: full imprint (title, author, publisher, year, ISBN, page count, artwork/typesetting credits as printed), PDF metadata, provenance of the text, a chapter table with page ranges, and how to cite it |
| `chapters/…` | One note per chapter, **in the book's own order** — including its quirks (a book whose printed contents orders Chapter 11 between 3 and 4 keeps that order) |
| subject notes | Canonical notes, one per real-world subject, **merging every source** and naming which source says what where they differ |
| `concepts/` | The reusable vocabulary — 150–500 words each, so a term can be linked instead of re-explained |
| `GLOSSARY.md` | Hand-written core definitions **plus** a machine-merged roster of every term any note defined |
| `TOPICS.md` | The same vault sliced by tag/theme instead of by source |
| `MOC.md`, `MAP.md`, `README.md` | Hub (everything reachable), comparative map of the sources, and scope/copyright/what-this-is-not |
| `indexes/` | Correspondence/lookup tables, generated rather than hand-typed |

Every note carries YAML frontmatter with source, author, year, pages, and **tags in fixed families** — tags are
part of the deliverable, not decoration. Every note ends up reachable from `MOC.md`.

## Procedure

### 1. Find the vault, and find the house style first

Resolve the vault (a directory containing `.obsidian/`; see the `obsidian` skill — do not assume
`~/Documents/Obsidian Vault`). Search for existing sibling vaults before writing anything:

```bash
find <vault> -maxdepth 3 -name "*.md" -not -path "*/.obsidian/*" | head
```

If the user already has literature vaults, **read one and mirror its conventions** — frontmatter key order, tag
vocabulary, `generated.by: process:<name>` stamp, glossary style, cross-link phrasing. Matching the existing
house style is worth more than any improvement you could invent, and it is the fastest way to stop guessing.
Put the new vault at `<vault>/knowledge/<book-slug>/` when the vault has a `knowledge/` folder.

### 2. Inspect the source before trusting it

```bash
python <pdf-skill>/scripts/pdf_read.py "book.pdf" --meta
```

Check `encrypted`, `page_count` and `likely_scanned_pages`. Keep the PDF's own metadata (Title/Author/Creator)
for the source note. Then extract per-page text with pdfplumber into one JSON, and from that write
**page-ranged `.txt` files** carrying explicit markers:

```
--- [se p.76] ---
<page text>
```

The markers are the whole point: they survive into the children's output as `(p. 76)` citations, and one file per
chapter group keeps each child's input small instead of dumping the corpus into one context.

### 3. Map the structure before delegating

Detect chapter start pages and build the chapter → page-range table **yourself**, before spawning anyone. Also
detect front/back matter (contents, dedication, index, appendix, footnotes) and give it its own ranges. A child
that has to rediscover the chapter boundaries wastes its whole run, and a brief with wrong ranges produces
confidently wrong citations.

### 4. Write a conventions contract

Write `CONVENTIONS.md` into a scratch work directory (**not** the vault) containing the frontmatter schema, the
closed tag taxonomy, the layout for each note type, the linking convention, and the content rules. Every child
reads it first. Without it, three children emit three incompatible frontmatter shapes and the generated indexes
cannot parse them.

See `templates/conventions.md` for a known-good contract to copy and parameterise.

### 5. Fan out: one subagent per chapter group

One `delegate_task` call with all tasks; group 2–4 chapters per child. In every child's context include:

- the path to `CONVENTIONS.md`, as the first thing to read;
- the page-ranged source `.txt` files it owns, and **no others**;
- the exact page ranges it is responsible for;
- **the exact wikilink paths of every sibling file** — the other notes are being written in parallel, so a child
  cannot discover them. Give the full list of planned paths up front and it can link to notes that do not yet exist.
- the instruction to **end every note with a `## Terms introduced` two-column table** (`| Term | Working sense |`).
  This is what makes the glossary possible: the parent merges hundreds of rows programmatically instead of
  children racing to write one shared file.
- the citation format, e.g. `(p. N)`, or `(2003, p. N)` / `(2009, p. N)` when several sources are in play, so
  the two books stay distinguishable in merged notes.

Add this line to every brief: **"If the source text contradicts anything in this brief, follow the source, and
report the discrepancy in your summary."** It costs nothing and it is how you find out your own assumptions were
wrong rather than inheriting them library-wide.

### 6. Verify on disk — a child's summary is a self-report

Run a checking script over the vault after each wave: frontmatter present and parseable, the mandatory tag
present on every note, the terms table present with a sane row count, byte size, citation count.
`scripts/verify_vault.py` does exactly this. Then compare the file count on disk against the count you planned —
before announcing the vault is finished, count the files, not the tasks that reported success.

### 7. Build the glossary and indexes programmatically

Do not hand-write 400 glossary rows. Parse the markdown the children produced:

- merge every `## Terms introduced` row into one de-duplicated roster, joining multiple working senses with `·`;
- **hand-write the ~50 core definitions yourself** and put them first — the merged roster gives coverage, the
  curated table gives the system's spine. A machine-merged-only glossary reads like a word list;
- parse the per-subject correspondence tables into one master table (one row per subject, one column per
  tradition);
- generate the full roster and the tag index from frontmatter.

See `references/extraction-and-indexing.md` for the split of which script builds which file.

### 8. Re-run the builders after the last wave

Builders are idempotent and cheap: run them after every wave, and once more at the end so the generated tables
reflect the final file set. A table built when only half the notes existed shows em-dashes and looks broken.

## Content rules — put these in the contract and enforce them

1. **Summarise in your own words.** Short quoted phrases only (a key definition, ≤ ~12 words), always page-cited.
   Never reproduce passages. These are study maps, not reproductions, and the sources are in copyright.
2. **Record claims as claims.** When a book attributes conditions, diseases or benefits to something, write
   "the book associates …" with a page cite, and stop. Never convert it into fact, diagnosis or advice.
3. **Describe practice, do not teach it.** For meditation, healing or energy practices, capture the structure,
   purpose and stated stages. Do not reproduce step-by-step procedures — including the parts the book itself
   hedges (advanced/energetic practices). Those belong to the source's institutions and teachers.
4. **Say what the material is.** If the sources are esoteric, metaphysical or religious, the README and the
   subject notes state that this is a belief system being mapped, not verified science, and that the vault does
   not endorse it.
5. **Name the rights holder** in `README.md` and in each source note.

## Pitfalls

- **Write scripts to files; don't inline them.** Put multi-step Python in a `.py` file with `write_file` and run
  it with `terminal`. Heredoc-style inline scripts hit the consent guard, and a file on disk is re-runnable after
  each wave — which is exactly what step 8 requires.
- **Slug keys must match exactly.** When a lookup maps chapter files to canonical subject files, the chapter slug
  carries its ordinal prefix (`02-basic-chakra`) while the canonical slug does not (`basic-chakra`). Key the map
  by the real filename stem; keying it by a prefix-stripped version fails **silently** and yields a table of em-dashes.
- **Children label their tables freely.** The same column arrives as "Chinese medicine", "Chinese acupuncture",
  "Indian (Sanskrit)", "Tamil (Southern India)". Classify rows by keyword, never by exact label. Check the
  hit-rate afterwards and print it (`subjects with >=3 columns: N/M`) — a low count is the signal that a parser
  silently matched nothing.
- **One source of truth per column, then fall back.** When two kinds of note both carry correspondence data,
  assign each column a preferred source and use the other only to fill gaps. Concatenating both duplicates cells.
- **Strip label prefixes when merging** (`Kabbalistic sephirah · …`, `Taoist · …`) or every merged cell opens
  with a redundant label.
- **Escape pipes inside wikilinks in tables**: `[[path/to/note\|Label]]`. An unescaped pipe splits the cell and
  breaks the table.
- **Prefer root-relative wikilinks** (`[[knowledge/<slug>/concepts/prana|Prana]]`) over bare `[[Note Name]]`.
  Bare names resolve by filename anywhere in the vault and silently bind to the wrong note once two topic folders
  each contain a `README.md` or `GLOSSARY.md`.
- **Don't dump the whole book into one context.** Several medium page-ranged files beat one giant extract, and
  progress survives a timeout when each file is on disk.
- **Expect your own brief to be wrong.** Structure assumed from a title, chapter numbers assumed from a contents
  page, a "60-item list" assumed to exist — children working from the source will find these. Treat their
  reported discrepancies as corrections to record, not as noise to suppress.

## Support files

- `templates/conventions.md` — the contract handed to every note-writing subagent; copy and parameterise.
- `references/vault-layout.md` — the vault layout, frontmatter schema, tag taxonomy and per-note-type layouts.
- `references/extraction-and-indexing.md` — the scripted extraction → split → merge → verify pipeline.
- `scripts/verify_vault.py` — checks frontmatter, mandatory tag, terms table and citations across a vault.
