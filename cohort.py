import numpy as np

from common import BASE_YEAR, LATEST_YEAR, household_bootstrap, interval, persons, unemployment_by_fifth, with_scores

LAST_MONTH = 9


def one_year_later(p, year):
    months = p[p.month <= LAST_MONTH]
    before = months[(months.year == year - 1) & months.month_in_sample.between(1, 4) & months.employed & months.fifth.notna()]
    after = months[(months.year == year) & months.month_in_sample.between(5, 8)]
    after = after[["person", "month", "month_in_sample", "sex", "age", "unemployed"]]
    matched = before.drop(columns="unemployed").merge(after, on=["person", "month"], suffixes=("", "_later"))
    same_person = (
        (matched.month_in_sample_later == matched.month_in_sample + 4)
        & (matched.sex_later == matched.sex)
        & (matched.age_later - matched.age).between(0, 2)
    )
    return matched[same_person], len(before)


def difference(multipliers, base, latest):
    before = unemployment_by_fifth(base, multipliers[0])
    after = unemployment_by_fifth(latest, multipliers[1])
    return (after[5] - before[5]) - (after[1] - before[1])


def main():
    p = with_scores(persons())
    cohorts = {}
    for year in (BASE_YEAR, LATEST_YEAR):
        cohorts[year], candidates = one_year_later(p, year)
        rates = unemployment_by_fifth(cohorts[year])
        print(f"{year}: matched {len(cohorts[year]) / candidates:.0%}, least exposed {rates[1]:.2f}, most exposed {rates[5]:.2f}")
    base, latest = cohorts[BASE_YEAR], cohorts[LATEST_YEAR]
    low, high = interval(household_bootstrap([base, latest], lambda m: difference(m, base, latest)))
    print(f"difference in change {difference([1.0, 1.0], base, latest):+.2f} [{low:+.2f}, {high:+.2f}]")


if __name__ == "__main__":
    main()
