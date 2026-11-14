"""Расчёт метрик портфолио по выгрузке Bitrix24 (DDS-слой).

Запуск:  python analysis/metrics.py data/Bitrix24_DDS_dannye.xlsx
Сырые данные компании в репозиторий не входят; скрипт сохраняет
только агрегаты в data/aggregates/ и графики в images/.
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
AGG, IMG = ROOT / "data" / "aggregates", ROOT / "images"
MAIN, CLIENTS = "AI Academy (default)", "КЛИЕНТЫ"

FUNNEL = ["ВЗЯЛ В РАБОТУ", "КВАЛ ДАТА", "КВАЛ Л", "ЗАПИСАН НА КЭВ (МС/ПУ/КОНС)",
          "ПРОШЕЛ КЭВ (ИНТ/ТЕСТ)", "ЖДЕМ ПРЕДОПЛАТУ", "УСПЕШНАЯ СДЕЛКА"]
FUNNEL_STEPS = [("Взяли в работу", 0), ("Квалифицирован", 1), ("Записан на КЭВ", 3),
                ("Прошёл КЭВ", 4), ("Ждём предоплату", 5), ("Оплата", 6)]
LOSS_GROUPS = {
    "Не дозвонились / номер": ["НИ РАЗУ НЕ ДОЗВОНИЛСЯ", "НЕДОЗВОН", "НЕВЕРНЫЙ НОМЕР", "ИНСТА БЕЗ НОМЕРА"],
    "Не актуально": ["НЕ АКТУАЛЬНО", "НЕ ОСТАВЛЯЛ ЗАЯВКУ"],
    "Архив без причины": ["АРХИВ"],
    "Не целевая аудитория": ["НЕ ЦА", "JUNIOR", "НЕТ ПРОДУКТА", "ПАРТНЕРСТВО"],
    "Дубликаты": ["ДУБЛИКАТ", "СТАРЫЙ ЛИД"],
    "Отказ от обучения": ["ОТКАЗ ОТ ОБУЧЕНИЯ", "ДРУГАЯ ПРИЧИНА"],
    "Отказ по гранту": ["ГРАНТ ОТКАЗ"],
    "Дорого / выбрали других": ["ДОРОГО", "ВЫБРАЛИ ДРУГИХ"],
    "Время, формат, локация": ["НЕ ПОДХОДИТ ВРЕМЯ ОБУЧЕНИЯ", "НЕ ПОДХОДИТ ФОРМАТ ОБУЧЕНИЯ", "НЕУДОБНАЯ ЛОКАЦИЯ"],
}
MONTHS = [f"{i} МЕСЯЦ" for i in range(1, 8)]
TEAL, ORANGE = "#0E7C6B", "#C2410C"


def load(path):
    x = pd.read_excel(path, sheet_name=None)
    deals = x["Сделки"]
    history = pd.concat([
        x["История_событий_по_стадиям"][["ID_сделки", "Воронка", "Стадия"]],
        *(x[s][["ID_сделки", "Воронка", "Стадия"]] for s in
          ["Интервалы_стадий", "Интервалы_стадий_архив", "Интервалы_стадий_снимок"]),
    ])
    return deals, history


def funnel(deals, history):
    ids = set(deals.loc[deals["Воронка"] == MAIN, "ID_сделки"])
    h = history[(history["Воронка"] == MAIN) & history["ID_сделки"].isin(ids)]
    rows = [("Новый лид", h["ID_сделки"].nunique())]
    for label, i in FUNNEL_STEPS:
        # сделка «дошла до стадии», если в истории есть эта стадия или любая следующая
        rows.append((label, h.loc[h["Стадия"].isin(FUNNEL[i:]), "ID_сделки"].nunique()))
    df = pd.DataFrame(rows, columns=["stage", "deals"])
    df["step_conversion"] = (df["deals"] / df["deals"].shift()).round(3)
    return df


def loss_reasons(deals):
    lost = deals[(deals["Воронка"] == MAIN) & (deals["Статус"] == "Проиграна")]
    inv = {s: g for g, ss in LOSS_GROUPS.items() for s in ss}
    return (lost["Стадия"].map(inv).fillna("Прочее").value_counts()
            .rename_axis("reason").reset_index(name="deals"))


def by_direction(deals):
    m = deals[(deals["Воронка"] == MAIN) & (deals["Направление"] != "Не указано")]
    g = m.groupby("Направление").agg(leads=("ID_сделки", "count"),
                                     paid=("Статус", lambda s: (s == "Выиграна").sum()))
    g["conversion"] = (g["paid"] / g["leads"]).round(4)
    return g[g["leads"] >= 200].sort_values("conversion", ascending=False).reset_index()


def retention(deals, history):
    ids = set(deals.loc[deals["Воронка"] == CLIENTS, "ID_сделки"])
    h = history[(history["Воронка"] == CLIENTS) & history["ID_сделки"].isin(ids)]
    rows = [(i + 1, h.loc[h["Стадия"].isin(MONTHS[i:]), "ID_сделки"].nunique()) for i in range(len(MONTHS))]
    df = pd.DataFrame(rows, columns=["month", "students"])
    df["share_of_month_1"] = (df["students"] / df["students"].iloc[0]).round(3)
    return df


def data_quality(deals):
    m = deals[deals["Воронка"] == MAIN]
    won = m[m["Статус"] == "Выиграна"]
    cyc = deals["Длительность_цикла_дней"].dropna()
    return pd.DataFrame([
        ("Лиды без источника", round((m["Источник"] == "Не указано").mean(), 3)),
        ("Оплаты без источника", round((won["Источник"] == "Не указано").mean(), 3)),
        ("Лиды без направления", round((m["Направление"] == "Не указано").mean(), 3)),
        ("Отрицательная длительность цикла", round((cyc < 0).mean(), 3)),
    ], columns=["check", "share"])


def barh(df, label, value, path, title, highlight=(), fmt="{:,.0f}"):
    fig, ax = plt.subplots(figsize=(9, 0.45 * len(df) + 1))
    colors = [ORANGE if i in highlight else TEAL for i in range(len(df))]
    ax.barh(df[label], df[value], color=colors)
    ax.invert_yaxis()
    for i, v in enumerate(df[value]):
        ax.text(v, i, " " + fmt.format(v).replace(",", " "), va="center", fontsize=10)
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    ax.set_xticks([])
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(path):
    AGG.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(exist_ok=True)
    deals, history = load(path)
    f, l, d, r, q = (funnel(deals, history), loss_reasons(deals), by_direction(deals),
                     retention(deals, history), data_quality(deals))
    for name, df in [("funnel", f), ("loss_reasons", l), ("conversion_by_direction", d),
                     ("retention_by_month", r), ("data_quality", q)]:
        df.to_csv(AGG / f"{name}.csv", index=False)
        print(f"\n== {name}\n{df.to_string(index=False)}")
    barh(f, "stage", "deals", IMG / "funnel.png", "Воронка: сколько сделок дошли до стадии", highlight=(1,))
    barh(l, "reason", "deals", IMG / "loss_reasons.png", "Причины проигрыша сделок", highlight=(0,))
    barh(d, "Направление", "conversion", IMG / "conversion_by_direction.png",
         "Конверсия лида в оплату по направлениям", fmt="{:.1%}")
    r["label"] = r["month"].astype(str) + "-й месяц"
    barh(r, "label", "students", IMG / "retention.png", "Студенты, дошедшие хотя бы до N-го месяца", highlight=(1,))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data" / "Bitrix24_DDS_dannye.xlsx")
