import numpy as np
import pandas as pd

PERSONS = "data/persons.parquet"
SCORES = "data/scores.csv"
BASE_YEAR = 2022
LATEST_YEAR = 2026


def persons():
    p = pd.read_parquet(PERSONS)
    p["employed"] = p.status.isin([1, 2])
    p["unemployed"] = p.status.isin([3, 4])
    p["in_labour_force"] = p.status.between(1, 4)
    return p


def with_scores(p):
    scores = pd.read_csv(SCORES)
    scores = scores[scores.codes == 2018].set_index("occupation")[["exposure", "fifth", "remote_work"]]
    return p[p.year >= 2020].join(scores, on="occupation")


def monthly_cells(p):
    workers = p[p.in_labour_force & (p.occupation > 0)]
    cells = workers.assign(u=workers.weight * workers.unemployed)
    cells = cells.groupby(["year", "month", "occupation"])[["u", "weight"]].sum().reset_index()
    cells["codes"] = np.where(cells.year < 2020, 2010, 2018)
    cells = cells.merge(pd.read_csv(SCORES), on=["codes", "occupation"])
    cells[["u", "weight"]] = cells[["u", "weight"]].mul(cells.share, axis=0)
    cells["date"] = pd.to_datetime(dict(year=cells.year, month=cells.month, day=1))
    return cells


def rate(cells, by):
    totals = cells.groupby(by)[["u", "weight"]].sum()
    return 100 * totals.u / totals.weight


def november_to_september(frame, year):
    months = frame.year.astype(int) * 12 + frame.month.astype(int)
    return frame[(months >= (year - 1) * 12 + 11) & (months <= year * 12 + 9)]


def unemployment_by_fifth(frame, multiplier=1.0):
    weight = frame.weight.values * multiplier
    unemployed = weight * frame.unemployed.values
    fifth = frame.fifth.values
    return {k: 100 * unemployed[fifth == k].sum() / weight[fifth == k].sum() for k in (1, 5)}


def household_bootstrap(frames, statistic, draws=500, seed=0):
    rng = np.random.default_rng(seed)
    households = np.unique(np.concatenate([f.household.unique() for f in frames]))
    position = pd.Series(np.arange(len(households)), index=households)
    rows = [position[f.household].values for f in frames]
    out = []
    for _ in range(draws):
        counts = rng.multinomial(len(households), np.full(len(households), 1 / len(households)))
        out.append(statistic([counts[r] for r in rows]))
    return np.array(out)


def interval(draws):
    return np.quantile(draws, [0.025, 0.975], axis=0)
