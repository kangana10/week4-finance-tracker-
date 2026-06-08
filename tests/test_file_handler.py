"""
test_file_handler.py
Tests for save, load, backup, restore, CSV export/import.
"""

import json
import pytest
from pathlib import Path

from finance_tracker import file_handler as fh


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

SAMPLE_EXPENSES = [
    {"expense_id": 1, "date": "2024-06-01", "amount": 100.0, "category": "Food",      "description": "Lunch"},
    {"expense_id": 2, "date": "2024-06-02", "amount": 250.0, "category": "Transport", "description": "Auto"},
]

SAMPLE_BUDGETS = {"Food": 3000.0, "Transport": 1500.0}


@pytest.fixture
def tmp_json(tmp_path):
    """Return a temp path for the JSON file."""
    return tmp_path / "expenses.json"


@pytest.fixture
def tmp_backup_dir(tmp_path, monkeypatch):
    """Redirect backup directory to tmp_path/backup."""
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    monkeypatch.setattr(fh, "BACKUP_DIR", backup_dir)
    return backup_dir


@pytest.fixture
def tmp_exports_dir(tmp_path, monkeypatch):
    """Redirect exports directory to tmp_path/exports."""
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    monkeypatch.setattr(fh, "EXPORTS_DIR", exports_dir)
    return exports_dir


# ────────────────────────────────────────────────────────────────────────────
# 1. JSON save / load
# ────────────────────────────────────────────────────────────────────────────

class TestSaveLoad:
    def test_save_creates_file(self, tmp_json):
        ok = fh.save_expenses(SAMPLE_EXPENSES, SAMPLE_BUDGETS, filepath=tmp_json)
        assert ok is True
        assert tmp_json.exists()

    def test_load_returns_correct_data(self, tmp_json):
        fh.save_expenses(SAMPLE_EXPENSES, SAMPLE_BUDGETS, filepath=tmp_json)
        expenses, budgets = fh.load_expenses(filepath=tmp_json)
        assert len(expenses) == 2
        assert expenses[0]["description"] == "Lunch"
        assert budgets["Food"] == 3000.0

    def test_load_missing_file_raises(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            fh.load_expenses(filepath=missing)

    def test_load_corrupted_file_raises(self, tmp_json):
        tmp_json.write_text("NOT VALID JSON", encoding="utf-8")
        with pytest.raises(ValueError, match="Corrupted"):
            fh.load_expenses(filepath=tmp_json)

    def test_save_load_roundtrip(self, tmp_json):
        fh.save_expenses(SAMPLE_EXPENSES, SAMPLE_BUDGETS, filepath=tmp_json)
        expenses, budgets = fh.load_expenses(filepath=tmp_json)
        assert expenses == SAMPLE_EXPENSES
        assert budgets == SAMPLE_BUDGETS

    def test_json_file_has_version_field(self, tmp_json):
        fh.save_expenses(SAMPLE_EXPENSES, {}, filepath=tmp_json)
        raw = json.loads(tmp_json.read_text())
        assert raw.get("version") == "1.0"

    def test_empty_expenses_saves_ok(self, tmp_json):
        ok = fh.save_expenses([], {}, filepath=tmp_json)
        assert ok is True
        expenses, _ = fh.load_expenses(filepath=tmp_json)
        assert expenses == []


# ────────────────────────────────────────────────────────────────────────────
# 2. Backup & restore
# ────────────────────────────────────────────────────────────────────────────

class TestBackupRestore:
    def test_backup_creates_file(self, tmp_json, tmp_backup_dir):
        fh.save_expenses(SAMPLE_EXPENSES, SAMPLE_BUDGETS, filepath=tmp_json)
        backup_path = fh.create_backup(filepath=tmp_json)
        assert backup_path is not None
        assert backup_path.exists()

    def test_backup_no_source_returns_none(self, tmp_path, tmp_backup_dir):
        missing = tmp_path / "nosuchfile.json"
        result = fh.create_backup(filepath=missing)
        assert result is None

    def test_list_backups_returns_sorted(self, tmp_json, tmp_backup_dir):
        """Create two backups with distinct names and check they are listed newest-first."""
        import time
        fh.save_expenses(SAMPLE_EXPENSES, {}, filepath=tmp_json)
        b1 = fh.create_backup(filepath=tmp_json)
        time.sleep(1.1)                              # ensure different timestamp
        b2 = fh.create_backup(filepath=tmp_json)
        backups = fh.list_backups()
        assert len(backups) == 2
        # Most recent first (b2 > b1 lexicographically because timestamp is later)
        assert backups[0].name == b2.name
        assert backups[1].name == b1.name

    def test_restore_overwrites_current(self, tmp_json, tmp_backup_dir):
        # Save original, back it up
        fh.save_expenses(SAMPLE_EXPENSES, {}, filepath=tmp_json)
        backup = fh.create_backup(filepath=tmp_json)

        # Overwrite with empty
        fh.save_expenses([], {}, filepath=tmp_json)
        expenses_before, _ = fh.load_expenses(filepath=tmp_json)
        assert expenses_before == []

        # Restore
        ok = fh.restore_backup(backup, filepath=tmp_json)
        assert ok is True
        expenses_after, _ = fh.load_expenses(filepath=tmp_json)
        assert len(expenses_after) == 2

    def test_restore_missing_backup_returns_false(self, tmp_json, tmp_backup_dir):
        missing = tmp_backup_dir / "expenses_19990101_000000.json"
        assert fh.restore_backup(missing, filepath=tmp_json) is False


# ────────────────────────────────────────────────────────────────────────────
# 3. CSV export / import
# ────────────────────────────────────────────────────────────────────────────

class TestCsvExportImport:
    def test_export_creates_csv(self, tmp_exports_dir):
        path = fh.export_to_csv(SAMPLE_EXPENSES, filename="test_export.csv")
        assert path is not None
        assert path.exists()
        assert path.suffix == ".csv"

    def test_export_correct_row_count(self, tmp_exports_dir):
        path = fh.export_to_csv(SAMPLE_EXPENSES, filename="rows.csv")
        with open(path) as f:
            lines = f.readlines()
        # 1 header + 2 data rows
        assert len(lines) == 3

    def test_import_roundtrip(self, tmp_exports_dir):
        path = fh.export_to_csv(SAMPLE_EXPENSES, filename="roundtrip.csv")
        imported = fh.import_from_csv(path)
        assert len(imported) == 2
        assert imported[0]["description"] == "Lunch"
        assert imported[1]["amount"] == 250.0

    def test_import_missing_file_raises(self, tmp_path):
        missing = tmp_path / "nope.csv"
        with pytest.raises(FileNotFoundError):
            fh.import_from_csv(missing)

    def test_export_empty_list(self, tmp_exports_dir):
        path = fh.export_to_csv([], filename="empty.csv")
        assert path is not None
        imported = fh.import_from_csv(path)
        assert imported == []
