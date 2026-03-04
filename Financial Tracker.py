#Our idea for this final project was to create a useful project that can be used by everyone.
#Because of this, we decided to do a financial tracker, which allows you to input daily spending and
#see where you're at and the spending you've done this month. carlota

"""
Personal Finance Tracker (CSV-based) — User-friendly Quick Add

Change requested:
- Default date is TODAY (no prompt for date)
- User only types ONE line: category + amount (+ optional note)
  Examples:
    food 7.50 arepa + coffee
    transport 2.10 metro
    rent 120
  Also accepts amount first:
    7.50 food arepa + coffee

Everything else still works:
- Stores list of dicts
- Summaries (total, by category, biggest expense)
- Budgets + warnings
- Export report
- Optional charts (matplotlib)
"""

import csv
import os
from datetime import datetime, date
import matplotlib.pyplot as plt


# -----------------------------
# Helpers: validation & parsing
# -----------------------------

def parse_amount(amount_str: str) -> float:
    """Convert user input to a float amount. Raises ValueError if invalid."""
    try:
        amount = float(amount_str)
    except ValueError:
        raise ValueError("Amount must be a number (example: 12.50).")

    if amount == 0:
        raise ValueError("Amount cannot be 0.")
    return amount


def clean_category(cat: str) -> str:
    """Basic category cleaning (trim + title case)."""
    cat = cat.strip()
    if not cat:
        raise ValueError("Category cannot be empty.")
    return cat.title()


def safe_input(prompt: str) -> str:
    """Input wrapper to avoid accidental whitespace issues."""
    return input(prompt).strip()


def parse_quick_add(line: str):
    """
    Parse one-line quick add input.

    Accepted formats:
      - category amount [note...]
      - amount category [note...]

    Returns: (category, amount, note)

    Examples:
      "food 7.5 arepa" -> ("Food", 7.5, "arepa")
      "7.5 food arepa" -> ("Food", 7.5, "arepa")
      "rent 120" -> ("Rent", 120.0, "")
    """
    parts = line.strip().split()
    if len(parts) < 2:
        raise ValueError("Please type at least: category amount (example: food 7.50 coffee)")

    # Try interpreting second token as amount (category amount ...)
    try:
        cat = clean_category(parts[0])
        amt = parse_amount(parts[1])
        note = " ".join(parts[2:]).strip()
        return cat, amt, note
    except ValueError:
        pass

    # Try interpreting first token as amount (amount category ...)
    try:
        amt = parse_amount(parts[0])
        cat = clean_category(parts[1])
        note = " ".join(parts[2:]).strip()
        return cat, amt, note
    except ValueError:
        raise ValueError(
            "Could not parse. Use: category amount [note...] (example: food 7.50 arepa)\n"
            "Or: amount category [note...] (example: 7.50 food arepa)"
        )


# -----------------------------
# Core data loading/saving
# -----------------------------

