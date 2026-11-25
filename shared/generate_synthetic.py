#!/usr/bin/env python3
"""Seeded synthetic clinic data for the healthcare-analytics-daily series.

Everything in the database is fictional. It describes no real patient,
provider, clinic, or health system. Table and column names are generic
inventions. They are not Epic's Clarity, Caboodle, or Willow schema,
and this project is not affiliated with or endorsed by Epic Systems
Corporation.

Re-run:
    python shared/generate_synthetic.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")

SHARED_DIR = Path(__file__).resolve().parent
DB_PATH = SHARED_DIR / "clinic.db"
SAMPLE_DIR = SHARED_DIR / "samples"
DICT_PATH = SHARED_DIR / "data_dictionary.md"

SYSTEM_NAME = "Amber Ridge Health"

CLINICS = pd.DataFrame(
    [
        ("C01", "Maple Street Primary Care", "primary_care", "Urban", "North"),
        ("C02", "Oakridge Family Medicine", "primary_care", "Suburban", "North"),
        ("C03", "Cedar Hollow Clinic", "primary_care", "Rural", "West"),
        ("C04", "Lakeside Family Practice", "primary_care", "Suburban", "South"),
        ("C05", "Brookfield Medical Group", "primary_care", "Urban", "South"),
        ("C06", "Pine Ridge Clinic", "primary_care", "Rural", "West"),
        ("H01", "Ridgeline Community Hospital", "hospital", "Urban", "Central"),
    ],
    columns=["clinic_id", "clinic_name", "site_type", "geography", "region"],
)

PAYERS = pd.DataFrame(
    [
        ("MEDCR", "Medicare FFS", "medicare"),
        ("MCAID", "Medicaid", "medicaid"),
        ("SUMP", "Summit PPO", "commercial"),
        ("BRCH", "Birch HMO", "commercial"),
        ("SELF", "Self-pay", "self_pay"),
    ],
    columns=["payer_id", "payer_name", "payer_type"],
)

# Payer mix differs slightly by geography.
PAYER_WEIGHTS = {
    "Urban": [0.28, 0.18, 0.32, 0.17, 0.05],
    "Suburban": [0.26, 0.14, 0.36, 0.19, 0.05],
    "Rural": [0.34, 0.22, 0.26, 0.13, 0.05],
}

VISIT_TYPES = ["chronic_followup", "acute", "preventive", "new_patient"]
VISIT_TYPE_P = [0.45, 0.25, 0.20, 0.10]
SPECIALTIES_PC = ["Family Medicine", "Internal Medicine", "Pediatrics"]
AGE_BANDS = ["0-17", "18-34", "35-49", "50-64", "65-74", "75+"]
AGE_P = [0.12, 0.16, 0.20, 0.22, 0.18, 0.12]

DRUGS = pd.DataFrame(
    [
        ("D01", "metformin", "antidiabetic", 0, 0, 0.12),
        ("D02", "lisinopril", "antihypertensive", 0, 0, 0.08),
        ("D03", "atorvastatin", "statin", 0, 0, 0.15),
        ("D04", "amlodipine", "antihypertensive", 0, 0, 0.10),
        ("D05", "omeprazole", "ppi", 0, 0, 0.14),
        ("D06", "levothyroxine", "thyroid", 0, 0, 0.11),
        ("D07", "albuterol", "bronchodilator", 0, 0, 0.25),
        ("D08", "furosemide", "diuretic", 0, 0, 0.09),
        ("D09", "metoprolol", "beta_blocker", 0, 0, 0.10),
        ("D10", "losartan", "antihypertensive", 0, 0, 0.13),
        ("D11", "insulin glargine", "antidiabetic", 1, 0, 8.50),
        ("D12", "hydrocodone-acetaminophen", "opioid", 1, 0, 0.45),
        ("D13", "oxycodone", "opioid", 1, 0, 0.55),
        ("D14", "heparin", "anticoagulant", 1, 0, 0.30),
        ("D15", "enoxaparin", "anticoagulant", 1, 0, 1.80),
        ("D16", "vancomycin", "antibiotic", 1, 0, 2.10),
        ("D17", "cefazolin", "antibiotic", 0, 0, 0.40),
        ("D18", "ondansetron", "antiemetic", 0, 0, 0.22),
        ("D19", "hydromorphone", "opioid", 1, 0, 0.70),
        ("D20", "pantoprazole", "ppi", 0, 0, 0.18),
        ("D21", "aspirin", "antiplatelet", 0, 0, 0.03),
        ("D22", "warfarin", "anticoagulant", 1, 0, 0.16),
        ("D23", "apixaban", "anticoagulant", 1, 1, 14.50),
        ("D24", "insulin lispro (brand)", "antidiabetic", 1, 1, 18.00),
        ("D25", "insulin lispro (generic)", "antidiabetic", 1, 0, 6.50),
        ("D26", "rosuvastatin (brand)", "statin", 0, 1, 6.20),
        ("D27", "rosuvastatin (generic)", "statin", 0, 0, 0.28),
        ("D28", "acetaminophen", "analgesic", 0, 0, 0.04),
        ("D29", "ipratropium", "bronchodilator", 0, 0, 0.35),
        ("D30", "prednisone", "corticosteroid", 0, 0, 0.08),
    ],
    columns=["drug_id", "drug_name", "drug_class", "is_high_alert", "is_brand", "unit_cost"],
)

INPATIENT_CONDITIONS = [
    "heart_failure",
    "pneumonia",
    "copd",
    "sepsis",
    "joint_replacement",
    "other_medical",
    "other_surgical",
]
INPATIENT_P = [0.14, 0.13, 0.10, 0.08, 0.09, 0.28, 0.18]
# Probability a stay is followed by another stay within 30 days.
READMIT_P = {
    "heart_failure": 0.22,
    "pneumonia": 0.16,
    "copd": 0.19,
    "sepsis": 0.17,
    "joint_replacement": 0.05,
    "other_medical": 0.12,
    "other_surgical": 0.08,
}

ED_COMPLAINTS = [
    "chest_pain",
    "shortness_of_breath",
    "abdominal_pain",
    "injury",
    "fever_infection",
    "neuro_symptom",
    "other",
]
ED_COMPLAINT_P = [0.12, 0.11, 0.16, 0.18, 0.14, 0.08, 0.21]


def rng():
    return np.random.default_rng(SEED)


def build_dates() -> pd.DataFrame:
    days = pd.date_range(START, END, freq="D")
    d = pd.DataFrame({"date": days})
    d["date"] = d["date"].dt.strftime("%Y-%m-%d")
    d["year"] = days.year
    d["month"] = days.month
    d["month_name"] = days.strftime("%b")
    d["quarter"] = days.quarter
    d["year_month"] = days.strftime("%Y-%m")
    d["weekday"] = days.day_name()
    d["weekday_num"] = days.day_of_week  # Mon=0
    d["is_weekend"] = (days.day_of_week >= 5).astype(int)
    return d


def build_providers(rand: np.random.Generator) -> pd.DataFrame:
    rows = []
    n = 1
    for _, c in CLINICS.iterrows():
        if c.site_type == "primary_care":
            specs = ["Family Medicine", "Family Medicine", "Internal Medicine", "Pediatrics"]
            creds = ["MD", "NP", "MD", "MD"]
            slots = [6, 5, 6, 5]
            for spec, cred, slot in zip(specs, creds, slots):
                rows.append((f"PR{n:03d}", c.clinic_id, cred, spec, slot))
                n += 1
        else:
            for spec, cred, slot, k in [
                ("Emergency Medicine", "MD", 0, 6),
                ("Hospital Medicine", "MD", 0, 8),
            ]:
                for _ in range(k):
                    rows.append((f"PR{n:03d}", c.clinic_id, cred, spec, slot))
                    n += 1
    return pd.DataFrame(
        rows,
        columns=["provider_id", "clinic_id", "credential", "specialty", "daily_slot_capacity"],
    )


def build_patients(rand: np.random.Generator, n: int = 8000) -> pd.DataFrame:
    pc = CLINICS[CLINICS.site_type == "primary_care"].reset_index(drop=True)
    # Urban clinics have more assigned patients.
    clinic_p = np.array([0.22, 0.18, 0.12, 0.18, 0.20, 0.10])
    clinic_id = rand.choice(pc.clinic_id.to_numpy(), n, p=clinic_p)
    geo = dict(zip(pc.clinic_id, pc.geography))
    geography = np.array([geo[c] for c in clinic_id])
    payer_id = np.empty(n, dtype=object)
    for g, w in PAYER_WEIGHTS.items():
        m = geography == g
        payer_id[m] = rand.choice(PAYERS.payer_id.to_numpy(), int(m.sum()), p=w)
    age_band = rand.choice(AGE_BANDS, n, p=AGE_P)
    sex = rand.choice(["F", "M"], n, p=[0.53, 0.47])
    rural_flag = np.where(geography == "Rural", 1, np.where(geography == "Suburban", 0, 0))
    # A few urban/suburban patients are rural-residing.
    flip = rand.random(n) < 0.06
    rural_flag = np.where(flip & (geography != "Rural"), 1, rural_flag)

    # Condition prevalence rises with age.
    age_idx = pd.Series(age_band).map({b: i for i, b in enumerate(AGE_BANDS)}).to_numpy()
    p_dm = np.clip(0.02 + age_idx * 0.06, 0, 0.35)
    p_htn = np.clip(0.04 + age_idx * 0.10, 0, 0.55)
    p_hf = np.clip(0.002 + np.maximum(age_idx - 3, 0) * 0.04, 0, 0.16)
    p_copd = np.clip(0.01 + np.maximum(age_idx - 2, 0) * 0.03, 0, 0.14)
    has_diabetes = (rand.random(n) < p_dm).astype(int)
    has_hypertension = (rand.random(n) < p_htn).astype(int)
    has_heart_failure = (rand.random(n) < p_hf).astype(int)
    has_copd = (rand.random(n) < p_copd).astype(int)

    return pd.DataFrame(
        {
            "patient_id": [f"P{i:06d}" for i in range(1, n + 1)],
            "home_clinic_id": clinic_id,
            "age_band": age_band,
            "sex": sex,
            "rural_flag": rural_flag,
            "payer_id": payer_id,
            "has_diabetes": has_diabetes,
            "has_hypertension": has_hypertension,
            "has_heart_failure": has_heart_failure,
            "has_copd": has_copd,
        }
    )


def _weekday_dates() -> pd.DatetimeIndex:
    """Weekdays in the study window, used as the appointment calendar."""
    days = pd.date_range(START, END, freq="B")
    return days


def build_appointments(
    rand: np.random.Generator,
    patients: pd.DataFrame,
    providers: pd.DataFrame,
) -> pd.DataFrame:
    pc_providers = providers[providers.daily_slot_capacity > 0].reset_index(drop=True)
    days = _weekday_dates()
    # About 2,050 booked visits per month × 24 months ≈ 49k.
    # Draw a count per provider-day around that provider's capacity fill.
    rows_clinic = []
    rows_prov = []
    rows_date = []

    # C05 is busier on the books but will have more no-shows.
    fill = {"C01": 0.82, "C02": 0.80, "C03": 0.74, "C04": 0.81, "C05": 0.78, "C06": 0.72}

    for _, p in pc_providers.iterrows():
        cap = int(p.daily_slot_capacity)
        f = fill[p.clinic_id]
        # Poisson around fill * capacity, clipped to 0..cap+2 (overbooks slightly).
        lam = cap * f
        counts = rand.poisson(lam, size=len(days))
        counts = np.clip(counts, 0, cap + 2)
        # Light summer dip, January/December dip in completed demand already via no-show;
        # volume slightly lower around late Dec / early Jan and July.
        month = days.month
        counts = np.where(np.isin(month, [7, 8, 12]), np.maximum(counts - 1, 0), counts)
        for d, k in zip(days, counts):
            if k == 0:
                continue
            rows_clinic.extend([p.clinic_id] * int(k))
            rows_prov.extend([p.provider_id] * int(k))
            rows_date.extend([d] * int(k))

    n = len(rows_date)
    visit_date = pd.to_datetime(rows_date)
    clinic_id = np.array(rows_clinic, dtype=object)
    provider_id = np.array(rows_prov, dtype=object)

    # Patients usually visit their home clinic.
    by_home = {c: patients.loc[patients.home_clinic_id == c, "patient_id"].to_numpy() for c in CLINICS.clinic_id}
    all_ids = patients.patient_id.to_numpy()
    patient_id = np.empty(n, dtype=object)
    for c in np.unique(clinic_id):
        m = clinic_id == c
        k = int(m.sum())
        home = by_home[c]
        use_home = rand.random(k) < 0.88
        chosen = np.empty(k, dtype=object)
        chosen[use_home] = rand.choice(home, int(use_home.sum()))
        chosen[~use_home] = rand.choice(all_ids, int((~use_home).sum()))
        patient_id[m] = chosen

    pat = patients.set_index("patient_id")
    payer_id = pat.loc[patient_id, "payer_id"].to_numpy()
    rural_flag = pat.loc[patient_id, "rural_flag"].to_numpy()
    age_band = pat.loc[patient_id, "age_band"].to_numpy()

    visit_type = rand.choice(VISIT_TYPES, n, p=VISIT_TYPE_P)

    # Virtual share rises from ~25% in 2024 to ~31% in 2025.
    # Rural and 75+ more often audio; acute more often in person; new patients more in person.
    year_frac = (visit_date - START).days / 730.0
    p_virtual = 0.24 + 0.08 * year_frac
    p_virtual = np.where(visit_type == "acute", p_virtual - 0.10, p_virtual)
    p_virtual = np.where(visit_type == "new_patient", p_virtual - 0.08, p_virtual)
    p_virtual = np.where(visit_type == "chronic_followup", p_virtual + 0.06, p_virtual)
    p_virtual = np.clip(p_virtual, 0.08, 0.50)
    is_virtual = rand.random(n) < p_virtual
    # Among virtual, audio share is higher for rural and 75+.
    p_audio = np.where(rural_flag == 1, 0.42, 0.22)
    p_audio = np.where(age_band == "75+", p_audio + 0.18, p_audio)
    p_audio = np.clip(p_audio, 0.10, 0.70)
    is_audio = is_virtual & (rand.random(n) < p_audio)
    modality = np.where(~is_virtual, "in_person", np.where(is_audio, "audio", "video"))

    # Lead time: virtual much shorter; acute short; C05 longer in person.
    lead_base = np.select(
        [visit_type == "acute", modality != "in_person", visit_type == "new_patient"],
        [
            rand.integers(0, 5, n),
            rand.integers(1, 9, n),
            rand.integers(7, 28, n),
        ],
        default=rand.integers(5, 22, n),
    )
    lead_base = lead_base + np.where(clinic_id == "C05", rand.integers(3, 12, n), 0)
    lead_base = lead_base + np.where(
        (clinic_id == "C05") & (modality == "in_person"), rand.integers(2, 10, n), 0
    )
    lead_days = np.clip(lead_base, 0, 60).astype(int)
    booked_date = visit_date - pd.to_timedelta(lead_days, unit="D")

    # Cancellation then no-show, else completed.
    p_cancel = np.full(n, 0.085)
    p_cancel = np.where(visit_type == "preventive", p_cancel + 0.02, p_cancel)
    p_cancel = np.where(lead_days > 21, p_cancel + 0.03, p_cancel)

    p_ns = np.select(
        [modality == "in_person", modality == "video"],
        [0.155, 0.086],
        default=0.072,
    )
    p_ns = p_ns + np.select(
        [
            visit_type == "acute",
            visit_type == "preventive",
            visit_type == "new_patient",
        ],
        [-0.035, 0.028, 0.040],
        default=0.0,
    )
    p_ns = p_ns + np.clip((lead_days - 7) * 0.0035, 0, 0.12)
    p_ns = p_ns + np.select(
        [payer_id == "MCAID", payer_id == "MEDCR", payer_id == "BRCH", payer_id == "SELF"],
        [0.035, -0.015, 0.010, 0.020],
        default=0.0,
    )
    p_ns = p_ns + np.where(clinic_id == "C05", 0.055, 0.0)
    # Seasonal: slightly higher in Dec/Jan, lower in Jun-Aug.
    month = visit_date.month.to_numpy()
    p_ns = p_ns + np.where(np.isin(month, [12, 1]), 0.015, 0.0)
    p_ns = p_ns + np.where(np.isin(month, [6, 7, 8]), -0.010, 0.0)
    # Gentle improvement over the window (~1.5 pp).
    p_ns = p_ns - 0.015 * year_frac
    p_ns = np.clip(p_ns, 0.02, 0.45)

    u = rand.random(n)
    status = np.where(u < p_cancel, "cancelled", np.where(u < p_cancel + p_ns, "no_show", "completed"))

    appt_id = [f"A{i:06d}" for i in range(1, n + 1)]
    return pd.DataFrame(
        {
            "appointment_id": appt_id,
            "patient_id": patient_id,
            "provider_id": provider_id,
            "clinic_id": clinic_id,
            "booked_date": booked_date.strftime("%Y-%m-%d"),
            "visit_date": visit_date.strftime("%Y-%m-%d"),
            "visit_type": visit_type,
            "modality": modality,
            "status": status,
            "lead_days": lead_days,
        }
    )



def build_claims_full(
    rand: np.random.Generator,
    appointments: pd.DataFrame,
    patients: pd.DataFrame,
    stays: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    completed = appointments[appointments.status == "completed"].merge(
        patients[["patient_id", "payer_id"]], on="patient_id", how="left"
    )
    base = completed.visit_type.map(
        {
            "acute": 165.0,
            "chronic_followup": 145.0,
            "preventive": 190.0,
            "new_patient": 230.0,
        }
    ).to_numpy()
    mod_fac = completed.modality.map({"in_person": 1.0, "video": 0.95, "audio": 0.62}).to_numpy()
    billed = np.round(base * mod_fac * rand.uniform(0.90, 1.10, len(completed)), 2)
    payer = completed.payer_id.to_numpy()
    # Denial probability.
    p_den = np.select(
        [payer == "BRCH", payer == "MCAID", payer == "SUMP", payer == "SELF", payer == "MEDCR"],
        [0.139, 0.090, 0.062, 0.110, 0.053],
        default=0.07,
    )
    p_den = p_den + np.where(completed.modality.to_numpy() == "audio", 0.06, 0.0)
    p_den = np.clip(p_den, 0.02, 0.30)
    # A slice of claims are still pending (more recent, and a stubborn old tail).
    visit_dt = pd.to_datetime(completed.visit_date)
    recency_days = (END - visit_dt).dt.days.to_numpy()
    p_pending = np.clip(0.03 + np.where(recency_days < 45, 0.18, 0.0), 0.02, 0.30)
    # Small stuck-AR tail on older commercial/Medicaid claims.
    p_pending = p_pending + np.where((recency_days > 120) & np.isin(payer, ["BRCH", "MCAID", "SELF"]), 0.04, 0.0)

    u = rand.random(len(completed))
    status = np.where(u < p_pending, "pending", np.where(u < p_pending + p_den, "denied", "paid"))

    denial_reasons = np.array(
        [
            "authorization",
            "coding",
            "eligibility",
            "timely_filing",
            "medical_necessity",
            "duplicate",
        ]
    )
    denial_p = [0.28, 0.24, 0.18, 0.08, 0.14, 0.08]
    reason = np.where(status == "denied", rand.choice(denial_reasons, len(completed), p=denial_p), None)

    paid = np.where(status == "paid", np.round(billed * rand.uniform(0.62, 0.88, len(completed)), 2), 0.0)
    # Days to payment for paid claims; AR days for pending (age from service to study end).
    days_to_payment = np.where(
        status == "paid",
        np.clip(rand.lognormal(3.0, 0.7, len(completed)).astype(int), 8, 180),
        None,
    )
    ar_days = np.where(status == "pending", recency_days, np.where(status == "denied", recency_days, 0))

    prof = pd.DataFrame(
        {
            "claim_id": [f"CL{i:06d}" for i in range(1, len(completed) + 1)],
            "appointment_id": completed.appointment_id.to_numpy(),
            "stay_id": None,
            "patient_id": completed.patient_id.to_numpy(),
            "clinic_id": completed.clinic_id.to_numpy(),
            "service_date": completed.visit_date.to_numpy(),
            "payer_id": payer,
            "billed_amount": billed,
            "paid_amount": paid,
            "claim_status": status,
            "denial_reason": reason,
            "days_to_payment": days_to_payment,
            "ar_days": ar_days,
            "claim_type": "professional",
        }
    )
    rows.append(prof)
    next_id = len(prof) + 1

    # Hospital claims for inpatient stays.
    st = stays.merge(patients[["patient_id", "payer_id"]], on="patient_id", how="left")
    billed_ip = np.round(
        st.los_days.to_numpy() * rand.uniform(1800, 3200, len(st))
        + st.principal_condition.map(
            {
                "heart_failure": 2200,
                "pneumonia": 1800,
                "copd": 1700,
                "sepsis": 4500,
                "joint_replacement": 8000,
                "other_medical": 1400,
                "other_surgical": 3500,
            }
        ).to_numpy(),
        2,
    )
    payer = st.payer_id.to_numpy()
    p_den = np.select(
        [payer == "BRCH", payer == "MCAID", payer == "SUMP", payer == "SELF", payer == "MEDCR"],
        [0.11, 0.08, 0.05, 0.10, 0.04],
        default=0.06,
    )
    disch = pd.to_datetime(st.discharge_date)
    recency_days = (END - disch).dt.days.to_numpy()
    p_pending = np.clip(0.04 + np.where(recency_days < 45, 0.20, 0.0), 0.02, 0.30)
    p_pending = p_pending + np.where((recency_days > 120) & np.isin(payer, ["BRCH", "MCAID"]), 0.05, 0.0)
    u = rand.random(len(st))
    status = np.where(u < p_pending, "pending", np.where(u < p_pending + p_den, "denied", "paid"))
    reason = np.where(status == "denied", rand.choice(denial_reasons, len(st), p=denial_p), None)
    paid = np.where(status == "paid", np.round(billed_ip * rand.uniform(0.55, 0.85, len(st)), 2), 0.0)
    days_to_payment = np.where(
        status == "paid",
        np.clip(rand.lognormal(3.2, 0.7, len(st)).astype(int), 10, 200),
        None,
    )
    ar_days = np.where(status == "pending", recency_days, np.where(status == "denied", recency_days, 0))
    hosp = pd.DataFrame(
        {
            "claim_id": [f"CL{i:06d}" for i in range(next_id, next_id + len(st))],
            "appointment_id": None,
            "stay_id": st.stay_id.to_numpy(),
            "patient_id": st.patient_id.to_numpy(),
            "clinic_id": st.facility_id.to_numpy(),
            "service_date": st.discharge_date.to_numpy(),
            "payer_id": payer,
            "billed_amount": billed_ip,
            "paid_amount": paid,
            "claim_status": status,
            "denial_reason": reason,
            "days_to_payment": days_to_payment,
            "ar_days": ar_days,
            "claim_type": "hospital",
        }
    )
    return pd.concat([prof, hosp], ignore_index=True)


def build_inpatient(rand: np.random.Generator, patients: pd.DataFrame, providers: pd.DataFrame) -> pd.DataFrame:
    hospitalists = providers[providers.specialty == "Hospital Medicine"].provider_id.to_numpy()
    # ~4,200 index stays over 24 months, plus readmissions.
    n_index = 2500
    # Prefer older / HF / COPD patients for medical admissions.
    weights = (
        1.0
        + patients.has_heart_failure * 3.0
        + patients.has_copd * 2.0
        + patients.has_diabetes * 0.6
        + patients.age_band.isin(["65-74", "75+"]) * 1.4
    ).to_numpy()
    weights = weights / weights.sum()
    idx_patients = rand.choice(patients.patient_id.to_numpy(), n_index, replace=True, p=weights)
    admit = START + pd.to_timedelta(rand.integers(0, (END - START).days - 12, n_index), unit="D")
    condition = rand.choice(INPATIENT_CONDITIONS, n_index, p=INPATIENT_P)
    # Align condition with flags when present.
    pat = patients.set_index("patient_id")
    has_hf = pat.loc[idx_patients, "has_heart_failure"].to_numpy()
    has_copd = pat.loc[idx_patients, "has_copd"].to_numpy()
    condition = np.where((has_hf == 1) & (rand.random(n_index) < 0.45), "heart_failure", condition)
    condition = np.where((has_copd == 1) & (condition != "heart_failure") & (rand.random(n_index) < 0.35), "copd", condition)

    los_mu = np.select(
        [
            condition == "heart_failure",
            condition == "pneumonia",
            condition == "copd",
            condition == "sepsis",
            condition == "joint_replacement",
            condition == "other_surgical",
        ],
        [4.5, 4.0, 3.8, 6.0, 3.2, 4.0],
        default=3.4,
    )
    los = np.clip(rand.normal(los_mu, 1.4, n_index).round().astype(int), 1, 21)
    discharge = admit + pd.to_timedelta(los, unit="D")
    # Drop stays that would discharge after the window end + a few days; clip instead.
    overflow = discharge > END
    discharge = pd.Series(discharge).where(~overflow, END).to_numpy()
    los = (pd.to_datetime(discharge) - pd.to_datetime(admit)).days
    los = np.clip(los, 1, None)

    disposition = rand.choice(
        ["home", "home_with_services", "snf", "transfer", "expired"],
        n_index,
        p=[0.62, 0.18, 0.12, 0.05, 0.03],
    )
    # Expired and transfers don't get 30-day readmits generated from this stay.
    can_readmit = ~np.isin(disposition, ["expired", "transfer"])

    rows = {
        "patient_id": list(idx_patients),
        "provider_id": list(rand.choice(hospitalists, n_index)),
        "facility_id": ["H01"] * n_index,
        "admission_date": list(pd.to_datetime(admit).strftime("%Y-%m-%d")),
        "discharge_date": list(pd.to_datetime(discharge).strftime("%Y-%m-%d")),
        "los_days": list(los),
        "principal_condition": list(condition),
        "discharge_disposition": list(disposition),
        "is_index_stay": [1] * n_index,
    }

    # Generate at most one 30-day return per index stay (keeps the definition clean).
    p = np.array([READMIT_P[c] for c in condition])
    will = can_readmit & (rand.random(n_index) < p)
    # Arrival 3-30 days after discharge, if still in window.
    gap = rand.integers(3, 31, n_index)
    readmit_admit = pd.to_datetime(discharge) + pd.to_timedelta(gap, unit="D")
    for i in np.where(will)[0]:
        a = readmit_admit[i]
        if a > END - pd.Timedelta(days=1):
            continue
        r_los = int(np.clip(int(rand.normal(4.0, 1.5)), 1, 18))
        r_disch = min(a + pd.Timedelta(days=r_los), END)
        r_los = max((r_disch - a).days, 1)
        r_disp = rand.choice(
            ["home", "home_with_services", "snf", "transfer", "expired"],
            p=[0.50, 0.22, 0.16, 0.07, 0.05],
        )
        # Same or related condition.
        r_cond = condition[i] if rand.random() < 0.7 else rand.choice(INPATIENT_CONDITIONS, p=INPATIENT_P)
        rows["patient_id"].append(idx_patients[i])
        rows["provider_id"].append(rand.choice(hospitalists))
        rows["facility_id"].append("H01")
        rows["admission_date"].append(a.strftime("%Y-%m-%d"))
        rows["discharge_date"].append(r_disch.strftime("%Y-%m-%d"))
        rows["los_days"].append(r_los)
        rows["principal_condition"].append(r_cond)
        rows["discharge_disposition"].append(r_disp)
        rows["is_index_stay"].append(0)

    n = len(rows["patient_id"])
    df = pd.DataFrame(rows)
    df.insert(0, "stay_id", [f"S{i:06d}" for i in range(1, n + 1)])
    return df


def build_ed(rand: np.random.Generator, patients: pd.DataFrame, providers: pd.DataFrame) -> pd.DataFrame:
    ed_docs = providers[providers.specialty == "Emergency Medicine"].provider_id.to_numpy()
    n = 8000
    # Prefer some repeat ED users but mostly unique-ish draws.
    weights = (
        1.0
        + patients.has_heart_failure * 1.5
        + patients.has_copd * 1.4
        + patients.age_band.isin(["0-17", "75+"]) * 0.5
    ).to_numpy()
    weights = weights / weights.sum()
    patient_id = rand.choice(patients.patient_id.to_numpy(), n, replace=True, p=weights)

    # Arrival pattern: weekdays slightly higher, hour peaks at 10 and 18.
    # Sample day uniformly then hour from a weighted distribution.
    day_offsets = rand.integers(0, (END - START).days + 1, n)
    arrive_day = START + pd.to_timedelta(day_offsets, unit="D")
    hours = np.arange(24)
    # Relative volume by hour.
    hour_w = np.array(
        [3, 2, 2, 2, 2, 3, 5, 7, 9, 11, 12, 11, 10, 10, 9, 9, 10, 12, 13, 11, 8, 6, 5, 4],
        dtype=float,
    )
    hour_w /= hour_w.sum()
    hour = rand.choice(hours, n, p=hour_w)
    # Monday bump already implicit if we don't bias weekday; add a Monday increase via rejection-free shift.
    weekday = arrive_day.day_of_week.to_numpy()
    # Slightly resample a slice of weekend visits onto Monday to create a Monday peak.
    weekend = weekday >= 5
    move = weekend & (rand.random(n) < 0.18)
    arrive_day = pd.to_datetime(arrive_day)
    arrive_day = arrive_day + pd.to_timedelta(np.where(move, -arrive_day.day_of_week.to_numpy() + 0, 0), unit="D")
    minute = rand.integers(0, 60, n)
    arrival = arrive_day + pd.to_timedelta(hour, unit="h") + pd.to_timedelta(minute, unit="m")
    # Clip to window.
    arrival = pd.Series(arrival).clip(lower=START, upper=END + pd.Timedelta(hours=23))

    acuity = rand.choice([1, 2, 3, 4, 5], n, p=[0.04, 0.14, 0.38, 0.30, 0.14])
    complaint = rand.choice(ED_COMPLAINTS, n, p=ED_COMPLAINT_P)

    # Waits rise with volume hour and for lower acuity.
    hour_load = hour_w[hour] / hour_w.min()
    door_to_triage = np.clip(rand.normal(8 + hour_load * 2, 3, n), 1, 45).round().astype(int)
    door_to_provider = np.clip(
        rand.normal(15 + (acuity - 1) * 12 + hour_load * 8, 10, n),
        door_to_triage + 2,
        240,
    ).round().astype(int)
    los = np.clip(
        door_to_provider + rand.normal(80 + (6 - acuity) * 15, 25, n),
        door_to_provider + 10,
        600,
    ).round().astype(int)

    # LWBS rises sharply when door-to-provider is long and acuity is 4-5.
    p_lwbs = np.clip(0.01 + np.maximum(door_to_provider - 45, 0) * 0.002 + np.where(acuity >= 4, 0.03, 0.0), 0, 0.25)
    is_lwbs = rand.random(n) < p_lwbs
    # Disposition for the rest.
    p_admit = np.select([acuity == 1, acuity == 2, acuity == 3, acuity == 4], [0.70, 0.45, 0.18, 0.06], default=0.02)
    u = rand.random(n)
    disposition = np.where(
        is_lwbs,
        "lwbs",
        np.where(u < p_admit, "admit", np.where(u < p_admit + 0.03, "transfer", "discharge")),
    )
    # If LWBS, provider time may be missing; los is time until left.
    door_to_provider_out = np.where(is_lwbs, np.minimum(door_to_provider, rand.integers(20, 90, n)), door_to_provider)
    los_out = np.where(is_lwbs, door_to_provider_out + rand.integers(5, 25, n), los)

    triage_ts = arrival + pd.to_timedelta(door_to_triage, unit="m")
    provider_ts = np.where(
        is_lwbs & (rand.random(n) < 0.7),
        pd.NaT,
        (arrival + pd.to_timedelta(door_to_provider_out, unit="m")).to_numpy(),
    )
    depart_ts = arrival + pd.to_timedelta(los_out, unit="m")

    def fmt(s):
        return pd.to_datetime(s).dt.strftime("%Y-%m-%d %H:%M:%S")

    # provider_ts may contain NaT
    prov_series = pd.to_datetime(pd.Series(provider_ts))
    prov_fmt = prov_series.dt.strftime("%Y-%m-%d %H:%M:%S")
    prov_fmt = prov_fmt.where(prov_series.notna(), other=None)

    return pd.DataFrame(
        {
            "ed_visit_id": [f"E{i:06d}" for i in range(1, n + 1)],
            "patient_id": patient_id,
            "facility_id": "H01",
            "provider_id": rand.choice(ed_docs, n),
            "arrival_ts": fmt(pd.to_datetime(arrival)),
            "triage_ts": fmt(pd.to_datetime(triage_ts)),
            "provider_ts": prov_fmt.to_numpy(),
            "depart_ts": fmt(pd.to_datetime(depart_ts)),
            "acuity": acuity,
            "chief_complaint_group": complaint,
            "disposition": disposition,
            "door_to_triage_minutes": door_to_triage,
            "door_to_provider_minutes": np.where(pd.isna(prov_series), None, door_to_provider_out),
            "los_minutes": los_out,
        }
    )


def build_meds(
    rand: np.random.Generator,
    stays: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # 4-7 orders per stay.
    n_stays = len(stays)
    k = rand.integers(4, 8, n_stays)
    stay_id = np.repeat(stays.stay_id.to_numpy(), k)
    patient_id = np.repeat(stays.patient_id.to_numpy(), k)
    facility_id = np.repeat(stays.facility_id.to_numpy(), k)
    admit = np.repeat(pd.to_datetime(stays.admission_date).to_numpy(), k)
    los = np.repeat(stays.los_days.to_numpy(), k)
    condition = np.repeat(stays.principal_condition.to_numpy(), k)
    n = len(stay_id)

    # Weight drugs by condition a little.
    drug_ids = DRUGS.drug_id.to_numpy()
    base_p = np.full(len(DRUGS), 1.0)
    # Will draw per row with slight condition bias using choice then swap.
    drug_id = rand.choice(drug_ids, n)
    # HF stays more often get furosemide, lisinopril, metoprolol.
    hf = condition == "heart_failure"
    drug_id[hf] = rand.choice(["D08", "D02", "D09", "D21", "D14", "D01", "D20", "D03"], int(hf.sum()))
    copd = condition == "copd"
    drug_id[copd] = rand.choice(["D07", "D29", "D30", "D20", "D09", "D08", "D18"], int(copd.sum()))
    # Randomly mix in other drugs so it's not deterministic.
    mix = rand.random(n) < 0.45
    drug_id[mix] = rand.choice(drug_ids, int(mix.sum()))

    drug = DRUGS.set_index("drug_id")
    drug_name = drug.loc[drug_id, "drug_name"].to_numpy()
    drug_class = drug.loc[drug_id, "drug_class"].to_numpy()
    is_high_alert = drug.loc[drug_id, "is_high_alert"].to_numpy()
    is_brand = drug.loc[drug_id, "is_brand"].to_numpy()
    unit_cost = drug.loc[drug_id, "unit_cost"].to_numpy() * rand.uniform(0.95, 1.05, n)
    quantity = rand.integers(1, 9, n)
    route = np.where(np.isin(drug_class, ["opioid", "anticoagulant", "antibiotic"]) & (rand.random(n) < 0.45), "IV", "PO")
    # Order time: during the stay.
    offset_h = rand.uniform(1, np.maximum(los * 24 - 2, 2), n)
    ordered_at = pd.to_datetime(admit) + pd.to_timedelta(offset_h, unit="h")
    status = rand.choice(["completed", "completed", "completed", "discontinued", "cancelled"], n)
    # A few high-alert orders cancelled (stand-in for an alert-driven stop, not an Epic alert table).
    cancel_ha = (is_high_alert == 1) & (rand.random(n) < 0.08)
    status = np.where(cancel_ha, "cancelled", status)

    orders = pd.DataFrame(
        {
            "med_order_id": [f"M{i:06d}" for i in range(1, n + 1)],
            "stay_id": stay_id,
            "patient_id": patient_id,
            "facility_id": facility_id,
            "drug_id": drug_id,
            "drug_name": drug_name,
            "drug_class": drug_class,
            "is_high_alert": is_high_alert,
            "is_brand": is_brand,
            "route": route,
            "quantity": quantity,
            "unit_cost": np.round(unit_cost, 2),
            "estimated_cost": np.round(unit_cost * quantity, 2),
            "ordered_at": pd.to_datetime(ordered_at).strftime("%Y-%m-%d %H:%M:%S"),
            "order_status": status,
        }
    )

    # Administrations for completed / discontinued orders (scheduled doses during remaining LOS).
    active = orders[orders.order_status != "cancelled"].copy()
    # 1-4 doses per order, more if LOS longer and not a one-time med.
    remain_h = []
    # Vectorized dose counts
    stay_los_map = dict(zip(stays.stay_id, stays.los_days))
    stay_adm_map = dict(zip(stays.stay_id, stays.admission_date))
    los_a = active.stay_id.map(stay_los_map).to_numpy()
    n_doses = np.clip(rand.choice([1, 2, 3], len(active), p=[0.45, 0.40, 0.15]), 1, 3)

    admin_order = np.repeat(active.med_order_id.to_numpy(), n_doses)
    admin_stay = np.repeat(active.stay_id.to_numpy(), n_doses)
    admin_patient = np.repeat(active.patient_id.to_numpy(), n_doses)
    na = len(admin_order)
    # Schedule doses every 8-12 hours after order time, clipped to discharge.
    order_ts = pd.to_datetime(np.repeat(active.ordered_at.to_numpy(), n_doses))
    # dose index within order
    dose_idx = np.concatenate([np.arange(int(x)) for x in n_doses])
    interval_h = 8
    scheduled = order_ts + pd.to_timedelta(dose_idx * interval_h, unit="h")
    # Night shift (23-07) has more missed / late doses.
    hour = scheduled.hour
    is_night = (hour >= 23) | (hour < 7)
    p_miss = np.where(is_night, 0.09, 0.035)
    p_late = np.where(is_night, 0.16, 0.07)
    p_refused = 0.02
    u = rand.random(na)
    admin_status = np.where(
        u < p_miss,
        "missed",
        np.where(u < p_miss + p_refused, "refused", np.where(u < p_miss + p_refused + p_late, "late", "given")),
    )
    late_min = np.where(admin_status == "late", rand.integers(61, 180, na), np.where(admin_status == "given", rand.integers(0, 40, na), None))
    given_at = []
    sched_list = scheduled
    for i in range(na):
        if admin_status[i] in ("given", "late"):
            given_at.append((sched_list[i] + pd.to_timedelta(int(late_min[i]), unit="m")).strftime("%Y-%m-%d %H:%M:%S"))
        else:
            given_at.append(None)

    admins = pd.DataFrame(
        {
            "admin_id": [f"AD{i:07d}" for i in range(1, na + 1)],
            "med_order_id": admin_order,
            "stay_id": admin_stay,
            "patient_id": admin_patient,
            "scheduled_at": pd.to_datetime(scheduled).strftime("%Y-%m-%d %H:%M:%S"),
            "administered_at": given_at,
            "admin_status": admin_status,
            "minutes_from_schedule": late_min,
        }
    )
    return orders, admins


def build_quality(rand: np.random.Generator, patients: pd.DataFrame) -> pd.DataFrame:
    """Simple quality-measure events for later CMS-style days (not official specs)."""
    rows = []
    i = 1
    # Flu vax: all patients, two seasons (2024-25, 2025-26 start).
    # Higher rates in 65+, lower in 18-34.
    for season, start, end in [
        ("2024-25", "2024-09-01", "2025-03-31"),
        ("2025-26", "2025-09-01", "2025-12-31"),
    ]:
        p = patients.age_band.map(
            {"0-17": 0.48, "18-34": 0.28, "35-49": 0.36, "50-64": 0.48, "65-74": 0.68, "75+": 0.72}
        ).to_numpy()
        got = rand.random(len(patients)) < p
        # For 2025-26 season the window is shorter so slightly lower observed rate already in p? keep p.
        result_date = pd.to_datetime(start) + pd.to_timedelta(
            rand.integers(0, max((pd.Timestamp(end) - pd.Timestamp(start)).days, 1), len(patients)),
            unit="D",
        )
        for pid, flag, dt, band in zip(patients.patient_id, got, result_date, patients.age_band):
            rows.append(
                {
                    "quality_event_id": f"Q{i:06d}",
                    "patient_id": pid,
                    "measure_id": "influenza_immunization",
                    "measure_period": season,
                    "as_of_date": dt.strftime("%Y-%m-%d") if flag else end,
                    "is_denominator": 1,
                    "is_numerator": int(flag),
                    "result_value": None,
                }
            )
            i += 1

    # A1C monitoring among diabetes patients: at least one result in each calendar year.
    dm = patients[patients.has_diabetes == 1]
    for year, start, end in [("2024", "2024-01-01", "2024-12-31"), ("2025", "2025-01-01", "2025-12-31")]:
        p = 0.78
        got = rand.random(len(dm)) < p
        values = np.round(rand.normal(7.4, 1.1, len(dm)), 1)
        values = np.clip(values, 5.0, 14.0)
        dts = pd.to_datetime(start) + pd.to_timedelta(rand.integers(0, 360, len(dm)), unit="D")
        dts = pd.Series(dts).clip(upper=pd.Timestamp(end))
        for pid, flag, dt, val in zip(dm.patient_id, got, dts, values):
            rows.append(
                {
                    "quality_event_id": f"Q{i:06d}",
                    "patient_id": pid,
                    "measure_id": "diabetes_a1c_tested",
                    "measure_period": year,
                    "as_of_date": dt.strftime("%Y-%m-%d"),
                    "is_denominator": 1,
                    "is_numerator": int(flag),
                    "result_value": float(val) if flag else None,
                }
            )
            i += 1

    # Colorectal screening: age 50-75 stand-in (50-64 and 65-74 bands).
    crc = patients[patients.age_band.isin(["50-64", "65-74"])]
    got = rand.random(len(crc)) < 0.62
    dts = START + pd.to_timedelta(rand.integers(0, 700, len(crc)), unit="D")
    dts = pd.Series(dts).clip(upper=END)
    for pid, flag, dt in zip(crc.patient_id, got, dts):
        rows.append(
            {
                "quality_event_id": f"Q{i:06d}",
                "patient_id": pid,
                "measure_id": "colorectal_screening",
                "measure_period": "2024-2025",
                "as_of_date": dt.strftime("%Y-%m-%d"),
                "is_denominator": 1,
                "is_numerator": int(flag),
                "result_value": None,
            }
        )
        i += 1

    return pd.DataFrame(rows)


def build_dirty_extract(rand: np.random.Generator, appointments: pd.DataFrame) -> pd.DataFrame:
    """A messy appointment extract sample for later data-quality days. Known defect rates."""
    raw = appointments.sample(n=8000, random_state=SEED).copy().reset_index(drop=True)
    n = len(raw)

    # ~1.5% exact duplicate rows (same appointment_id), enough to find in a sample.
    n_dup = 120
    dups = raw.sample(n_dup, random_state=SEED).copy()
    raw = pd.concat([raw, dups], ignore_index=True)

    # 0.2% null clinic_id.
    idx = rand.choice(raw.index.to_numpy(), 80, replace=False)
    raw.loc[idx, "clinic_id"] = None

    # 0.2% visit_date before booked_date (swap).
    idx = rand.choice(raw.index.to_numpy(), 80, replace=False)
    b, v = raw.loc[idx, "booked_date"].copy(), raw.loc[idx, "visit_date"].copy()
    raw.loc[idx, "booked_date"] = v.to_numpy()
    raw.loc[idx, "visit_date"] = b.to_numpy()

    # 0.15% inconsistent status casing / aliases.
    idx = rand.choice(raw.index.to_numpy(), 60, replace=False)
    raw.loc[idx, "status"] = raw.loc[idx, "status"].map(
        {"completed": "Completed", "no_show": "NoShow", "cancelled": "CANCELED"}
    ).fillna(raw.loc[idx, "status"])

    # 0.1% visit_date slightly after the study window.
    idx = rand.choice(raw.index.to_numpy(), 40, replace=False)
    raw.loc[idx, "visit_date"] = "2026-03-15"

    # 0.15% modality typo / mixed labels.
    idx = rand.choice(raw.index.to_numpy(), 60, replace=False)
    raw.loc[idx, "modality"] = raw.loc[idx, "modality"].map(
        {"in_person": "In Person", "video": "VIDEO", "audio": "audio-only"}
    ).fillna(raw.loc[idx, "modality"])

    raw.insert(0, "extract_row_id", np.arange(1, len(raw) + 1))
    return raw


def build_provider_sessions(providers: pd.DataFrame) -> pd.DataFrame:
    """Weekday session capacity for productivity days. Hospitals have no clinic sessions."""
    pc = providers[providers.daily_slot_capacity > 0]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    rows = []
    for _, p in pc.iterrows():
        for wd in weekdays:
            # Slightly lighter Fridays.
            slots = int(p.daily_slot_capacity) - (1 if wd == "Friday" else 0)
            rows.append((p.provider_id, p.clinic_id, wd, max(slots, 6)))
    return pd.DataFrame(rows, columns=["provider_id", "clinic_id", "weekday", "slot_capacity"])


def _write_dictionary(counts: dict[str, int], path: Path) -> None:
    lines = [
        f"# Data dictionary — {SYSTEM_NAME} (synthetic)",
        "",
        "All tables and columns are generic names invented for this series. "
        "They are **not** Epic Clarity, Caboodle, or Willow schema, and this "
        "project is not affiliated with or endorsed by Epic Systems Corporation.",
        "",
        "Every row is generated from a fixed seed (`SEED=42`) and describes no "
        "real patient, provider, or organization. Identifiers are zero-padded "
        "codes (`P000001`, `A000001`). There are no names, dates of birth, "
        "addresses, phone numbers, or other direct identifiers.",
        "",
        f"Study window: **{START.date()}** to **{END.date()}**.",
        "",
        "## Tables and row counts",
        "",
        "| Table | Rows | Grain |",
        "|---|---:|---|",
        f"| dim_clinic | {counts['dim_clinic']:,} | one row per clinic or hospital |",
        f"| dim_payer | {counts['dim_payer']:,} | one row per payer |",
        f"| dim_drug | {counts['dim_drug']:,} | one row per medication product |",
        f"| dim_provider | {counts['dim_provider']:,} | one row per provider |",
        f"| dim_patient | {counts['dim_patient']:,} | one row per patient |",
        f"| dim_date | {counts['dim_date']:,} | one row per calendar day |",
        f"| fact_appointment | {counts['fact_appointment']:,} | one scheduled outpatient visit |",
        f"| fact_claim | {counts['fact_claim']:,} | one claim (professional or hospital) |",
        f"| fact_inpatient_stay | {counts['fact_inpatient_stay']:,} | one hospital stay |",
        f"| fact_ed_visit | {counts['fact_ed_visit']:,} | one emergency visit |",
        f"| fact_medication_order | {counts['fact_medication_order']:,} | one inpatient medication order |",
        f"| fact_medication_admin | {counts['fact_medication_admin']:,} | one scheduled administration |",
        f"| fact_quality_event | {counts['fact_quality_event']:,} | one measure evaluation for a patient and period |",
        f"| fact_provider_session | {counts['fact_provider_session']:,} | one provider × weekday capacity row |",
        f"| raw_appointment_extract | {counts['raw_appointment_extract']:,} | messy extract (duplicates and defects included) |",
        "",
        "## Column notes",
        "",
        "- `fact_appointment.status`: `completed`, `no_show`, or `cancelled`.",
        "- `fact_appointment.modality`: `in_person`, `video`, or `audio`.",
        "- `fact_appointment.visit_type`: `chronic_followup`, `acute`, `preventive`, or `new_patient`.",
        "- No-show rate used in this series: no-shows ÷ (completed + no-shows). Cancellations are excluded.",
        "- `fact_claim.claim_status`: `paid`, `denied`, or `pending`. `ar_days` is aged from service date to 2025-12-31 for unpaid claims.",
        "- 30-day readmissions are **not** pre-flagged; compute them in SQL from `fact_inpatient_stay` dates.",
        "- `fact_ed_visit.disposition`: `discharge`, `admit`, `transfer`, or `lwbs` (left without being seen).",
        "- `fact_medication_admin.admin_status`: `given`, `late` (>60 minutes), `missed`, or `refused`.",
        "- `raw_appointment_extract` is an 8,000-row sample plus injected defects (the only dirty table). Known issue types: duplicate appointment IDs, null clinic IDs, reversed dates, mixed-case status and modality labels, and a few out-of-window dates.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def generate(db_path: Path = DB_PATH) -> dict[str, int]:
    rand = rng()
    dim_date = build_dates()
    dim_provider = build_providers(rand)
    dim_patient = build_patients(rand)
    fact_appointment = build_appointments(rand, dim_patient, dim_provider)
    fact_inpatient_stay = build_inpatient(rand, dim_patient, dim_provider)
    fact_ed_visit = build_ed(rand, dim_patient, dim_provider)
    fact_claim = build_claims_full(rand, fact_appointment, dim_patient, fact_inpatient_stay)
    fact_medication_order, fact_medication_admin = build_meds(rand, fact_inpatient_stay)
    fact_quality_event = build_quality(rand, dim_patient)
    fact_provider_session = build_provider_sessions(dim_provider)
    raw_appointment_extract = build_dirty_extract(rand, fact_appointment)

    tables = {
        "dim_clinic": CLINICS,
        "dim_payer": PAYERS,
        "dim_drug": DRUGS,
        "dim_provider": dim_provider,
        "dim_patient": dim_patient,
        "dim_date": dim_date,
        "fact_appointment": fact_appointment,
        "fact_claim": fact_claim,
        "fact_inpatient_stay": fact_inpatient_stay,
        "fact_ed_visit": fact_ed_visit,
        "fact_medication_order": fact_medication_order,
        "fact_medication_admin": fact_medication_admin,
        "fact_quality_event": fact_quality_event,
        "fact_provider_session": fact_provider_session,
        "raw_appointment_extract": raw_appointment_extract,
    }

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        for name, df in tables.items():
            df.to_sql(name, conn, index=False, if_exists="replace")
        conn.execute("CREATE INDEX ix_appt_visit_date ON fact_appointment(visit_date)")
        conn.execute("CREATE INDEX ix_appt_clinic ON fact_appointment(clinic_id)")
        conn.execute("CREATE INDEX ix_claim_status ON fact_claim(claim_status)")
        conn.execute("CREATE INDEX ix_stay_patient ON fact_inpatient_stay(patient_id)")
        conn.execute("CREATE INDEX ix_ed_arrival ON fact_ed_visit(arrival_ts)")
        conn.commit()
        conn.execute("VACUUM")
    finally:
        conn.close()

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    fact_appointment.head(500).to_csv(SAMPLE_DIR / "appointments_sample.csv", index=False)

    counts = {name: len(df) for name, df in tables.items()}
    _write_dictionary(counts, DICT_PATH)
    return counts


def main() -> int:
    counts = generate()
    print(f"Wrote {DB_PATH}")
    for name, n in counts.items():
        print(f"  {name:28s} {n:>8,}")
    size_mb = DB_PATH.stat().st_size / 1e6
    print(f"  file size                    {size_mb:8.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
