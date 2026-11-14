-- Удержание: сколько студентов дошли хотя бы до N-го месяца обучения (воронка «КЛИЕНТЫ»).
WITH reached AS (
    SELECT deal_id, MAX(SUBSTRING(stage FROM '^(\d+) МЕСЯЦ$')::int) AS max_month
    FROM dds.deal_stage_history
    WHERE pipeline = 'КЛИЕНТЫ' AND stage ~ '^\d+ МЕСЯЦ$'
    GROUP BY deal_id
)
SELECT m AS month,
       COUNT(*) FILTER (WHERE max_month >= m) AS students,
       ROUND(COUNT(*) FILTER (WHERE max_month >= m)::numeric
             / NULLIF(COUNT(*) FILTER (WHERE max_month >= 1), 0), 3) AS share_of_month_1
FROM reached, generate_series(1, 7) AS m
GROUP BY m
ORDER BY m;
