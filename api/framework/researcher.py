import time
import pandas as pd
from collections import Counter

from framework.api import wos_search, get_records
from framework.utils import build_name_queries, is_target_author, parse_record

def find_researcher_ids(first_name, last_name, org=None, max_pages=5, limit=10):
    rows = []
    counter = Counter()
    queries = build_name_queries(first_name, last_name, org=org)

    for query in queries:
        for page in range(1, max_pages + 1):
            data = wos_search(query, page=page, limit=limit)
            records = get_records(data)

            if not records:
                break

            for rec in records:
                authors = rec.get("names", {}).get("authors", [])
                title = rec.get("title")
                uid = rec.get("uid")

                for a in authors:
                    display_name = a.get("displayName", "")
                    rid = a.get("researcherId")

                    if is_target_author(display_name, first_name, last_name):
                        # WOS returns "Last, First" — convert to "First Last"
                        if "," in display_name:
                            parts = display_name.split(",", 1)
                            formatted_name = f"{parts[1].strip()} {parts[0].strip()}"
                        else:
                            formatted_name = display_name
                        rows.append({
                            "uid": uid,
                            "title": title,
                            "display_name": formatted_name,
                            "researcher_id": rid
                        })
                        if rid:
                            counter[rid] += 1

            meta = data.get("metadata", {})
            total = meta.get("total")

            if len(records) < limit:
                break
            if total is not None and page * limit >= total:
                break

            time.sleep(0.25)

    df = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    return df, counter

def keep_target_author(df, first_name, last_name):
    if df.empty:
        return df

    def has_target(authors_str):
        parts = [x.strip() for x in str(authors_str).split(";")]
        return any(is_target_author(p, first_name, last_name) for p in parts)

    return df[df["authors"].apply(has_target)].reset_index(drop=True)

_papers_cache = {}

def get_papers_by_researcher_id(researcher_id, max_pages=20, limit=50):
    if researcher_id in _papers_cache:
        return _papers_cache[researcher_id].copy()

    rows = []
    seen = set()
    query = f'AI=("{researcher_id}")'

    for page in range(1, max_pages + 1):
        data = wos_search(query, page=page, limit=limit)
        records = get_records(data)

        if not records:
            break

        for rec in records:
            row = parse_record(rec)
            uid = row["uid"]
            if uid not in seen:
                rows.append(row)
                seen.add(uid)

        meta = data.get("metadata", {})
        total = meta.get("total")

        if len(records) < limit:
            break
        if total is not None and page * limit >= total:
            break

        time.sleep(0.25)

    df = pd.DataFrame(rows)
    if df.empty:
        _papers_cache[researcher_id] = df.copy()
        return df

    df = df.drop_duplicates(subset=["uid"], keep="first")
    result_df = df.reset_index(drop=True)
    _papers_cache[researcher_id] = result_df.copy()
    return result_df