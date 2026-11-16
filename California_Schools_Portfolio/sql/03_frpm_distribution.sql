WITH categorized AS (
  SELECT "Percent (%) Eligible FRPM (K-12)" AS frpm_share,
    CASE WHEN "Percent (%) Eligible FRPM (K-12)" <= 0.25 THEN 'Low'
         WHEN "Percent (%) Eligible FRPM (K-12)" <= 0.50 THEN 'Moderate'
         WHEN "Percent (%) Eligible FRPM (K-12)" <= 0.75 THEN 'High'
         ELSE 'Very High' END AS category
  FROM frpm WHERE "Academic Year" = '2014-2015'
    AND "Percent (%) Eligible FRPM (K-12)" BETWEEN 0 AND 1
)
SELECT category, COUNT(*) AS school_records,
       ROUND(100.0 * AVG(frpm_share), 2) AS mean_frpm_percent
FROM categorized GROUP BY category
ORDER BY CASE category WHEN 'Low' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'High' THEN 3 ELSE 4 END;
