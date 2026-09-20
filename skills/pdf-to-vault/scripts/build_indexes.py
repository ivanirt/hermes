# build_indexes.py — generate the mechanical indexes for a literature vault
#
#   python build_indexes.py --root <vault-subdir> --vault <obsidian-vault-root> \
#       --link-prefix knowledge/bookslug/ --outdir indexes
#
# Emits three things, all rebuilt from the notes themselves:
#
#   1. <outdir>/CROSS-REFERENCE.md  every note's '## Correspondences' table, pivoted
#      into one row per note. Handles both table shapes seen in practice:
#        wide  -> header mentions traditions (Kabbalah/Taoist/Sanskrit/...), one data row
#        tall  -> 'Aspect | Correspondence [| Page]', one row per tradition
#   2. <outdir>/FULL-LIST.md         every note, grouped by folder, with counts
#   3. TOPICS.md                     the vault sliced by tag family (from frontmatter)
#
# Nothing here is hardcoded to a particular book: traditions are discovered from the
# table headers, and tag families are discovered from the tags themselves.
import argparse
import collections
import os
import re

TRADITION_HINTS = ('kabbal', 'taoist', 'chinese', 'indian', 'sanskrit', 'tamil',
                   'acupun', 'egyptian', 'hindu', 'buddh', 'christian', 'hebrew')


def fm_of(txt):
    fm = {}
    if txt.startswith('---'):
        end = txt.find('\n---', 3)
        for line in txt[3:end].splitlines():
            if re.match(r'^[a-z_]+:', line):
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm


def section(txt, heading):
    """Body of a '## <heading>' section, up to the next '## '."""
    m = re.search(r'(?m)^##\s+' + re.escape(heading) + r'\s*$', txt)
    if not m:
        return None
    rest = txt[m.end():]
    nxt = re.search(r'(?m)^##\s+', rest)
    return rest[:nxt.start()] if nxt else rest


def tables(body):
    """Yield (header_cells, [data_rows]) for each markdown table in body."""
    rows = [l.strip() for l in body.splitlines() if l.strip().startswith('|')]
    out, i = [], 0
    while i < len(rows):
        chunk = []
        while i < len(rows) and rows[i].startswith('|'):
            chunk.append(rows[i])
            i += 1
        cells = [[c.strip() for c in r.strip('|').split('|')] for r in chunk]
        data = [c for c in cells if not set(''.join(c)) <= set('-: ')]
        if len(data) >= 2:
            out.append((data[0], data[1:]))
    return out


def classify(label):
    """Map a row label to a tradition key. Order matters: test 'tamil' before
    'indian' because 'Tamil (Southern India)' contains both."""
    l = label.lower()
    if 'tamil' in l:
        return 'tamil'
    for h in TRADITION_HINTS:
        if h in l:
            return h
    return None


