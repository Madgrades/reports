"""Tests for metadata module."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from pdf_table_extractor.metadata import FileMetadata, load_metadata, save_metadata, should_skip_pdf


def test_file_metadata_from_dict() -> None:
    """Test creating FileMetadata from dictionary."""
    data: dict[str, Any] = {'size': 1024, 'mtime': 123456.789, 'hash': 'abc123'}
    metadata = FileMetadata.from_dict(data)
    
    assert metadata.size == 1024
    assert metadata.mtime == 123456.789
    assert metadata.hash == 'abc123'


def test_file_metadata_to_dict() -> None:
    """Test converting FileMetadata to dictionary."""
    metadata = FileMetadata(size=1024, mtime=123456.789, hash='abc123')
    data = metadata.to_dict()
    
    assert data == {'size': 1024, 'mtime': 123456.789, 'hash': 'abc123'}


def test_file_metadata_matches() -> None:
    """Test metadata matching."""
    metadata1 = FileMetadata(size=1024, mtime=123456.789, hash='abc123')
    metadata2 = FileMetadata(size=1024, mtime=123456.789, hash='abc123')
    metadata3 = FileMetadata(size=2048, mtime=123456.789, hash='abc123')
    
    assert metadata1.matches(metadata2)
    assert not metadata1.matches(metadata3)


def test_load_metadata_not_exists(tmp_path: Path) -> None:
    """Test loading metadata when file doesn't exist."""
    result = load_metadata(tmp_path)
    assert result is None


def test_save_and_load_metadata(tmp_path: Path) -> None:
    """Test saving and loading metadata."""
    metadata = FileMetadata(size=1024, mtime=123456.789, hash='abc123')
    
    save_metadata(tmp_path, metadata)
    loaded = load_metadata(tmp_path)
    
    assert loaded is not None
    assert loaded.matches(metadata)


def test_should_skip_pdf_no_output_dir(tmp_path: Path) -> None:
    """Test skipping when output directory doesn't exist."""
    pdf_path = tmp_path / 'test.pdf'
    pdf_path.write_text('fake pdf')
    output_dir = tmp_path / 'output'
    
    assert not should_skip_pdf(pdf_path, output_dir)


@patch('pdf_table_extractor.metadata.FileMetadata.from_file')
def test_should_skip_pdf_unchanged(mock_from_file: Mock, tmp_path: Path) -> None:
    """Test skipping when PDF hasn't changed."""
    pdf_path = tmp_path / 'test.pdf'
    pdf_path.write_text('fake pdf')
    
    output_dir = tmp_path / 'output'
    pdf_output_dir = output_dir / 'test'
    pdf_output_dir.mkdir(parents=True)
    
    metadata = FileMetadata(size=1024, mtime=123456.789, hash='abc123')
    save_metadata(pdf_output_dir, metadata)
    
    mock_from_file.return_value = metadata
    
    assert should_skip_pdf(pdf_path, output_dir)
