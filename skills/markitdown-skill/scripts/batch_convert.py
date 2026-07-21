#!/usr/bin/env python3
"""
Batch convert multiple files to markdown using MarkItDown
"""

import sys
import argparse
from pathlib import Path
from markitdown import MarkItDown


def convert_file(md_converter, input_path, output_dir=None, verbose=False):
    """Convert a single file to markdown"""
    input_path = Path(input_path)
    
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        return False
    
    # Determine output path
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{input_path.stem}.md"
    else:
        output_path = input_path.with_suffix(".md")
    
    try:
        if verbose:
            print(f"Converting: {input_path}")
        
        result = md_converter.convert(str(input_path))
        output_path.write_text(result.text_content)
        
        if verbose:
            print(f"Saved to: {output_path}")
        
        return True
    
    except Exception as e:
        print(f"Error converting {input_path}: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Batch convert files to markdown using MarkItDown"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Files to convert (supports glob patterns)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory (default: same as input file)"
    )
    parser.add_argument(
        "-p", "--plugins",
        action="store_true",
        help="Enable plugins"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--llm-model",
        help="LLM model for image descriptions (e.g., gpt-4o)"
    )
    parser.add_argument(
        "--docintel-endpoint",
        help="Azure Document Intelligence endpoint"
    )
    
    args = parser.parse_args()
    
    # Initialize MarkItDown
    md_kwargs = {"enable_plugins": args.plugins}
    
    if args.llm_model:
        try:
            from openai import OpenAI
            client = OpenAI()
            md_kwargs["llm_client"] = client
            md_kwargs["llm_model"] = args.llm_model
        except ImportError:
            print("Error: openai package required for LLM features", file=sys.stderr)
            print("Install with: pip install openai", file=sys.stderr)
            sys.exit(1)
    
    if args.docintel_endpoint:
        md_kwargs["docintel_endpoint"] = args.docintel_endpoint
    
    md = MarkItDown(**md_kwargs)
    
    # Process files
    success_count = 0
    total_count = 0
    
    for file_pattern in args.files:
        # Handle glob patterns
        if "*" in file_pattern or "?" in file_pattern:
            files = list(Path(".").glob(file_pattern))
        else:
            files = [Path(file_pattern)]
        
        for file_path in files:
            total_count += 1
            if convert_file(md, file_path, args.output_dir, args.verbose):
                success_count += 1
    
    # Summary
    if args.verbose or total_count > 1:
        print(f"\nConverted {success_count}/{total_count} files")
    
    sys.exit(0 if success_count == total_count else 1)


if __name__ == "__main__":
    main()
