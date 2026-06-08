"""
main.py
Entry point for the Personal Finance Tracker application.
Wires together all modules and drives the menu loop.
"""

from datetime import datetime
from pathlib import Path

from finance_tracker.expense import Expense, ValidationError, VALID_CATEGORIES
from finance_tracker.expense_manager import ExpenseManager
from finance_tracker import file_handler as fh
from finance_tracker import reports
from finance_tracker import utils


BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║         PERSONAL  FINANCE  TRACKER  v1.0                 ║
║                   Week 4 Final Project                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

MENU = """
┌──────────────────────────────────────────┐
│               MAIN  MENU                 │
├──────────────────────────────────────────┤
│  1. Add New Expense                       │
│  2. View All Expenses                     │
│  3. Search & Filter Expenses              │
│  4. Delete an Expense                     │
│  5. Generate Monthly Report               │
│  6. View Category Breakdown               │
│  7. Set / Update Budget                   │
│  8. View Budget Status                    │
│  9. View Statistics                       │
│ 10. Export Data to CSV                    │
│ 11. Import Data from CSV                  │
│ 12. Backup / Restore Data                 │
│  0. Save & Exit                           │
└──────────────────────────────────────────┘
"""


class FinanceTrackerApp:
    """Main application class — orchestrates user interaction."""

    def __init__(self):
        self.manager = ExpenseManager()
        self._load_on_startup()

    # ------------------------------------------------------------------ #
    # Startup / shutdown
    # ------------------------------------------------------------------ #

    def _load_on_startup(self):
        """Try to load existing data. Create empty store if none found."""
        try:
            expenses, budgets = fh.load_expenses()
            self.manager.load_from_list(expenses)
            self.manager.budgets = budgets
            print(f"  Loaded {len(self.manager.all_expenses())} expense(s) from file.")
        except FileNotFoundError:
            print("  No existing data found — starting fresh.")
        except (ValueError, PermissionError) as e:
            print(f"  [WARNING] Could not load data: {e}")
            print("  Starting with empty data. Your old file may be corrupted.")

    def _save(self) -> bool:
        """Persist current data to JSON."""
        return fh.save_expenses(self.manager.to_list(), self.manager.budgets)

    # ------------------------------------------------------------------ #
    # Run loop
    # ------------------------------------------------------------------ #

    def run(self):
        print(BANNER)
        while True:
            print(MENU)
            choice = input("  Enter choice: ").strip()

            if choice == "1":
                self._add_expense()
            elif choice == "2":
                self._view_all()
            elif choice == "3":
                self._search()
            elif choice == "4":
                self._delete_expense()
            elif choice == "5":
                self._monthly_report()
            elif choice == "6":
                self._category_breakdown()
            elif choice == "7":
                self._set_budget()
            elif choice == "8":
                self._budget_status()
            elif choice == "9":
                self._statistics()
            elif choice == "10":
                self._export_csv()
            elif choice == "11":
                self._import_csv()
            elif choice == "12":
                self._backup_restore()
            elif choice == "0":
                self._exit()
                break
            else:
                print("  [!] Invalid option. Enter a number from 0 to 12.")

    # ------------------------------------------------------------------ #
    # Menu actions
    # ------------------------------------------------------------------ #

    def _add_expense(self):
        print("\n  ── ADD NEW EXPENSE ──────────────────────────────")
        try:
            amount = utils.prompt_float("  Amount (Rs): ")
            if amount is None:
                print("  Cancelled.")
                return

            category = utils.prompt_category("Select category:")
            if category is None:
                print("  Cancelled.")
                return

            description = utils.prompt_non_empty("  Description: ")
            if description is None:
                print("  Description cannot be blank. Cancelled.")
                return

            date = utils.prompt_date("  Date (YYYY-MM-DD)")

            exp = Expense(
                amount=amount,
                category=category,
                description=description,
                date=date,
            )
            self.manager.add_expense(exp)

            if self._save():
                print(f"\n  ✓ Expense added (ID {exp.expense_id}):")
                print(f"    {exp}")
            else:
                print("  [!] Expense added in memory but could NOT be saved to disk.")

        except ValidationError as e:
            print(f"  [!] Validation error: {e}")

    def _view_all(self):
        print("\n  ── ALL EXPENSES ──────────────────────────────────")
        expenses = self.manager.all_expenses()
        if not expenses:
            print("  No expenses recorded yet.")
            return
        print(f"\n  {'ID':<6} {'DATE':<12} {'CATEGORY':<15} {'AMOUNT':>12}  DESCRIPTION")
        print(f"  {'─'*65}")
        for exp in expenses:
            desc = exp.description[:35] + "…" if len(exp.description) > 36 else exp.description
            print(f"  {exp.expense_id:<6} {exp.date:<12} {exp.category:<15} Rs{exp.amount:>10,.2f}  {desc}")
        print(f"  {'─'*65}")
        total = self.manager.total()
        print(f"  {'TOTAL':<6} {'':<12} {'':<15} Rs{total:>10,.2f}")

    def _search(self):
        print("\n  ── SEARCH & FILTER ─────────────────────────────")
        print("  (Press Enter to skip any filter)\n")

        keyword = input("  Keyword in description/category: ").strip() or None

        # Category filter
        cat_choice = utils.prompt_category("Filter by category? (0 to skip)")
        # If user chose 0 / cancelled, cat_choice is None

        month_raw = input("  Month (YYYY-MM, or blank): ").strip() or None
        if month_raw:
            try:
                year, month = utils.parse_year_month(month_raw)
                month_str = f"{year:04d}-{month:02d}"
            except ValueError as e:
                print(f"  [!] {e} — month filter ignored.")
                month_str = None
        else:
            month_str = None

        min_amt_raw = input("  Min amount (or blank): ").strip()
        max_amt_raw = input("  Max amount (or blank): ").strip()
        min_amt = float(min_amt_raw) if min_amt_raw else None
        max_amt = float(max_amt_raw) if max_amt_raw else None

        results = self.manager.search(
            keyword=keyword,
            category=cat_choice,
            month=month_str,
            min_amount=min_amt,
            max_amount=max_amt,
        )

        print(f"\n  Found {len(results)} expense(s):\n")
        if not results:
            print("  No matching expenses.")
            return

        for exp in results:
            print(f"  {exp}")
        print(f"\n  Total: Rs{self.manager.total(results):,.2f}")

    def _delete_expense(self):
        print("\n  ── DELETE EXPENSE ───────────────────────────────")
        raw = input("  Enter expense ID to delete (or blank to cancel): ").strip()
        if not raw:
            print("  Cancelled.")
            return
        try:
            eid = int(raw)
        except ValueError:
            print("  [!] ID must be a number.")
            return

        exp = self.manager.get_by_id(eid)
        if exp is None:
            print(f"  [!] No expense found with ID {eid}.")
            return

        print(f"\n  About to delete: {exp}")
        if not utils.prompt_yes_no("  Confirm?"):
            print("  Cancelled.")
            return

        self.manager.remove_expense(eid)
        if self._save():
            print(f"  ✓ Expense {eid} deleted.")
        else:
            print("  [!] Deleted in memory but could not save to disk.")

    def _monthly_report(self):
        print("\n  ── MONTHLY REPORT ───────────────────────────────")
        year, month = utils.current_year_month()
        raw = input(f"  Month (YYYY-MM) [{year:04d}-{month:02d}]: ").strip()
        if raw:
            try:
                year, month = utils.parse_year_month(raw)
            except ValueError as e:
                print(f"  [!] {e}")
                return
        expenses = self.manager.expenses_for_month(year, month)
        print(reports.monthly_report(expenses, year, month))

    def _category_breakdown(self):
        print("\n  ── CATEGORY BREAKDOWN ───────────────────────────")
        print("  1. All time")
        print("  2. Specific month")
        choice = input("  Choose [1/2]: ").strip()
        if choice == "2":
            year, month = utils.current_year_month()
            raw = input(f"  Month (YYYY-MM) [{year:04d}-{month:02d}]: ").strip()
            if raw:
                try:
                    year, month = utils.parse_year_month(raw)
                except ValueError as e:
                    print(f"  [!] {e}")
                    return
            expenses = self.manager.expenses_for_month(year, month)
        else:
            expenses = self.manager.all_expenses()
        print(reports.category_breakdown(expenses))

    def _set_budget(self):
        print("\n  ── SET / UPDATE BUDGET ──────────────────────────")
        print("  Set a monthly budget for a category.\n")
        cat = utils.prompt_category("Which category?")
        if cat is None:
            print("  Cancelled.")
            return
        current = self.manager.budgets.get(cat, 0)
        print(f"  Current budget for {cat}: Rs{current:,.2f}")
        amount = utils.prompt_float("  New budget amount (Rs): ")
        if amount is None:
            print("  Cancelled.")
            return
        try:
            self.manager.set_budget(cat, amount)
            if self._save():
                print(f"  ✓ Budget for {cat} set to Rs{amount:,.2f}")
            else:
                print("  [!] Budget updated in memory but could not save.")
        except ValidationError as e:
            print(f"  [!] {e}")

    def _budget_status(self):
        print("\n  ── BUDGET STATUS ────────────────────────────────")
        year, month = utils.current_year_month()
        raw = input(f"  Month (YYYY-MM) [{year:04d}-{month:02d}]: ").strip()
        if raw:
            try:
                year, month = utils.parse_year_month(raw)
            except ValueError as e:
                print(f"  [!] {e}")
                return
        status = self.manager.budget_status(year, month)
        print(reports.budget_report(status))

    def _statistics(self):
        expenses = self.manager.all_expenses()
        print(reports.statistics_report(expenses))

    def _export_csv(self):
        print("\n  ── EXPORT TO CSV ────────────────────────────────")
        expenses = self.manager.to_list()
        if not expenses:
            print("  No expenses to export.")
            return
        path = fh.export_to_csv(expenses)
        if path:
            print(f"  ✓ Exported {len(expenses)} record(s) to:\n    {path}")
        else:
            print("  [!] Export failed.")

    def _import_csv(self):
        print("\n  ── IMPORT FROM CSV ──────────────────────────────")
        raw = input("  Path to CSV file: ").strip()
        if not raw:
            print("  Cancelled.")
            return
        csv_path = Path(raw).expanduser()
        try:
            records = fh.import_from_csv(csv_path)
        except (FileNotFoundError, ValueError, OSError) as e:
            print(f"  [!] {e}")
            return

        print(f"  Found {len(records)} record(s). This will ADD them to existing data.")
        if not utils.prompt_yes_no("  Continue?"):
            print("  Cancelled.")
            return

        added = 0
        for rec in records:
            try:
                rec.pop("expense_id", None)   # let manager assign fresh IDs
                exp = Expense.from_dict(rec)
                self.manager.add_expense(exp)
                added += 1
            except ValidationError as e:
                print(f"  [!] Skipped one record: {e}")

        if self._save():
            print(f"  ✓ Imported {added} expense(s).")
        else:
            print("  [!] Imported in memory but could not save.")

    def _backup_restore(self):
        print("\n  ── BACKUP / RESTORE ─────────────────────────────")
        print("  1. Create backup now")
        print("  2. Restore from backup")
        print("  0. Back")
        choice = input("  Choose [0-2]: ").strip()

        if choice == "1":
            path = fh.create_backup()
            if path:
                print(f"  ✓ Backup saved to:\n    {path}")

        elif choice == "2":
            backups = fh.list_backups()
            if not backups:
                print("  No backups found.")
                return
            print("\n  Available backups:")
            for i, bp in enumerate(backups[:10], 1):
                print(f"    {i}. {bp.name}")
            raw = input("  Select backup number (or 0 to cancel): ").strip()
            if raw == "0":
                print("  Cancelled.")
                return
            try:
                idx = int(raw) - 1
                if not (0 <= idx < len(backups[:10])):
                    raise ValueError
            except ValueError:
                print("  [!] Invalid selection.")
                return

            chosen = backups[idx]
            print(f"\n  Restoring: {chosen.name}")
            print("  [WARNING] This will overwrite your current data!")
            if not utils.prompt_yes_no("  Are you sure?"):
                print("  Cancelled.")
                return

            if fh.restore_backup(chosen):
                self._load_on_startup()
                print(f"  ✓ Restored from {chosen.name}")
            else:
                print("  [!] Restore failed.")

    def _exit(self):
        print("\n  Saving data...")
        if self._save():
            print("  ✓ Data saved.")
        else:
            print("  [!] Could not save — check file permissions.")
        print("\n  Thank you for using Personal Finance Tracker! 👋")
        print("  ─" * 33 + "\n")


def main():
    app = FinanceTrackerApp()
    app.run()


if __name__ == "__main__":
    main()
