-- Normalize 2-digit county + 5-digit district + 7-digit school identifiers.
WITH f AS (
 SELECT printf('%02d%05d%07d', CAST("County Code" AS INTEGER),
        "District Code", CAST("School Code" AS INTEGER)) AS cds,
        100.0 * "Percent (%) Eligible FRPM (K-12)" AS frpm_percent
 FROM frpm WHERE "Academic Year" = '2014-2015'
   AND "County Code" IS NOT NULL AND "District Code" IS NOT NULL
   AND "School Code" IS NOT NULL
   AND "Percent (%) Eligible FRPM (K-12)" BETWEEN 0 AND 1
)
SELECT t.cds, t.sname AS school, t.cname AS county, f.frpm_percent,
       t.AvgScrRead + t.AvgScrMath + t.AvgScrWrite AS total_sat,
       t.NumTstTakr AS test_takers, t.enroll12 AS grade12_enrollment
FROM satscores t JOIN f ON t.cds = f.cds
WHERE t.rtype = 'S' AND t.NumTstTakr > 0
  AND t.AvgScrRead BETWEEN 200 AND 800 AND t.AvgScrMath BETWEEN 200 AND 800
  AND t.AvgScrWrite BETWEEN 200 AND 800
ORDER BY t.cds;
