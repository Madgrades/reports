"""PDF table extraction processor."""

import logging
from pathlib import Path
from typing import Any

import camelot  # type: ignore[import-untyped]

from pdf_table_extractor.metadata import FileMetadata, save_metadata, should_skip_pdf

logger = logging.getLogger(__name__)


def extract_tables_from_pdf(
    pdf_path: Path,
    output_dir: Path,
    output_format: str = 'csv',
    flavor: str = 'stream',
    pages: str = 'all',
    skip_existing: bool = True
) -> None:
    """
    Extract tables from a PDF file and save to the specified format.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save output files
        output_format: Output format (csv, json, excel, html, markdown, sqlite)
        flavor: Camelot flavor ('stream' or 'lattice')
        pages: Pages to process (default: 'all', or e.g., '1', '1-3', '1,3,5')
        skip_existing: Whether to skip PDFs that have already been processed
    """
    if skip_existing and should_skip_pdf(pdf_path, output_dir):
        logger.info(f"Skipping {pdf_path.name} (already processed, unchanged)")
        return
    
    logger.info(f"Processing {pdf_path.name} with {flavor} flavor (pages: {pages})...")

    try:
        tables = camelot.read_pdf(str(pdf_path), flavor=flavor, pages=pages)  # type: ignore[no-untyped-call]

        if not tables:
            logger.warning(f"No tables found in {pdf_path.name}")
            return

        logger.info(f"Found {len(tables)} table(s) in {pdf_path.name}")  # type: ignore[arg-type]

        base_name = pdf_path.stem
        pdf_output_dir = output_dir / base_name
        pdf_output_dir.mkdir(parents=True, exist_ok=True)

        _export_tables(tables, pdf_output_dir, base_name, output_format)
        
        # Save metadata after successful processing
        metadata = FileMetadata.from_file(pdf_path)
        save_metadata(pdf_output_dir, metadata)

    except Exception as e:
        logger.error(f"Error processing {pdf_path.name}: {e}")


def _export_tables(tables: Any, output_dir: Path, base_name: str, output_format: str) -> None:
    """Export tables to the specified format."""
    export_map: dict[str, tuple[str, str, str | None]] = {
        'csv': (f'{base_name}.csv', 'csv', 'multiple CSV files if >1 table'),
        'json': (f'{base_name}.json', 'json', None),
        'excel': (f'{base_name}.xlsx', 'excel', None),
        'html': (f'{base_name}.html', 'html', None),
        'markdown': (f'{base_name}.md', 'markdown', None),
        'sqlite': (f'{base_name}.db', 'sqlite', None),
    }
    
    if output_format not in export_map:
        logger.error(f"Unknown output format: {output_format}")
        return
    
    filename, fmt, note = export_map[output_format]
    output_path = output_dir / filename
    
    # CSV format needs special handling (no extension in path)
    if output_format == 'csv':
        tables.export(str(output_dir / base_name) + '.csv', f=fmt)  # type: ignore[attr-defined]
        logger.info(f"Exported to {output_dir}/ ({note})")
    else:
        tables.export(str(output_path), f=fmt)  # type: ignore[attr-defined]
        logger.info(f"Exported to {output_path}")


def process_directory(
    input_dir: Path,
    output_dir: Path,
    output_format: str = 'csv',
    flavor: str = 'stream',
    recursive: bool = False,
    pages: str = 'all',
    skip_existing: bool = True,
    validate_only: bool = False
) -> bool:
    """
    Process all PDF files in a directory.

    Args:
        input_dir: Directory containing PDF files
        output_dir: Directory to save output files
        output_format: Output format
        flavor: Camelot flavor ('stream' or 'lattice')
        recursive: Whether to search subdirectories
        pages: Pages to process (default: 'all', or e.g., '1', '1-3', '1,3,5')
        skip_existing: Whether to skip PDFs that have already been processed
        validate_only: Only validate that all PDFs are processed, don't actually process
        
    Returns:
        True if all PDFs are processed (or processing succeeded), False if validation failed
    """
    pattern = '**/*.pdf' if recursive else '*.pdf'
    pdf_files = sorted(input_dir.glob(pattern))

    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return True

    logger.info(f"Found {len(pdf_files)} PDF file(s) to {'validate' if validate_only else 'process'}")

    unprocessed_files = []
    
    for pdf_path in pdf_files:
        relative_path = pdf_path.relative_to(input_dir)
        pdf_output_dir = output_dir / relative_path.parent
        
        if validate_only:
            # In validate mode, check if PDF has been processed
            if not should_skip_pdf(pdf_path, pdf_output_dir):
                logger.error(f"❌ {pdf_path.name} has not been processed")
                unprocessed_files.append(pdf_path.name)
            else:
                logger.info(f"✓ {pdf_path.name} is processed")
        else:
            # Normal processing mode
            extract_tables_from_pdf(
                pdf_path, 
                pdf_output_dir, 
                output_format, 
                flavor, 
                pages, 
                skip_existing
            )

    if validate_only:
        if unprocessed_files:
            logger.error(f"Validation failed: {len(unprocessed_files)} unprocessed file(s)")
            return False
        logger.info("✓ Validation passed: All PDFs are processed")
        return True
    
    logger.info("Processing complete!")
    return True
