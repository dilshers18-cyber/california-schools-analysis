WITH scored AS (
 SELECT cds, sname AS school, cname AS county, NumTstTakr AS test_takers,
        enroll12 AS grade12_enrollment,
        AvgScrRead + AvgScrMath + AvgScrWrite AS total_sat
 FROM satscores WHERE rtype = 'S' AND NumTstTakr > 0
   AND AvgScrRead BETWEEN 200 AND 800 AND AvgScrMath BETWEEN 200 AND 800
   AND AvgScrWrite BETWEEN 200 AND 800
), ranked AS (
 SELECT *, RANK() OVER (ORDER BY total_sat DESC) AS sat_rank FROM scored
)
SELECT * FROM ranked WHERE sat_rank <= 10 ORDER BY sat_rank, school;
