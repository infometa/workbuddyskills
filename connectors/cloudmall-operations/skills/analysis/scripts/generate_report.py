#!/usr/bin/env python3
"""Generate local HTML and optional PDF; never install dependencies."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--data-file', type=Path)
    source.add_argument('--html-file', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path.cwd())
    parser.add_argument('--name', default='report')
    parser.add_argument('--skip-pdf', action='store_true')
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()
    if args.name in ('.', '..') or any(c in args.name for c in '/\\'):
        parser.error('--name must be a file name, not a path')
    directory = args.output_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    html = directory / (args.name + '.html')
    scripts = Path(__file__).resolve().parent
    if args.data_file:
        subprocess.run([sys.executable, str(scripts / 'ecommerce_report.py'), '--data-file',
                        str(args.data_file.resolve()), '--output', str(html)], check=True)
    else:
        source_html = args.html_file.resolve()
        if not source_html.is_file():
            parser.error('HTML source does not exist')
        if source_html != html:
            shutil.copyfile(source_html, html)
    print(str(html))
    if not args.skip_pdf:
        node = shutil.which('node')
        if not node:
            print('PDF unavailable: Node.js missing; HTML retained.', file=sys.stderr)
            return
        pdf = directory / (args.name + '.pdf')
        result = subprocess.run([node, str(scripts / 'html2pdf.js'), str(html), '-o', str(pdf)])
        if result.returncode == 0 and pdf.is_file():
            print(str(pdf))
        else:
            print('PDF conversion failed or dependencies missing; deliver the HTML above.', file=sys.stderr)


if __name__ == '__main__':
    main()
