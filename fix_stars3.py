import pathlib
p = pathlib.Path('app/static/js/subjects.js')
t = p.read_text('utf-8')
old = r'return "\u2605".repeat(level) + "\u2606".repeat(5 - level);'
new = r'return "\u2605".repeat(level);'
if old in t:
    t = t.replace(old, new)
    p.write_text(t, 'utf-8')
    print('OK - stars fixed')
else:
    print('still not found')
    # Try searching for the pattern
    import re
    m = re.search(r'return.*repeat\(level\).*', t)
    if m:
        print('Found:', repr(m.group()))
