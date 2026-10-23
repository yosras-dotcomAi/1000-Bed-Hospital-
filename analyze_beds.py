"""
1,000-Bed Hospital: Bed Capacity & Operational Performance Analysis
-------------------------------------------------------------------
Uses a SYNTHETIC dataset for a fictional hospital (no real patient data).

Input : Hospital_1000Bed_Dataset.xlsx
Output: department_scorecard.csv, kpi_scorecard.csv and 4 charts (PNG)
"""

import pandas as pd
import matplotlib.pyplot as plt

FILE = "Hospital_1000Bed_Dataset.xlsx"

# KPI targets taken from the KPI_Targets sheet of the dataset
OCC_TARGET = 0.85
ICU_LIMIT = 0.92
ALOS_TARGET = 4.5
ED_WAIT_TARGET_MIN = 30
CRITICAL = ["ICU Adult", "ICU Pediatric", "CCU"]

TEAL, GREY, RED = "#2a9d8f", "#b0b0b0", "#d1495b"

# ---------- Load ----------
beds = pd.read_excel(FILE, sheet_name="Hospital_Bed_Daily")
adm = pd.read_excel(FILE, sheet_name="Patient_Admissions")
flow = pd.read_excel(FILE, sheet_name="Patient_Flow")
staff = pd.read_excel(FILE, sheet_name="Staffing")
status = pd.read_excel(FILE, sheet_name="Bed_Status")
forecast = pd.read_excel(FILE, sheet_name="Forecast_Data")

# ---------- 1. Occupancy by department ----------
occ = beds.groupby("Department").agg(
    avg_occupancy=("Occupancy_Pct", "mean"),
    peak_occupancy=("Occupancy_Pct", "max"),
    days_above_90=("Occupancy_Pct", lambda s: (s > 0.90).mean()),
    days_above_95=("Occupancy_Pct", lambda s: (s > 0.95).mean()),
)

# ---------- 2. Length of stay by department ----------
alos = adm.groupby("Department")["LOS_Days"].mean().rename("avg_los_days")

# ---------- 3. Nurse workload (occupied beds per nurse, daily counts) ----------
ratio = staff.merge(beds, on=["Date", "Department"])
ratio["patients_per_nurse"] = ratio["Occupied_Beds"] / ratio["Nurses"]
nurse = ratio.groupby("Department")["patients_per_nurse"].mean()

scorecard = occ.join(alos).join(nurse).round(3).sort_values("avg_occupancy", ascending=False)
scorecard.to_csv("department_scorecard.csv")
print(scorecard.to_string())

# ---------- 4. Hospital-wide KPIs vs targets ----------
daily = beds.groupby("Date")[["Occupied_Beds", "Total_Beds"]].sum()
hospital_occ = (daily["Occupied_Beds"] / daily["Total_Beds"]).mean()

flow["ed_to_ward_min"] = (flow["Ward_Admission"] - flow["ED_Arrival"]).dt.total_seconds() / 60
ed_median = flow["ed_to_ward_min"].median()
ed_met = (flow["ed_to_ward_min"] < ED_WAIT_TARGET_MIN).mean()

icu_adult = beds[beds["Department"] == "ICU Adult"].set_index("Date")["Occupancy_Pct"]

cleaning_share = (status["Status"] == "Cleaning").mean()

kpis = pd.DataFrame([
    ["Hospital bed occupancy", f"{hospital_occ:.1%}", "85%", "Met" if abs(hospital_occ - OCC_TARGET) < 0.01 else "Off target"],
    ["ICU Adult occupancy", f"{icu_adult.mean():.1%}", "<92%", "Not met" if icu_adult.mean() >= ICU_LIMIT else "Met"],
    ["ICU Adult days above 92%", f"{(icu_adult > ICU_LIMIT).mean():.0%}", "-", "-"],
    ["Average length of stay", f"{adm['LOS_Days'].mean():.2f} days", "4.5 days", "Met" if adm["LOS_Days"].mean() <= ALOS_TARGET else "Not met"],
    ["ED arrival to ward admission (median)", f"{ed_median:.0f} min", "<30 min", "Not met"],
    ["Patients meeting the 30-min ED target", f"{ed_met:.0%}", "-", "-"],
    ["Beds in 'Cleaning' status", f"{cleaning_share:.1%}", "-", "-"],
    ["Forecast occupancy, next 30 days (avg)", f"{forecast['Predicted_Occupancy_Pct'].mean():.1%}", "85%", "-"],
], columns=["KPI", "Result", "Target", "Status"])
kpis.to_csv("kpi_scorecard.csv", index=False)
print("\n", kpis.to_string(index=False))

# ---------- Charts ----------
# Chart 1: occupancy by department
s = scorecard.sort_values("avg_occupancy")
colors = [RED if (d in CRITICAL and v >= ICU_LIMIT) else TEAL for d, v in zip(s.index, s["avg_occupancy"])]
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(s.index, s["avg_occupancy"] * 100, color=colors)
ax.axvline(OCC_TARGET * 100, color="black", linestyle="--", linewidth=1)
ax.text(OCC_TARGET * 100 + 0.3, -0.7, "85% target", fontsize=8)
ax.set_xlim(60, 100)
ax.set_xlabel("Average occupancy (%)")
ax.set_title("Average Bed Occupancy by Department")
plt.tight_layout()
plt.savefig("chart_occupancy_by_department.png", dpi=150)
plt.close()

# Chart 2: ICU Adult daily occupancy
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(icu_adult.index, icu_adult * 100, color=TEAL, linewidth=1.5)
ax.axhline(ICU_LIMIT * 100, color=RED, linestyle="--", linewidth=1)
ax.text(icu_adult.index[0], ICU_LIMIT * 100 + 0.4, "92% safe limit", color=RED, fontsize=8)
ax.set_ylabel("Occupancy (%)")
ax.set_title("ICU Adult: Daily Bed Occupancy")
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig("chart_icu_adult_trend.png", dpi=150)
plt.close()

# Chart 3: ED arrival to ward admission
fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(flow["ed_to_ward_min"], bins=30, color=TEAL, edgecolor="white")
ax.axvline(ED_WAIT_TARGET_MIN, color=RED, linestyle="--", linewidth=1.2)
ax.text(ED_WAIT_TARGET_MIN + 3, ax.get_ylim()[1] * 0.9, "30-min target", color=RED, fontsize=8)
ax.set_xlabel("Minutes from ED arrival to ward admission")
ax.set_ylabel("Patients")
ax.set_title("ED to Ward Admission Time")
plt.tight_layout()
plt.savefig("chart_ed_wait_time.png", dpi=150)
plt.close()

# Chart 4: average length of stay (excluding day-case dialysis)
a = scorecard.drop(index="Dialysis", errors="ignore").sort_values("avg_los_days")
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(a.index, a["avg_los_days"], color=TEAL)
ax.axvline(ALOS_TARGET, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Average length of stay (days)")
ax.set_title("Average Length of Stay by Department (4.5-day target)")
plt.tight_layout()
plt.savefig("chart_length_of_stay.png", dpi=150)
plt.close()

print("\nDone: 2 CSV files and 4 charts saved.")
