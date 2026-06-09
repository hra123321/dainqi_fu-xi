import pathlib, sys, re
sys.stdout.reconfigure(encoding='utf-8')

p = pathlib.Path('app/templates/exam.html')
t = p.read_text('utf-8')

# Fix 1: broken div
t = t.replace('<div     <div id=\"emptyState\"', '<div id=\"emptyState\"')
print('Fix 1: div repaired')

# Fix 2: remove duplicate content after last endblock
matches = [(m.start(), m.end()) for m in re.finditer(r'\{% endblock %\}', t)]
if matches:
    t = t[:matches[-1][1]]
    print('Fix 2: %d endblocks handled' % len(matches))

# Fix 3: star labels
# The JS template literals look like: 
# <span title=\"\u96be\u5ea6\">\U0001f4ca </span>
# We want: <span style=\"font-size:12px;color:var(--text-muted)\">\u96be\u5ea6: </span>
# (remove emoji, replace title with visible label)

# Pattern 1: difficulty
t = t.replace(
    '<span title=\"\u96be\u5ea6\">\U0001f4ca </span>',
    '<span style=\"font-size:12px;color:var(--text-muted)\">\u96be\u5ea6: </span>'
)
print('Fix 3a: difficulty label')

# Pattern 2: exam importance  
t = t.replace(
    '<span title=\"\u8003\u8bd5\u91cd\u8981\u6027\">\U0001f4dd </span>',
    '<span style=\"font-size:12px;color:var(--text-muted)\">\u8003\u8bd5\u91cd\u8981: </span>'
)
print('Fix 3b: exam label')

# Pattern 3: engineering importance
t = t.replace(
    '<span title=\"\u5de5\u7a0b\u91cd\u8981\u6027\">\u2699\ufe0f </span>',
    '<span style=\"font-size:12px;color:var(--text-muted)\">\u5de5\u7a0b\u91cd\u8981: </span>'
)
print('Fix 3c: engineering label')

# Fix 4: compress blank lines
t = re.sub(r'\n{4,}', '\n\n\n', t)
print('Fix 4: blank lines compressed')

p.write_text(t, 'utf-8')
print('\nAll fixes applied! Size: %d bytes' % len(t))

# Verify
t2 = p.read_text('utf-8')
count1 = 0
count2 = 0
count3 = 0
for line in t2.splitlines():
    if '\u96be\u5ea6:' in line and 'renderStars(diff)' in line:
        count1 += 1
    if '\u8003\u8bd5\u91cd\u8981:' in line and 'renderStars(examImp)' in line:
        count2 += 1
    if '\u5de5\u7a0b\u91cd\u8981:' in line and 'renderStars(engImp)' in line:
        count3 += 1
print('Verify: 难度=%d, 考试重要=%d, 工程重要=%d' % (count1, count2, count3))
