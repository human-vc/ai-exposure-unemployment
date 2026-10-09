# Unemployment by AI exposure: checks on a SIEPR policy brief

[What Is Really Happening to Jobs?](https://siepr.stanford.edu/publications/policy-brief/what-really-happening-jobs-separating-ai-hype-reality) (Mahoney, McEntarfer and Wahal, SIEPR, July 2026) reports that unemployment in the most AI-exposed fifth of occupations has risen 0.77 points since 2022, against 0.85 for the least exposed fifth. This repo rebuilds that comparison from the public monthly Current Population Survey files, January 2015 to September 2026, and uses it to address three points the brief leaves open.

## Results

The brief leaves three points open, and the scripts take them in turn.

**Does the aggregate comparison hold with later data?**
- With the brief's smoothing, the most exposed fifth is up 0.74 to 0.80 for any endpoint from 2025 Q4 to 2026 Q3. The least exposed fifth is up 0.33, 0.73, 0.35 and 0.08, because its unemployment rises every winter.
- With the same calendar months compared, the most exposed fifth is up 0.77 and the least exposed 0.27. The difference is 0.50 (95% interval 0.07 to 0.91).
- Among people employed a year earlier, the share unemployed a year later went from 1.03% to 1.74% in the most exposed fifth and from 2.20% to 2.15% in the least exposed.

**Is disruption hidden in parts of the labor market?**
- The top tenth of workers by exposure is up 0.89 and the top twentieth 0.87, close to the 0.77 for the whole fifth.
- The gap is absent through 2023, opens during 2024, narrows in 2025 and widens again in 2026.

**Can other factors account for the rise?**
- The cycle: the most exposed fifth normally moves 0.5 points for each point of the overall rate. Its rise is 4.6 times what that predicts. For the least exposed fifth the ratio is 0.5.
- Over-hiring: occupations that grew faster between 2020 and 2022 show no larger rise.
- Remote work: AI exposure and remote-work ability cannot be separated across all occupations (correlation 0.72). Among remote-capable occupations, the most exposed third rose 0.66 points more than the least exposed third (0.12 to 1.21).

The same pattern in the same survey is reported by Ahn and Carollo (Federal Reserve Board, September 2026) and by Borovičková and Macaluso (Richmond Fed, August 2026).

## Limits

- The brief does not state how "since 2022" is computed. The smoothed line ending at 2026 Q1 gives 0.73 and 0.80.
- Exposure is scored by occupation, and the unemployed are classed by their last job.
- October 2025 was not collected, so 2025 Q4 has two months.

## Run

```
pip install -r requirements.txt
python download_cps.py 2015 2026 data/cps
python build_persons.py data/cps data/persons.parquet
python build_scores.py data/scores.csv
python endpoint.py
python matched_change.py
python cohort.py
python pockets.py
python other_factors.py
```

`build_scores.py` needs these files in `data/raw/`: `AIOE_DataAppendix.xlsx` (Felten, Raj and Seamans), `onet251_abilities.xlsx` (O*NET 25.1 Abilities), `occ2018.xlsx` (Census 2018 occupation code list and crosswalk) and `dn_onet.csv` (Dingel and Neiman). It also needs `occ_2010_2018_cps_crosswalk.dta` from the Economic Innovation Group [replication archive](https://github.com/EIG-Research/AI-unemployment) in `data/eig/AI Unemployment Data/`.
