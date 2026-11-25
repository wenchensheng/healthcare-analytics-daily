-- Day 001: Monthly clinic no-show rate by visit type
-- Definition: no-show rate = no-shows / (completed + no-shows). Cancellations excluded.
-- Data: shared/clinic.db (synthetic Amber Ridge Health appointments, Jan 2024–Dec 2025)

/* name: overall */
SELECT
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment
WHERE status IN ('completed', 'no_show');

/* name: cancelled_excluded */
SELECT COUNT(*) AS cancelled_visits
FROM fact_appointment
WHERE status = 'cancelled';

/* name: by_year */
SELECT
    strftime('%Y', visit_date) AS year,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment
WHERE status IN ('completed', 'no_show')
GROUP BY 1
ORDER BY 1;

/* name: by_visit_type */
SELECT
    visit_type,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct,
    ROUND(AVG(lead_days), 1) AS avg_lead_days,
    ROUND(100.0 * AVG(CASE WHEN lead_days > 14 THEN 1.0 ELSE 0.0 END), 1) AS pct_lead_over_14_days
FROM fact_appointment
WHERE status IN ('completed', 'no_show')
GROUP BY 1
ORDER BY no_show_rate_pct DESC;

/* name: by_modality */
SELECT
    modality,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment
WHERE status IN ('completed', 'no_show')
GROUP BY 1
ORDER BY no_show_rate_pct DESC;

/* name: by_clinic */
SELECT
    a.clinic_id,
    c.clinic_name,
    c.geography,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment AS a
JOIN dim_clinic AS c ON c.clinic_id = a.clinic_id
WHERE a.status IN ('completed', 'no_show')
GROUP BY 1, 2, 3
ORDER BY no_show_rate_pct DESC;

/* name: c05_vs_peers */
SELECT
    CASE WHEN clinic_id = 'C05' THEN 'C05 Brookfield' ELSE 'Peer clinics' END AS clinic_group,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment
WHERE status IN ('completed', 'no_show')
GROUP BY 1
ORDER BY clinic_group;

/* name: monthly_overall */
WITH monthly AS (
    SELECT
        strftime('%Y-%m', visit_date) AS year_month,
        COUNT(*) AS eligible_visits,
        SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
        1.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*) AS no_show_rate
    FROM fact_appointment
    WHERE status IN ('completed', 'no_show')
    GROUP BY 1
)
SELECT
    year_month,
    eligible_visits,
    no_shows,
    ROUND(100.0 * no_show_rate, 1) AS no_show_rate_pct,
    ROUND(
        100.0 * (no_show_rate - LAG(no_show_rate) OVER (ORDER BY year_month)),
        1
    ) AS mom_change_pp,
    ROUND(
        100.0 * AVG(no_show_rate) OVER (
            ORDER BY year_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        1
    ) AS ma3_rate_pct
FROM monthly
ORDER BY year_month;

/* name: monthly_by_visit_type */
SELECT
    strftime('%Y-%m', visit_date) AS year_month,
    visit_type,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment
WHERE status IN ('completed', 'no_show')
GROUP BY 1, 2
ORDER BY 1, 2;

/* name: monthly_by_modality */
SELECT
    strftime('%Y-%m', visit_date) AS year_month,
    modality,
    COUNT(*) AS eligible_visits,
    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_rate_pct
FROM fact_appointment
WHERE status IN ('completed', 'no_show')
GROUP BY 1, 2
ORDER BY 1, 2;

/* name: virtual_share_by_year */
SELECT
    strftime('%Y', visit_date) AS year,
    COUNT(*) AS completed_visits,
    SUM(CASE WHEN modality IN ('video', 'audio') THEN 1 ELSE 0 END) AS virtual_completed,
    ROUND(
        100.0 * SUM(CASE WHEN modality IN ('video', 'audio') THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS virtual_share_pct
FROM fact_appointment
WHERE status = 'completed'
GROUP BY 1
ORDER BY 1;
