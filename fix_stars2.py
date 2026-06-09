import pathlib
p = pathlib.Path('app/static/js/subjects.js')
t = p.read_text('utf-8')
old = '\u2605' + '.repeat(level) + ' + '\u2606' + '.repeat(5 - level);'
new = '\u2605' + '.repeat(level);'
if old in t:
    t = t.replace(old, new)
    p.write_text(t, 'utf-8')
    print('OK')
else:
    print('not found - checking...')
    for i, line in enumerate(t.splitlines()):
        if 'repeat' in line and 'level' in line:
            print(repr(line.strip()[:100]))
