"""
reports.py
Generates text-based reports and ASCII visualisations.
"""

from datetime import datetime
from typing import Dict, List, Optional

from finance_tracker.expense import Expense, VALID_CATEGORIES


# ------------------------------------------------------------------ #
# Formatting helpers
# ------------------------------------------------------------------ #

BAR_WIDTH = 30   # max bar length in characters


def _bar(value: float, max_value: float, width: int = BAR_WIDTH) -> str:
    """Return an ASCII progress bar."""
    if max_value == 0:
        return " " * width
    filled = int(round(value / max_value * width))
    return "█" * filled + "░" * (width - filled)


def _divider(char: str = "─", width: int = 65) -> str:
    return char * width


# ------------------------------------------------------------------ #
# Monthly report
# ------------------------------------------------------------------ #

def monthly_report(expenses: List[Expense], year: int, month: int) -> str:
    """Return a formatted monthly report string."""
    month_name = datetime(year, month, 1).strftime("%B %Y")
    lines = []

    lines.append(_divider("═"))
    lines.append(f"  MONTHLY REPORT  —  {month_name}".center(65))
    lines.append(_divider("═"))

    if not expenses:
        lines.append("  No expenses recorded for this period.")
        lines.append(_divider("═"))
        return "\n".join(lines)

    total = sum(e.amount for e in expenses)

    # Category breakdown
    cat_totals: Dict[str, float] = {}
    for exp in expenses:
        cat_totals[exp.category] = round(cat_totals.get(exp.category, 0) + exp.amount, 2)
    cat_totals = dict(sorted(cat_totals.items(), key=lambda x: x[1], reverse=True))
    max_cat_total = max(cat_totals.values())

    lines.append("")
    lines.append(f"  {'CATEGORY':<18} {'AMOUNT':>12}   {'SHARE':>6}   BAR")
    lines.append(f"  {_divider('-', 60)}")
    for cat, amt in cat_totals.items():
        share = amt / total * 100
        bar = _bar(amt, max_cat_total)
        lines.append(f"  {cat:<18} Rs{amt:>10,.2f}  {share:>5.1f}%   {bar}")

    lines.append(f"  {_divider('-', 60)}")
    lines.append(f"  {'TOTAL':<18} Rs{total:>10,.2f}")
    lines.append("")

    # Individual expenses
    lines.append(f"  {'#':<5} {'DATE':<12} {'CATEGORY':<15} {'AMOUNT':>12}  DESCRIPTION")
    lines.append(f"  {_divider('-', 60)}")
    for exp in sorted(expenses, key=lambda e: e.date):
        desc = exp.description[:28] + "…" if len(exp.description) > 29 else exp.description
        lines.append(
            f"  {exp.expense_id:<5} {exp.date:<12} {exp.category:<15} Rs{exp.amount:>10,.2f}  {desc}"
        )

    lines.append(_divider("═"))
    return "\n".join(lines)


# ------------------------------------------------------------------ #
# Category breakdown
# ------------------------------------------------------------------ #

def category_breakdown(expenses: List[Expense]) -> str:
    """Return an ASCII bar chart of spending by category."""
    lines = []
    lines.append(_divider("═"))
    lines.append("  CATEGORY BREAKDOWN".center(65))
    lines.append(_divider("═"))

    if not expenses:
        lines.append("  No expenses to analyse.")
        lines.append(_divider("═"))
        return "\n".join(lines)

    cat_totals: Dict[str, float] = {}
    for exp in expenses:
        cat_totals[exp.category] = round(cat_totals.get(exp.category, 0) + exp.amount, 2)

    total = sum(cat_totals.values())
    max_val = max(cat_totals.values())

    lines.append("")
    for cat in VALID_CATEGORIES:
        amt = cat_totals.get(cat, 0)
        if amt == 0:
            continue
        share = amt / total * 100
        bar = _bar(amt, max_val)
        lines.append(f"  {cat:<15} {bar}  Rs{amt:>9,.2f}  ({share:.1f}%)")

    lines.append("")
    lines.append(f"  {'ALL CATEGORIES':<15}   Total: Rs{total:,.2f}")
    lines.append(_divider("═"))
    return "\n".join(lines)


# ------------------------------------------------------------------ #
# Statistics
# ------------------------------------------------------------------ #

def statistics_report(expenses: List[Expense]) -> str:
    """Return a general statistics summary."""
    lines = []
    lines.append(_divider("═"))
    lines.append("  STATISTICS OVERVIEW".center(65))
    lines.append(_divider("═"))

    if not expenses:
        lines.append("  No expenses recorded yet.")
        lines.append(_divider("═"))
        return "\n".join(lines)

    amounts = [e.amount for e in expenses]
    total = sum(amounts)
    avg = total / len(amounts)
    min_exp = min(expenses, key=lambda e: e.amount)
    max_exp = max(expenses, key=lambda e: e.amount)

    # Monthly trend
    monthly: Dict[str, float] = {}
    for exp in expenses:
        key = exp.date[:7]
        monthly[key] = round(monthly.get(key, 0) + exp.amount, 2)
    monthly = dict(sorted(monthly.items()))

    lines.append("")
    lines.append(f"  Total Expenses Recorded : {len(expenses)}")
    lines.append(f"  Total Amount Spent      : Rs{total:,.2f}")
    lines.append(f"  Average per Expense     : Rs{avg:,.2f}")
    lines.append(f"  Smallest Expense        : Rs{min_exp.amount:,.2f}  ({min_exp.description[:35]})")
    lines.append(f"  Largest  Expense        : Rs{max_exp.amount:,.2f}  ({max_exp.description[:35]})")
    lines.append("")

    if len(monthly) > 1:
        lines.append("  MONTHLY TREND")
        lines.append(f"  {_divider('-', 55)}")
        max_m = max(monthly.values())
        for ym, amt in monthly.items():
            bar = _bar(amt, max_m, width=25)
            lines.append(f"  {ym}  {bar}  Rs{amt:>10,.2f}")
        lines.append("")

    lines.append(_divider("═"))
    return "\n".join(lines)


# ------------------------------------------------------------------ #
# Budget status
# ------------------------------------------------------------------ #

def budget_report(status: dict) -> str:
    """Return a budget-vs-spent report."""
    lines = []
    lines.append(_divider("═"))
    lines.append("  BUDGET STATUS".center(65))
    lines.append(_divider("═"))

    if not status:
        lines.append("  No budgets set. Use option 6 to set budgets.")
        lines.append(_divider("═"))
        return "\n".join(lines)

    lines.append("")
    lines.append(f"  {'CATEGORY':<18} {'BUDGET':>10}  {'SPENT':>10}  {'LEFT':>10}  STATUS")
    lines.append(f"  {_divider('-', 60)}")
    for cat, info in status.items():
        budget = info["budget"]
        spent = info["spent"]
        remaining = info["remaining"]
        if remaining < 0:
            flag = "OVER BUDGET"
        elif remaining < budget * 0.1:
            flag = "WARNING"
        else:
            flag = "OK"
        lines.append(
            f"  {cat:<18} Rs{budget:>8,.2f}  Rs{spent:>8,.2f}  Rs{remaining:>8,.2f}  {flag}"
        )

    lines.append(_divider("═"))
    return "\n".join(lines)
