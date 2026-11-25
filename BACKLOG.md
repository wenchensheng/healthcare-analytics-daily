# Backlog

Thirty concrete day topics. Day 001 is done. Each remaining line is one small, complete exercise that should take well under a day and still produce a real finding. Data sources point at tables in [`shared/clinic.db`](shared/clinic.db) unless a public CMS file is named.

Check a line off when the day folder is added and the root README index is updated.

- [x] **Day 001.** Monthly clinic no-show rate and trend by visit type. Data: synthetic `fact_appointment`.
- [ ] **Day 002.** Access: share of visits booked more than 14 days out, by clinic and modality. Data: synthetic `fact_appointment`.
- [ ] **Day 003.** No-show rate by lead-time band and payer. Data: synthetic `fact_appointment`, `dim_payer`.
- [ ] **Day 004.** Clinic outlier: which site's no-show rate stays above the network, month after month (z-score / window functions). Data: synthetic `fact_appointment`.
- [ ] **Day 005.** Data-quality audit of an appointment extract: duplicates, null clinics, reversed dates, mixed labels. Data: synthetic `raw_appointment_extract`.
- [ ] **Day 006.** Claim denial rate by payer and denial reason. Data: synthetic `fact_claim`, `dim_payer`.
- [ ] **Day 007.** Accounts receivable aging: share of unpaid balances older than 120 days. Data: synthetic `fact_claim`.
- [ ] **Day 008.** 30-day all-cause readmission rate by principal condition (computed from stay dates, not a pre-flag). Data: synthetic `fact_inpatient_stay`.
- [ ] **Day 009.** Heart-failure readmissions: observed rate vs a simple age-band expected rate. Data: synthetic `fact_inpatient_stay`, `dim_patient`.
- [ ] **Day 010.** ED door-to-provider time and left-without-being-seen rate by hour of day. Data: synthetic `fact_ed_visit`.
- [ ] **Day 011.** ED arrival heatmap (weekday × hour) and a staffing implication for the peak cells. Data: synthetic `fact_ed_visit`.
- [ ] **Day 012.** A simple 14-day forecast of ED arrivals from the recent daily trend. Data: synthetic `fact_ed_visit`.
- [ ] **Day 013.** Late and missed medication administration rate by night vs day shift (Willow-style pharmacy operations; not Epic's schema). Data: synthetic `fact_medication_admin`.
- [ ] **Day 014.** High-alert medication orders and cancellation rate vs other drug classes. Data: synthetic `fact_medication_order`, `dim_drug`.
- [ ] **Day 015.** Generic substitution opportunity: brand vs generic share and estimated cost difference for the same drug class. Data: synthetic `fact_medication_order`, `dim_drug`.
- [ ] **Day 016.** Opioid ordering rate by attending specialty during inpatient stays. Data: synthetic `fact_medication_order`, `fact_inpatient_stay`, `dim_provider`.
- [ ] **Day 017.** Patient retention: share of patients with a return primary-care visit within 12 months of an index visit. Data: synthetic `fact_appointment`.
- [ ] **Day 018.** New-to-established: time from first completed visit to the third visit (window `LAG` / `LEAD`). Data: synthetic `fact_appointment`.
- [ ] **Day 019.** Provider productivity: completed visits versus weekday session capacity. Data: synthetic `fact_appointment`, `fact_provider_session`.
- [ ] **Day 020.** Telehealth share at Amber Ridge vs a CMS national Medicare telehealth benchmark. Data: synthetic `fact_appointment` plus public CMS Medicare Telehealth Trends.
- [ ] **Day 021.** Audio-only use and in-person versus virtual mix by rurality and age band. Data: synthetic `fact_appointment`, `dim_patient`.
- [ ] **Day 022.** Influenza immunization rate among eligible patients, two seasons (CMS-style logic, not an official CMS spec). Data: synthetic `fact_quality_event`, `dim_patient`.
- [ ] **Day 023.** Diabetes A1C monitoring: share of patients with diabetes who have a result in the calendar year. Data: synthetic `fact_quality_event`, `dim_patient`.
- [ ] **Day 024.** Python cleaning notebook: standardize status and modality labels, repair date order, quarantine bad rows. Data: synthetic `raw_appointment_extract`.
- [ ] **Day 025.** Loose duplicate-patient check: same home clinic, age band, and tightly clustered visit dates. Data: synthetic `dim_patient`, `fact_appointment`.
- [ ] **Day 026.** Window-function drill: 3-month running no-show average and monthly clinic rank. Data: synthetic `fact_appointment`.
- [ ] **Day 027.** Days from inpatient discharge to first primary-care follow-up, by condition and disposition. Data: synthetic `fact_inpatient_stay`, `fact_appointment`.
- [ ] **Day 028.** Denial rework queue: unpaid denials with recoverable reasons (coding, authorization) vs low-yield reasons. Data: synthetic `fact_claim`.
- [ ] **Day 029.** Inpatient pharmacy spend concentration: top drug classes as a share of estimated medication cost (Willow-style; not Epic's schema). Data: synthetic `fact_medication_order`.
- [ ] **Day 030.** Year-in-review executive brief: eight KPIs, one chart pack, three recommended actions. Data: the shared synthetic tables used across earlier days.
