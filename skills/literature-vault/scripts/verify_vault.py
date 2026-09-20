#!/usr/bin/env python3
"""Structural check for a literature vault.

Verifies, per note: YAML frontmatter present and parseable, the mandatory source tag present,
a '## Terms introduced' table present with a sane row count, plus byte size, wikilink count and
citation count. Read the PROBLEMS list rather than assuming it is all bad: hand-written front
matter (README, MOC, MAP, sources, indexes) legitimately has no terms table.

Usage:
    python verify_vault.py <vault-root> --tag source/my-book [--terms-section "## Terms introduced"]
"""
import argparse
import os
import re
import sys

FRONT_KEYS = ('type', 'title', 'source', 'author', 'book_year', 'tags')


def parse_frontmatter(text):
    fm = {}
    if not text.startswith('---'):
        return None
    end = text.find('\n---', 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        m = re.match(r'^([a-z_]+):(.*)$', line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


def count_terms(text, section):
    if section not in text:
        return None
    tail = text.split(section, 1)[1]
    rows = [l for l in tail.splitlines()
            if l.strip().startswith('|') and not set(l.strip()) <= set('|-: ')]
    rows = [r for r in rows if r.strip('| ').split('|')[0].strip().lower() != 'term']
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--tag', required=True, help='mandatory tag every note must carry')
    ap.add_argument('--terms-section', default='## Terms introduced')
    ap.add_argument('--min-terms', type=int, default=5)
    ap.add_argument('--quiet', action='store_true', help='only print problems and totals')
    args = ap.parse_args()

    rows, problems, total_terms = [], [], 0
    for dirpath, _, filenames in os.walk(args.root):
        for fn in sorted(filenames):
            if not fn.endswith('.md'):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, args.root).replace('\\', '/')
            with open(path, encoding='utf-8') as fh:
                text = fh.read()

            fm = parse_frontmatter(text)
            if fm is None:
                problems.append((rel, 'no frontmatter'))
                fm = {}
            else:
                for k in FRONT_KEYS:
                    if k not in fm:
                        problems.append((rel, 'frontmatter missing %s' % k))
                if args.tag not in fm.get('tags', ''):
                    problems.append((rel, 'missing mandatory tag %s' % args.tag))

            nterms = count_terms(text, args.terms_section)
            if nterms is None:
                problems.append((rel, 'no %s table' % args.terms_section.strip('# ')))
            elif nterms < 1:
                problems.append((rel, 'terms table header only'))
            elif nterms < args.min_terms:
                problems.append((rel, 'terms table thin (%d rows)' % nterms))
            else:
                total_terms += nterms

            links = len(re.findall(r'\[\[', text))
            cites = len(re.findall(r'\(p\. ?\d+', text)) + len(
                re.findall(r'\(\d{4}, p\. ?\d+', text))
            rows.append((rel, fm.get('type', '-'), fm.get('source', '-'),
                         len(text), nterms if nterms is not None else 0, links, cites))

    if not args.quiet:
        print('%-58s %-9s %-22s %7s %5s %5s %5s'
              % ('file', 'type', 'source', 'bytes', 'trm', 'lnk', 'cit'))
        for r in rows:
            print('%-58s %-9s %-22s %7d %5d %5d %5d' % r)

    print('\nnotes: %d | bytes: %d | terms rows: %d'
          % (len(rows), sum(r[3] for r in rows), total_terms))
    if problems:
        print('\nPROBLEMS:')
        for rel, what in problems:
            print('  %-58s %s' % (rel, what))
    else:
        print('PROBLEMS: none')

    uncited = [r[0] for r in rows if r[6] == 0 and r[1] in ('Chapter', 'Chakra', 'Concept')]
    if uncited:
        print('\nnotes with no page citations (expected for front matter only):')
        for rel in uncited:
            print('  ' + rel)
    return 0


if __name__ == '__main__':
    sys.exit(main())
