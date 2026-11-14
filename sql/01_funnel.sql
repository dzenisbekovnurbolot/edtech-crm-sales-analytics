-- Воронка «по факту прохождения»: сколько сделок дошли до стадии или дальше.
-- Таблицы DDS-слоя: dds.deals (сделки), dds.deal_stage_history (история смен стадий).
WITH stages(stage_name, ord) AS (
    VALUES ('ВЗЯЛ В РАБОТУ', 1), ('КВАЛ ДАТА', 2), ('КВАЛ Л', 2),
           ('ЗАПИСАН НА КЭВ (МС/ПУ/КОНС)', 3), ('ПРОШЕЛ КЭВ (ИНТ/ТЕСТ)', 4),
           ('ЖДЕМ ПРЕДОПЛАТУ', 5), ('УСПЕШНАЯ СДЕЛКА', 6)
),
deal_max AS (
    SELECT h.deal_id, MAX(COALESCE(s.ord, 0)) AS max_ord
    FROM dds.deal_stage_history h
    JOIN dds.deals d ON d.deal_id = h.deal_id AND d.pipeline = 'AI Academy (default)'
    LEFT JOIN stages s ON s.stage_name = h.stage
    GROUP BY h.deal_id
),
levels(ord, label) AS (
    VALUES (0, 'Новый лид'), (1, 'Взяли в работу'), (2, 'Квалифицирован'),
           (3, 'Записан на КЭВ'), (4, 'Прошёл КЭВ'), (5, 'Ждём предоплату'), (6, 'Оплата')
)
SELECT l.label,
       COUNT(dm.deal_id) AS deals,
       ROUND(COUNT(dm.deal_id)::numeric
             / NULLIF(LAG(COUNT(dm.deal_id)) OVER (ORDER BY l.ord), 0), 3) AS step_conversion
FROM levels l
LEFT JOIN deal_max dm ON dm.max_ord >= l.ord
GROUP BY l.ord, l.label
ORDER BY l.ord;
