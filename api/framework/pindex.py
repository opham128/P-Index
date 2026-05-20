import time
import pandas as pd
import concurrent.futures

from framework.api import wos_search, get_records
from framework.utils import parse_record, percentile_rank, is_target_author

def get_author_rank_and_count(authors_str, first_name, last_name):
    if not authors_str or not isinstance(authors_str, str):
        return 1, 1
    authors = [a.strip() for a in authors_str.split(";")]
    num_authors = len(authors)
    for idx, auth in enumerate(authors):
        if is_target_author(auth, first_name, last_name):
            return idx + 1, num_authors
    return 1, num_authors

# =====================================================================
# ORIGINAL SLOW METHOD (Active)
# =====================================================================
def get_journal_year_cell(journal, year, max_pages=50, limit=50):
    rows = []

    for page in range(1, max_pages + 1):
        query = f'SO=("{journal}") AND FPY={int(year)} AND DT=("Article" OR "Review")'
        try:
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
        except Exception as e:
            print(f"Error on page {page} for {journal} {year}: {e}")
            if "WOS_RATE_LIMIT" in str(e):
                raise e
            break

        time.sleep(0.25)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["uid"], keep="first")
    df = df.drop_duplicates(subset=["title", "year"], keep="first")
    return df.reset_index(drop=True)

def compute_pindex(papers_df, first_name=None, last_name=None):
    pairs = papers_df[["journal", "year"]].dropna().drop_duplicates()
    # Filter out empty strings that were used to replace NaNs
    pairs = pairs[(pairs["journal"].astype(str).str.strip() != "") & (pairs["year"].astype(str).str.strip() != "")]

    cell_cache = {}
    for _, row in pairs.iterrows():
        journal = str(row["journal"]).strip()
        year_raw = str(row["year"]).strip().split(".")[0]  # Normalize "2021.0" -> "2021"
        key = (journal, year_raw)
        try:
            cell_cache[key] = get_journal_year_cell(journal, int(year_raw))
        except Exception as e:
            print(f"Error fetching cell for {journal} {year_raw}: {e}")
            if "WOS_RATE_LIMIT" in str(e):
                raise e
            cell_cache[key] = pd.DataFrame()

    prs = []
    cell_sizes = []
    raw_weights = []
    author_ranks = []
    num_authors_list = []

    for _, row in papers_df.iterrows():
        # Normalize key to match how it was stored in cell_cache
        journal = str(row["journal"]).strip()
        year_raw = str(row["year"]).strip().split(".")[0]
        key = (journal, year_raw)
        cell_df = cell_cache.get(key, pd.DataFrame())

        if "times_cited" in cell_df.columns and len(cell_df) > 0:
            pr = percentile_rank(row["times_cited"], cell_df["times_cited"])
            cell_size = len(cell_df)
        else:
            pr = None
            cell_size = None

        prs.append(pr)
        cell_sizes.append(cell_size)

        # Calculate raw weight if first_name and last_name are provided
        if first_name and last_name and pr is not None:
            rank, num_authors = get_author_rank_and_count(row.get("authors", ""), first_name, last_name)
            if rank is not None and num_authors is not None:
                weight = 2.0 * (num_authors - rank + 1) / (num_authors * (num_authors + 1))
                raw_weights.append(weight)
                author_ranks.append(rank)
                num_authors_list.append(num_authors)
            else:
                raw_weights.append(None)
                author_ranks.append(None)
                num_authors_list.append(None)
        else:
            raw_weights.append(None)
            author_ranks.append(None)
            num_authors_list.append(None)

    # Normalize raw weights so that their sum equals the number of papers (their average is 1.0)
    valid_weights = [w for w in raw_weights if w is not None]
    if valid_weights and len(valid_weights) > 0:
        sum_weights = sum(valid_weights)
        avg_weight = sum_weights / len(valid_weights)
        if avg_weight == 0:
            avg_weight = 1.0
        normalized_weights = [w / avg_weight if w is not None else None for w in raw_weights]
    else:
        normalized_weights = [None] * len(raw_weights)

    # Compute final weighted percentile ranks
    weighted_prs = []
    for pr, w in zip(prs, normalized_weights):
        if pr is not None and w is not None:
            weighted_prs.append(pr * w)
        else:
            weighted_prs.append(None)

    out = papers_df.copy()
    out["pr"] = prs
    out["cell_size"] = cell_sizes
    out["weight"] = normalized_weights
    out["raw_weight"] = raw_weights
    out["pr_weighted"] = weighted_prs
    out["author_rank"] = author_ranks
    out["num_authors"] = num_authors_list

    pindex = out["pr"].dropna().mean()
    pindex_weighted = out["pr_weighted"].dropna().mean() if first_name and last_name else None
    
    # Calculate total documents retrieved from the WOS API for this run
    total_docs = sum(len(df) for df in cell_cache.values())
    
    return out, pindex, pindex_weighted, total_docs


