-- Day DAY_NUMBER: DAY_TITLE
-- Definition: (write the metric definition here)
-- Data: shared/clinic.db (synthetic)

/* name: overall */
SELECT
    COUNT(*) AS n
FROM fact_appointment;