def load_transactions(csv_filename: str):
    """Load transactions from CSV into a list of dictionaries."""
    transactions = []
    if not os.path.exists(csv_filename):
        return transactions

    try:
        with open(csv_filename, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    d = datetime.strptime(row["date"], "%Y-%m-%d").date()
                    amt = float(row["amount"])
                    cat = row["category"].strip()
                    note = row.get("note", "").strip()
                except Exception:
                    continue

                transactions.append({"date": d, "amount": amt, "category": cat, "note": note})
    except Exception as e:
        print(f"⚠️ Could not read file: {e}")

    return transactions


def save_transactions(csv_filename: str, transactions):
    """Save transactions to CSV (overwrite)."""
    try:
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["date", "amount", "category", "note"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in transactions:
                writer.writerow({
                    "date": t["date"].isoformat(),
                    "amount": f"{t['amount']:.2f}",
                    "category": t["category"],
                    "note": t["note"]
                })
    except Exception as e:
        print(f"⚠️ Could not save file: {e}")


# -----------------------------
# Feature: QUICK ADD (today by default)
# -----------------------------

def add_transaction_quick(transactions):
    """
    Quick add:
    - Default date is today
    - User types: category amount [note...]
    """
    print("\nQuick Add (date defaults to today)")
    print("Examples:  food 7.50 arepa + coffee   |   7.50 food arepa + coffee   |   rent 120")
    while True:
        line = safe_input("Enter transaction: ")
        try:
            cat, amt, note = parse_quick_add(line)
            break
        except ValueError as e:
            print(f"❌ {e}")

    transactions.append({
        "date": date.today(),
        "amount": amt,
        "category": cat,
        "note": note
    })

    print(f"✅ Added: {date.today().isoformat()} | €{amt:.2f} | {cat} | {note}")


# -----------------------------
# Summaries
# -----------------------------

def filter_by_month(transactions, month):
    """
    month format: 'YYYY-MM' or None.
    Yields transactions in that month.
    """
    if month is None:
        for t in transactions:
            yield t
        return

    try:
        dt = datetime.strptime(month, "%Y-%m")
        y, m = dt.year, dt.month
    except ValueError:
        for t in transactions:
            yield t
        return

    for t in transactions:
        if t["date"].year == y and t["date"].month == m:
            yield t


def total_spending(transactions, month=None) -> float:
    """Total spending (positive amounts only)."""
    total = 0.0
    for t in filter_by_month(transactions, month):
        if t["amount"] > 0:
            total += t["amount"]
    return total


def totals_by_category(transactions, month=None):
    """Dict category -> total spending (positive amounts only)."""
    totals = {}
    for t in filter_by_month(transactions, month):
        if t["amount"] > 0:
            cat = t["category"]
            totals[cat] = totals.get(cat, 0.0) + t["amount"]
    return totals


def biggest_expense(transactions, month=None):
    """Biggest single expense (positive amount)."""
    biggest = None
    for t in filter_by_month(transactions, month):
        if t["amount"] > 0:
            if biggest is None or t["amount"] > biggest["amount"]:
                biggest = t
    return biggest


def print_summary(transactions, month=None):
    """Print summary metrics."""
    print(f"\n📊 Summary for {month}" if month else "\n📊 Summary (all time)")

    total = total_spending(transactions, month)
    print(f"Total spending: €{total:.2f}")

    by_cat = totals_by_category(transactions, month)
    if not by_cat:
        print("No spending transactions found.")
    else:
        print("\nSpending by category:")
        for cat in sorted(by_cat.keys()):
            print(f"  - {cat}: €{by_cat[cat]:.2f}")

    big = biggest_expense(transactions, month)
    if big:
        print("\nBiggest expense:")
        print(f"  - €{big['amount']:.2f} | {big['category']} | {big['date'].isoformat()} | {big['note']}")
    else:
        print("\nBiggest expense: (none)")


# -----------------------------
# Budgets + warnings
# -----------------------------

def set_budgets():
    """Set monthly budgets per category. Returns dict category -> budget."""
    budgets = {}
    print("\nSet monthly budgets (enter blank category to stop).")
    while True:
        cat = safe_input("Category (blank to finish): ")
        if cat == "":
            break
        try:
            cat = clean_category(cat)
        except ValueError as e:
            print(f"❌ {e}")
            continue

        amt_str = safe_input(f"Monthly budget for {cat} (€): ")
        try:
            amt = parse_amount(amt_str)
            if amt < 0:
                print("❌ Budget must be positive.")
                continue
            budgets[cat] = amt
        except ValueError as e:
            print(f"❌ {e}")

    print("✅ Budgets set." if budgets else "No budgets set.")
    return budgets


def budget_warnings(transactions, budgets, month):
    """Warn if spending exceeds budget for the given month (YYYY-MM)."""
    if not budgets:
        print("\nNo budgets set.")
        return

    by_cat = totals_by_category(transactions, month)
    print(f"\n💸 Budget check for {month}")

    any_warning = False
    for cat, limit in budgets.items():
        spent = by_cat.get(cat, 0.0)
        if spent > limit:
            any_warning = True
            over = spent - limit
            print(f"⚠️ {cat}: spent €{spent:.2f} (budget €{limit:.2f}) → over by €{over:.2f}")
        else:
            print(f"✅ {cat}: spent €{spent:.2f} / €{limit:.2f}")

    if not any_warning:
        print("🎉 No categories are over budget.")


# -----------------------------
# Export report
# -----------------------------

def export_summary_report(transactions, filename, month=None):
    """Export a summary report to a .txt file."""
    total = total_spending(transactions, month)
    by_cat = totals_by_category(transactions, month)
    big = biggest_expense(transactions, month)

    header = f"Summary Report - {month}" if month else "Summary Report - All time"
    lines = [
        header,
        "=" * len(header),
        f"Total spending: €{total:.2f}",
        "",
        "Spending by category:"
    ]

    if not by_cat:
        lines.append("  (no spending transactions)")
    else:
        for cat in sorted(by_cat.keys()):
            lines.append(f"  - {cat}: €{by_cat[cat]:.2f}")

    lines += ["", "Biggest expense:"]
    if big:
        lines.append(f"  - €{big['amount']:.2f} | {big['category']} | {big['date'].isoformat()} | {big['note']}")
    else:
        lines.append("  (none)")

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ Exported report to: {filename}")
    except Exception as e:
        print(f"⚠️ Could not export report: {e}")


# -----------------------------
# Charts (optional)
# -----------------------------

def plot_category_spending(transactions, month=None):
    """Plot spending by category (requires matplotlib)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️ matplotlib is not installed, so charts are unavailable.")
        return

    data = totals_by_category(transactions, month)
    if not data:
        print("No spending to plot.")
        return

    categories = sorted(data.keys())
    values = [data[c] for c in categories]

    plt.figure()
    plt.bar(categories, values)
    plt.title(f"Spending by Category ({month})" if month else "Spending by Category (All time)")
    plt.xlabel("Category")
    plt.ylabel("Spending (€)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.show()


# -----------------------------
# Extra: list + delete + menu UI
# -----------------------------

def list_transactions(transactions, month=None):
    """Print transactions (optionally filtered by month)."""
    tx = list(filter_by_month(transactions, month))
    if not tx:
        print("\n(no transactions)")
        return

    tx.sort(key=lambda t: (t["date"], t["category"]))
    print("\nTransactions:")
    for i, t in enumerate(tx, start=1):
        sign = "-" if t["amount"] < 0 else ""
        print(f"{i:>3}. {t['date'].isoformat()} | {sign}€{abs(t['amount']):.2f} | {t['category']} | {t['note']}")


def delete_transaction(transactions):
    """Delete a transaction by index (from sorted view)."""
    if not transactions:
        print("No transactions to delete.")
        return

    sorted_tx = sorted(transactions, key=lambda t: (t["date"], t["category"]))
    for i, t in enumerate(sorted_tx, start=1):
        sign = "-" if t["amount"] < 0 else ""
        print(f"{i:>3}. {t['date'].isoformat()} | {sign}€{abs(t['amount']):.2f} | {t['category']} | {t['note']}")

    choice = safe_input("Enter the number to delete (or blank to cancel): ")
    if choice == "":
        return

    try:
        idx = int(choice)
        if idx < 1 or idx > len(sorted_tx):
            print("❌ Invalid number.")
            return
    except ValueError:
        print("❌ Please type a valid integer.")
        return

    to_remove = sorted_tx[idx - 1]
    transactions.remove(to_remove)
    print("✅ Deleted.")


def ask_month_optional():
    """Ask user for a month in YYYY-MM or blank for all time."""
    month = safe_input("Month (YYYY-MM) or press Enter for all time: ")
    return month if month else None


def main():
    csv_file = "transactions.csv"
    report_file = "summary_report.txt"

    transactions = load_transactions(csv_file)
    budgets = {}

    while True:
        print("\n" + "-" * 45)
        print("Personal Finance Tracker (Quick Add)")
        print("-" * 45)
        print("1) Quick add transaction (today by default)")
        print("2) List transactions")
        print("3) Show summary")
        print("4) Delete transaction")
        print("5) Set monthly budgets")
        print("6) Check budget warnings")
        print("7) Export summary report")
        print("8) Plot spending by category (optional)")
        print("9) Save & Exit")

        choice = safe_input("Choose an option (1-9): ")

        if choice == "1":
            add_transaction_quick(transactions)

        elif choice == "2":
            month = ask_month_optional()
            list_transactions(transactions, month)

        elif choice == "3":
            month = ask_month_optional()
            print_summary(transactions, month)

        elif choice == "4":
            delete_transaction(transactions)

        elif choice == "5":
            budgets = set_budgets()

        elif choice == "6":
            month = safe_input("Month for budget check (YYYY-MM): ")
            budget_warnings(transactions, budgets, month)

        elif choice == "7":
            month = ask_month_optional()
            export_summary_report(transactions, report_file, month)

        elif choice == "8":
            month = ask_month_optional()
            plot_category_spending(transactions, month)

        elif choice == "9":
            save_transactions(csv_file, transactions)
            print(f"✅ Saved to {csv_file}. Bye!")
            break

        else:
            print("❌ Invalid choice. Please pick 1-9.")


if __name__ == "__main__":
    main()
