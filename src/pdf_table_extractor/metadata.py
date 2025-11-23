"""Metadata handling for PDF processing."""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

METADATA_FILENAME = '.pdf_metadata.json'


@dataclass
class FileMetadata:
    """Metadata for a PDF file."""
    size: int
    mtime: float
    hash: str
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'FileMetadata':
        """Create metadata from a file."""
        stat = file_path.stat()
        return cls(
            size=stat.st_size,
            mtime=stat.st_mtime,
            hash=_compute_file_hash(file_path)
        )
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'FileMetadata':
        """Create metadata from a dictionary."""
        return cls(
            size=data['size'],
            mtime=data['mtime'],
            hash=data['hash']
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def matches(self, other: 'FileMetadata') -> bool:
        """Check if this metadata matches another."""
        return (
            self.size == other.size and
            self.mtime == other.mtime and
            self.hash == other.hash
        )


def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_metadata(output_dir: Path) -> FileMetadata | None:
    """Load metadata from output directory."""
    metadata_path = output_dir / METADATA_FILENAME
    if not metadata_path.exists():
        return None
    
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            return FileMetadata.from_dict(data)
    except Exception as e:
        logger.warning(f"Failed to load metadata from {metadata_path}: {e}")
        return None


def save_metadata(output_dir: Path, metadata: FileMetadata) -> None:
    """Save metadata to output directory."""
    metadata_path = output_dir / METADATA_FILENAME
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save metadata to {metadata_path}: {e}")


def should_skip_pdf(pdf_path: Path, output_dir: Path) -> bool:
    """Check if PDF should be skipped based on metadata."""
    pdf_output_dir = output_dir / pdf_path.stem
    
    if not pdf_output_dir.exists():
        return False
    
    existing_metadata = load_metadata(pdf_output_dir)
    if not existing_metadata:
        return False
    
    current_metadata = FileMetadata.from_file(pdf_path)
    
    return existing_metadata.matches(current_metadata)
