#!/usr/bin/env python3
"""
Extract tables from PDF files using Camelot.

Supports multiple output formats: csv, json, excel, html, markdown, sqlite.
"""

import argparse
import logging
from pathlib import Path

from pdf_table_extractor.pdf_processor import process_directory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress verbose Camelot logging
logging.getLogger('camelot').setLevel(logging.WARNING)


SUPPORTED_FORMATS = {
    'csv': 'CSV file',
    'json': 'JSON format',
    'excel': 'Excel spreadsheet',
    'html': 'HTML table',
    'markdown': 'Markdown table',
    'sqlite': 'SQLite database',
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Extract tables from PDF files using Camelot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported output formats:
{chr(10).join(f'  {fmt}: {desc}' for fmt, desc in SUPPORTED_FORMATS.items())}

Examples:
  # Extract all PDFs in data/ to CSV
  extract-tables data/ csv/

  # Extract to JSON format
  extract-tables data/ output/ --format json

  # Use lattice flavor instead of stream
  extract-tables data/ csv/ --flavor lattice

  # Process subdirectories recursively
  extract-tables data/ csv/ --recursive

  # Test with first page only
  extract-tables data/ csv/ --recursive --pages 1

  # Force reprocessing of all files
  extract-tables data/ csv/ --recursive --force
        """,
    )

    parser.add_argument('input_dir', type=Path, help='Directory containing PDF files')

    parser.add_argument('output_dir', type=Path, help='Directory to save output files')

    parser.add_argument(
        '-f',
        '--format',
        choices=list(SUPPORTED_FORMATS.keys()),
        default='csv',
        help='Output format (default: csv)',
    )

    parser.add_argument(
        '--flavor',
        choices=['stream', 'lattice'],
        default='stream',
        help='Camelot parsing flavor (default: stream). Use "lattice" for PDFs with clear table borders.',
    )

    parser.add_argument(
        '--pages',
        type=str,
        default='all',
        help='Pages to process (default: all). Examples: "1" for first page only, "1-3" for pages 1-3, "1,3,5" for specific pages',
    )

    parser.add_argument(
        '-r',
        '--recursive',
        action='store_true',
        help='Process PDF files in subdirectories recursively',
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocessing of all PDFs, even if already processed',
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate that all PDFs have been processed (for CI). Fails if any PDF needs processing.',
    )

    parser.add_argument(
        '-j',
        '--jobs',
        type=int,
        default=None,
        metavar='N',
        help='Number of parallel workers (default: number of CPU cores)',
    )

    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not args.input_dir.exists():
        logger.error(f'Input directory does not exist: {args.input_dir}')
        return

    if not args.input_dir.is_dir():
        logger.error(f'Input path is not a directory: {args.input_dir}')
        return

    success = process_directory(
        args.input_dir,
        args.output_dir,
        args.format,
        args.flavor,
        args.recursive,
        args.pages,
        skip_existing=not args.force,
        validate_only=args.validate,
        max_workers=args.jobs,
    )

    if args.validate and not success:
        logger.error('Validation failed: Some PDFs have not been processed')
        exit(1)


if __name__ == '__main__':
    main()
