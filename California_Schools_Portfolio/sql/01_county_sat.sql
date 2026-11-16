-- School-weighted and test-taker-weighted means answer different questions.
SELECT s.County AS county, COUNT(*) AS schools_with_scores,
       SUM(t.NumTstTakr) AS test_takers,
       ROUND(AVG(t.AvgScrRead + t.AvgScrMath + t.AvgScrWrite), 2) AS mean_school_sat,
       ROUND(SUM(1.0 * t.NumTstTakr * (t.AvgScrRead + t.AvgScrMath + t.AvgScrWrite))
             / NULLIF(SUM(t.NumTstTakr), 0), 2) AS weighted_sat
FROM schools s JOIN satscores t ON s.CDSCode = t.cds
WHERE t.rtype = 'S' AND t.NumTstTakr > 0
  AND t.AvgScrRead BETWEEN 200 AND 800
  AND t.AvgScrMath BETWEEN 200 AND 800
  AND t.AvgScrWrite BETWEEN 200 AND 800
GROUP BY s.County ORDER BY mean_school_sat DESC;