def first_alnum(s, default='#'):
    m = re.search(r'[A-Za-z0-9]', s or '')
    return m.group(0).upper() if m else default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--vault', help='Obsidian vault root (for relative paths/links)')
    ap.add_argument('--link-prefix', default='', help='e.g. knowledge/bookslug/')
    ap.add_argument('--outdir', default='indexes')
    ap.add_argument('--topics', action='store_true',
                    help='also emit TOPICS.md. OFF by default: a hand-curated MOC/TOPICS is '
                         'usually better, and regenerating silently overwrites it.')
    ap.add_argument('--crossref-dirs', default='',
                    help='comma-separated subfolders to index correspondences from; '
                         'default: every folder except the outdir')
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    outdir = os.path.join(root, a.outdir)
    os.makedirs(outdir, exist_ok=True)

    notes = {}
    for dirpath, _, files in os.walk(root):
        for fn in sorted(files):
            if not fn.endswith('.md'):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace('\\', '/')
            top = rel.split('/')[0]
            if rel.startswith(a.outdir + '/') or rel in ('README.md', 'MOC.md', 'MAP.md',
                                                         'TOPICS.md', 'GLOSSARY.md'):
                continue
            txt = open(p, encoding='utf-8').read()
            notes[rel] = {'txt': txt, 'fm': fm_of(txt), 'top': top}

    link = lambda rel: '[[%s%s|%s]]' % (a.link_prefix, rel[:-3], rel[:-3])

    # ---- 1. cross-reference ----
    only = [d.strip() for d in a.crossref_dirs.split(',') if d.strip()]
    rows_out = []
    for rel, n in sorted(notes.items()):
        if only and n['top'] not in only:
            continue
        body = section(n['txt'], 'Correspondences') or section(n['txt'], 'Correspondence')
        if not body:
            continue
        tabs = tables(body)
        if not tabs:
            continue
        header, data = tabs[0]
        vals = collections.OrderedDict()
        wide = sum(1 for h in header if any(t in h.lower() for t in TRADITION_HINTS)) >= 2
        if wide:
            for i, h in enumerate(header):
                for d in data:
                    if i < len(d) and d[i] and set(d[i]) != {'-'}:
                        vals[h] = d[i]
        else:
            for d in data:
                key = d[0]
                kind = classify(key)
                if not kind:
                    continue  # only tradition-labelled rows belong in a cross-reference
                val = d[1] if len(d) > 1 else ''
                if val:
                    vals[kind] = (vals[kind] + ' · ' + val) if kind in vals else val
        if vals:
            rows_out.append((rel, n['fm'].get('title', rel.split('/')[-1][:-3]), vals))

    cols = collections.OrderedDict()
    for _, _, vals in rows_out:
        for k in vals:
            c = classify(k) or k
            cols.setdefault(c, k)

    body = ['| Note | ' + ' | '.join(cols.values()) + ' |',
            '|' + '---|' * (len(cols) + 1)]
    for rel, title, vals in rows_out:
        cells = []
        for c, sample in cols.items():
            v = ''
            for k, val in vals.items():
                if (classify(k) or k) == c:
                    v = (v + ' · ' + val) if v else val
            cells.append(v or '—')
        body.append('| %s | %s |' % (link(rel), ' | '.join(cells)))
    cross = ('---\ntype: Index\ntitle: "Cross-reference — per-note correspondence rows"\n'
             'tags: [index, status/draft]\nstatus: draft\n---\n\n'
             '# Cross-reference\n\n'
             'Mechanically collected from each note\'s `## Correspondences` table. '
             'Columns are discovered from the table headers, not hardcoded.\n\n'
             + '\n'.join(body) + '\n\n*%d notes contributed.*\n' % len(rows_out))
    open(os.path.join(outdir, 'CROSS-REFERENCE.md'), 'w', encoding='utf-8', newline='\n').write(cross)

    # ---- 2. full list ----
    groups = collections.OrderedDict()
    for rel, n in sorted(notes.items()):
        groups.setdefault(n['top'], []).append((rel, n['fm'].get('title', '')))
    fl = ['---\ntype: Index\ntitle: "FULL-LIST — every note in this vault"\n'
          'tags: [index, status/draft]\nstatus: draft\n---\n\n# Full list of notes\n\n']
    for top, items in groups.items():
        fl.append('## %s (%d)\n\n| Note | Title |\n|---|---|\n' % (top, len(items)))
        for rel, title in items:
            fl.append('| %s | %s |\n' % (link(rel), title))
        fl.append('\n')
    fl.append('**Total notes indexed: %d**\n' % len(notes))
    open(os.path.join(outdir, 'FULL-LIST.md'), 'w', encoding='utf-8', newline='\n').write(''.join(fl))
    print('FULL-LIST.md: %d notes across %d groups' % (len(notes), len(groups)))

    if not a.topics:
        print('TOPICS.md: skipped (pass --topics to emit; it overwrites any hand-curated file)')
        return

    # ---- 3. topics by tag family ----
    fam = collections.defaultdict(lambda: collections.defaultdict(list))
    for rel, n in sorted(notes.items()):
        for t in [x.strip() for x in n['fm'].get('tags', '').strip('[]').split(',') if x.strip()]:
            fam[t.split('/')[0] if '/' in t else 'domain'][t].append(rel)
    tp = ['---\ntype: Index\ntitle: "TOPICS — the vault by tag"\n'
          'tags: [index, status/draft]\nstatus: draft\n---\n\n# TOPICS\n\n'
          'The same vault sliced by tag rather than by folder.\n\n']
    for f in sorted(fam):
        tp.append('## `%s/`\n\n' % f if f != 'domain' else '## bare domain tags\n\n')
        for t, rels in sorted(fam[f].items(), key=lambda kv: -len(kv[1])):
            tp.append('### `%s` — %d\n\n' % (t, len(rels)))
            for rel in rels:
                tp.append('- %s\n' % link(rel))
            tp.append('\n')
    open(os.path.join(root, 'TOPICS.md'), 'w', encoding='utf-8', newline='\n').write(''.join(tp))

    print('CROSS-REFERENCE.md: %d notes, %d columns %s'
          % (len(rows_out), len(cols), list(cols.values())))
    print('TOPICS.md: %d tag families, %d distinct tags'
          % (len(fam), sum(len(v) for v in fam.values())))


if __name__ == '__main__':
    main()
