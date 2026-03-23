#!/usr/bin/env python3
"""
NCBI E-utilities Tool for ScienceClaw

Provides programmatic access to NCBI databases via E-utilities REST API.
Supports esearch, efetch, esummary, and elink endpoints with built-in
rate limiting (10 req/sec with API key, 3 req/sec without) and error handling.

Environment variables:
    NCBI_API_KEY  - API key for higher rate limits (get from https://www.ncbi.nlm.nih.gov/account/settings/)
    NCBI_EMAIL    - Contact email (recommended by NCBI)
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import requests


# ── Configuration ────────────────────────────────────────────────────────────

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "scienceclaw@example.com")


# ── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Token-bucket style rate limiter for NCBI E-utilities."""

    def __init__(self, requests_per_second: float = 3.0):
        self.min_delay = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait(self):
        """Block until it's safe to make the next request."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()


# 10 req/sec with API key, 3 req/sec without (NCBI policy)
_rate_limit = RateLimiter(10.0 if NCBI_API_KEY else 3.0)


# ── HTTP helpers ─────────────────────────────────────────────────────────────

def _base_params() -> Dict[str, str]:
    """Return common params shared by all E-utilities requests."""
    params: Dict[str, str] = {}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL
    return params


def _eutils_get(
    endpoint: str,
    params: Dict[str, str],
    max_retries: int = 4,
    timeout: int = 30,
) -> requests.Response:
    """
    Make a GET request to an E-utilities endpoint with rate limiting
    and exponential backoff on transient errors.
    """
    url = f"{EUTILS_BASE}/{endpoint}"
    params = {**_base_params(), **params}

    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        _rate_limit.wait()
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429 or resp.status_code >= 500:
                # Transient — retry with backoff
                wait = 2 ** attempt
                print(
                    f"NCBI returned {resp.status_code}; retrying in {wait}s "
                    f"(attempt {attempt + 1}/{max_retries})...",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            # Non-retryable error
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            wait = 2 ** attempt
            print(
                f"Request error: {exc}; retrying in {wait}s "
                f"(attempt {attempt + 1}/{max_retries})...",
                file=sys.stderr,
            )
            time.sleep(wait)

    raise RuntimeError(
        f"NCBI E-utilities request failed after {max_retries} attempts"
        + (f": {last_exc}" if last_exc else "")
    )


# ── esearch ──────────────────────────────────────────────────────────────────

def esearch(
    db: str,
    query: str,
    max_results: int = 10,
    sort: str = "relevance",
) -> Dict[str, Any]:
    """
    Search an NCBI database and return matching IDs.

    Returns dict with keys: count, ids, query_translation
    """
    params = {
        "db": db,
        "term": query,
        "retmax": str(max_results),
        "sort": sort,
        "retmode": "json",
    }
    resp = _eutils_get("esearch.fcgi", params)
    data = resp.json()

    result = data.get("esearchresult", {})
    return {
        "count": int(result.get("count", 0)),
        "ids": result.get("idlist", []),
        "query_translation": result.get("querytranslation", ""),
    }


# ── efetch ───────────────────────────────────────────────────────────────────

def efetch(db: str, ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch full records from NCBI.

    For pubmed, parses XML and returns structured article dicts.
    For other dbs, returns raw text per record.
    """
    if not ids:
        return []

    params = {
        "db": db,
        "id": ",".join(ids),
        "retmode": "xml",
    }
    resp = _eutils_get("efetch.fcgi", params)

    if db == "pubmed":
        return _parse_pubmed_xml(resp.text)

    # Generic: return raw text split by ID
    return [{"id": uid, "data": resp.text} for uid in ids]


