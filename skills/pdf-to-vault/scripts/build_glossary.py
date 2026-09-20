# build_glossary.py — merge every note's '## Terms introduced' table into one glossary
#
#   python build_glossary.py --root <vault-subdir> --core <core.md> [--out GLOSSARY.md]
#
# The vault builds itself a glossary by requiring every note to end with a
# two-column '## Terms introduced' table. This merges them:
#   * normalises the term key (case, whitespace, emphasis) for de-duplication
#   * joins senses defined in different notes with ' · '
#   * lists which notes define each term
#   * omits terms already covered by the hand-written --core section
#   * groups the roster by initial letter
#
# --core is a markdown file whose core table rows start with '| **Term**';
# those terms are parsed out and excluded from the roster.
import argparse
import collections
import os
import re


def norm(t):
    t = re.sub(r'\s+', ' ', t.strip().lower())
    return t.strip('*_` ')


def clean_label(s):
    """Strip the source table's own emphasis/quotes so the label is plain text.

    Notes commonly write terms already bolded (| **Prana** | ...). Without this the
    emitted row becomes ****Prana**** and, worse, every label starts with '*' so the
    A-Z grouping collapses into a single '#' bucket.
    """
    s = s.strip()
    s = re.sub(r'^[*_`\s]+', '', s)
    s = re.sub(r'[*_`\s]+$', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def initial(label):
    """First alphanumeric character, for A-Z grouping (skips quotes/brackets)."""
    m = re.search(r'[A-Za-z0-9]', label)
    L = m.group(0).upper() if m else '#'
    return L if L.isalpha() else '#'


TERMS_HEADING = re.compile(r'(?m)^##\s+Terms introduced\s*$')


def core_terms(core_txt):
    out = set()
    for line in core_txt.splitlines():
        if line.startswith('| **'):
            m = re.match(r'\|\s*\*\*(.+?)\*\*', line)
            if m:
                for part in re.split(r'\s*/\s*|\s*·\s*', m.group(1)):
                    out.add(norm(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--core', help='hand-written core glossary markdown to prepend')
    ap.add_argument('--out', default='GLOSSARY.md')
    ap.add_argument('--link-prefix', default='',
                    help='prefix for generated wikilinks so they are resolved from the Obsidian '
                         'vault root, e.g. knowledge/bookslug/ . Obsidian resolves a path-style '
                         '[[a/b]] from the vault root, so a subfolder vault NEEDS this.')
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    core_txt = open(a.core, encoding='utf-8').read().rstrip() if a.core else ''
    cores = core_terms(core_txt)

    terms = collections.OrderedDict()
    for dirpath, _, files in os.walk(root):
        for fn in sorted(files):
            if not fn.endswith('.md'):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace('\\', '/')
            txt = open(p, encoding='utf-8').read()
            if rel == a.out:
                continue  # never read the file we are writing
            if not TERMS_HEADING.search(txt):
                continue
            link = '[[%s%s|%s]]' % (a.link_prefix, rel[:-3], rel[:-3])
            body = TERMS_HEADING.split(txt, 1)[1]
            for line in body.splitlines():
                line = line.strip()
                if not line.startswith('|'):
                    continue
                cells = [c.strip() for c in line.strip('|').split('|')]
                if len(cells) < 2:
                    continue
                head, sense = cells[0], cells[1]
                if not head or set(head) <= set('-: ') or clean_label(head).lower() == 'term':
                    continue
                k = norm(head)
                e = terms.setdefault(k, {'label': clean_label(cells[0]), 'senses': [], 'where': []})
                if sense and sense not in e['senses']:
                    e['senses'].append(clean_label(sense))
                if link not in e['where']:
                    e['where'].append(link)

    roster = []
    for k in sorted(terms):
        if k in cores:
            continue
        e = terms[k]
        sense = ' · '.join(e['senses'][:2]) + (' · …' if len(e['senses']) > 2 else '')
        roster.append((e['label'], sense.replace('|', '/'), ' '.join(e['where'][:3])))

    by_letter = collections.OrderedDict()
    for lab, sense, where in roster:
        by_letter.setdefault(initial(lab), []).append((lab, sense, where))

    out = core_txt + '\n\n'
    out += ('Terms in this roster: **%d**. With the core table: **%d** terms in total.\n\n'
            % (len(roster), len(roster) + len(cores)))
    for L in sorted(by_letter):
        out += '### %s\n\n| Term | Working sense | Defined in |\n|---|---|---|\n' % L
        for lab, sense, where in by_letter[L]:
            out += '| **%s** | %s | %s |\n' % (lab, sense, where)
        out += '\n'

    dest = os.path.join(root, a.out)
    open(dest, 'w', encoding='utf-8', newline='\n').write(out)
    print('%s written: %d bytes | unique terms %d | roster %d | core %d'
          % (a.out, len(out), len(terms), len(roster), len(cores)))


if __name__ == '__main__':
    main()
