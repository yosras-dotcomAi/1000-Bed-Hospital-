# 1,000-Bed Hospital: Capacity and Operational Performance

> **Note on data:** This is a case study of a **fictional** 1,000-bed hospital using a **synthetic** dataset. No real patient or hospital data is used. The project is built to show strategic analysis skills in healthcare: data modelling, KPI validation and executive reporting.

| | |
|---|---|
| **Live dashboard** | [Open the Streamlit app](STREAMLIT-LINK) |
| **Project slides** | [View the presentation](docs/Hospital_1000Bed_Slides.pptx) |

## Objective

Assess bed capacity and operational performance of a large hospital against 10 executive KPIs, find where the pressure is, and be clear about what the data can and cannot support.

## The Dataset

`data/Hospital_1000Bed_Dataset.xlsx`: 8 sheets, about 108,000 rows, 92 days (27 April to 27 July 2026).

| Sheet | Rows | Content |
|---|---|---|
| Departments | 12 | Beds, category and floor per department |
| Hospital_Bed_Daily | 1,104 | Daily total, occupied and available beds by department |
| Patient_Admissions | 10,200 | Admission and discharge dates, length of stay, type, outcome |
| Staffing | 1,104 | Daily nurses, physicians and support staff by department |
| Bed_Status | 92,000 | Daily status of each of the 1,000 beds |
| Patient_Flow | 3,500 | ED arrival, ward admission, ICU transfer and discharge times |
| Forecast_Data | 30 | 30-day occupancy forecast with bounds |
| KPI_Targets | 10 | The 10 KPIs, their targets and definitions |

## Interactive dashboard

The [live Streamlit dashboard](STREAMLIT-LINK) has seven tabs and filters for department and dates: an executive scorecard, bed capacity, critical care, patient flow and length of stay, staffing and turnover, the forecast, and dataset checks.

## The 10 KPIs against their targets

| KPI | Result | Target | Status |
|---|---|---|---|
| Bed occupancy rate | 84.7% | 85% | On target |
| Average length of stay | 4.28 days | 4.5 days | On target |
| Bed turnover rate (from admissions) | 3.2 | 7 per bed per month | Below threshold (see checks below) |
| ED waiting time (median) | 152 min | under 30 min | Above threshold |
| ICU Adult occupancy | 92.3% | under 92% | Above threshold |
| Nurse-to-patient ratio, general wards | 1:4.9 | 1:5 | On target |
| Nurse-to-patient ratio, ICU and CCU | 1:2.0 | 1:2 | On target |
| Readmission rate | not measurable | under 5% | Not measurable |
| Bed cleaning turnaround | not measurable | under 60 min | Not measurable |
| Forecast accuracy (MAPE) | not measurable | under 8% | Not measurable |

## Key Findings

1. **Overall capacity is on target, but departments differ.** Occupancy is 84.7% hospital-wide, while ICU Adult runs at 92.3% and CCU at 88.8%. Isolation (67.1%), Dialysis (76.0%) and Pediatrics (76.7%) have spare capacity.
2. **Critical care is the pressure point.** ICU Adult exceeded the 92% safe limit on 49 of 92 days (53%), with a longest run of 6 days in a row. CCU exceeded it on 24 days and ICU Pediatric on 8.
3. **Patients wait about 2.5 hours for a ward bed.** The median time from ED arrival to ward admission is 152 minutes against a 30-minute target. No patient met it, only 2.6% were admitted within 60 minutes, and the wait is similar for every receiving ward.
4. **Staffing sits exactly on target, with no margin.** Average ratios match the targets (1:2 in critical care, 1:5 on wards), but the ratio is worse than the target on 33% of critical care unit-days and 40% of ward-days. Staffing is a daily headcount, so a shift-level ratio would be higher.
5. **Length of stay is on target** at 4.28 days (4.37 days without day-case dialysis).

## Honest Data Checks

