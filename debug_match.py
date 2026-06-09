import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

t = pathlib.Path('app/templates/exam.html').read_text('utf-8')

# Find the line
target_line = None
for line in t.splitlines():
    if 'renderStars' in line and '\u96be\u5ea6' in line:
        target_line = line.strip()
        break

print('File line repr:', repr(target_line))
print('File line len:', len(target_line))

# Build my replacement  
diff_expr = ''
my_old = '<span title=\"\u96be\u5ea6\">\U0001f4ca ' + diff_expr + '</span>'
print('My string repr:', repr(my_old))
print('My string len:', len(my_old))

# Compare
if target_line == my_old:
    print('MATCH!')
else:
    print('DIFFERENT!')
    # Find first difference
    for i in range(min(len(target_line), len(my_old))):
        if target_line[i] != my_old[i]:
            print('Diff at %d: file=%d(%s) mine=%d(%s)' % (
                i, ord(target_line[i]), repr(target_line[i]),
                ord(my_old[i]), repr(my_old[i])))
            break
    print('File hex:', target_line.encode('utf-8').hex()[:50])
    print('My hex:', my_old.encode('utf-8').hex()[:50])
