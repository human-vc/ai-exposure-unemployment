import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import BASE_YEAR, LATEST_YEAR, interval, november_to_september, persons, with_scores

MIN_RESPONDENTS = 200
REMOTE_CUTOFF = 0.5
DRAWS = 400


def by_occupation(frame):
    table = frame.assign(u=frame.weight * frame.unemployed).groupby("occupation").agg(
        u=("u", "sum"), weight=("weight", "sum"), n=("weight", "size"),
        exposure=("exposure", "first"), remote_work=("remote_work", "first"),
    )
    table["rate"] = 100 * table.u / table.weight
    return table


def regression(occupations, columns):
    data = occupations.dropna(subset=columns)
    design = pd.DataFrame({c: (data[c] - np.average(data[c], weights=data.weight)) / data[c].std() for c in columns})
    fit = sm.WLS(data.change, sm.add_constant(design), weights=data.weight).fit(cov_type="HC1")
    return "  ".join(f"{c} {fit.params[c]:+.2f} ({fit.bse[c]:.2f})" for c in columns)


def growth_2020_to_2022(workers):
    employed = workers[workers.employed]
    early = employed[(employed.year == 2020) & (employed.month <= 2)].groupby("occupation").weight.sum() / 2
    later = employed[employed.year == BASE_YEAR].groupby("occupation").weight.sum() / 12
    return np.log(later / early).replace([np.inf, -np.inf], np.nan).rename("growth")


def high_minus_low(occupations):
    change = lambda rows: np.average(rows.rate_latest, weights=rows.weight_latest) - np.average(rows.rate, weights=rows.weight)
    return change(occupations[occupations.third == 2]) - change(occupations[occupations.third == 0])


def main():
    workers = with_scores(persons())
    workers = workers[workers.in_labour_force & workers.exposure.notna()]
    base = by_occupation(november_to_september(workers, BASE_YEAR))
    latest = by_occupation(november_to_september(workers, LATEST_YEAR))
    occupations = base.join(latest[["rate", "weight", "n"]], rsuffix="_latest", how="inner")
    occupations["change"] = occupations.rate_latest - occupations.rate
    occupations = occupations.join(growth_2020_to_2022(workers))
    large = occupations[(occupations.n >= MIN_RESPONDENTS) & (occupations.n_latest >= MIN_RESPONDENTS)]
    for columns in (["exposure"], ["remote_work"], ["growth"], ["exposure", "remote_work", "growth"]):
        print(regression(large, columns))

    rng = np.random.default_rng(0)
    known = occupations.dropna(subset=["remote_work"])
    for name, group in (("remote-capable", known[known.remote_work >= REMOTE_CUTOFF]), ("other", known[known.remote_work < REMOTE_CUTOFF])):
        group = group.assign(third=pd.qcut(group.exposure.rank(method="first"), 3, labels=False))
        draws = [high_minus_low(group.sample(frac=1, replace=True, random_state=int(rng.integers(1e9)))) for _ in range(DRAWS)]
        low, high = interval(np.array(draws))
        print(f"{name:15s} high minus low exposure {high_minus_low(group):+.2f} [{low:+.2f}, {high:+.2f}]  {len(group)} occupations")


if __name__ == "__main__":
    main()
