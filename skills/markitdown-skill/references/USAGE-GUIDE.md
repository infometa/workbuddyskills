# MarkItDown Usage Guide

Detailed examples and patterns for document conversion.

## CLI Usage

### Basic Conversion

```bash
# To stdout
markitdown document.pdf

# To file
markitdown document.pdf -o output.md

# From stdin
cat document.pdf | markitdown > output.md
```

### Web Content

```bash
# Fetch and convert URL
markitdown https://example.com/docs -o docs.md

# GitHub README
markitdown https://raw.githubusercontent.com/user/repo/main/README.md
```

### Batch Processing

```bash
# Convert all PDFs
for file in *.pdf; do
  markitdown "$file" -o "${file%.pdf}.md"
done

# Using the included script
python scripts/batch_convert.py docs/*.pdf -o markdown/ -v
```

### Advanced Options

```bash
# Enable plugins
markitdown --use-plugins file.pdf

# List plugins
markitdown --list-plugins

# Azure Document Intelligence (complex PDFs)
markitdown file.pdf -d -e "<endpoint>" -o output.md
```

---

## Python API

### Basic Usage

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

### With LLM Image Descriptions

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this image in detail"
)
result = md.convert("image.jpg")
print(result.text_content)
```

### Azure Document Intelligence

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="https://your-endpoint.cognitiveservices.azure.com/")
result = md.convert("complex-layout.pdf")
print(result.text_content)
```

### Batch Processing

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()

for pdf_file in Path("docs/").glob("*.pdf"):
    result = md.convert(str(pdf_file))
    output_path = pdf_file.with_suffix(".md")
    output_path.write_text(result.text_content)
```

### Error Handling

```python
from markitdown import MarkItDown

md = MarkItDown()

try:
    result = md.convert("file.pdf")
    print(result.text_content)
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install 'markitdown[pdf]'")
except Exception as e:
    print(f"Conversion failed: {e}")
```

---

## Format-Specific Examples

### PDF Documents

```bash
# Simple extraction
markitdown document.pdf -o document.md

# Complex layouts (Azure)
markitdown document.pdf -d -e "<endpoint>" -o document.md
```

### PowerPoint Presentations

```bash
markitdown presentation.pptx -o slides.md
```

```python
# With LLM image descriptions
from openai import OpenAI
md = MarkItDown(llm_client=OpenAI(), llm_model="gpt-4o")
result = md.convert("presentation.pptx")
```

### Excel Spreadsheets

```bash
markitdown spreadsheet.xlsx -o data.md
```

Output format:
```markdown
## Sheet1

| Column A | Column B | Column C |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
```

### Images (OCR)

```bash
# Requires Tesseract OCR
markitdown scanned-document.jpg -o extracted.md
```

### Audio Transcription

```bash
pip install 'markitdown[audio-transcription]'
markitdown recording.mp3 -o transcript.md
```

### YouTube Videos

```bash
pip install 'markitdown[youtube-transcription]'
markitdown "https://youtube.com/watch?v=VIDEO_ID" -o transcript.md
```

### ZIP Archives

```bash
# Iterates over all files inside
markitdown archive.zip -o contents.md
```

---

## Integration Patterns

### LLM Document Analysis

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown()
client = OpenAI()

# Convert document
result = md.convert("contract.pdf")

# Analyze with LLM
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Analyze this contract for key terms"},
        {"role": "user", "content": result.text_content}
    ]
)
print(response.choices[0].message.content)
```

### RAG Pipeline

```python
from markitdown import MarkItDown

md = MarkItDown()

# Convert knowledge base
documents = []
for file in ["doc1.pdf", "doc2.docx", "doc3.pptx"]:
    result = md.convert(file)
    documents.append({
        "source": file,
        "content": result.text_content
    })

# Feed to vector database...
```

### LangChain Integration

```python
from markitdown import MarkItDown
from langchain.docstore.document import Document

md = MarkItDown()

def load_document(file_path):
    result = md.convert(file_path)
    return Document(
        page_content=result.text_content,
        metadata={"source": file_path}
    )
```

### FastAPI Endpoint

```python
from fastapi import FastAPI, UploadFile
from markitdown import MarkItDown

app = FastAPI()
md = MarkItDown()

@app.post("/convert")
async def convert_file(file: UploadFile):
    content = await file.read()
    result = md.convert(content)
    return {"markdown": result.text_content}
```

---

## Performance Tips

1. **Reuse MarkItDown instance** for batch processing
2. **Reduce image resolution** if OCR speed matters
3. **Use Azure Document Intelligence** for complex PDF layouts
4. **Audio transcription** is roughly real-time

## Output Format

MarkItDown preserves:
- Headings (H1-H6)
- Lists (ordered/unordered)
- Tables
- Links
- Code blocks
- Images (as markdown syntax)

**Note:** Optimized for LLM consumption, not pixel-perfect reproduction.
