import pathlib
p = pathlib.Path('app/static/js/subjects.js')
t = p.read_text('utf-8')

old_func = '''function renderStars(level) {
    return "\u2605".repeat(level) + "\u2606".repeat(5 - level);
}'''

new_func = '''function renderStars(level) {
    return "\u2605".repeat(level);
}'''

if old_func in t:
    t = t.replace(old_func, new_func)
    p.write_text(t, 'utf-8')
    print('✅ renderStars 已更新 - 只显示实心星星')
else:
    print('⚠️ 未找到旧函数')
    idx = t.find('renderStars')
    if idx >= 0:
        print('当前位置:', t[idx:idx+120])
