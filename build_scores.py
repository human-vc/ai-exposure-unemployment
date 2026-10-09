import sys

import pandas as pd

RAW = "data/raw"
EIG = "data/eig/AI Unemployment Data"
RENAME = {"Visual Color Discrimination": "Visual Color Determination"}


def rows_for(table, soc):
    match = table[table.soc == soc]
    return match if len(match) else table[table.soc.str.startswith(soc.rstrip("X0"))]


def exposure_by_occupation(codes):
    abilities = pd.read_excel(f"{RAW}/onet251_abilities.xlsx")
    abilities = abilities[abilities["Scale Name"] == "Importance"]
    abilities = abilities.assign(soc=abilities["O*NET-SOC Code"].str[:7], ability=abilities["Element Name"].replace(RENAME))
    wide = abilities.pivot_table(index=["O*NET-SOC Code", "soc"], columns="ability", values="Data Value").reset_index(level="soc")
    importance = pd.DataFrame({
        int(code): rows_for(wide, soc).drop(columns="soc").mean()
        for code, soc in zip(codes.occupation, codes.soc) if len(rows_for(wide, soc))
    }).T
    scaled = (importance - importance.min() + 1e-6) / (importance.max() - importance.min() + 1e-6)
    weights = scaled.div(scaled.sum(axis=1), axis=0)
    by_ability = pd.read_excel(f"{RAW}/AIOE_DataAppendix.xlsx", sheet_name="Appendix E")
    by_ability = by_ability.set_index(by_ability.columns[0])[by_ability.columns[1]]
    return weights[by_ability.index].mul(by_ability, axis=1).sum(axis=1)


def remote_work_by_occupation():
    remote = pd.read_csv(f"{RAW}/dn_onet.csv")
    remote = remote.assign(soc=remote.onetsoccode.str[:7])
    cross = pd.read_excel(f"{RAW}/occ2018.xlsx", sheet_name="2010 to 2018 Crosswalk ", header=None, skiprows=4, dtype=str)
    cross = cross.iloc[:, [0, 4]].ffill()
    cross.columns = ["soc", "occupation"]
    cross = cross[cross.occupation.str.fullmatch(r"\d{4}", na=False)]
    cross["remote_work"] = [rows_for(remote, soc.strip()).teleworkable.mean() for soc in cross.soc]
    return cross.assign(occupation=cross.occupation.astype(int)).groupby("occupation").remote_work.mean()


def main(out_path):
    codes = pd.read_excel(f"{RAW}/occ2018.xlsx", sheet_name="2018 Census Occ Code List", header=None, skiprows=5, dtype=str)
    codes = codes.iloc[:, 2:4]
    codes.columns = ["occupation", "soc"]
    codes = codes[codes.occupation.str.fullmatch(r"\d{4}", na=False) & codes.soc.notna() & (codes.soc != "none")]
    codes["soc"] = codes.soc.str.strip()

    exposure = exposure_by_occupation(codes)
    current = pd.DataFrame({"occupation": exposure.index, "exposure": exposure.values})
    current["fifth"] = pd.qcut(current.exposure.rank(method="first"), 5, labels=False) + 1
    current["remote_work"] = current.occupation.map(remote_work_by_occupation())
    current = current.assign(codes="2018", share=1.0)

    sample = pd.read_stata(f"{EIG}/occ_2010_2018_cps_crosswalk.dta", convert_categoricals=False)
    sample = sample[(sample.occ > 0) & (sample.occ2010 < 9999)]
    links = sample.groupby(["occ2010", "occ"]).wtfinl.sum().reset_index()
    links["share"] = links.wtfinl / links.groupby("occ2010").wtfinl.transform("sum")
    earlier = links.merge(current.drop(columns=["share", "codes"]), left_on="occ", right_on="occupation")
    earlier = earlier.assign(occupation=earlier.occ2010, codes="2010")

    columns = ["codes", "occupation", "share", "exposure", "fifth", "remote_work"]
    pd.concat([earlier[columns], current[columns]]).to_csv(out_path, index=False)
    print(len(current), "current codes,", earlier.occupation.nunique(), "earlier codes")


if __name__ == "__main__":
    main(sys.argv[1])
