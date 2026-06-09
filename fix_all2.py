import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

t = pathlib.Path('app/templates/exam.html').read_text('utf-8')

# Build target strings carefully
diff_expr = ''
exam_expr = ''
eng_expr = ''

# targets
old1 = '<span title=\"\u96be\u5ea6\">\U0001f4ca ' + diff_expr + '</span>'
old2 = '<span title=\"\u8003\u8bd5\u91cd\u8981\u6027\">\U0001f4dd ' + exam_expr + '</span>'
old3 = '<span title=\"\u5de5\u7a0b\u91cd\u8981\u6027\">\u2699\ufe0f ' + eng_expr + '</span>'

# new labels
sty = 'font-size:12px;color:var(--text-muted)'
new1 = '<span style=\"' + sty + '\">\u96be\u5ea6: ' + diff_expr + '</span>'
new2 = '<span style=\"' + sty + '\">\u8003\u8bd5\u91cd\u8981: ' + exam_expr + '</span>'
new3 = '<span style=\"' + sty + '\">\u5de5\u7a0b\u91cd\u8981: ' + eng_expr + '</span>'

# Check
c1 = t.count(old1)
c2 = t.count(old2)
c3 = t.count(old3)
print('找到: old1=%d, old2=%d, old3=%d' % (c1, c2, c3))

if c1 > 0:
    t = t.replace(old1, new1)
if c2 > 0:
    t = t.replace(old2, new2)
if c3 > 0:
    t = t.replace(old3, new3)

# Also need to fix subjects.js renderStars
js = pathlib.Path('app/static/js/subjects.js').read_text('utf-8')
js_old = 'return \"\\u2605\".repeat(level) + \"\\u2606\".repeat(5 - level);'
js_new = 'return \"\\u2605\".repeat(level);'
js = js.replace(js_old, js_new)
pathlib.Path('app/static/js/subjects.js').write_text(js, 'utf-8')
print('subjects.js renderStars fixed')

pathlib.Path('app/templates/exam.html').write_text(t, 'utf-8')
print('exam.html labels fixed')
print('大小: %d bytes' % len(t))
