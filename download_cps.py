import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URL = "https://www2.census.gov/programs-surveys/cps/datasets/{year}/basic/{mon}{yy}pub.zip"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def fetch(job):
    year, month, out_dir = job
    path = Path(out_dir) / f"{year}-{month + 1:02d}.zip"
    if path.exists():
        return None
    url = URL.format(year=year, mon=MONTHS[month], yy=str(year)[2:])
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=300).read()
    except Exception as exc:
        return f"{year}-{month + 1:02d} {exc}"
    path.write_bytes(data)
    return None


def main(first_year, last_year, out_dir):
    jobs = [(y, m, out_dir) for y in range(first_year, last_year + 1) for m in range(12)]
    with ThreadPoolExecutor(4) as pool:
        missing = [r for r in pool.map(fetch, jobs) if r]
    print("missing:", missing)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
