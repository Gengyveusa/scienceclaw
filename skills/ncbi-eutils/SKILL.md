---
name: ncbi-eutils
description: "Query NCBI databases via E-utilities API (esearch, efetch, esummary, elink). Search PubMed, fetch abstracts, get document summaries, and find related articles across NCBI databases. Requires NCBI_API_KEY env var for full rate limits (10 req/sec)."
license: Unknown
metadata:
    skill-author: ScienceClaw Team
---

# NCBI E-utilities

Programmatic access to NCBI's Entrez databases via E-utilities REST API. Supports searching PubMed, fetching article abstracts, retrieving document summaries, and discovering related articles across NCBI databases.

## Overview

NCBI E-utilities provide programmatic access to the Entrez system of interconnected databases including PubMed, PubMed Central, GenBank, Protein, Gene, and more. This skill wraps four core endpoints:

- **esearch** — Search any NCBI database and retrieve matching IDs
- **efetch** — Fetch full records (abstracts, sequences, etc.)
- **esummary** — Get document summaries (DocSums) for a list of IDs
- **elink** — Find related or linked records across databases

## Usage

### Search PubMed:
```bash
python3 {baseDir}/scripts/ncbi_eutils.py esearch --db pubmed --query "CRISPR gene editing" --max-results 10
```

### Fetch abstracts by PMID:
```bash
python3 {baseDir}/scripts/ncbi_eutils.py efetch --db pubmed --ids 35648464,33141092 --format json
```

### Get document summaries:
```bash
python3 {baseDir}/scripts/ncbi_eutils.py esummary --db pubmed --ids 35648464,33141092
```

### Find related articles:
```bash
python3 {baseDir}/scripts/ncbi_eutils.py elink --db pubmed --ids 35648464 --link-db pubmed
```

### Search and fetch in one step:
```bash
python3 {baseDir}/scripts/ncbi_eutils.py esearch --db pubmed --query "AlphaFold protein" --max-results 5 --fetch
```

## Parameters

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--db` | NCBI database name (pubmed, protein, gene, etc.) | pubmed |
| `--format` | Output format: summary, json | summary |

### esearch Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--query` | Search query (supports Entrez syntax) | Required |
| `--max-results` | Maximum number of results | 10 |
| `--sort` | Sort order (relevance, date, first_author) | relevance |
| `--fetch` | Also fetch full records for results | false |

### efetch Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--ids` | Comma-separated list of IDs | Required |

### esummary Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--ids` | Comma-separated list of IDs | Required |

### elink Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--ids` | Comma-separated list of IDs | Required |
| `--link-db` | Target database for links | same as --db |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NCBI_API_KEY` | NCBI API key for 10 req/sec rate limit (3 req/sec without) |
| `NCBI_EMAIL` | Contact email for NCBI (recommended) |

## Notes

- Set `NCBI_API_KEY` for 10 requests/second (vs 3/second without)
- Rate limiting and exponential backoff are built in
- Supports all NCBI Entrez databases (pubmed, protein, nucleotide, gene, etc.)
- Search queries support full Entrez/PubMed syntax including field tags and boolean operators
