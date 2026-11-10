"""
1,000-Bed Hospital: Bed Capacity and Operational Performance Dashboard

A FICTIONAL hospital with SYNTHETIC data (no real patient data).
Data: data/Hospital_1000Bed_Dataset.xlsx (8 sheets, 27 Apr to 27 Jul 2026, 92 days).

Run:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="1,000-Bed Hospital Dashboard", page_icon="🏥", layout="wide")

NAVY, TEAL, GREEN, GOLD, RED, GREY = "#1B3A5C", "#2C9C93", "#3E9B6F", "#D8A73D", "#D1495B", "#7F93A8"
STATUS_COLOR = {"On target": GREEN, "Above threshold": RED, "Below threshold": GOLD, "Not measurable": "#6B7C8F"}
OCC_TARGET, ICU_LIMIT, ALOS_TARGET, ED_TARGET, TURNOVER_TARGET = 0.85, 0.92, 4.5, 30, 7
CRITICAL = ["ICU Adult", "ICU Pediatric", "CCU"]
STATUS_ORDER = ["Occupied", "Available", "Cleaning", "Reserved", "Maintenance"]
STATUS_BAR = {"Occupied": "#4A7FB5", "Available": TEAL, "Cleaning": GOLD, "Reserved": "#8E7CC3", "Maintenance": RED}

st.markdown(
    """
