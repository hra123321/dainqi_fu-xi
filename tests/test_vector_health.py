import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb

from app.vector_db.client import COURSE_MATERIALS, VectorDBClient


def test_supported_chroma_version():
    version = tuple(int(part) for part in chromadb.__version__.split(".")[:2])
    assert version >= (1, 5)


def test_vector_database_can_initialize_and_write():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        database = VectorDBClient(temp_dir)
        collection = database.get_or_create_collection(COURSE_MATERIALS)
        collection.add(
            ids=["health-check"],
            documents=["向量数据库健康检查"],
            metadatas=[{"domain_id": "health"}],
        )
        assert collection.count() == 1


if __name__ == "__main__":
    test_supported_chroma_version()
    test_vector_database_can_initialize_and_write()
    print("PASS: test_vector_health")
