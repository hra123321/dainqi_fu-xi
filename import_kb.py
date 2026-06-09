import sys, json, pathlib
sys.stdout.reconfigure(encoding='utf-8')

# Import directly using the project's vector DB client
sys.path.insert(0, str(pathlib.Path.cwd()))
from app.vector_db.client import vector_db, COURSE_MATERIALS

# Read knowledge entries
entries = json.loads(pathlib.Path('data/knowledge_entries.json').read_text('utf-8'))
print('读取 %d 条知识条目' % len(entries))

# Get or create the course_materials collection
col = vector_db.get_or_create_collection(COURSE_MATERIALS)
print('Collection 名: %s' % col.name)

# Add entries in batches of 50
batch_size = 50
for i in range(0, len(entries), batch_size):
    batch = entries[i:i+batch_size]
    ids = [e['id'] for e in batch]
    texts = [e['text'] for e in batch]
    metadatas = [e['metadata'] for e in batch]
    
    col.add(
        documents=texts,
        ids=ids,
        metadatas=metadatas
    )
    print('  已添加批次 %d-%d' % (i+1, min(i+batch_size, len(entries))))

# Verify
count = col.count()
print('\n导入完成! Collection 中共 %d 条文档' % count)

# Show collections summary
for c in vector_db.get_all_collections():
    print('  %s: %d 条' % (c['name'], c['doc_count']))
