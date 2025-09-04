# Gluco-check-tracker
Gluco Check Tracer is a simple and user-friendly system designed to remind patients to check their blood sugar levels at regular intervals. With a customizable reminder system, patients can set alerts to check their blood sugar every 6 hours or according to their specific needs. Our system is perfect for elderly
#!/usr/bin/env python3
# gluco_check_tracker.py

import csv
import os
from datetime import datetime
from statistics import mean

FILENAME = "gluco_check_data.csv"
COLUMNS = ["Date", "Time", "Glucose_mg_dL", "Notes"]


def ensure_csv(path: str = FILENAME) -> None:
    """
    Ensure the CSV file exists and has the correct header.
    If file doesn't exist or the header is wrong/empty, (re)create with header.
    """
    need_header = True
    if os.path.exists(path):
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header == COLUMNS:
                    need_header = False
        except Exception:
            # If we can't read it safely, we'll recreate it with a header.
            pass

    if need_header:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)


def prompt_float(prompt: str, min_val: float = 20.0, max_val: float = 600.0) -> float:
    """
    Prompt user for a float within [min_val, max_val]. Re-ask until valid.
    Typical human glucose: ~70–180 mg/dL; we allow wider bounds to avoid blocking.
    """
    while True:
        raw = input(prompt).strip()
        try:
            val = float(raw)
            if not (min_val <= val <= max_val):
                print(f"⚠️ Please enter a value between {min_val} and {max_val}.")
                continue
            return val
        except ValueError:
            print("⚠️ Please enter a numeric value (e.g., 110).")


def prompt_datetime(default_now=True):
    """
    Let user accept current date/time or enter their own (YYYY-MM-DD / HH:MM).
    """
    now = datetime.now()
    if default_now:
        use_now = input(f"Use current date/time {now.strftime('%Y-%m-%d %H:%M')}? (Y/n): ").strip().lower()
        if use_now in ("", "y", "yes"):
            return now.strftime("%Y-%m-%d"), now.strftime("%H:%M")

    # Date
    while True:
        d = input("Enter date (YYYY-MM-DD): ").strip()
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            date_s = dt.strftime("%Y-%m-%d")
            break
        except ValueError:
            print("⚠️ Invalid date format. Example: 2025-09-04")

    # Time
    while True:
        t = input("Enter time (HH:MM, 24h): ").strip()
        try:
            tm = datetime.strptime(t, "%H:%M")
            time_s = tm.strftime("%H:%M")
            break
        except ValueError:
            print("⚠️ Invalid time format. Example: 14:30")

    return date_s, time_s


def log_reading():
    """Log a new glucose reading with validation."""
    ensure_csv()
    print("\n— Log New Reading —")
    date_s, time_s = prompt_datetime(default_now=True)
    glucose = prompt_float("Enter glucose level (mg/dL): ")
    notes = input("Any notes (e.g., fasting, post-meal, exercise): ").strip()

    with open(FILENAME, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([date_s, time_s, f"{glucose:.1f}", notes])

    print("✅ Reading saved.\n")


def read_all_rows():
    """Read all rows as list of dicts. Skips header automatically."""
    ensure_csv()
    rows = []
    with open(FILENAME, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def view_records():
    """Pretty-print all records (if any)."""
    rows = read_all_rows()
    if not rows:
        print("\n📭 No records yet.\n")
        return

    print("\n📋 Past Glucose Records:\n")
    print(f"{'Date':<12} {'Time':<6} {'Glucose':>9}   Notes")
    print("-" * 60)
    for r in rows:
        date_s = r.get("Date", "")
        time_s = r.get("Time", "")
        glu = r.get("Glucose_mg_dL", "")
        notes = r.get("Notes", "")
        print(f"{date_s:<12} {time_s:<6} {glu:>9}   {notes}")
    print("")


def show_stats():
    """
    Compute basic stats: count, average, min, max.
    Handles empty file safely and non-numeric rows gracefully.
    """
    rows = read_all_rows()
    vals = []
    for r in rows:
        try:
            vals.append(float(r.get("Glucose_mg_dL", "").strip()))
        except (ValueError, AttributeError):
            continue

    if not vals:
        print("\n⚠️ No numeric readings available yet.\n")
        return

    avg = mean(vals)
    mn = min(vals)
    mx = max(vals)
    print("\n📊 Stats")
    print("-" * 20)
    print(f"Count:   {len(vals)}")
    print(f"Average: {avg:.1f} mg/dL")
    print(f"Min:     {mn:.1f} mg/dL")
    print(f"Max:     {mx:.1f} mg/dL\n")


def main():
    ensure_csv()
    while True:
        print("=== 🩸 Gluco-Check Tracker ===")
        print("1) Log new reading")
        print("2) View all records")
        print("3) Show statistics (avg/min/max)")
        print("4) Exit")
        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            log_reading()
        elif choice == "2":
            view_records()
        elif choice == "3":
            show_stats()
        elif choice == "4":
            print("Goodbye 👋 Stay healthy!")
            break
        else:
            print("⚠️ Invalid option. Try again.\n")


if __name__ == "__main__":
    main()
