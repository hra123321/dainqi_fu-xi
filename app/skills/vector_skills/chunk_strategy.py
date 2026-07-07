from typing import Dict, List


def smart_chunk(texts: List[str], chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    chunks = []
    current = ""

    for text in texts:
        paragraphs = [paragraph.strip() for paragraph in text.split("\n") if paragraph.strip()]
        for paragraph in paragraphs:
            if len(current) + len(paragraph) > chunk_size:
                if current.strip():
                    chunks.append({"text": current.strip(), "index": len(chunks)})
                prefix = current[-overlap:] if len(current) > overlap else ""
                current = f"{prefix}\n{paragraph}".strip() if prefix else paragraph
            else:
                current = f"{current}\n{paragraph}".strip() if current else paragraph

    if current.strip():
        chunks.append({"text": current.strip(), "index": len(chunks)})

    return chunks


def validate_chunks(chunks: List[Dict]) -> List[str]:
    issues = []
    for chunk in chunks:
        text = chunk.get("text", "")
        index = chunk.get("index", "?")
        if len(text) < 10:
            issues.append(f"片段 {index} 过短")
        if len(text) > 2000:
            issues.append(f"片段 {index} 过长")
    return issues
