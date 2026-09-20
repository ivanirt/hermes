# vault_verify.py — structural verification for a literature vault
#
#   python vault_verify.py --root <vault-subdir>
#   python vault_verify.py --root <vault-subdir> --links
#   python vault_verify.py --root <vault-subdir> --fix-newlines
#   python vault_verify.py --root <vault-subdir> --vault <obsidian-vault-root>
#
# Checks: frontmatter parses, mandatory tags present, pages field present, a
# '## Terms introduced' table exists on chapter/subject notes, and every
# [[wikilink]] resolves to a real .md file in the vault.
import argparse
import collections
import os
import re

NOTE_TYPES_NEEDING_TERMS = ('Chapter', 'Chakra', 'Subject', 'Appendix')


def fm_of(txt):
    fm = {}
    if txt.startswith('---'):
        end = txt.find('\n---', 3)
        for line in txt[3:end].splitlines():
            if re.match(r'^[a-z_]+:', line):
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm


def terms_count(txt):
    if '## Terms introduced' not in txt:
        return None
    tail = txt.split('## Terms introduced', 1)[1]
    rows = [l for l in tail.splitlines()
            if l.strip().startswith('|') and set(l.strip()) - set('|-: ') != set()]
    return max(0, len(rows) - 1)  # drop the header row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, help='the vault subfolder to check')
    ap.add_argument('--vault', help='Obsidian vault root for link resolution (default: --root)')
    ap.add_argument('--require-tag', default='source/',
                    help='prefix of a mandatory tag; every note must carry one matching it')
    ap.add_argument('--links', action='store_true', help='also run the broken-link check')
    ap.add_argument('--fix-newlines', action='store_true', help='add missing trailing newlines')
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    vault = os.path.abspath(a.vault or a.root)

    existing = set()
    for dirpath, _, files in os.walk(vault):
        for fn in files:
            if fn.endswith('.md'):
                rel = os.path.relpath(os.path.join(dirpath, fn), vault).replace('\\', '/')
                existing.add(rel[:-3])

    rows, problems = [], []
    breaks = collections.defaultdict(set)
    fixed = 0

    for dirpath, _, files in os.walk(root):
        for fn in sorted(files):
            if not fn.endswith('.md'):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace('\\', '/')
            txt = open(p, encoding='utf-8').read()

            if not txt.endswith('\n'):
                if a.fix_newlines:
                    open(p, 'w', encoding='utf-8', newline='\n').write(txt + '\n')
                    fixed += 1
                else:
                    problems.append((rel, 'missing trailing newline'))

            fm = fm_of(txt)
            if not fm:
                problems.append((rel, 'no frontmatter'))
            tags = fm.get('tags', '')
            if a.require_tag and a.require_tag not in tags:
                problems.append((rel, 'missing mandatory tag %r' % a.require_tag))
            if 'status/' not in tags:
                problems.append((rel, 'missing status/<x> tag'))
            if not fm.get('pages'):
                problems.append((rel, 'frontmatter has no pages field'))

            tc = terms_count(txt)
            if tc is None and fm.get('type') in NOTE_TYPES_NEEDING_TERMS:
                problems.append((rel, 'no Terms introduced table'))

            nlinks = len(re.findall(r'\[\[', txt))
            cites = (len(re.findall(r'\(p\. ?\d+', txt))
                     + len(re.findall(r'\((?:19|20)\d\d, p\. ?\d+', txt)))

            for m in re.finditer(r'\[\[([^\]]+)\]\]', txt):
                path = m.group(1).split('|')[0].split('#')[0].strip()
                path = path.replace('\\|', '|').rstrip('\\').strip()
                if path and path not in existing:
                    breaks[rel].add(path)

            rows.append((rel, fm.get('type', '-'), fm.get('source', '-'),
                         len(txt), tc if tc is not None else 0, nlinks, cites))

    print('%-58s %-9s %-26s %7s %5s %5s %5s' %
          ('file', 'type', 'source', 'bytes', 'trm', 'lnk', 'cit'))
    for r in rows:
        print('%-58s %-9s %-26s %7d %5d %5d %5d' % r)
    print('\nTOTAL files: %d   total bytes: %d' % (len(rows), sum(r[3] for r in rows)))
    if fixed:
        print('added trailing newline to %d files' % fixed)

    if a.links:
        print('\nwikilinks: %d' % sum(r[5] for r in rows))
        if breaks:
            for rel in sorted(breaks):
                print('BROKEN  %s -> %s' % (rel, sorted(breaks[rel])))
        else:
            print('NO BROKEN LINKS')

    print('\nPROBLEMS: %s' % (problems if problems else 'none'))


if __name__ == '__main__':
    main()
