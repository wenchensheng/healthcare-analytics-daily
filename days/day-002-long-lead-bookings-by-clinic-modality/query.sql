-- Day 002: Share of visits booked more than 14 days out, by clinic and modality
-- Definition: long-lead share = scheduled visits with lead_days > 14 ÷ all scheduled visits.
--   lead_days = visit_date - booked_date. Every scheduled visit counts (completed,
--   no-show, and cancelled), because the booking window is set when the slot is booked.
-- Data: shared/clinic.db (synthetic), fact_appointment and dim_clinic, Jan 2024-Dec 2025.

/* name: overall */
SELECT
    COUNT(*) AS scheduled_visits,
    SUM(CASE WHEN lead_days > 14 THEN 1 ELSE 0 END) AS booked_over_14_days,
    ROUND(100.0 * SUM(CASE WHEN lead_days > 14 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_14_days,
    ROUND(AVG(lead_days), 1) AS avg_lead_days
FROM fact_appointment;

/* name: lead_days_check */
-- Data check: the stored lead_days should equal visit_date - booked_date on every row.
SELECT
    COUNT(*) AS scheduled_visits,
    SUM(CASE WHEN CAST(julianday(visit_date) - julianday(booked_date) AS INTEGER) <> lead_days
             THEN 1 ELSE 0 END) AS mismatched_rows,
    SUM(CASE WHEN booked_date > visit_date THEN 1 ELSE 0 END) AS booked_after_visit,
    MIN(lead_days) AS min_lead_days,
    MAX(lead_days) AS max_lead_days
FROM fact_appointment;

/* name: by_modality */
SELECT
    modality,
    COUNT(*) AS scheduled_visits,
    SUM(CASE WHEN lead_days > 14 THEN 1 ELSE 0 END) AS booked_over_14_days,
    ROUND(100.0 * SUM(CASE WHEN lead_days > 14 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_14_days,
    ROUND(AVG(lead_days), 1) AS avg_lead_days
FROM fact_appointment
GROUP BY 1
ORDER BY pct_over_14_days DESC;

/* name: lead_percentiles_by_modality */
-- Median and 90th-percentile lead time with ROW_NUMBER (nearest-rank method).
WITH ranked AS (
    SELECT
        modality,
        lead_days,
        ROW_NUMBER() OVER (PARTITION BY modality ORDER BY lead_days) AS rn,
        COUNT(*) OVER (PARTITION BY modality) AS n
    FROM fact_appointment
)
SELECT
    modality,
    MAX(n) AS scheduled_visits,
    MAX(CASE WHEN rn = CAST((n + 1) / 2 AS INTEGER) THEN lead_days END) AS median_lead_days,
    MAX(CASE WHEN rn = CAST(0.9 * n + 0.999999 AS INTEGER) THEN lead_days END) AS p90_lead_days
FROM ranked
GROUP BY 1
ORDER BY median_lead_days DESC;

/* name: by_clinic */
SELECT
    a.clinic_id,
    c.clinic_name,
    COUNT(*) AS scheduled_visits,
    SUM(CASE WHEN a.lead_days > 14 THEN 1 ELSE 0 END) AS booked_over_14_days,
    ROUND(100.0 * SUM(CASE WHEN a.lead_days > 14 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_14_days,
    ROUND(AVG(a.lead_days), 1) AS avg_lead_days
FROM fact_appointment AS a
JOIN dim_clinic AS c ON c.clinic_id = a.clinic_id
GROUP BY 1, 2
ORDER BY pct_over_14_days DESC;

/* name: clinic_by_modality */
SELECT
    a.clinic_id,
    c.clinic_name,
    a.modality,
    COUNT(*) AS scheduled_visits,
    SUM(CASE WHEN a.lead_days > 14 THEN 1 ELSE 0 END) AS booked_over_14_days,
    ROUND(100.0 * SUM(CASE WHEN a.lead_days > 14 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_14_days,
    ROUND(AVG(a.lead_days), 1) AS avg_lead_days
FROM fact_appointment AS a
JOIN dim_clinic AS c ON c.clinic_id = a.clinic_id
GROUP BY 1, 2, 3
ORDER BY 1, 3;

/* name: in_person_c05_vs_peers */
SELECT
    CASE WHEN clinic_id = 'C05' THEN 'C05 Brookfield' ELSE 'Peer clinics' END AS clinic_group,
    COUNT(*) AS scheduled_visits,
    SUM(CASE WHEN lead_days > 14 THEN 1 ELSE 0 END) AS booked_over_14_days,
    ROUND(100.0 * SUM(CASE WHEN lead_days > 14 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_14_days,
    ROUND(AVG(lead_days), 1) AS avg_lead_days
FROM fact_appointment
WHERE modality = 'in_person'
GROUP BY 1
ORDER BY 1;

/* name: in_person_c05_vs_peers_by_visit_type */
SELECT
    visit_type,
    CASE WHEN clinic_id = 'C05' THEN 'C05 Brookfield' ELSE 'Peer clinics' END AS clinic_group,
    COUNT(*) AS scheduled_visits,
    ROUND(100.0 * SUM(CASE WHEN lead_days > 14 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_14_days,
    ROUND(AVG(lead_days), 1) AS avg_lead_days
FROM fact_appointment
WHERE modality = 'in_person'
GROUP BY 1, 2
ORDER BY 1, 2;

/* name: lead_band_by_modality */
WITH banded AS (
    SELECT
        modality,
        CASE
            WHEN lead_days <= 3 THEN '1: 0-3 days'
            WHEN lead_days <= 7 THEN '2: 4-7 days'
            WHEN lead_days <= 14 THEN '3: 8-14 days'
            WHEN lead_days <= 28 THEN '4: 15-28 days'
            ELSE '5: 29+ days'
        END AS lead_band
    FROM fact_appointment
)
SELECT
    modality,
    lead_band,
    COUNT(*) AS scheduled_visits,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY modality), 1) AS pct_of_modality
FROM banded
GROUP BY 1, 2
ORDER BY 1, 2;

/* name: by_year_modality */
SELECT
    strftime('%Y', visit_date) AS year,
    modality,
    COUNT(*) AS scheduled_visits,
    ROUND(100.0 * SUM(CASE WHEN lead_days > 14 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_14_days
FROM fact_appointment
GROUP BY 1, 2
ORDER BY 1, 2;

/* name: in_person_no_show_by_booking_window */
-- Why it matters: no-show rate (no-shows ÷ completed + no-shows) for in-person visits
-- booked within 14 days versus further out. Day 003 breaks this into finer bands.
SELECT
    CASE WHEN lead_days > 14 THEN 'over_14_days' ELSE '14_days_or_less' END AS booking_window,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment
WHERE modality = 'in_person'
  AND status IN ('completed', 'no_show')
GROUP BY 1
ORDER BY 1;
