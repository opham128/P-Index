import pandas as pd

def normalize_name(s):
    s = str(s).strip().lower()

    if "," in s:
        last, first = [x.strip() for x in s.split(",", 1)]
        return first, last

    parts = s.split()
    if len(parts) >= 2:
        return parts[0], parts[-1]

    return "", s

def is_target_author(display_name, first_name, last_name):
    f, l = normalize_name(display_name)
    return f == first_name.strip().lower() and l == last_name.strip().lower()

def build_name_queries(first_name, last_name):
    initial = first_name[0]
    return [
        f'AU=("{last_name}, {first_name}")',
        f'AU=("{first_name} {last_name}")',
        f'AU=("{last_name} {initial}")'
    ]

def get_times_cited(x):
    citations = x.get("citations", [])
    if citations and isinstance(citations[0], dict):
        return citations[0].get("count", 0)
    return 0

def get_author_names(x):
    authors = x.get("names", {}).get("authors", [])
    if isinstance(authors, list):
        return [a.get("displayName", "") for a in authors]
    return []

def parse_record(x):
    source = x.get("source", {})
    identifiers = x.get("identifiers", {})

    return {
        "uid": x.get("uid"),
        "title": x.get("title"),
        "journal": source.get("sourceTitle"),
        "year": source.get("publishYear"),
        "times_cited": get_times_cited(x),
        "doi": identifiers.get("doi"),
        "document_types": "; ".join(x.get("types", [])),
        "source_types": "; ".join(x.get("sourceTypes", [])),
        "authors": "; ".join(get_author_names(x))
    }

def percentile_rank(c, comp):
    comp = pd.Series(comp).dropna()
    if len(comp) == 0 or pd.isna(c):
        return None

    lower = (comp < c).sum()
    equal = (comp == c).sum()
    return (lower + 0.5 * equal) / len(comp)