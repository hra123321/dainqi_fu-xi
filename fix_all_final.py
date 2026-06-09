import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

t = pathlib.Path('app/templates/exam.html').read_text('utf-8')

# Fix 1: broken div
t = t.replace('<div     <div id="emptyState"', '<div id="emptyState"')
print("Fix 1: div OK")

# Fix 2: endblock cleanup
import re
matches = [(m.start(), m.end()) for m in re.finditer(r'\{% endblock %\}', t)]
if matches:
    t = t[:matches[-1][1]]
print("Fix 2: endblock OK (%d found)" % len(matches))

# Fix 3: star labels with visible text
s = 'font-size:12px;color:var(--text-muted)'
old1 = '<span title="\u96be\u5ea6">\U0001f4ca ${renderStars(diff)}</span>'
new1 = '<span style="' + s + '">\u96be\u5ea6: ${renderStars(diff)}</span>'
t = t.replace(old1, new1)

old2 = '<span title="\u8003\u8bd5\u91cd\u8981\u6027">\U0001f4dd ${renderStars(examImp)}</span>'
new2 = '<span style="' + s + '">\u8003\u8bd5\u91cd\u8981: ${renderStars(examImp)}</span>'
t = t.replace(old2, new2)

old3 = '<span title="\u5de5\u7a0b\u91cd\u8981\u6027">\u2699\ufe0f ${renderStars(engImp)}</span>'
new3 = '<span style="' + s + '">\u5de5\u7a0b\u91cd\u8981: ${renderStars(engImp)}</span>'
t = t.replace(old3, new3)

# Fix 4: renderStars in subjects.js - only filled stars, no empty ones
js = pathlib.Path('app/static/js/subjects.js').read_text('utf-8')
js = js.replace(
    'return "\\u2605".repeat(level) + "\\u2606".repeat(5 - level);',
    'return "\\u2605".repeat(level);'
)
pathlib.Path('app/static/js/subjects.js').write_text(js, 'utf-8')
print("Fix 4: subjects.js renderStars OK")

pathlib.Path('app/templates/exam.html').write_text(t, 'utf-8')
print("\nAll fixes applied! Size: %d bytes" % len(t))

# Verify
t2 = pathlib.Path('app/templates/exam.html').read_text('utf-8')
c = sum(1 for l in t2.splitlines() if '\u96be\u5ea6:' in l and 'renderStars(diff)' in l)
print("难度标签: %d 处" % c)
c2 = sum(1 for l in t2.splitlines() if '\u8003\u8bd5\u91cd\u8981' in l)
print("考试重要标签: %d 处" % c2)
c3 = sum(1 for l in t2.splitlines() if '\u5de5\u7a0b\u91cd\u8981' in l)
print("工程重要标签: %d 处" % c3)
print("破损div:", "无" if '<div     <div' not in t2 else "还有!")
