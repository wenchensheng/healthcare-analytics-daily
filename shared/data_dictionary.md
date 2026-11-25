# Data dictionary — Amber Ridge Health (synthetic)

All tables and columns are generic names invented for this series. They are **not** Epic Clarity, Caboodle, or Willow schema, and this project is not affiliated with or endorsed by Epic Systems Corporation.

Every row is generated from a fixed seed (`SEED=42`) and describes no real patient, provider, or organization. Identifiers are zero-padded codes (`P000001`, `A000001`). There are no names, dates of birth, addresses, phone numbers, or other direct identifiers.

Study window: **2024-01-01** to **2025-12-31**.

## Tables and row counts

| Table | Rows | Grain |
|---|---:|---|
| dim_clinic | 7 | one row per clinic or hospital |
| dim_payer | 5 | one row per payer |
| dim_drug | 30 | one row per medication product |
| dim_provider | 38 | one row per provider |
| dim_patient | 8,000 | one row per patient |
| dim_date | 731 | one row per calendar day |
| fact_appointment | 49,538 | one scheduled outpatient visit |
| fact_claim | 39,998 | one claim (professional or hospital) |
| fact_inpatient_stay | 2,806 | one hospital stay |
| fact_ed_visit | 8,000 | one emergency visit |
| fact_medication_order | 15,396 | one inpatient medication order |
| fact_medication_admin | 20,410 | one scheduled administration |
| fact_quality_event | 22,046 | one measure evaluation for a patient and period |
| fact_provider_session | 120 | one provider × weekday capacity row |
| raw_appointment_extract | 8,120 | messy extract (duplicates and defects included) |

## Column notes

- `fact_appointment.status`: `completed`, `no_show`, or `cancelled`.
- `fact_appointment.modality`: `in_person`, `video`, or `audio`.
- `fact_appointment.visit_type`: `chronic_followup`, `acute`, `preventive`, or `new_patient`.
- No-show rate used in this series: no-shows ÷ (completed + no-shows). Cancellations are excluded.
- `fact_claim.claim_status`: `paid`, `denied`, or `pending`. `ar_days` is aged from service date to 2025-12-31 for unpaid claims.
- 30-day readmissions are **not** pre-flagged; compute them in SQL from `fact_inpatient_stay` dates.
- `fact_ed_visit.disposition`: `discharge`, `admit`, `transfer`, or `lwbs` (left without being seen).
- `fact_medication_admin.admin_status`: `given`, `late` (>60 minutes), `missed`, or `refused`.
- `raw_appointment_extract` is an 8,000-row sample plus injected defects (the only dirty table). Known issue types: duplicate appointment IDs, null clinic IDs, reversed dates, mixed-case status and modality labels, and a few out-of-window dates.
