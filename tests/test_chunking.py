import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.skills.vector_skills.chunk_strategy import smart_chunk, validate_chunks


def main():
    chunks = smart_chunk(
        ["第一段内容\n第二段内容", "第三段内容\n第四段内容"],
        chunk_size=12,
        overlap=2,
    )
    assert len(chunks) >= 2
    assert all("text" in chunk for chunk in chunks)
    issues = validate_chunks(chunks)
    assert isinstance(issues, list)
    print("PASS: test_chunking")


if __name__ == "__main__":
    main()