- **The bed turnover gap needs care.** Turnover calculated from the admissions table is 3.2 discharges per bed per month, but that table explains only 55% of occupied bed-days (42,672 of 77,954). Using occupancy and length of stay together, the implied turnover is about 5.9, still below the target of 7 but much closer. The admissions table appears to be a partial record.
- **Readmission rate cannot be measured:** every one of the 10,200 Patient_IDs is unique, so no patient appears twice.
- **Bed cleaning turnaround cannot be measured:** only a daily bed status exists, with no start and end times.
- **Forecast accuracy cannot be measured:** the forecast covers future dates, so there are no actual values to compare with.
- **Checks that passed:** bed status matches the daily bed counts for every department-day, total beds equal 1,000 on every day, and length of stay matches the admission and discharge dates in every record.

## Suggested Actions (for discussion)

These are hypotheses from a synthetic dataset, to be tested with real operational data.

1. Protect ICU Adult capacity through step-down and early-discharge pathways.
2. Shorten ED boarding by tracking the time from bed request to bed ready, with staged targets.
3. Rebalance under-used capacity in Isolation, Dialysis and Pediatrics.
4. Add a float pool for high-occupancy days in critical care.
5. Close the measurement gaps: capture patient re-visits, bed-cleaning timestamps and forecast actuals.

## How to Run

```
pip install -r requirements.txt
python hospital_capacity_analysis.py    # creates department_scorecard.csv, kpi_scorecard.csv and 4 charts
streamlit run app.py                    # opens the interactive dashboard
```

## Repository Structure

```
1000-Bed-Hospital-/
├── app.py                              # Streamlit dashboard
├── requirements.txt
├── .streamlit/
│   └── config.toml                     # Dashboard theme
├── hospital_capacity_analysis.py       # KPI analysis and charts
├── data/
│   └── Hospital_1000Bed_Dataset.xlsx   # Synthetic dataset (8 sheets)
├── docs/
│   └── Hospital_1000Bed_Slides.pptx
└── README.md
```

## Project Status

- [x] Synthetic dataset and Python KPI analysis
- [x] Power BI executive dashboard (star schema, DAX measures, KPI validation)
- [x] Interactive Streamlit dashboard
- [x] Project slides
- [ ] Tableau Public rebuild (in progress)

## Author

**Yosra El Nagar**, Cath Lab Head Nurse moving into Healthcare Data Analytics [LinkedIn](https://www.linkedin.com/in/yosra-nagar-9a6862118/)

---

## 🇸🇦 ملخص بالعربي

دراسة حالة تحليلية لمستشفى **وهمي** سعته 1000 سرير، ببيانات **اصطناعية**، لا توجد فيها أي بيانات مرضى حقيقية. الهدف بناء بورتفوليو يوضح مهارات التحليل الاستراتيجي في الرعاية الصحية.

- **الإشغال العام على المستهدف (84.7%)**، لكن الأقسام مختلفة جداً: العناية المركزة للبالغين 92.3%، بينما العزل وغسيل الكلى والأطفال فيها طاقة غير مستغلة.
- **العناية المركزة هي نقطة الضغط:** تجاوزت العناية المركزة للبالغين الحد الآمن (92%) في 49 يوماً من 92.
- **الانتظار طويل:** الوسيط من وصول الطوارئ إلى دخول القسم 152 دقيقة مقابل هدف 30 دقيقة.
- **التمريض على الهدف تماماً بلا هامش أمان**، والنسبة أسوأ من الهدف في ثلث الأيام تقريباً.
- **صراحة منهجية:** ثلاثة مؤشرات لا يمكن قياسها (إعادة الدخول، زمن تنظيف السرير، دقة التنبؤ)، وفجوة معدل دوران الأسرّة تحتاج حذراً لأن جدول الدخول يغطي 55% فقط من أيام الإشغال.
- **جديد:** لوحة تفاعلية على Streamlit ببيانات وتحليل المشروع نفسه.
