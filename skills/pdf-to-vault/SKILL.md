---
name: pdf-to-vault
version: 1.0.0
author: Hermes Agent
description: "Turn source PDFs or books into a linked Obsidian vault."
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [obsidian, pdf, literature-vault, glossary, wikilinks, delegation]
    category: note-taking
    related_skills: [obsidian, pdf, literature-vault]
---

# PDF books → Obsidian literature vault

Turn one or more source books (PDF/EPUB) into a navigable Obsidian vault: per-chapter notes cited to page
numbers, per-subject canonical notes, a merged glossary, correspondence tables, and a hub that links it all.

## When to use

- "Review the main concepts in these books, create md files with metadata of the source, categorise the info
  and add it as tags, create a glossary and a list of concepts, save them in an Obsidian structure and connect
  the concepts and files."
- Any 2+ book mapping exercise where the deliverable is a vault, not a summary.

## Resolve the vault path FIRST (never assume)

File tools do not expand shell variables. Get a concrete absolute path before writing anything:

1. `${HERMES_HOME:-~/.hermes}/.env` → `OBSIDIAN_VAULT_PATH` (Windows: `~/AppData/Local/hermes/.env`).
2. If empty, look for an existing vault: `search_files(target='files', pattern='.obsidian')` under the home dir.
3. If still nothing, use `~/Documents/Obsidian Vault`.
4. **Ask the user rather than guessing** if more than one candidate exists — writing into the wrong vault is the
   one mistake that is expensive to undo.

When you do establish the path, append `OBSIDIAN_VAULT_PATH=<path>` to that `.env` so later sessions stop
asking. Edit `.env` with `write_file`, **never `printf`/`echo`** — `\U`/`\a` in a Windows path are read as
escape sequences and silently corrupt the value (observed: `C:\Users\ivani...` became
`C:\Users\ivani\u0007i_local...`).

## The house convention beats your instinct

**Check for an existing literature vault in the target vault before designing anything.**
`search_files(pattern='*.md', target='files', path=<vault>)` and look for a sibling folder of the same kind
(e.g. `knowledge/<book-slug>/`). If one exists, READ its `README.md` plus one chapter note and one concept note,
and mirror its frontmatter keys, tag families, folder names and link style. Consistency with what the user
already has is worth more than your preferred schema.

## Procedure

### 1. Inspect the PDFs before extracting

```bash
python <pdf-skill>/scripts/pdf_read.py book.pdf --meta
```

Check `encrypted` (decrypt first) and `likely_scanned_pages`. Empty `extract_text()` plus page images means
there is no text layer → route to the pdf skill's `references/ocr-extraction.md`. **Do not fabricate text.**

### 2. Extract to page-marked text, one file per chapter

Do NOT hand a whole book to a subagent. Dump it to a scratch work dir (**outside** the vault) as plain `.txt`
with an explicit marker before every page:

```
--- [se p.76] ---
<page text>
```

The marker is what makes citation possible — instruct every writer to cite `(p. 76)`. Per-chapter files keep
each subagent's input small and let you re-dispatch one chapter without redoing the book.

Find chapter page ranges by searching the extracted text for the chapter-title strings from the printed TOC.
**Verify the TOC against the body**: printed contents pages lie (a real case listed Chapter Eleven between
Three and Four — a printing quirk to preserve, not to "fix").

### 3. Write CONVENTIONS.md in the work dir — the highest-leverage step

Every subagent reads it. It must specify, with a copy-pasteable example:

- **Frontmatter schema** with exact key order: `type, title, aliases, source, author, book_year, isbn, pages,
  tags, concepts, up, status, generated`. Use `pages: "2009: 77-92; 2003: 107-115"` when a note merges two books.
- **A closed tag taxonomy** (4-6 families). Open-ended tagging produces an unusable tag pane. Families that
  work: `source/<work>` (mandatory), `book/<title>`, bare domain tags (`kabbalah`, `taoism`), `theme/<kind>`,
  `status/draft`.
- **Per-note-type layouts**, named section by section. Mirror the source book's own headings when it has a
  template — one book used a fixed 8-heading per-chapter template that mapped 1:1 onto the note layout.
