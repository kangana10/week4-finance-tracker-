"""
file_handler.py
Handles all file I/O: JSON persistence, CSV export/import, and backups.
"""

import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# Default paths (relative to project root)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backup"
EXPORTS_DIR = DATA_DIR / "exports"
EXPENSES_FILE = DATA_DIR / "expenses.json"


def ensure_directories():
    """Create data directories if they don't exist."""
    for directory in (DATA_DIR, BACKUP_DIR, EXPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ #
# JSON persistence
# ------------------------------------------------------------------ #

def save_expenses(expenses: List[dict], budgets: dict, filepath: Path = EXPENSES_FILE) -> bool:
    """
    Save expenses and budgets to a JSON file.
    Returns True on success, False on failure.
    """
    ensure_directories()
    payload = {
        "version": "1.0",
        "last_saved": datetime.now().isoformat(),
        "budgets": budgets,
        "expenses": expenses,
    }
    try:
        # Write to a temp file first, then rename (atomic write)
        tmp_path = filepath.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        tmp_path.replace(filepath)
        return True
    except PermissionError:
        print(f"  [ERROR] Permission denied: cannot write to {filepath}")
        return False
    except OSError as e:
        print(f"  [ERROR] File system error: {e}")
        return False


def load_expenses(filepath: Path = EXPENSES_FILE) -> Tuple[List[dict], dict]:
    """
    Load expenses and budgets from JSON file.
    Returns (expenses_list, budgets_dict).
    Raises FileNotFoundError if file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
        expenses = payload.get("expenses", [])
        budgets = payload.get("budgets", {})
        return expenses, budgets
    except json.JSONDecodeError as e:
        raise ValueError(f"Corrupted data file ({filepath}): {e}")
    except PermissionError:
        raise PermissionError(f"Permission denied: cannot read {filepath}")


# ------------------------------------------------------------------ #
# Backup & restore
# ------------------------------------------------------------------ #

def create_backup(filepath: Path = EXPENSES_FILE) -> Optional[Path]:
    """
    Copy the current data file to the backup directory with a timestamp.
    Returns the backup path on success, None if source does not exist.
    """
    ensure_directories()
    if not filepath.exists():
        print("  [INFO] No data file to back up yet.")
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"expenses_{timestamp}.json"
    try:
        shutil.copy2(filepath, backup_path)
        return backup_path
    except OSError as e:
        print(f"  [ERROR] Backup failed: {e}")
        return None


def list_backups() -> List[Path]:
    """Return a sorted list of backup files (most recent first)."""
    ensure_directories()
    backups = sorted(BACKUP_DIR.glob("expenses_*.json"), reverse=True)
    return backups


def restore_backup(backup_path: Path, filepath: Path = EXPENSES_FILE) -> bool:
    """
    Restore a backup file to the main data location.
    Returns True on success.
    """
    if not backup_path.exists():
        print(f"  [ERROR] Backup not found: {backup_path}")
        return False
    try:
        shutil.copy2(backup_path, filepath)
        return True
    except OSError as e:
        print(f"  [ERROR] Restore failed: {e}")
        return False


# ------------------------------------------------------------------ #
# CSV export / import
# ------------------------------------------------------------------ #

CSV_HEADERS = ["expense_id", "date", "amount", "category", "description"]


def export_to_csv(expenses: List[dict], filename: Optional[str] = None) -> Optional[Path]:
    """
    Export a list of expense dicts to a CSV file in the exports directory.
    Returns the export path on success, None on failure.
    """
    ensure_directories()
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"expenses_{timestamp}.csv"
    export_path = EXPORTS_DIR / filename
    try:
        with open(export_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(expenses)
        return export_path
    except OSError as e:
        print(f"  [ERROR] CSV export failed: {e}")
        return None


def import_from_csv(filepath: Path) -> List[dict]:
    """
    Import expense dicts from a CSV file.
    Returns a list of dicts (IDs will be re-assigned by ExpenseManager).
    """
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    results = []
    try:
        with open(filepath, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["amount"] = float(row["amount"])
                row["expense_id"] = int(row["expense_id"]) if row.get("expense_id") else None
                results.append(row)
        return results
    except (KeyError, ValueError) as e:
        raise ValueError(f"Malformed CSV file: {e}")
    except OSError as e:
        raise OSError(f"Cannot read CSV file: {e}")
