import numpy as np

from common import (BASE_YEAR, LATEST_YEAR, household_bootstrap, interval, monthly_cells, november_to_september,
                    persons, rate, with_scores)
from matched_change import cyclical_sensitivity

TOP_SHARES = {"top tenth": 0.90, "top twentieth": 0.95}
MONTHS = ["2022-12", "2023-12", "2024-12", "2025-09", "2026-09"]


def change_in_group(multipliers, base, latest, members):
    rates = []
    for frame, multiplier in zip((base, latest), multipliers):
        weight = frame.weight.values * multiplier
        inside = frame.occupation.isin(members).values
        rates.append(100 * (weight * frame.unemployed.values)[inside].sum() / weight[inside].sum())
    return rates[1] - rates[0]


def main():
    p = persons()
    workers = with_scores(p)
    workers = workers[workers.in_labour_force & workers.exposure.notna()]
    base, latest = november_to_september(workers, BASE_YEAR), november_to_september(workers, LATEST_YEAR)
    by_exposure = workers.groupby("occupation").agg(weight=("weight", "sum"), exposure=("exposure", "first")).sort_values("exposure")
    cumulative = by_exposure.weight.cumsum() / by_exposure.weight.sum()
    for name, cutoff in TOP_SHARES.items():
        members = set(cumulative[cumulative > cutoff].index)
        low, high = interval(household_bootstrap([base, latest], lambda m: change_in_group(m, base, latest, members), draws=300))
        print(f"{name:14s} {change_in_group([1.0, 1.0], base, latest, members):+.2f} [{low:+.2f}, {high:+.2f}]  {len(members)} occupations")

    cells = monthly_cells(p)
    sensitivity = cyclical_sensitivity(cells)
    by_fifth = rate(cells, ["date", "fifth"]).unstack().rolling(12).mean()
    overall = rate(cells, ["date"]).rolling(12).mean()
    gap = by_fifth[5] - by_fifth[1]
    net = gap - (sensitivity[5] - sensitivity[1]) * overall
    start = f"{BASE_YEAR}-09-01"
    print("\ngap between most and least exposed, 12-month average, relative to September 2022")
    for month in MONTHS:
        print(f"{month}  {gap.loc[month + '-01'] - gap.loc[start]:+.2f}  net of cycle {net.loc[month + '-01'] - net.loc[start]:+.2f}")


if __name__ == "__main__":
    main()
