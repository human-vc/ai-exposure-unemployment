import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import (BASE_YEAR, LATEST_YEAR, household_bootstrap, interval, monthly_cells, november_to_september,
                    persons, rate, unemployment_by_fifth, with_scores)


def changes(multipliers, base, latest):
    before = unemployment_by_fifth(base, multipliers[0])
    after = unemployment_by_fifth(latest, multipliers[1])
    least, most = after[1] - before[1], after[5] - before[5]
    return np.array([least, most, most - least])


def cyclical_sensitivity(cells):
    early = cells[cells.year <= 2019]
    by_fifth = rate(early, ["date", "fifth"]).unstack()
    design = pd.get_dummies(by_fifth.index.month, drop_first=True).astype(float)
    design.index = by_fifth.index
    design["overall"] = rate(early, ["date"])
    design = sm.add_constant(design)
    return {k: sm.OLS(by_fifth[k], design).fit().params["overall"] for k in (1, 5)}


def main():
    p = persons()
    workers = with_scores(p)
    workers = workers[workers.in_labour_force & workers.fifth.notna()]
    base, latest = november_to_september(workers, BASE_YEAR), november_to_september(workers, LATEST_YEAR)
    point = changes([1.0, 1.0], base, latest)
    low, high = interval(household_bootstrap([base, latest], lambda m: changes(m, base, latest)))
    for name, value, a, b in zip(("least exposed", "most exposed", "difference"), point, low, high):
        print(f"{name:14s} {value:+.2f} [{a:+.2f}, {b:+.2f}]")

    cells = monthly_cells(p)
    sensitivity = cyclical_sensitivity(cells)
    overall = [rate(november_to_september(cells, y), ["codes"]).iloc[0] for y in (BASE_YEAR, LATEST_YEAR)]
    print(f"\noverall rate {overall[0]:.2f} to {overall[1]:.2f}")
    for k, name, actual in ((1, "least exposed", point[0]), (5, "most exposed", point[1])):
        predicted = sensitivity[k] * (overall[1] - overall[0])
        print(f"{name:14s} sensitivity {sensitivity[k]:.2f}, predicted {predicted:+.2f}, actual {actual:+.2f}, ratio {actual / predicted:.1f}")


if __name__ == "__main__":
    main()