- **The citation form** and the exact page-marker format.
- **HARD RULES** — see the content-safety section below.
- **The full list of link targets** that will exist (paths + slugs), so siblings can link to each other before
  any of them are written.
- **A required trailing `## Terms introduced` table** with exactly two columns:
  `| Term | Working sense as used here |`. This single requirement is what makes the glossary possible later:
  the merge is mechanical if every note ships a terms table, and impossible otherwise.

### 4. Delegate in two waves, batching 2-4 chapters per task

10 parallel subagents is the practical ceiling. Split by page range so no child sees more than ~30k chars.

- **Wave 1** — chapter notes (one task per 2-4 chapters of one book), plus canonical notes for the first part
  of the book's subject axis.
- **Wave 2** — canonical notes for the rest, plus concept notes (10-14 per task, grouped by theme).

Each task's context must contain: the CONVENTIONS.md path, its source `.txt` paths, exact output paths, the
book's bibliographic line, the link-target list, and the page-marker format. Repeat shared background in every
single task — children share no context. Ask for a small `output_schema` (`files`, `glossary_terms`, `notes`)
so the return is machine-readable.

### 5. Author the hub, sources and glossary core YOURSELF

Subagents write chapter/subject/concept notes. You write the notes that require whole-book judgement:
`README.md`, `MOC.md`, `MAP.md` (comparative map + chapter-interleave table + "where the books disagree"), the
bibliographic `sources/<book>.md` notes, the master correspondence table, and the **curated core of the
glossary** (the ~50 terms that carry the system, hand-written, each linking to the note that develops it).

This split is deliberate: a child cannot see the seams between chapters, and the seams are the most valuable
content in the vault.

### 6. Generate the mechanical indexes with scripts

Run the shipped scripts after each wave — `scripts/build_glossary.py`, `scripts/build_indexes.py`,
`scripts/vault_verify.py` (all three take `--root`; pass `--link-prefix knowledge/<slug>/` so generated
links resolve from the Obsidian vault root):

- **Glossary** — merge every note's terms table, de-duplicate on a normalised key, join differing senses with
  ` · `, and list which notes define each term. Append under the hand-written core.
- **Cross-reference index** — keyword-classify each row of each note's correspondence table
  (`'tamil' in label → tamil`; test `'tamil'` BEFORE `'indian'`, since "Tamil (Southern India)" contains both).
  Label variants differ between notes — classify, never match exact strings.
- **Rosters** (`FULL-LIST`, tag/theme index) — parse frontmatter and emit lists, with counts computed in Python
  and printed, so you can check the total against what was asked.

When the same table exists in two forms across note types (one book's chapter gives `Aspect | Correspondence`
rows; the merged subject note gives a single wide row), prefer the clean per-row source for its columns and the
merged note for what only it has, rather than concatenating both and doubling the text.

### 7. Verify — the gates

1. `vault_verify.py` → every note parses frontmatter, carries the mandatory tags, and (for chapter/subject
   notes) ships a terms table. Target: `PROBLEMS: none`.
2. Broken-link check → **0 unresolved**. Do not ship a vault with dangling wikilinks.
3. Cross-check the collected count against the plan (notes asked for vs notes on disk).
4. Spot-read at least one note written by each subagent. Self-reports are claims, not evidence.

## Pitfalls (all observed in practice)

- **A subagent returning `status=unknown` may still have written its files.** "Delegation owner exited before
  recording a terminal result" means the outcome is unknown — **check the filesystem**, then finish the missing
  files yourself. In one run, 2 of 10 tasks reported nothing and had in fact written everything except the last
  2 deliverables of a 12-item batch.
- **Children will catch YOUR errors if you tell them to prefer the source over your brief.** Say so explicitly:
  "If the brief conflicts with the source text, follow the source text and flag the discrepancy." Two brief
  errors in one run (a wrong subject↔body mapping, a non-existent numbered list) were caught and reported this
  way instead of being written into the vault as fact.
- **Missing trailing newline.** `patch` on a final line drops it, and some writers omit it. Normalise before
  finishing (`vault_verify.py --fix-newlines`). Harmless in Obsidian, but it makes every later diff noisy.
- **Wikilinks inside markdown tables.** `[[note|alias]]` works in Obsidian (wikilinks are parsed before tables),
  but a link checker that splits on `|` must strip the `\|` escape first or it reports hundreds of false broken
  links. Match whatever convention the vault already uses.
