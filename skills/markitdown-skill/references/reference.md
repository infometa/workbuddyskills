# MarkItDown API Reference

## MarkItDown Class

### Constructor

```python
class MarkItDown:
    def __init__(
        self,
        enable_plugins: bool = False,
        llm_client = None,
        llm_model: str = None,
        llm_prompt: str = None,
        docintel_endpoint: str = None
    )
```

**Parameters:**
- `enable_plugins` (bool): Enable 3rd-party plugins (default: False)
- `llm_client`: OpenAI-compatible client for image descriptions
- `llm_model` (str): Model name for image descriptions (e.g., "gpt-4o")
- `llm_prompt` (str): Custom prompt for image descriptions
- `docintel_endpoint` (str): Azure Document Intelligence endpoint

**Example:**
```python
from markitdown import MarkItDown

# Basic usage
md = MarkItDown()

# With plugins
md = MarkItDown(enable_plugins=True)

# With LLM image descriptions
from openai import OpenAI
client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")

# With Azure Document Intelligence
md = MarkItDown(docintel_endpoint="https://your-endpoint.cognitiveservices.azure.com/")
```

### convert() Method

```python
def convert(
    self,
    source: str | Path | bytes | BinaryIO
) -> ConversionResult
```

**Parameters:**
- `source`: File path (str/Path), bytes, or file-like object (binary mode)

**Returns:**
- `ConversionResult` object with `text_content` attribute

**Example:**
```python
# From file path
result = md.convert("document.pdf")

# From bytes
with open("document.pdf", "rb") as f:
    result = md.convert(f.read())

# From file-like object
with open("document.pdf", "rb") as f:
    result = md.convert(f)

print(result.text_content)
```

### convert_stream() Method

```python
def convert_stream(
    self,
    stream: BinaryIO,
    file_extension: str = None
) -> ConversionResult
```

**Parameters:**
- `stream` (BinaryIO): Binary file-like object (e.g., open file, io.BytesIO)
- `file_extension` (str): Optional file extension hint

**Returns:**
- `ConversionResult` object

**Example:**
```python
import io

# From BytesIO
data = io.BytesIO(pdf_bytes)
result = md.convert_stream(data, file_extension=".pdf")
```

## ConversionResult

```python
class ConversionResult:
    text_content: str  # Markdown output
```

**Attributes:**
- `text_content` (str): The converted markdown content

## CLI Usage

### Basic Commands

```bash
# Convert to stdout
markitdown <file>

# Convert to file
markitdown <file> -o <output.md>

# Pipe input
cat <file> | markitdown
```

### Options

```bash
markitdown --help
markitdown --list-plugins
markitdown --use-plugins <file>
markitdown <file> -d -e <endpoint>  # Azure Doc Intelligence
```

## Format-Specific Details

### PDF
- **Best for:** Text-based PDFs
- **Limitations:** Complex layouts may need Azure Document Intelligence
- **Dependencies:** `pip install 'markitdown[pdf]'`

### PowerPoint (.pptx)
- **Extracts:** Slide text, structure
- **Enhanced with:** LLM image descriptions
- **Dependencies:** `pip install 'markitdown[pptx]'`

### Word (.docx)
- **Preserves:** Headings, lists, tables, links
- **Dependencies:** `pip install 'markitdown[docx]'`

### Excel (.xlsx, .xls)
- **Extracts:** Tables, multiple sheets
- **Format:** Markdown tables
- **Dependencies:** `pip install 'markitdown[xlsx]'` or `'markitdown[xls]'`

### Images (jpg, png, etc.)
- **Extracts:** EXIF metadata + OCR text
- **Requires:** Tesseract OCR system dependency
- **Enhanced with:** LLM descriptions

### Audio (wav, mp3)
- **Extracts:** EXIF metadata + speech transcription
- **Dependencies:** `pip install 'markitdown[audio-transcription]'`
- **Note:** System audio libraries may be required

### YouTube
- **Extracts:** Video transcription (if available)
- **Dependencies:** `pip install 'markitdown[youtube-transcription]'`
- **Usage:** `markitdown "https://youtube.com/watch?v=VIDEO_ID"`

