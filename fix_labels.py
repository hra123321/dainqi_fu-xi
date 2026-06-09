import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

t = pathlib.Path('app/templates/exam.html').read_text('utf-8')
c1 = c2 = c3 = 0
result = []
for line in t.splitlines(True):
    if 'title=\"\u96be\u5ea6\"' in line and 'renderStars(diff)' in line:
        line = line.replace('\U0001f4ca ', '')  # remove chart emoji
        line = line.replace('title=\"\u96be\u5ea6\"', 'style=\"font-size:12px;color:var(--text-muted)\"')
        line = line.replace('', '\u96be\u5ea6: ')
        c1 += 1
    elif 'title=\"\u8003\u8bd5\u91cd\u8981\u6027\"' in line and 'renderStars(examImp)' in line:
        line = line.replace('\U0001f4dd ', '')  # remove memo emoji
        line = line.replace('title=\"\u8003\u8bd5\u91cd\u8981\u6027\"', 'style=\"font-size:12px;color:var(--text-muted)\"')
        line = line.replace('', '\u8003\u8bd5\u91cd\u8981: ')
        c2 += 1
    elif 'title=\"\u5de5\u7a0b\u91cd\u8981\u6027\"' in line and 'renderStars(engImp)' in line:
        line = line.replace('\u2699\ufe0f ', '')  # remove gear emoji
        line = line.replace('title=\"\u5de5\u7a0b\u91cd\u8981\u6027\"', 'style=\"font-size:12px;color:var(--text-muted)\"')
        line = line.replace('', '\u5de5\u7a0b\u91cd\u8981: ')
        c3 += 1
    result.append(line)

t = ''.join(result)
pathlib.Path('app/templates/exam.html').write_text(t, 'utf-8')
print('OK - 替换: 难度=%d, 考试重要=%d, 工程重要=%d' % (c1, c2, c3))
