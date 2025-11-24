"""PDF table extraction processor."""

import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import camelot  # pyright: ignore[reportMissingImports]

from pdf_table_extractor.metadata import FileMetadata, save_metadata, should_skip_pdf

logger = logging.getLogger(__name__)


def extract_tables_from_pdf(
    pdf_path: Path,
    output_dir: Path,
    output_format: str = 'csv',
    flavor: str = 'stream',
    pages: str = 'all',
    skip_existing: bool = True,
) -> tuple[str, bool, str | None]:
    """
    Extract tables from a PDF file and save to the specified format.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save output files
        output_format: Output format (csv, json, excel, html, markdown, sqlite)
        flavor: Camelot flavor ('stream' or 'lattice')
        pages: Pages to process (default: 'all', or e.g., '1', '1-3', '1,3,5')
        skip_existing: Whether to skip PDFs that have already been processed

    Returns:
        Tuple of (filename, success, error_message)
    """
    if skip_existing:
        should_skip, _skip_reason = should_skip_pdf(pdf_path, output_dir)
        if should_skip:
            return (pdf_path.name, True, 'skipped (already processed)')

    try:
        tables: Any = camelot.read_pdf(str(pdf_path), flavor=flavor, pages=pages)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

        if not tables:
            return (pdf_path.name, True, 'no tables found')

        base_name = pdf_path.stem
        pdf_output_dir = output_dir / base_name
        pdf_output_dir.mkdir(parents=True, exist_ok=True)

        _export_tables(tables, pdf_output_dir, base_name, output_format)

        # Save metadata after successful processing
        metadata = FileMetadata.from_file(pdf_path)
        save_metadata(pdf_output_dir, metadata)

        return (pdf_path.name, True, f'{len(tables)} table(s)')  # pyright: ignore[reportUnknownArgumentType]

    except Exception as e:
        return (pdf_path.name, False, str(e))


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
        raise ValueError(f'Unknown output format: {output_format}')

    filename, fmt, _ = export_map[output_format]
    output_path = output_dir / filename

    # CSV format needs special handling (no extension in path)
    if output_format == 'csv':
        tables.export(str(output_dir / base_name) + '.csv', f=fmt)
    else:
        tables.export(str(output_path), f=fmt)


def _process_single_pdf(
    pdf_path: Path,
    input_dir: Path,
    output_dir: Path,
    output_format: str,
    flavor: str,
    pages: str,
    skip_existing: bool,
) -> tuple[str, bool, str | None]:
    """Process a single PDF file (used for parallel processing)."""
    relative_path = pdf_path.relative_to(input_dir)
    pdf_output_dir = output_dir / relative_path.parent
    return extract_tables_from_pdf(
        pdf_path, pdf_output_dir, output_format, flavor, pages, skip_existing
    )


def process_directory(
    input_dir: Path,
    output_dir: Path,
    output_format: str = 'csv',
    flavor: str = 'stream',
    recursive: bool = False,
    pages: str = 'all',
    skip_existing: bool = True,
    validate_only: bool = False,
    max_workers: int | None = None,
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
        max_workers: Maximum number of parallel workers (default: number of CPUs)

    Returns:
        True if all PDFs are processed (or processing succeeded), False if validation failed
    """
    pattern = '**/*.pdf' if recursive else '*.pdf'
    pdf_files = sorted(input_dir.glob(pattern))

    if not pdf_files:
        logger.warning(f'No PDF files found in {input_dir}')
        return True

    if max_workers is None:
        max_workers = os.cpu_count() or 1

    logger.info(
        f'Found {len(pdf_files)} PDF file(s) to {"validate" if validate_only else "process"}'
    )
    if not validate_only:
        logger.info(f'Using {max_workers} parallel worker(s)')

    unprocessed_files: list[str] = []

    if validate_only:
        # Validation mode - check if PDFs are processed
        for pdf_path in pdf_files:
            relative_path = pdf_path.relative_to(input_dir)
            pdf_output_dir = output_dir / relative_path.parent

            should_skip, skip_reason = should_skip_pdf(pdf_path, pdf_output_dir)
            if not should_skip:
                logger.error(f'❌ {pdf_path.name}: {skip_reason}')
                unprocessed_files.append(pdf_path.name)
            else:
                logger.info(f'✓ {pdf_path.name} is processed')

        if unprocessed_files:
            logger.error(f'Validation failed: {len(unprocessed_files)} unprocessed file(s)')
            return False
        logger.info('✓ Validation passed: All PDFs are processed')
        return True

    # Processing mode - parallel extraction
    success_count = 0
    skipped_count = 0
    error_count = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_pdf = {
            executor.submit(
                _process_single_pdf,
                pdf_path,
                input_dir,
                output_dir,
                output_format,
                flavor,
                pages,
                skip_existing,
            ): pdf_path
            for pdf_path in pdf_files
        }

        # Process results as they complete
        for future in as_completed(future_to_pdf):
            pdf_path = future_to_pdf[future]
            try:
                filename, success, message = future.result()
                if success:
                    if message and 'skipped' in message:
                        logger.info(f'⊘ {filename}: {message}')
                        skipped_count += 1
                    elif message and 'no tables' in message:
                        logger.warning(f'⚠ {filename}: {message}')
                        success_count += 1
                    else:
                        logger.info(f'✓ {filename}: {message}')
                        success_count += 1
                else:
                    logger.error(f'✗ {filename}: {message}')
                    error_count += 1
            except Exception as e:
                logger.error(f'✗ {pdf_path.name}: unexpected error: {e}')
                error_count += 1

    # Summary
    total = len(pdf_files)
    logger.info(
        f'\nProcessing complete: {success_count} processed, '
        f'{skipped_count} skipped, {error_count} errors (total: {total})'
    )

    return True
