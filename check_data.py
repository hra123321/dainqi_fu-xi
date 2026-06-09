import pathlib, json, re
js = pathlib.Path('app/static/js/subjects.js').read_text('utf-8')

# Extract subjects data using regex since exec() is dangerous with untrusted data
start = js.find('const SUBJECTS = [')
end = js.rfind('];') + 2
data_text = js[start:end]
data_text = data_text.replace('const SUBJECTS = ', '')

# Parse as JSON-like (need to handle unicode escapes)
import json
data_text = data_text.replace("'", '"')
data_text = re.sub(r'(\w+):', r'"\1":', data_text)
data_text = data_text.replace('"icon": "📚"', '"icon": "book"')

print(f'Data text length: {len(data_text)}')
print(f'First 100 chars: {data_text[:100]}')
