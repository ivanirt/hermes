# CONVENTIONS — <vault-slug> literature vault

Vault root: `<absolute path>`

## What this vault is

Original study summaries of **<N>** sources by **<author>**:

- `<source-slug-1>` — *<Title>*, <publisher>, <year>. <ISBN>. <pages> pp.
- `<source-slug-2>` — *<Title>*, <publisher>, <year>. <ISBN>. <pages> pp.

<One line on how the sources relate — sequel, compilation, abridgement, same material retold.>

## HARD RULES

1. **Summarise in your own words.** Short verbatim phrases (≤ 12 words, in "quotes", attributed by page) are
   fine for key definitions. NEVER copy paragraphs or long passages. This is a study map, not a reproduction.
2. **Ground every substantive claim** with a page marker like `(p. 76)`. Page numbers refer to the PDF page
   printed in your source text as `[<abbrev> p.76]`. When several sources are in play, prefix the year:
   `(<year>, p. 76)`.
3. **Record claims as claims.** Where a source attributes a condition, disease or benefit to something, write
   "the book associates …" with the page, and stop. Never state it as fact, and never as medical advice or
   treatment guidance.
4. **No procedural instruction.** Practices (meditation, healing, energetic or advanced techniques) are described
   as *what the source says the practice is for and what its stages are* — not as steps to perform.
5. **Say what the material is.** This is an <esoteric/religious/theoretical> system, not verified science. Say so
   in the README and in the subject notes. Describe claims; do not endorse them.
6. **Every file starts with YAML frontmatter** exactly in this shape (fill in real values, keep key order):

```yaml
---
type: Chapter | <Subject> | Concept | Glossary | Index | Source | Book
title: "Human readable title"
aliases: []
source: <source-slug-1> | <source-slug-2> | both
author: <author>
book_year: <year>
pages: "40-62"
tags: [source/<vault-slug>, book/<source-slug-1>, <domain-tag>, theme/<theme>, status/draft]
concepts: [<concept-slug>, <concept-slug>]
up: "[[knowledge/<vault-slug>/MOC]]"
status: draft
generated:
  by: process:<vault-slug>-vault
  at: <YYYY-MM-DD>
---
```

Tag taxonomy — use ONLY these families (2-5 tags per note, plus the mandatory one):

- `source/<vault-slug>` (mandatory on every note)
- `book/<source-slug>` for each source, plus `book/both`
- domain tags: <list the closed set of single-word domain tags for this corpus>
- `theme/<one-of>`: <list theme tags — the *kind* of content, for cross-source slicing>
- `status/draft`

## Link convention

Root-relative wikilinks from the vault root, always with a label:

```
[[knowledge/<vault-slug>/chapters/<source-slug>/01-chapter-slug|Ch. 1 — Chapter Title]]
[[knowledge/<vault-slug>/<subject-dir>/<subject-slug>|Subject Name]]
[[knowledge/<vault-slug>/GLOSSARY|Glossary]]
```

Inside markdown tables, escape the pipe: `[[path/to/note\|Label]]`.

## Note layouts

**Chapter notes** (`chapters/<source-slug>/NN-slug.md`):

```
# <Short source name> — Ch. N: <Title>

> **Source:** <source, year, pp. X–Y> · **<Subject>:** <if any> · **Theme:** <…>

## In one paragraph
## Key claims
- **<claim>** — explanation (p. N)
## Structure of the chapter
## Correspondences (if the chapter gives a table) → markdown table
## Links
## Terms introduced → two-column table, last section
```

**Subject notes** (`<subject-dir>/<slug>.md`) — one canonical note per subject, merging every source:

```
Location / Description & appearance / <functional sections the sources use> /
Claims & associations (as the source states them) / Correspondences (table) / Links / Terms introduced
```

Name which source says what wherever they differ, rather than blending silently.

**Concept notes** (`concepts/<slug>.md`), 150–500 words: `## Definition`, `## In this system`,
`## Where it appears` (chapter links), `## Related`.

**Index notes** (`indexes/<SLUG>.md`): the generated table plus a `## Notes on the table` section explaining
how to read it, and a `## Links` block.

## The mandatory trailing table

**Every note ends with:**

```markdown
## Terms introduced

| Term | Working sense as used here |
|---|---|
| Example | The sense this chapter gives it |
```

Aim for 8–20 rows: every term the note defines or leans on. Give the original-language form in parentheses
where the source supplies one. This table is merged into the vault glossary by the parent process, so keep the
term spelled as the source spells it.

## Do not

- Do not create files outside the vault root you were given.
- Do not edit files another agent owns.
- Do not write README / MOC / MAP / GLOSSARY / TOPICS / indexes — the parent process owns those.
- Do not invent page numbers, ISBNs, or content not in the source text.
