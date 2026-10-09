import numpy as np
import pandas as pd

from common import BASE_YEAR, monthly_cells, persons, rate

SPAN = 0.5
LAST_QUARTERS = ["2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2", "2026Q3"]


def smooth(values, span=SPAN):
    n = len(values)
    x = np.arange(n, dtype=float)
    nearest = int(np.floor(span * n + 1e-9))
    out = np.zeros(n)
    for i in range(n):
        distance = np.abs(x - x[i])
        weight = np.clip(1 - (distance / np.sort(distance)[nearest - 1]) ** 3, 0, None) ** 3
        out[i] = np.polyval(np.polyfit(x, values, 2, w=np.sqrt(weight)), x[i])
    return out


def changes(quarterly):
    rows = []
    for last in LAST_QUARTERS:
        line = quarterly.loc[:last].apply(lambda column: pd.Series(smooth(column.values), index=column.index))
        change = line.loc[last] - line.loc[f"{BASE_YEAR}Q1":f"{BASE_YEAR}Q4"].mean()
        rows.append({"last_quarter": last, "least_exposed": change[1], "most_exposed": change[5]})
    return pd.DataFrame(rows)


def main():
    cells = monthly_cells(persons())
    cells["quarter"] = cells.date.dt.to_period("Q")
    print(changes(rate(cells, ["quarter", "fifth"]).unstack()).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
