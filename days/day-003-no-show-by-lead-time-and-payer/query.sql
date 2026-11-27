-- Day 003: No-show rate by lead-time band and payer
-- Definition: no-show rate = no-shows ÷ (completed + no-shows). Cancellations are excluded.
--   lead_days = visit_date - booked_date, grouped into five bands (same bands as Day 002).
--   Payer = the patient's payer on dim_patient (one payer per patient), labelled from dim_payer.
-- Data: shared/clinic.db (synthetic), fact_appointment, dim_patient, dim_payer, Jan 2024-Dec 2025.

/* name: payer_join_check */
-- Data check: every appointment should reach exactly one payer through dim_patient.
SELECT
    COUNT(*) AS scheduled_visits,
    SUM(CASE WHEN p.patient_id IS NULL THEN 1 ELSE 0 END) AS no_patient_match,
    SUM(CASE WHEN y.payer_id IS NULL THEN 1 ELSE 0 END) AS no_payer_match,
    (SELECT COUNT(*) FROM (SELECT patient_id FROM dim_patient GROUP BY 1 HAVING COUNT(*) > 1)) AS duplicate_patients
FROM fact_appointment AS a
LEFT JOIN dim_patient AS p ON p.patient_id = a.patient_id
LEFT JOIN dim_payer AS y ON y.payer_id = p.payer_id;

/* name: overall */
SELECT
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment
WHERE status IN ('completed', 'no_show');

/* name: by_lead_band */
WITH eligible AS (
    SELECT
        status,
        CASE
            WHEN lead_days <= 3 THEN '1: 0-3 days'
            WHEN lead_days <= 7 THEN '2: 4-7 days'
            WHEN lead_days <= 14 THEN '3: 8-14 days'
            WHEN lead_days <= 28 THEN '4: 15-28 days'
            ELSE '5: 29+ days'
        END AS lead_band
    FROM fact_appointment
    WHERE status IN ('completed', 'no_show')
)
SELECT
    lead_band,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_eligible
FROM eligible
GROUP BY 1
ORDER BY 1;

/* name: in_person_by_lead_band */
-- Same bands, in-person only, so the trend is not just virtual visits sitting in the short bands.
WITH eligible AS (
    SELECT
        status,
        CASE
            WHEN lead_days <= 3 THEN '1: 0-3 days'
            WHEN lead_days <= 7 THEN '2: 4-7 days'
            WHEN lead_days <= 14 THEN '3: 8-14 days'
            WHEN lead_days <= 28 THEN '4: 15-28 days'
            ELSE '5: 29+ days'
        END AS lead_band
    FROM fact_appointment
    WHERE status IN ('completed', 'no_show')
      AND modality = 'in_person'
)
SELECT
    lead_band,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM eligible
GROUP BY 1
ORDER BY 1;

