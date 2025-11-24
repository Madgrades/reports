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
    hash: str

    @classmethod
    def from_file(cls, file_path: Path) -> 'FileMetadata':
        """Create metadata from a file."""
        stat = file_path.stat()
        return cls(size=stat.st_size, hash=_compute_file_hash(file_path))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'FileMetadata':
        """Create metadata from a dictionary."""
        return cls(size=data['size'], hash=data['hash'])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def matches(self, other: 'FileMetadata') -> bool:
        """Check if this metadata matches another."""
        # Only compare hash and size (content-based), not mtime (timestamp-based)
        # This ensures validation works in CI where file timestamps differ
        return self.size == other.size and self.hash == other.hash


def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open('rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_metadata(output_dir: Path) -> FileMetadata | None:
    """Load metadata from output directory."""
    metadata_path = output_dir / METADATA_FILENAME
    if not metadata_path.exists():
        return None

    try:
        with metadata_path.open() as f:
            data = json.load(f)
            return FileMetadata.from_dict(data)
    except Exception as e:
        logger.warning(f'Failed to load metadata from {metadata_path}: {e}')
        return None


def save_metadata(output_dir: Path, metadata: FileMetadata) -> None:
    """Save metadata to output directory."""
    metadata_path = output_dir / METADATA_FILENAME
    try:
        with metadata_path.open('w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
    except Exception as e:
        logger.warning(f'Failed to save metadata to {metadata_path}: {e}')


def should_skip_pdf(pdf_path: Path, output_dir: Path) -> tuple[bool, str]:
    """
    Check if PDF should be skipped based on metadata.

    Returns:
        Tuple of (should_skip, reason) where reason explains why it shouldn't be skipped
    """
    pdf_output_dir = output_dir / pdf_path.stem

    if not pdf_output_dir.exists():
        return (False, 'not processed (output directory missing)')

    existing_metadata = load_metadata(pdf_output_dir)
    if not existing_metadata:
        return (False, 'not processed (metadata missing)')

    current_metadata = FileMetadata.from_file(pdf_path)

    if existing_metadata.matches(current_metadata):
        return (True, '')

    # Metadata exists but doesn't match - file has changed
    changes = []
    if existing_metadata.size != current_metadata.size:
        changes.append(f'size: {existing_metadata.size} → {current_metadata.size}')
    if existing_metadata.hash != current_metadata.hash:
        changes.append('hash changed')

    reason = f'out of date ({", ".join(changes)})'
    return (False, reason)