<style>
.block-container{padding-top:1.4rem;max-width:1300px}
.hero h1{font-size:2.0rem;margin:0 0 .2rem 0;color:inherit}
.hero p{color:inherit;opacity:.75;margin:0 0 .8rem 0;font-size:1.02rem}
.sim{background:#16263d;border:1px solid #2F4A6D;border-left:4px solid #D8A73D;color:#E6EEF7;border-radius:8px;padding:10px 14px;font-size:.92rem;margin-bottom:1rem}
.kpi{background:#142238;border:1px solid #243B5A;border-radius:12px;padding:14px 16px;height:100%}
.kpi .n{color:#C9DCF0;font-size:.82rem;min-height:2.3em}
.kpi .v{font-size:1.7rem;font-weight:700;color:#fff;line-height:1.15;margin-top:2px}
.kpi .v.sm{font-size:1.15rem;padding:.35rem 0}
.kpi .t{color:#8FA9C4;font-size:.78rem;margin-top:2px}
.kpi .s{color:#8FA9C4;font-size:.74rem;margin-top:5px;min-height:2.2em}
.chip{display:inline-block;border-radius:20px;padding:2px 10px;font-size:.72rem;font-weight:600;color:#fff;margin-top:6px}
.answer{background:#0F2238;border-left:4px solid #2C9C93;border-radius:8px;padding:14px 18px;margin:.6rem 0 1rem 0;color:#E6EEF7}
.answer h4{margin:0 0 .4rem 0;color:#fff}
.answer b{color:#fff}
.note{color:#7F93A8;font-size:.85rem}
</style>
""",
    unsafe_allow_html=True,
)

DATA_FILE = next((p for p in [Path(__file__).parent / "data" / "Hospital_1000Bed_Dataset.xlsx", Path(__file__).parent / "Hospital_1000Bed_Dataset.xlsx"] if p.exists()), None)


@st.cache_data(show_spinner="Loading the hospital dataset...")
def load():
    sheets = pd.read_excel(DATA_FILE, sheet_name=None)
    return sheets


if DATA_FILE is None:
    st.error("Dataset not found. Put Hospital_1000Bed_Dataset.xlsx in the data/ folder.")
    st.stop()

S = load()
dep_tbl = S["Departments"].set_index("Department")
beds, adm, flow, staff, status, fc, targets = (S["Hospital_Bed_Daily"], S["Patient_Admissions"], S["Patient_Flow"],
                                               S["Staffing"], S["Bed_Status"], S["Forecast_Data"], S["KPI_Targets"])
DATA_START, DATA_END = beds["Date"].min(), beds["Date"].max()
ALL_DEPS = dep_tbl.index.tolist()


def card(col, name, value, target="", sub="", chip=None):
    chip_html = f'<div class="chip" style="background:{STATUS_COLOR[chip]}">{chip}</div>' if chip else ""
    col.markdown(f'<div class="kpi"><div class="n">{name}</div><div class="v{" sm" if len(str(value)) > 12 else ""}">{value}</div><div class="t">{target}</div><div class="s">{sub}</div>{chip_html}</div>', unsafe_allow_html=True)


def style(fig, h=380, legend=True):
    fig.update_layout(height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=10, r=10, t=50, b=70 if legend else 10), showlegend=legend, font=dict(size=13),
                      legend=dict(orientation="h", y=-0.2, x=0, yanchor="top"))
    fig.update_xaxes(gridcolor="rgba(127,127,127,0.25)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(127,127,127,0.25)", zeroline=False)
    return fig


def longest_run(flags):
    best = cur = 0
    for v in flags:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


# ------------------------------------------------------------------ sidebar
st.sidebar.markdown("## Filters")
sel = st.sidebar.multiselect("Departments", ALL_DEPS, default=ALL_DEPS)
dr = st.sidebar.date_input("Dates", (DATA_START.date(), DATA_END.date()), min_value=DATA_START.date(), max_value=DATA_END.date())
d0, d1 = (pd.Timestamp(dr[0]), pd.Timestamp(dr[1])) if isinstance(dr, tuple) and len(dr) == 2 else (DATA_START, DATA_END)
n_days = (d1 - d0).days + 1
st.sidebar.markdown(f"**{len(sel)}** departments · **{n_days}** days · **{int(dep_tbl.loc[sel, 'Total_Beds'].sum()) if sel else 0:,}** beds")
st.sidebar.caption("Filters apply to every tab, except the Forecast tab and the dataset checks, which always use the whole hospital.")

# ------------------------------------------------------------------ header
st.markdown('<div class="hero"><h1>🏥 1,000-Bed Hospital: Capacity and Operational Performance</h1>'
            "<p>An executive view of bed occupancy, patient flow, staffing and critical care, with honest data checks</p></div>", unsafe_allow_html=True)
st.markdown('<div class="sim"><b>Fictional hospital, synthetic data.</b> No real patient data is used. The dataset was generated to practise strategic healthcare analytics, and it covers 27 April to 27 July 2026.</div>', unsafe_allow_html=True)

if not sel:
    st.info("Select at least one department in the sidebar.")
    st.stop()

in_range = lambda s: (s >= d0) & (s <= d1 + pd.Timedelta(hours=23, minutes=59))
b = beds[beds.Department.isin(sel) & in_range(beds.Date)]
a = adm[adm.Department.isin(sel) & in_range(adm.Admission_Date)]
dis = adm[adm.Department.isin(sel) & (adm.Discharge_Date >= d0) & (adm.Discharge_Date <= min(d1, DATA_END))]
fl = flow[flow.Ward_Department.isin(sel) & in_range(flow.ED_Arrival)].copy()
fl["ed_to_ward"] = (fl.Ward_Admission - fl.ED_Arrival).dt.total_seconds() / 60
stf = staff.merge(beds, on=["Date", "Department"])
stf = stf[stf.Department.isin(sel) & in_range(stf.Date)].copy()
stf["pts_per_nurse"] = stf.Occupied_Beds / stf.Nurses
bs = status[status.Department.isin(sel) & in_range(status.Date)]

# ------------------------------------------------------------------ KPI calculations
occ = b.Occupied_Beds.sum() / b.Total_Beds.sum()
months = n_days / 30.44
total_beds = dep_tbl.loc[sel, "Total_Beds"].sum()
turnover = len(dis) / total_beds / months
alos = a.LOS_Days.mean() if len(a) else np.nan
alos_nodia = a[a.Department != "Dialysis"].LOS_Days.mean() if len(a[a.Department != "Dialysis"]) else np.nan
ed_med = fl.ed_to_ward.median() if len(fl) else np.nan
ed_30 = (fl.ed_to_ward < ED_TARGET).mean() if len(fl) else np.nan
icu = b[b.Department == "ICU Adult"]
icu_occ = icu.Occupancy_Pct.mean() if len(icu) else np.nan
icu_days_over = (icu.Occupancy_Pct > ICU_LIMIT).sum() if len(icu) else 0
gw = stf[stf.Department.map(dep_tbl.Category) == "Inpatient Ward"]
cc = stf[stf.Department.isin(CRITICAL)]
gw_ratio = gw.Occupied_Beds.sum() / gw.Nurses.sum() if len(gw) else np.nan
cc_ratio = cc.Occupied_Beds.sum() / cc.Nurses.sum() if len(cc) else np.nan
gw_over = (gw.pts_per_nurse > 5).mean() if len(gw) else np.nan
cc_over = (cc.pts_per_nurse > 2).mean() if len(cc) else np.nan
clean_share = (bs.Status == "Cleaning").mean() if len(bs) else np.nan
pid_unique = adm.Patient_ID.is_unique


def st_le(v, limit):
    return "n/a" if pd.isna(v) else ("On target" if v <= limit else "Above threshold")


kpi_rows = [
    ("Bed occupancy rate", f"{occ:.1%}", "Target 85%", f"{len(b):,} department-days", "On target" if abs(occ - OCC_TARGET) < 0.01 else ("Above threshold" if occ > OCC_TARGET else "Below threshold")),
    ("Average length of stay", "n/a" if pd.isna(alos) else f"{alos:.2f} days", "Target 4.5 days", f"{alos_nodia:.2f} days without day-case dialysis" if not pd.isna(alos_nodia) else "", st_le(alos, ALOS_TARGET)),
    ("Bed turnover rate", f"{turnover:.1f}", "Target 7 discharges per bed per month", "see Dataset checks tab", "On target" if turnover >= TURNOVER_TARGET else "Below threshold"),
    ("ED waiting time (median)", "n/a" if pd.isna(ed_med) else f"{ed_med:.0f} min", "Target under 30 min", "" if pd.isna(ed_30) else f"{ed_30:.1%} of patients within 30 min", "n/a" if pd.isna(ed_med) else ("On target" if ed_med < ED_TARGET else "Above threshold")),
    ("Readmission rate", "Not measurable", "Target under 5%", "Every Patient_ID is unique" if pid_unique else "", "Not measurable"),
    ("ICU Adult occupancy", "n/a" if pd.isna(icu_occ) else f"{icu_occ:.1%}", "Safe limit under 92%", "" if pd.isna(icu_occ) else f"above 92% on {icu_days_over} of {len(icu)} days", "n/a" if pd.isna(icu_occ) else ("On target" if icu_occ < ICU_LIMIT else "Above threshold")),
    ("Nurse-to-patient ratio, general wards", "n/a" if pd.isna(gw_ratio) else f"1:{gw_ratio:.1f}", "Target 1:5 or better", "" if pd.isna(gw_over) else f"worse than 1:5 on {gw_over:.0%} of ward-days", "n/a" if pd.isna(gw_ratio) else ("On target" if gw_ratio <= 5 else "Above threshold")),
    ("Nurse-to-patient ratio, ICU and CCU", "n/a" if pd.isna(cc_ratio) else f"1:{cc_ratio:.1f}", "Target 1:2 or better", "" if pd.isna(cc_over) else f"worse than 1:2 on {cc_over:.0%} of unit-days", "n/a" if pd.isna(cc_ratio) else ("On target" if cc_ratio <= 2.005 else "Above threshold")),
    ("Bed cleaning turnaround", "Not measurable", "Target under 60 min", "No timestamps" + ("" if pd.isna(clean_share) else f" · {clean_share:.1%} of bed-days in cleaning"), "Not measurable"),
    ("Forecast accuracy (MAPE)", "Not measurable", "Target under 8%", "Forecast covers future dates only", "Not measurable"),
]
hosp_daily = beds.groupby("Date")[["Occupied_Beds", "Total_Beds"]].sum()
hosp_daily["occ"] = hosp_daily.Occupied_Beds / hosp_daily.Total_Beds

t1, t2, t3, t4, t5, t6, t7 = st.tabs(["🎯 Executive scorecard", "🛏️ Bed capacity", "🚨 Critical care", "🔄 Patient flow and stay",
                                       "👩‍⚕️ Staffing and turnover", "🔮 Forecast", "🔎 Dataset checks"])

# ================================================================== TAB 1
with t1:
    st.markdown("#### The 10 executive KPIs against their targets")
    for r in range(2):
        cols = st.columns(5)
        for col, row in zip(cols, kpi_rows[r * 5:(r + 1) * 5]):
            name, val, tgt, sub, stt = row
            card(col, name, val, tgt, sub, stt if stt in STATUS_COLOR else None)
        st.markdown("&nbsp;", unsafe_allow_html=True)

    crit_over = icu_days_over
    st.markdown(
        '<div class="answer"><h4>What the data says</h4>'
        + (f"<b>Critical care is the pressure point.</b> ICU Adult averaged {icu_occ:.1%} occupancy and was above the 92% safe limit on {crit_over} of {len(icu)} days. " if not pd.isna(icu_occ) else "")
        + (f"<b>Patients wait too long for a ward bed.</b> The median time from ED arrival to ward admission was {ed_med:.0f} minutes against a 30-minute target, and {ed_30:.1%} of patients met it. " if not pd.isna(ed_med) else "")
        + f"<b>Overall capacity is on target</b> at {occ:.1%} occupancy, which hides large differences between departments. "
        + f"<b>Three KPIs cannot be measured with this dataset</b> (readmission, bed cleaning time, forecast accuracy), and the bed turnover figure needs care. See the Dataset checks tab."
        "</div>", unsafe_allow_html=True)

    st.markdown("#### Suggested actions for discussion")
    bd = b.groupby("Department").Occupancy_Pct.mean().sort_values()
    low = bd.head(3)
    first = (f"1. **Protect ICU Adult capacity.** Review step-down and early-discharge pathways, because the unit is over its safe limit on {icu_days_over} of {len(icu)} days.\n"
             if len(icu) else "1. **Protect critical care capacity.** Review step-down and early-discharge pathways for the units near the 92% limit.\n")
    second = "2. **Shorten ED boarding.** Track the time from bed request to bed ready, and test staged targets (for example 60, then 30 minutes).\n"
    third = "3. **Rebalance under-used capacity.** The lowest average occupancy is in " + ", ".join(f"{d} ({v:.0%})" for d, v in low.items()) + ", so beds or staff there could be flexed.\n"
    fourth = "4. **Add a staffing buffer for peak days.** Critical care averages exactly the 1:2 ratio but is worse on many days, so a float pool for high-occupancy days is worth modelling."
    st.markdown(first + second + third + fourth)
    st.caption("These are hypotheses from a simulated dataset, to be tested with real operational data.")

# ================================================================== TAB 2
with t2:
    st.markdown("#### Bed occupancy")
    dep_occ = b.groupby("Department").agg(avg=("Occupancy_Pct", "mean"), peak=("Occupancy_Pct", "max"),
                                          d90=("Occupancy_Pct", lambda s: (s > .90).mean()), d95=("Occupancy_Pct", lambda s: (s > .95).mean())).sort_values("avg")
    left, right = st.columns(2)
    with left:
        cols_ = [RED if (d in CRITICAL and v >= ICU_LIMIT) else (GOLD if v > OCC_TARGET else TEAL) for d, v in dep_occ["avg"].items()]
        fig = go.Figure(go.Bar(x=dep_occ["avg"] * 100, y=dep_occ.index, orientation="h", marker_color=cols_, text=[f"{v:.1f}%" for v in dep_occ["avg"] * 100], textposition="outside", cliponaxis=False))
        fig.add_vline(x=85, line=dict(color="#888", dash="dash"), annotation_text="85% target", annotation_position="top")
        fig.update_layout(title="Average occupancy by department", xaxis=dict(range=[50, 105], title="%"))
        st.plotly_chart(style(fig, 440, False), width="stretch")
        st.caption("Red: critical care at or above the 92% limit. Gold: above the 85% target. Teal: at or below target.")
    with right:
        daily = b.groupby("Date")[["Occupied_Beds", "Total_Beds"]].sum()
        daily["occ"] = daily.Occupied_Beds / daily.Total_Beds * 100
        daily["ma7"] = daily["occ"].rolling(7).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily.index, y=daily["occ"], name="Daily occupancy", mode="lines", line=dict(color=TEAL, width=1.6)))
        fig.add_trace(go.Scatter(x=daily.index, y=daily.ma7, name="7-day trailing average", mode="lines", line=dict(color=NAVY if False else GOLD, width=3)))
        fig.add_hline(y=85, line=dict(color="#888", dash="dash"), annotation_text="85% target")
        fig.update_layout(title="Selected departments: daily occupancy", yaxis_title="%")
        st.plotly_chart(style(fig, 440), width="stretch")
    wk = b.assign(week=b.Date - pd.to_timedelta(b.Date.dt.dayofweek, unit="D")).groupby(["Department", "week"]).Occupancy_Pct.mean().unstack() * 100
    wk = wk.loc[dep_occ.index[::-1]]
    fig = go.Figure(go.Heatmap(z=wk.values, x=[c.strftime("%d %b") for c in wk.columns], y=wk.index, colorscale=[[0, "#EAF3FC"], [0.5, "#80C8FF"], [1, "#1B3A5C"]],
                               zmin=60, zmax=100, text=np.round(wk.values, 0), texttemplate="%{text:.0f}", colorbar=dict(title="%")))
    fig.update_layout(title="Weekly average occupancy by department (week starting)")
    st.plotly_chart(style(fig, 440, False), width="stretch")
    show = dep_occ.sort_values("avg", ascending=False).assign(avg=lambda d: d.avg * 100, peak=lambda d: d.peak * 100, d90=lambda d: d.d90 * 100, d95=lambda d: d.d95 * 100)
    show.columns = ["Average %", "Peak %", "Days above 90% (%)", "Days above 95% (%)"]
    with st.expander("Show the table"):
        st.dataframe(show.round(1), width="stretch")

# ================================================================== TAB 3
with t3:
    st.markdown("#### Critical care against the 92% safe limit")
    units = [u for u in CRITICAL if u in sel]
    if not units:
        st.info("Select ICU Adult, ICU Pediatric or CCU to see this tab.")
    else:
        cols = st.columns(len(units))
        for col, u in zip(cols, units):
            g = b[b.Department == u].sort_values("Date")
            over = g.Occupancy_Pct > ICU_LIMIT
            card(col, u, f"{g.Occupancy_Pct.mean():.1%}", "Average occupancy", f"above 92% on {int(over.sum())} of {len(g)} days · longest run {longest_run(over)} days · peak {g.Occupancy_Pct.max():.1%}",
                 "Above threshold" if g.Occupancy_Pct.mean() >= ICU_LIMIT else "On target")
        st.markdown("&nbsp;")
        fig = go.Figure()
        for u, c in zip(units, [RED, GOLD, TEAL]):
            g = b[b.Department == u].sort_values("Date")
            fig.add_trace(go.Scatter(x=g.Date, y=g.Occupancy_Pct * 100, name=u, mode="lines", line=dict(width=2.2, color=c)))
        fig.add_hline(y=92, line=dict(color=RED, dash="dash"), annotation_text="92% safe limit", annotation_position="top left")
        fig.update_layout(title="Daily occupancy", yaxis_title="%")
        st.plotly_chart(style(fig, 420), width="stretch")
        left, right = st.columns(2)
        with left:
            wd = b[b.Department.isin(units)].assign(day=lambda d: d.Date.dt.day_name(), over=lambda d: d.Occupancy_Pct > ICU_LIMIT)
            order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            wd = wd.groupby(["day", "Department"]).over.mean().unstack().reindex(order) * 100
            fig = go.Figure()
            for u, c in zip(units, [RED, GOLD, TEAL]):
                fig.add_trace(go.Bar(x=wd.index, y=wd[u], name=u, marker_color=c))
            fig.update_layout(barmode="group", title="Share of days above 92%, by weekday", yaxis_title="% of days")
            st.plotly_chart(style(fig, 360), width="stretch")
        with right:
            ia = b[b.Department == "ICU Adult"].sort_values("Date")
            if len(ia):
                fig = go.Figure(go.Histogram(x=ia.Available_Beds, marker_color=RED, nbinsx=15))
                fig.update_layout(title="ICU Adult: free beds per day", xaxis_title="Available beds", yaxis_title="Days")
                st.plotly_chart(style(fig, 360, False), width="stretch")
        icu_fl = fl[fl.ICU_Transfer.notna()]
        if len(fl):
            st.caption(f"{len(icu_fl)} of {len(fl):,} ED patients ({len(icu_fl) / len(fl):.1%}) in the selection were later transferred to intensive care, a median of {((icu_fl.ICU_Transfer - icu_fl.Ward_Admission).dt.total_seconds() / 3600).median():.0f} hours after reaching the ward." if len(icu_fl) else "No ICU transfers in the selection.")

# ================================================================== TAB 4
with t4:
    st.markdown("#### Patient flow and length of stay")
    if fl.empty:
        st.info("No ED flow records for the selected departments and dates.")
    else:
        cols = st.columns(4)
        card(cols[0], "Median ED to ward time", f"{ed_med:.0f} min", "Target under 30 min", f"middle 50% between {fl.ed_to_ward.quantile(.25):.0f} and {fl.ed_to_ward.quantile(.75):.0f} min", "Above threshold")
        card(cols[1], "Within 30 minutes", f"{ed_30:.1%}", "", f"{(fl.ed_to_ward <= 60).mean():.1%} within 60 min · {(fl.ed_to_ward <= 120).mean():.0%} within 2 hours")
        card(cols[2], "Average length of stay", f"{alos:.2f} days", "Target 4.5 days", f"{len(a):,} admissions", "On target" if alos <= ALOS_TARGET else "Above threshold")
        card(cols[3], "Longest wait", f"{fl.ed_to_ward.max() / 60:.1f} h", "", f"{len(fl):,} ED flow records")
        st.markdown("&nbsp;")
        left, right = st.columns(2)
        with left:
            fig = go.Figure(go.Histogram(x=fl.ed_to_ward, xbins=dict(size=10), marker_color=TEAL))
            fig.add_vline(x=30, line=dict(color=RED, dash="dash"), annotation_text="30-min target")
            fig.add_vline(x=ed_med, line=dict(color=GOLD, dash="dot"), annotation_text=f"median {ed_med:.0f}", annotation_position="top right")
            fig.update_layout(title="ED arrival to ward admission", xaxis_title="Minutes", yaxis_title="Patients")
            st.plotly_chart(style(fig, 380, False), width="stretch")
        with right:
            wd = fl.groupby("Ward_Department").ed_to_ward.median().sort_values()
            fig = go.Figure(go.Bar(x=wd.values, y=wd.index, orientation="h", marker_color=TEAL, text=[f"{v:.0f}" for v in wd.values], textposition="outside", cliponaxis=False))
            fig.add_vline(x=30, line=dict(color=RED, dash="dash"))
            fig.update_layout(title="Median wait by receiving ward (minutes)", xaxis=dict(range=[0, max(200, wd.max() * 1.2)]))
            st.plotly_chart(style(fig, 380, False), width="stretch")
        left, right = st.columns(2)
        with left:
            los = a.groupby("Department").LOS_Days.mean().sort_values()
            fig = go.Figure(go.Bar(x=los.values, y=los.index, orientation="h", marker_color=[GOLD if v > ALOS_TARGET else TEAL for v in los.values],
                                   text=[f"{v:.1f}" for v in los.values], textposition="outside", cliponaxis=False))
            fig.add_vline(x=4.5, line=dict(color="#888", dash="dash"), annotation_text="4.5 days")
            fig.update_layout(title="Average length of stay by department (days)", xaxis=dict(range=[0, max(8, los.max() * 1.15)]))
            st.plotly_chart(style(fig, 420, False), width="stretch")
            st.caption("Dialysis is a day-case service (about 0 days), which pulls the hospital average down.")
        with right:
            hr = fl.ED_Arrival.dt.hour.value_counts().sort_index()
            fig = go.Figure(go.Bar(x=hr.index, y=hr.values, marker_color=NAVY if False else TEAL))
            fig.update_layout(title="ED arrivals by hour of day", xaxis_title="Hour", yaxis_title="Patients")
            st.plotly_chart(style(fig, 210, False), width="stretch")
            out = a.Outcome.value_counts()
            fig = go.Figure(go.Bar(x=out.index, y=out.values / out.sum() * 100, marker_color=[GREEN, GOLD, RED, GREY][: len(out)], text=[f"{v / out.sum():.1%}" for v in out.values], textposition="outside", cliponaxis=False))
            fig.update_layout(title="Admission outcomes (%)", yaxis=dict(range=[0, 110]))
            st.plotly_chart(style(fig, 210, False), width="stretch")

# ================================================================== TAB 5
with t5:
    st.markdown("#### Nurse workload and bed turnover")
    st.caption("Staffing is recorded as one daily headcount, so the ratio below is occupied beds per nurse on the day. A shift-level ratio would be higher.")
    r = stf.groupby("Department").agg(ratio=("pts_per_nurse", "mean"), over=("pts_per_nurse", lambda s: np.nan)).drop(columns="over")
    r["category"] = r.index.map(dep_tbl.Category)
    r["limit"] = np.where(r.index.isin(CRITICAL), 2, 5)
    r["over_share"] = [(stf[stf.Department == d].pts_per_nurse > lim + 0.0005).mean() * 100 for d, lim in zip(r.index, r.limit)]
    r = r.sort_values("ratio")
    left, right = st.columns(2)
    with left:
        eligible = r[r.category.isin(["Critical Care", "Inpatient Ward"])]
        fig = go.Figure(go.Bar(x=eligible.ratio, y=eligible.index, orientation="h", marker_color=[RED if v > l + .005 else TEAL for v, l in zip(eligible.ratio, eligible.limit)],
                               text=[f"1:{v:.1f}" for v in eligible.ratio], textposition="outside", cliponaxis=False))
        fig.update_layout(title="Average patients per nurse (critical care limit 2, wards limit 5)", xaxis=dict(range=[0, 6.5], title="Patients per nurse"))
        st.plotly_chart(style(fig, 400, False), width="stretch")
    with right:
        fig = go.Figure(go.Bar(x=eligible.over_share, y=eligible.index, orientation="h", marker_color=GOLD, text=[f"{v:.0f}%" for v in eligible.over_share], textposition="outside", cliponaxis=False))
        fig.update_layout(title="Share of days worse than the target ratio", xaxis=dict(range=[0, 110], title="% of days"))
        st.plotly_chart(style(fig, 400, False), width="stretch")
    st.info("Average ratios sit almost exactly on the targets, so there is no safety margin: on a large share of days the ratio is worse than the target.")

    st.markdown("#### Bed turnover and bed status")
    left, right = st.columns(2)
    with left:
        tv = (dis.groupby("Department").size() / dep_tbl.loc[sel, "Total_Beds"] / months).reindex(sel).dropna().sort_values()
        fig = go.Figure(go.Bar(x=tv.values, y=tv.index, orientation="h", marker_color=GOLD, text=[f"{v:.1f}" for v in tv.values], textposition="outside", cliponaxis=False))
        fig.add_vline(x=7, line=dict(color=RED, dash="dash"), annotation_text="target 7")
        fig.update_layout(title="Discharges per bed per month", xaxis=dict(range=[0, 8.5]))
        st.plotly_chart(style(fig, 420, False), width="stretch")
        st.caption("Taken from the admissions table. It does not reconcile with the bed census, see the Dataset checks tab.")
    with right:
        mix = bs.groupby(["Department", "Status"]).size().unstack(fill_value=0)
        mix = mix.div(mix.sum(axis=1), axis=0) * 100
        mix = mix.reindex(columns=[c for c in STATUS_ORDER if c in mix.columns]).sort_values("Occupied")
        fig = go.Figure()
        for s_ in mix.columns:
            fig.add_trace(go.Bar(x=mix[s_], y=mix.index, orientation="h", name=s_, marker_color=STATUS_BAR[s_]))
        fig.update_layout(barmode="stack", title="Bed status mix by department (% of bed-days)", xaxis=dict(range=[0, 100]))
        st.plotly_chart(style(fig, 420), width="stretch")

# ================================================================== TAB 6
with t6:
    st.markdown("#### 30-day occupancy forecast (whole hospital)")
    hist = hosp_daily.reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fc.Date, y=fc.Upper_Bound * 100, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=fc.Date, y=fc.Lower_Bound * 100, mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(44,156,147,0.25)", name="Forecast range"))
    fig.add_trace(go.Scatter(x=hist.Date, y=hist.occ * 100, mode="lines", name="Actual", line=dict(color=NAVY if False else GOLD, width=2)))
    fig.add_trace(go.Scatter(x=fc.Date, y=fc.Predicted_Occupancy_Pct * 100, mode="lines", name="Forecast", line=dict(color=TEAL, width=3)))
    fig.add_hline(y=85, line=dict(color="#888", dash="dash"), annotation_text="85% target")
    fig.update_layout(title="Actual occupancy and forecast", yaxis=dict(title="%", range=[70, 100]))
    st.plotly_chart(style(fig, 440), width="stretch")
    cols = st.columns(3)
    card(cols[0], "Forecast average", f"{fc.Predicted_Occupancy_Pct.mean():.1%}", "Next 30 days", f"from {fc.Date.min():%d %b} to {fc.Date.max():%d %b}")
    card(cols[1], "Forecast range", f"{fc.Lower_Bound.min():.1%} to {fc.Upper_Bound.max():.1%}", "", "")
    last7 = hosp_daily.occ.tail(7).mean()
    card(cols[2], "Last 7 days actual", f"{last7:.1%}", "", f"gap to forecast: {(fc.Predicted_Occupancy_Pct.mean() - last7) * 100:+.1f} points")
    st.info("Forecast accuracy (MAPE) cannot be calculated: the forecast covers future dates only, so there are no actuals to compare with. Once those days pass, compare the forecast with the actual occupancy, and judge it against the 8% target.")

# ================================================================== TAB 7
with t7:
    st.markdown("#### Dataset checks: what can and cannot be concluded")
    all_occ_days = beds.Occupied_Beds.sum()
    all_los = adm.LOS_Days.sum()
    st.markdown("**Checks that passed**")
    bs_cnt = status.groupby(["Date", "Department", "Status"]).size().unstack(fill_value=0)
    m = beds.set_index(["Date", "Department"]).join(bs_cnt)
    ok_status = bool(((m.Occupied_Beds - m.Occupied).abs().max() == 0) and ((m.Available_Beds - m.Available).abs().max() == 0))
    ok_total = bool((beds.groupby("Date").Total_Beds.sum() == dep_tbl.Total_Beds.sum()).all())
    ok_los = bool((adm.Discharge_Date - adm.Admission_Date).dt.days.eq(adm.LOS_Days).all())
    mark = lambda ok: "✅" if ok else "❌"
    st.markdown(f"- {mark(ok_status)} **Bed status matches the daily bed counts** for every department-day.\n"
                f"- {mark(ok_total)} **Total beds add up to {dep_tbl.Total_Beds.sum():,}** on all {beds.Date.nunique()} days.\n"
                f"- {mark(ok_los)} **Length of stay matches the admission and discharge dates** in every record.")
    st.markdown("**Findings that limit the conclusions**")
    rec = pd.DataFrame({"census": beds.groupby("Department").Occupied_Beds.sum()})
    start, end = beds.Date.min(), beds.Date.max()
    nights = {}
    for d_, g in adm.groupby("Department"):
        e = np.minimum(g.Discharge_Date - pd.Timedelta(days=1), end)
        s_ = np.maximum(g.Admission_Date, start)
        nights[d_] = int(np.maximum((e - s_).dt.days + 1, 0).sum())
    rec["nights"] = pd.Series(nights)
    rec["coverage"] = rec.nights / rec.census * 100
    cover = rec.nights.sum() / rec.census.sum()
    implied_turn = hosp_daily.occ.mean() * 30.44 / adm[adm.Department != "Dialysis"].LOS_Days.mean()
    st.markdown(f"- ⚠️ **The admissions table covers only {cover:.0%} of occupied bed-days.** Patient nights from admissions: {rec.nights.sum():,}. Occupied bed-days in the bed census: {rec.census.sum():,}. This makes the turnover figure from admissions ({len(adm[adm.Discharge_Date <= end]) / 1000 / (92 / 30.44):.1f} per bed per month) look worse than it probably is. Using occupancy and length of stay together, the implied turnover is about **{implied_turn:.1f}**, still below the target of 7, but far closer. The admissions table appears to be a partial record.\n"
                f"- ⚠️ **Readmission rate cannot be measured:** every one of the {len(adm):,} Patient_IDs is unique, so no patient appears twice.\n"
                f"- ⚠️ **Bed cleaning turnaround cannot be measured:** there are no start and end times, only a daily status ({(status.Status == 'Cleaning').mean():.1%} of bed-days are in cleaning).\n"
                f"- ⚠️ **Forecast accuracy cannot be measured:** there are no actual values for the forecast dates.\n"
                f"- ⚠️ **Staffing is a daily headcount**, so nurse ratios are daily averages, not shift ratios.\n"
                f"- ⚠️ **The first week has fewer discharges** because patients admitted before 27 April are not in the data, which slightly lowers turnover for any period that includes it.")
    fig = go.Figure()
    rr = rec.sort_values("census")
    fig.add_trace(go.Bar(y=rr.index, x=rr.census, orientation="h", name="Occupied bed-days (bed census)", marker_color=NAVY if False else TEAL))
    fig.add_trace(go.Bar(y=rr.index, x=rr.nights, orientation="h", name="Patient nights from admissions", marker_color=GOLD))
    fig.update_layout(barmode="group", title="Do admissions explain the occupied beds? (whole hospital)", xaxis_title="Bed-days")
    st.plotly_chart(style(fig, 520), width="stretch")
    st.caption("Dialysis shows almost no patient nights because it is a day-case service with a length of stay near 0, while its beds are counted as occupied each day.")
    st.markdown("**How the KPI status is decided:** On target = meets the target in the KPI_Targets sheet (occupancy within one point). Above threshold = worse than the limit. Below threshold = turnover under the target. Not measurable = the dataset does not contain what the KPI needs.")
    st.markdown("---\n**Yosra El Nagar**, Cath Lab Head Nurse moving into Healthcare Data Analytics · [LinkedIn](https://www.linkedin.com/in/yosra-nagar-9a6862118/) · [GitHub](https://github.com/yosras-dotcomAi/1000-Bed-Hospital-)")
