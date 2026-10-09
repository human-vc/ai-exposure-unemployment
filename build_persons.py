import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

FIELDS = {
    "household": (1, 15), "household2": (71, 75), "line": (147, 148), "month_in_sample": (63, 64),
    "age": (122, 123), "sex": (129, 130), "status": (180, 181), "reason": (405, 406),
    "weight": (846, 855), "occupation": (860, 863),
}


def read_month(path):
    archive = zipfile.ZipFile(path)
    lines = pd.Series(archive.read(archive.namelist()[0]).decode("latin1").splitlines())
    frame = pd.DataFrame({name: lines.str.slice(a - 1, b).str.strip() for name, (a, b) in FIELDS.items()})
    numeric = [c for c in frame.columns if c not in ("household", "household2")]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame = frame[(frame.age >= 16) & frame.status.between(1, 7) & (frame.weight > 0)].copy()
    frame["weight"] = frame.weight / 10000
    year, month = map(int, path.stem.split("-"))
    frame["year"], frame["month"] = year, month
    frame["person"] = frame.household + "-" + frame.household2 + "-" + frame.line.astype(int).astype(str)
    return frame.drop(columns=["household2", "line"])


def main(cps_dir, out_path):
    frames = []
    for path in sorted(Path(cps_dir).glob("*.zip")):
        frames.append(read_month(path))
        print(path.stem, flush=True)
    out = pd.concat(frames, ignore_index=True)
    for column in ("month_in_sample", "age", "sex", "status", "reason", "occupation", "year", "month"):
        out[column] = out[column].fillna(-1).astype(np.int16)
    out.to_parquet(out_path, index=False)
    print(len(out), "person-months")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
