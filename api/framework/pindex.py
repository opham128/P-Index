import time
import pandas as pd

from framework.api import wos_search, get_records
from framework.utils import parse_record, percentile_rank

def get_journal_year_cell(journal, year, max_pages=50, limit=50):
    rows = []

    for page in range(1, max_pages + 1):
        query = f'SO=("{journal}") AND FPY={int(year)} AND DT=("Article" OR "Review")'
        data = wos_search(query, page=page, limit=limit)
        records = get_records(data)

        if not records:
            break

        for rec in records:
            rows.append(parse_record(rec))

        meta = data.get("metadata", {})
        total = meta.get("total")

        if len(records) < limit:
            break
        if total is not None and page * limit >= total:
            break

        time.sleep(0.25)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["uid"], keep="first")
    df = df.drop_duplicates(subset=["title", "year"], keep="first")
    return df.reset_index(drop=True)

def compute_pindex(papers_df):
    pairs = papers_df[["journal", "year"]].dropna().drop_duplicates()

    cell_cache = {}
    for _, row in pairs.iterrows():
        key = (row["journal"], row["year"])
        cell_cache[key] = get_journal_year_cell(row["journal"], row["year"])

    prs = []
    cell_sizes = []

    for _, row in papers_df.iterrows():
        key = (row["journal"], row["year"])
        cell_df = cell_cache.get(key, pd.DataFrame())

        if "times_cited" in cell_df.columns and len(cell_df) > 0:
            pr = percentile_rank(row["times_cited"], cell_df["times_cited"])
            cell_size = len(cell_df)
        else:
            pr = None
            cell_size = None

        prs.append(pr)
        cell_sizes.append(cell_size)

    out = papers_df.copy()
    out["pr"] = prs
    out["cell_size"] = cell_sizes

    pindex = out["pr"].dropna().mean()
    return out, pindex