def _parse_pubmed_xml(xml_text: str) -> List[Dict[str, Any]]:
    """Parse PubMed efetch XML into structured article dicts."""
    articles: List[Dict[str, Any]] = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return [{"error": "Failed to parse PubMed XML", "raw": xml_text[:500]}]

    for pa in root.findall(".//PubmedArticle"):
        mc = pa.find("MedlineCitation")
        if mc is None:
            continue

        pmid_el = mc.find("PMID")
        pmid = pmid_el.text if pmid_el is not None else ""

        article_el = mc.find("Article")
        if article_el is None:
            articles.append({"pmid": pmid})
            continue

        # Title
        title_el = article_el.find("ArticleTitle")
        title = _text_or(title_el, "")

        # Abstract
        abstract_parts = []
        abs_el = article_el.find("Abstract")
        if abs_el is not None:
            for at in abs_el.findall("AbstractText"):
                label = at.get("Label", "")
                text = "".join(at.itertext())
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        abstract = " ".join(abstract_parts)

        # Authors
        authors = []
        for auth in article_el.findall(".//Author"):
            last = _text_or(auth.find("LastName"), "")
            initials = _text_or(auth.find("Initials"), "")
            if last:
                authors.append(f"{last} {initials}".strip())

        # Journal
        journal_el = article_el.find("Journal")
        journal = ""
        year = ""
        volume = ""
        issue = ""
        if journal_el is not None:
            journal = _text_or(journal_el.find("Title"), "")
            ji = journal_el.find("JournalIssue")
            if ji is not None:
                volume = _text_or(ji.find("Volume"), "")
                issue = _text_or(ji.find("Issue"), "")
                pd = ji.find("PubDate")
                if pd is not None:
                    year = _text_or(pd.find("Year"), "")

        # DOI
        doi = ""
        pd_el = pa.find("PubmedData")
        if pd_el is not None:
            for aid in pd_el.findall(".//ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = aid.text or ""
                    break

        # MeSH terms
        mesh_terms = []
        for mh in mc.findall(".//MeshHeading/DescriptorName"):
            if mh.text:
                mesh_terms.append(mh.text)

        # Keywords
        keywords = []
        for kw in mc.findall(".//Keyword"):
            if kw.text:
                keywords.append(kw.text)

        articles.append({
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": journal,
            "year": year,
            "volume": volume,
            "issue": issue,
            "doi": doi,
            "mesh_terms": mesh_terms,
            "keywords": keywords,
        })

    return articles


def _text_or(el, default: str = "") -> str:
    """Extract text from an XML element, or return default."""
    if el is None:
        return default
    return "".join(el.itertext()) or default


# ── esummary ─────────────────────────────────────────────────────────────────

def esummary(db: str, ids: List[str]) -> List[Dict[str, Any]]:
    """
    Get document summaries (DocSums) for a list of UIDs.
    """
    if not ids:
        return []

    params = {
        "db": db,
        "id": ",".join(ids),
        "retmode": "json",
    }
    resp = _eutils_get("esummary.fcgi", params)
    data = resp.json()

    result = data.get("result", {})
    uid_list = result.get("uids", ids)

    summaries = []
    for uid in uid_list:
        doc = result.get(uid, {})
        if doc:
            doc["uid"] = uid
            summaries.append(doc)

    return summaries


# ── elink ────────────────────────────────────────────────────────────────────

def elink(
    db: str,
    ids: List[str],
    link_db: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Find related or linked records across NCBI databases.

    Args:
        db: Source database
        ids: Source UIDs
        link_db: Target database (defaults to same as source for related records)
    """
    if not ids:
        return []

    params = {
        "dbfrom": db,
        "db": link_db or db,
        "id": ",".join(ids),
        "retmode": "json",
    }
    resp = _eutils_get("elink.fcgi", params)
    data = resp.json()

    links: List[Dict[str, Any]] = []
    for linkset in data.get("linksets", []):
        source_ids = linkset.get("ids", [])
        link_groups = linkset.get("linksetdbs", [])
        for lg in link_groups:
            links.append({
                "source_ids": source_ids,
                "link_name": lg.get("linkname", ""),
                "target_db": lg.get("dbto", ""),
                "linked_ids": [str(lid) for lid in lg.get("links", [])],
            })

    return links


# ── Formatters ───────────────────────────────────────────────────────────────

def format_esearch(result: Dict[str, Any]) -> str:
    lines = [
        f"Search returned {result['count']} total results.",
        f"Returning {len(result['ids'])} IDs: {', '.join(result['ids'])}",
    ]
    if result.get("query_translation"):
        lines.append(f"Query translation: {result['query_translation']}")
    return "\n".join(lines)


def format_articles(articles: List[Dict[str, Any]]) -> str:
    if not articles:
        return "No articles found."
    lines = [f"Fetched {len(articles)} article(s):\n" + "-" * 80]
    for i, a in enumerate(articles, 1):
        authors_str = ", ".join(a.get("authors", [])[:3])
        if len(a.get("authors", [])) > 3:
            authors_str += " et al."
        lines.append(f"\n{i}. {a.get('title', 'N/A')}")
        lines.append(f"   Authors: {authors_str}")
        lines.append(f"   {a.get('journal', '')} ({a.get('year', '')})")
        lines.append(f"   PMID: {a.get('pmid', '')}")
        if a.get("doi"):
            lines.append(f"   DOI: {a['doi']}")
        if a.get("abstract"):
            abstract = a["abstract"]
            if len(abstract) > 300:
                abstract = abstract[:300] + "..."
            lines.append(f"   Abstract: {abstract}")
    lines.append("\n" + "-" * 80)
    return "\n".join(lines)


def format_summaries(summaries: List[Dict[str, Any]]) -> str:
    if not summaries:
        return "No summaries found."
    lines = [f"Document summaries ({len(summaries)}):\n" + "-" * 80]
    for i, s in enumerate(summaries, 1):
        uid = s.get("uid", "?")
        title = s.get("title", s.get("Title", "N/A"))
        source = s.get("source", s.get("fulljournalname", ""))
        pubdate = s.get("pubdate", s.get("epubdate", ""))
        lines.append(f"\n{i}. [{uid}] {title}")
        if source:
            lines.append(f"   Source: {source}")
        if pubdate:
            lines.append(f"   Date: {pubdate}")
    lines.append("\n" + "-" * 80)
    return "\n".join(lines)


def format_links(links: List[Dict[str, Any]]) -> str:
    if not links:
        return "No links found."
    lines = [f"Found {len(links)} link group(s):\n" + "-" * 80]
    for i, lg in enumerate(links, 1):
        lines.append(
            f"\n{i}. {lg['link_name']} → {lg['target_db']} "
            f"({len(lg['linked_ids'])} linked records)"
        )
        if lg["linked_ids"]:
            sample = lg["linked_ids"][:10]
            lines.append(f"   IDs: {', '.join(sample)}")
            if len(lg["linked_ids"]) > 10:
                lines.append(f"   ... and {len(lg['linked_ids']) - 10} more")
    lines.append("\n" + "-" * 80)
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NCBI E-utilities: search, fetch, summarize, and link NCBI records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s esearch --db pubmed --query "CRISPR gene editing" --max-results 10
  %(prog)s efetch  --db pubmed --ids 35648464,33141092
  %(prog)s esummary --db pubmed --ids 35648464
  %(prog)s elink  --db pubmed --ids 35648464 --link-db pmc
  %(prog)s esearch --db pubmed --query "AlphaFold" --fetch --format json
""",
    )
    sub = parser.add_subparsers(dest="command", help="E-utility endpoint")

    # esearch
    p_search = sub.add_parser("esearch", help="Search an NCBI database")
    p_search.add_argument("--db", default="pubmed", help="Database (default: pubmed)")
    p_search.add_argument("--query", "-q", required=True, help="Search query")
    p_search.add_argument("--max-results", "-m", type=int, default=10, help="Max results (default: 10)")
    p_search.add_argument("--sort", "-s", default="relevance", help="Sort order")
    p_search.add_argument("--fetch", action="store_true", help="Also fetch full records")
    p_search.add_argument("--format", "-f", default="summary", choices=["summary", "json"], help="Output format")

    # efetch
    p_fetch = sub.add_parser("efetch", help="Fetch full records by ID")
    p_fetch.add_argument("--db", default="pubmed", help="Database (default: pubmed)")
    p_fetch.add_argument("--ids", required=True, help="Comma-separated IDs")
    p_fetch.add_argument("--format", "-f", default="summary", choices=["summary", "json"], help="Output format")

    # esummary
    p_sum = sub.add_parser("esummary", help="Get document summaries")
    p_sum.add_argument("--db", default="pubmed", help="Database (default: pubmed)")
    p_sum.add_argument("--ids", required=True, help="Comma-separated IDs")
    p_sum.add_argument("--format", "-f", default="summary", choices=["summary", "json"], help="Output format")

    # elink
    p_link = sub.add_parser("elink", help="Find related/linked records")
    p_link.add_argument("--db", default="pubmed", help="Source database (default: pubmed)")
    p_link.add_argument("--ids", required=True, help="Comma-separated source IDs")
    p_link.add_argument("--link-db", default=None, help="Target database (default: same as --db)")
    p_link.add_argument("--format", "-f", default="summary", choices=["summary", "json"], help="Output format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "esearch":
            result = esearch(
                db=args.db,
                query=args.query,
                max_results=args.max_results,
                sort=args.sort,
            )
            if args.fetch and result["ids"]:
                articles = efetch(args.db, result["ids"])
                if args.format == "json":
                    print(json.dumps({"search": result, "articles": articles}, indent=2))
                else:
                    print(format_esearch(result))
                    print()
                    print(format_articles(articles))
            else:
                if args.format == "json":
                    print(json.dumps(result, indent=2))
                else:
                    print(format_esearch(result))

        elif args.command == "efetch":
            id_list = [i.strip() for i in args.ids.split(",") if i.strip()]
            articles = efetch(args.db, id_list)
            if args.format == "json":
                print(json.dumps(articles, indent=2))
            else:
                print(format_articles(articles))

        elif args.command == "esummary":
            id_list = [i.strip() for i in args.ids.split(",") if i.strip()]
            summaries = esummary(args.db, id_list)
            if args.format == "json":
                print(json.dumps(summaries, indent=2))
            else:
                print(format_summaries(summaries))

        elif args.command == "elink":
            id_list = [i.strip() for i in args.ids.split(",") if i.strip()]
            links = elink(args.db, id_list, link_db=args.link_db)
            if args.format == "json":
                print(json.dumps(links, indent=2))
            else:
                print(format_links(links))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
