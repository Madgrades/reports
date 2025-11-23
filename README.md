# reports

## PDF Table Extraction

This project provides a flexible tool to extract tables from PDF files using Camelot.

### Quick Start with Dev Container

1. Open this project in VS Code
2. When prompted, click "Reopen in Container" (or use Command Palette: "Dev Containers: Reopen in Container")
3. Wait for the container to build (dependencies install automatically via `onCreateCommand`)
4. If you rebuilt the container, install the package:
   ```bash
   make install
   ```
5. Run the CLI tool:
   ```bash
   extract-tables data/ csv/ --recursive
   ```

### Manual Setup

If you prefer not to use the dev container:

```bash
# Clone with submodules
git clone --recurse-submodules <repository-url>

# Or if already cloned, initialize submodules
git submodule update --init --recursive

# Install system dependencies (Ubuntu/Debian)
bash scripts/install-system-deps.sh

# Install Python dependencies and package
bash scripts/install.sh
```

### Usage

The package installs a CLI command `extract-tables`:

```bash
# Basic usage: extract to CSV
extract-tables data/ csv/

# Extract to JSON format
extract-tables data/ output/ --format json

# Use lattice flavor (for PDFs with clear table borders)
extract-tables data/ csv/ --flavor lattice

# Process subdirectories recursively
extract-tables data/ csv/ --recursive

# Validate all PDFs have been processed (for CI)
extract-tables -f csv -r --validate data csv

# See all options
extract-tables --help
```

Or use the Python module directly:

```bash
python -m pdf_table_extractor.extract_tables data/ csv/ --recursive
```

### Supported Output Formats

- **csv**: CSV files (one per table)
- **json**: JSON format
- **excel**: Excel spreadsheet (.xlsx)
- **html**: HTML table
- **markdown**: Markdown table
- **sqlite**: SQLite database

### Camelot Flavors

- **stream** (default): Best for PDFs without clear table borders
- **lattice**: Best for PDFs with visible table lines

### CI/CD Validation

To validate that all PDFs have been processed (without actually processing them), use the `--validate` flag:

```bash
extract-tables -f csv -r --validate data csv
```

This is useful in CI to ensure the extraction has been run before committing. It:
- Checks metadata to verify all PDFs are processed
- Exits with code 1 if any PDFs are unprocessed
- Runs in <1 second (doesn't process PDFs)
- Uses the same validation logic as the main tool

Example Makefile target:
```makefile
validate:
	extract-tables -f csv -r --validate data csv
```

See `.github/workflows/ci.yml` for a GitHub Actions example.
