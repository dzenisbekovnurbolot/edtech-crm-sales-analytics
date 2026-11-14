-- Проверки качества данных CRM перед построением отчётов.
SELECT
  ROUND(AVG((source = 'Не указано')::int), 3)                               AS leads_without_source,
  ROUND(AVG((source = 'Не указано')::int) FILTER (WHERE status = 'Выиграна'), 3) AS paid_without_source,
  ROUND(AVG((direction = 'Не указано')::int), 3)                            AS leads_without_direction,
  ROUND(AVG((closed_at < created_at)::int) FILTER (WHERE closed_at IS NOT NULL), 3) AS negative_cycle_share
FROM dds.deals
WHERE pipeline = 'AI Academy (default)';