# =====================================================================
# NEW OPTIMIZED METHOD (Commented out for reference)
# =====================================================================
# def get_journal_year_cell_fast(journal, year, max_pages=2, limit=50):
#     rows = []
# 
#     for page in range(1, max_pages + 1):
#         query = f'SO=("{journal}") AND FPY={int(year)} AND DT=("Article" OR "Review")'
#         try:
#             data = wos_search(query, page=page, limit=limit)
#             records = get_records(data)
#             
#             if not records:
#                 break
# 
#             for rec in records:
#                 rows.append(parse_record(rec))
# 
#             meta = data.get("metadata", {})
#             total = meta.get("total")
# 
#             if len(records) < limit:
#                 break
#             if total is not None and page * limit >= total:
#                 break
#         except Exception as e:
#             print(f"Error on page {page} for {journal} {year}: {e}")
#             break
# 
#         time.sleep(0.25)
# 
#     df = pd.DataFrame(rows)
#     if df.empty:
#         return df
# 
#     df = df.drop_duplicates(subset=["uid"], keep="first")
#     df = df.drop_duplicates(subset=["title", "year"], keep="first")
#     return df.reset_index(drop=True)
# 
# def compute_pindex_fast(papers_df):
#     pairs = papers_df[["journal", "year"]].dropna().drop_duplicates()
#     # Filter out empty strings that were used to replace NaNs
#     pairs = pairs[(pairs["journal"].astype(str).str.strip() != "") & (pairs["year"].astype(str).str.strip() != "")]
# 
#     cell_cache = {}
#     
#     def fetch_cell(journal, year):
#         try:
#             return (journal, year), get_journal_year_cell_fast(journal, year, max_pages=2)
#         except Exception as e:
#             print(f"Error fetching cell for {journal} {year}: {e}")
#             return (journal, year), pd.DataFrame()
# 
#     with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
#         futures = [executor.submit(fetch_cell, row["journal"], row["year"]) for _, row in pairs.iterrows()]
#         for future in concurrent.futures.as_completed(futures):
#             key, cell_df = future.result()
#             cell_cache[key] = cell_df
# 
#     prs = []
#     cell_sizes = []
# 
#     for _, row in papers_df.iterrows():
#         key = (row["journal"], row["year"])
#         cell_df = cell_cache.get(key, pd.DataFrame())
# 
#         if "times_cited" in cell_df.columns and len(cell_df) > 0:
#             pr = percentile_rank(row["times_cited"], cell_df["times_cited"])
#             cell_size = len(cell_df)
#         else:
#             pr = None
#             cell_size = None
# 
#         prs.append(pr)
#         cell_sizes.append(cell_size)
# 
#     out = papers_df.copy()
#     out["pr"] = prs
#     out["cell_size"] = cell_sizes
# 
#     pindex = out["pr"].dropna().mean()
#     
#     total_docs = sum(len(df) for df in cell_cache.values())
#     return out, pindex, total_docs