- **Don't let a child write `README`/`MOC`/`GLOSSARY`.** They collide with each other and with you. Assign index
  files to exactly one owner and state "do not create these" in every child's context.
- **Two books ≠ one book twice.** When a later compilation reprints an earlier book minus a layer (real case:
  a 2009 compilation described itself as the 2003 original "without the Kabbalistic part"), the canonical
  subject notes must merge the two and name which book says what, rather than blending silently.
- **Regenerating an index overwrites hand-fixes.** If you patch a generated file's frontmatter, patch the
  generator's template too, or the next run silently reverts it.
- **A note that merely *mentions* a marker string gets parsed as a source.** Write the detection as a
  line-anchored regex (`(?m)^##\s+Terms introduced\s*$`) and skip the file you are writing
  (`if rel == out: continue`). Otherwise a sentence in the README that quotes the heading makes the
  generator read its own prose as data — this produced 26 phantom terms and a self-referential glossary.
- **Term labels arrive already bolded.** Notes commonly write `| **Prana** | ... |`. Strip existing emphasis
  before re-wrapping, or rows render as `****Prana****` and — worse — every label starts with `*`, so the
  whole A–Z grouping collapses into one `#` bucket. Same for the letter grouping: take the first *alphanumeric*
  character, not `label[0]`.
- **Never match table labels by exact string.** Child notes invent their own labels for the same idea
  ("Chinese medicine", "Chinese acupuncture (equivalent point)", "Acupunct"). Classify by keyword, and order
  the tests so the most specific wins ('tamil' before 'indian').

## Content-safety rules to put in CONVENTIONS.md

Set these whenever the source is esoteric, medical, legal or practice-oriented. They keep the vault a study map
instead of a reproduction or an instruction manual:

1. **Summarise in your own words.** Short quotes ≤ 12 words with a page citation are fine. Never copy paragraphs.
   The vault is a map, not an edition.
2. **Cite every substantive claim** with a page marker.
3. **Health claims are recorded as the book's claims** — "The book associates X with Y" — never as fact,
   diagnosis or treatment guidance. State that nothing here is medical advice.
4. **Practice is described, not taught.** Capture structure, purpose and named stages; do not reproduce
   step-by-step procedures, rituals or recitation texts, especially anything a reader could attempt unguided.
5. **Say what the system is.** One line in README, MOC and every subject note: an esoteric/metaphysical system,
   not verified science; described as the author presents it, not endorsed.
6. **Attribute and disclaim.** Publisher of record, ISBN, artwork credits, and that copyright stays with the
   rights holder.

## Verification

All three scripts take `--root <vault-subdir>`; add `--vault <obsidian-vault-root>` so link resolution works
when the literature vault is a subfolder of a bigger vault.

- `python scripts/vault_verify.py --root <sub> --vault <root>` → `PROBLEMS: none`, printing a per-file table of
  type / source / bytes / terms-table rows / wikilinks / citations.
- `python scripts/vault_verify.py --root <sub> --vault <root> --links` → `NO BROKEN LINKS`. **This is the
gate that matters** — dangling wikilinks are the one defect a reader notices immediately.
- `python scripts/build_glossary.py --root <sub> --core <hand-written-core.md> --link-prefix <prefix>/` → writes
  GLOSSARY.md and prints `unique terms / roster / core`; sanity-check that zero terms silently vanished.
- `python scripts/build_indexes.py --root <sub> --link-prefix <prefix>/ --outdir indexes` → prints
  `N notes, M columns` for the cross-reference. **Watch M**: if it is anywhere near N you have fallen into a
  column-per-label trap and the table is unusable — tighten the classifier.
- Then read the cross-reference and roster yourself and *curate*: they are raw material for the hand-written
  MOC/MAP/glossary-core, not a finished product. `--topics` is opt-in for this reason.
- Open the folder in Obsidian and confirm the graph is connected (every note reachable from MOC).
- Finally, spot-read one note from each subagent. A `PROBLEMS: none` run proves the *shape* is right, never that
  the *content* is. Three of the most valuable findings in one real run (a printed-TOC quirk, a wrong mapping in
  my own brief, and two internal contradictions in the source book) were only visible by reading.