/* name: by_payer */
SELECT
    y.payer_id,
    y.payer_name,
    y.payer_type,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct,
    ROUND(AVG(a.lead_days), 1) AS avg_lead_days,
    ROUND(100.0 * SUM(CASE WHEN a.lead_days > 14 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_over_14_days
FROM fact_appointment AS a
JOIN dim_patient AS p ON p.patient_id = a.patient_id
JOIN dim_payer AS y ON y.payer_id = p.payer_id
WHERE a.status IN ('completed', 'no_show')
GROUP BY 1, 2, 3
ORDER BY no_show_rate_pct DESC;

/* name: payer_by_lead_band */
WITH eligible AS (
    SELECT
        y.payer_id,
        y.payer_name,
        a.status,
        CASE
            WHEN a.lead_days <= 3 THEN '1: 0-3 days'
            WHEN a.lead_days <= 7 THEN '2: 4-7 days'
            WHEN a.lead_days <= 14 THEN '3: 8-14 days'
            WHEN a.lead_days <= 28 THEN '4: 15-28 days'
            ELSE '5: 29+ days'
        END AS lead_band
    FROM fact_appointment AS a
    JOIN dim_patient AS p ON p.patient_id = a.patient_id
    JOIN dim_payer AS y ON y.payer_id = p.payer_id
    WHERE a.status IN ('completed', 'no_show')
)
SELECT
    payer_id,
    payer_name,
    lead_band,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM eligible
GROUP BY 1, 2, 3
ORDER BY 1, 3;

/* name: payer_spread_by_lead_band */
-- Within each lead band: lowest and highest payer rate and the gap between them (percentage points).
WITH eligible AS (
    SELECT
        y.payer_name,
        a.status,
        CASE
            WHEN a.lead_days <= 3 THEN '1: 0-3 days'
            WHEN a.lead_days <= 7 THEN '2: 4-7 days'
            WHEN a.lead_days <= 14 THEN '3: 8-14 days'
            WHEN a.lead_days <= 28 THEN '4: 15-28 days'
            ELSE '5: 29+ days'
        END AS lead_band
    FROM fact_appointment AS a
    JOIN dim_patient AS p ON p.patient_id = a.patient_id
    JOIN dim_payer AS y ON y.payer_id = p.payer_id
    WHERE a.status IN ('completed', 'no_show')
),
rates AS (
    SELECT
        lead_band,
        payer_name,
        100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*) AS rate
    FROM eligible
    GROUP BY 1, 2
),
ranked AS (
    SELECT
        lead_band,
        payer_name,
        rate,
        ROW_NUMBER() OVER (PARTITION BY lead_band ORDER BY rate) AS rn_low,
        ROW_NUMBER() OVER (PARTITION BY lead_band ORDER BY rate DESC) AS rn_high
    FROM rates
)
SELECT
    lead_band,
    MAX(CASE WHEN rn_low = 1 THEN payer_name END) AS lowest_payer,
    ROUND(MAX(CASE WHEN rn_low = 1 THEN rate END), 1) AS lowest_rate_pct,
    MAX(CASE WHEN rn_high = 1 THEN payer_name END) AS highest_payer,
    ROUND(MAX(CASE WHEN rn_high = 1 THEN rate END), 1) AS highest_rate_pct,
    ROUND(MAX(rate) - MIN(rate), 1) AS spread_pp
FROM ranked
GROUP BY 1
ORDER BY 1;

/* name: payer_observed_vs_expected */
-- Indirect standardization: expected no-shows if each payer's visits had the network rate
-- for their lead band and modality. Observed ÷ expected > 1 means more no-shows than the
-- booking pattern alone explains.
WITH eligible AS (
    SELECT
        y.payer_id,
        y.payer_name,
        a.modality,
        CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END AS is_no_show,
        CASE
            WHEN a.lead_days <= 3 THEN '1: 0-3 days'
            WHEN a.lead_days <= 7 THEN '2: 4-7 days'
            WHEN a.lead_days <= 14 THEN '3: 8-14 days'
            WHEN a.lead_days <= 28 THEN '4: 15-28 days'
            ELSE '5: 29+ days'
        END AS lead_band
    FROM fact_appointment AS a
    JOIN dim_patient AS p ON p.patient_id = a.patient_id
    JOIN dim_payer AS y ON y.payer_id = p.payer_id
    WHERE a.status IN ('completed', 'no_show')
),
network_rate AS (
    SELECT lead_band, modality, AVG(is_no_show) AS cell_rate
    FROM eligible
    GROUP BY 1, 2
)
SELECT
    e.payer_id,
    e.payer_name,
    COUNT(*) AS eligible_visits,
    SUM(e.is_no_show) AS observed_no_shows,
    ROUND(SUM(n.cell_rate), 1) AS expected_no_shows,
    ROUND(100.0 * SUM(e.is_no_show) / COUNT(*), 1) AS observed_rate_pct,
    ROUND(100.0 * SUM(n.cell_rate) / COUNT(*), 1) AS expected_rate_pct,
    ROUND(SUM(e.is_no_show) / SUM(n.cell_rate), 2) AS observed_to_expected
FROM eligible AS e
JOIN network_rate AS n ON n.lead_band = e.lead_band AND n.modality = e.modality
GROUP BY 1, 2
ORDER BY observed_to_expected DESC;