### HTML
- **Preserves:** Document structure
- **No extra dependencies**

### CSV/JSON/XML
- **Converts:** To readable markdown format
- **No extra dependencies**

### ZIP
- **Behavior:** Iterates over all files inside
- **No extra dependencies**

### EPUB
- **Extracts:** eBook content
- **No extra dependencies**

## Environment Requirements

### Python Version
- **Required:** Python 3.10 or higher
- **Recommended:** Python 3.12

### Virtual Environment (Recommended)

```bash
# Standard Python
python -m venv .venv
source .venv/bin/activate

# uv
uv venv --python=3.12 .venv
source .venv/bin/activate

# Conda
conda create -n markitdown python=3.12
conda activate markitdown
```

### System Dependencies

**Tesseract OCR** (for image text extraction):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Audio libraries** (for audio transcription):
- Platform-specific dependencies for speech_recognition library
- Check: https://github.com/Uberi/speech_recognition

## Azure Document Intelligence

For high-quality PDF conversion with complex layouts:

### Setup

1. Create Azure Document Intelligence resource
2. Get endpoint and API key
3. Set environment variable: `AZURE_DOCUMENT_INTELLIGENCE_KEY=<your-key>`

### Usage

**CLI:**
```bash
markitdown document.pdf -d -e "<endpoint>" -o output.md
```

**Python:**
```python
md = MarkItDown(docintel_endpoint="<endpoint>")
result = md.convert("document.pdf")
```

### More Info
https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/

## Plugin System

### Finding Plugins
Search GitHub for: `#markitdown-plugin`

### Using Plugins

**CLI:**
```bash
markitdown --list-plugins
markitdown --use-plugins file.pdf
```

**Python:**
```python
md = MarkItDown(enable_plugins=True)
```

### Creating Plugins
See: `packages/markitdown-sample-plugin` in the repository

## Error Handling

### Common Issues

**Missing dependencies:**
```python
try:
    result = md.convert("file.pdf")
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install 'markitdown[pdf]'")
```

**File format not supported:**
```python
try:
    result = md.convert("file.unknown")
except ValueError as e:
    print(f"Unsupported format: {e}")
```

**Conversion errors:**
```python
try:
    result = md.convert("file.pdf")
except Exception as e:
    print(f"Conversion failed: {e}")
```

## Performance Tips

1. **Batch processing:** Reuse MarkItDown instance
2. **Large files:** Consider chunking or streaming
3. **OCR:** Reduce image resolution if speed matters
4. **Audio:** Expect real-time or slower transcription
5. **Azure Doc Intel:** Best for complex PDFs, costs apply

## Output Format Notes

- **Goal:** LLM-friendly markdown, not pixel-perfect reproduction
- **Structure:** Preserves headings, lists, tables, links
- **Images:** Converted to markdown image syntax
- **Tables:** Converted to markdown tables (may lose complex formatting)
- **Styling:** Bold, italic preserved when possible
- **Layout:** Linear document structure (no multi-column preservation)

## Integration Examples

### LangChain Document Loader

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

### LlamaIndex Document

```python
from markitdown import MarkItDown
from llama_index import Document

md = MarkItDown()

def create_llama_doc(file_path):
    result = md.convert(file_path)
    return Document(text=result.text_content)
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

## Breaking Changes (v0.0.1 → v0.1.0)

1. **Dependencies:** Now organized into feature groups
   - Use `pip install 'markitdown[all]'` for backward compatibility

2. **convert_stream():** Now requires binary file-like objects
   - Changed from text (io.StringIO) to binary (io.BytesIO)

3. **DocumentConverter:** Interface changed to streams instead of paths
   - No temporary files created anymore
   - Plugin authors need to update code

## Resources

- **GitHub:** https://github.com/microsoft/markitdown
- **PyPI:** https://pypi.org/project/markitdown/
- **Issues:** https://github.com/microsoft/markitdown/issues
- **Contributing:** See CONTRIBUTING.md in repository
