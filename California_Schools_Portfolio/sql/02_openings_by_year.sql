-- Recorded opening dates, not net additions or a complete historical inventory.
SELECT CAST(strftime('%Y', OpenDate) AS INTEGER) AS opening_year,
       COUNT(*) AS recorded_openings
FROM schools
WHERE School IS NOT NULL AND strftime('%Y', OpenDate) IS NOT NULL
GROUP BY opening_year ORDER BY opening_year;
