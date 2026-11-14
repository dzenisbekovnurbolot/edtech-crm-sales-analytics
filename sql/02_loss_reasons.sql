-- Причины проигрыша: стадии закрытия сгруппированы в категории.
SELECT CASE
         WHEN stage IN ('НИ РАЗУ НЕ ДОЗВОНИЛСЯ','НЕДОЗВОН','НЕВЕРНЫЙ НОМЕР','ИНСТА БЕЗ НОМЕРА') THEN 'Не дозвонились / номер'
         WHEN stage IN ('НЕ АКТУАЛЬНО','НЕ ОСТАВЛЯЛ ЗАЯВКУ')                                  THEN 'Не актуально'
         WHEN stage = 'АРХИВ'                                                                  THEN 'Архив без причины'
         WHEN stage IN ('НЕ ЦА','JUNIOR','НЕТ ПРОДУКТА','ПАРТНЕРСТВО')                          THEN 'Не целевая аудитория'
         WHEN stage IN ('ДУБЛИКАТ','СТАРЫЙ ЛИД')                                               THEN 'Дубликаты'
         WHEN stage IN ('ОТКАЗ ОТ ОБУЧЕНИЯ','ДРУГАЯ ПРИЧИНА')                                  THEN 'Отказ от обучения'
         WHEN stage = 'ГРАНТ ОТКАЗ'                                                            THEN 'Отказ по гранту'
         WHEN stage IN ('ДОРОГО','ВЫБРАЛИ ДРУГИХ')                                             THEN 'Дорого / выбрали других'
         WHEN stage IN ('НЕ ПОДХОДИТ ВРЕМЯ ОБУЧЕНИЯ','НЕ ПОДХОДИТ ФОРМАТ ОБУЧЕНИЯ','НЕУДОБНАЯ ЛОКАЦИЯ') THEN 'Время, формат, локация'
         ELSE 'Прочее'
       END AS reason,
       COUNT(*) AS deals
FROM dds.deals
WHERE pipeline = 'AI Academy (default)' AND status = 'Проиграна'
GROUP BY 1
ORDER BY deals DESC;
