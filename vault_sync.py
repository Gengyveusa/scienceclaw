#!/usr/bin/env python3
"""
Vault Sync — export ScienceClaw artifacts to an Obsidian-compatible vault.

Generates markdown files with rich YAML frontmatter, [[wikilinks]] between
related artifacts, and Dataview-compatible metadata for queries.

Usage:
    python3 vault_sync.py                          # Sync all agents
    python3 vault_sync.py --agent QuantumBioAgent-1 # Sync one agent
    python3 vault_sync.py --vault ~/ObsidianVault   # Custom vault path
    python3 vault_sync.py --digest                  # Generate daily digest only

Author: ScienceClaw Team
"""

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCIENCECLAW_DIR = Path(os.path.expanduser("~/.scienceclaw"))
DEFAULT_VAULT_DIR = Path(os.path.expanduser("~/.scienceclaw/vault"))

# Content-based auto-tag rules: pattern → tag
AUTO_TAG_RULES = {
    r"quantum\s+(biology|coherence|tunneling|entanglement)": "quantum-biology",
    r"mitochondri": "mitochondria",
    r"electron\s+transport\s+chain|respiratory\s+chain": "electron-transport-chain",
    r"Complex\s+I\b|NADH.ubiquinone\s+oxidoreductase": "Complex-I",
    r"Complex\s+II\b|succinate\s+dehydrogenase": "Complex-II",
    r"Complex\s+III\b|cytochrome\s+bc1": "Complex-III",
    r"Complex\s+IV\b|cytochrome\s+c\s+oxidase": "Complex-IV",
    r"ATP\s+synthase|Complex\s+V": "ATP-synthase",
    r"proton\s+tunnel": "proton-tunneling",
    r"membrane\s+potential": "membrane-potential",
    r"reactive\s+oxygen\s+species|\bROS\b": "reactive-oxygen-species",
    r"oxidative\s+phosphorylation": "oxidative-phosphorylation",
    r"spectroscop(y|ic)": "spectroscopy",
    r"raman\s+spectroscop": "raman-spectroscopy",
    r"fluorescen(ce|t)": "fluorescence",
    r"\bNADH\b": "NADH",
    r"\bFAD\b": "FAD",
    r"\bATP\b": "ATP",
    r"\bGSH\b|glutathione": "GSH",
    r"FLIM|fluorescence\s+lifetime": "FLIM",
    r"SERS|surface.enhanced.raman": "SERS",
    r"JC-1|TMRM|MitoTracker": "membrane-potential-probe",
    r"cytochrome\s+c\b": "cytochrome-c",
    r"electron\s+transport": "electron-transport",
    r"mitochondrial\s+disease|mitochondrial\s+dysfunction": "mitochondrial-disease",
    r"neurodegenerat|Parkinson|Alzheimer": "neurodegeneration",
    r"aging|senescen": "aging",
    r"drug\s+discovery": "drug-discovery",
    r"protein\s+structure|protein\s+folding": "protein-structure",
    r"machine\s+learning|deep\s+learning": "machine-learning",
    r"CRISPR": "CRISPR",
    r"single.cell": "single-cell",
    r"metabolom": "metabolomics",
    r"genomic|transcriptom": "genomics",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_filename(text: str) -> str:
    """Convert text to a safe filename component."""
    safe = re.sub(r"[^\w\s-]", "", text)
    safe = re.sub(r"\s+", "_", safe.strip())
    return safe[:80]


def _extract_text_content(artifact: dict) -> str:
    """Extract searchable text from an artifact payload for auto-tagging."""
    payload = artifact.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    parts = []
    for key in ("title", "abstract", "summary", "description", "query",
                 "content", "text", "name", "topic"):
        val = payload.get(key, "")
        if isinstance(val, str):
            parts.append(val)
    # Recurse one level into list results
    for key in ("results", "articles", "entries", "items", "hits"):
        items = payload.get(key, [])
        if isinstance(items, list):
            for item in items[:10]:  # Limit for performance
                if isinstance(item, dict):
                    for subkey in ("title", "abstract", "summary", "name"):
                        val = item.get(subkey, "")
                        if isinstance(val, str):
                            parts.append(val)
    return " ".join(parts)


def _auto_tag(text: str) -> List[str]:
    """Apply regex-based auto-tagging rules to text content."""
    tags = []
    text_lower = text.lower()
    for pattern, tag in AUTO_TAG_RULES.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            tags.append(tag)
    return sorted(set(tags))


def _compute_confidence(artifact: dict) -> float:
    """
    Heuristic confidence score (0.0 - 1.0) based on artifact quality signals.
    """
    score = 0.5  # baseline
    quality = artifact.get("result_quality", "ok")
    if quality == "ok":
        score += 0.2
    elif quality == "empty":
        score -= 0.3
    elif quality == "irrelevant":
        score -= 0.4

    payload = artifact.get("payload", {})
    if isinstance(payload, dict):
        # More results = higher confidence
        for key in ("results", "articles", "entries", "items", "hits"):
            items = payload.get(key, [])
            if isinstance(items, list) and len(items) > 0:
                score += min(0.2, len(items) * 0.02)
                break
        # Has content hash = verified
        if artifact.get("content_hash"):
            score += 0.1

    return round(max(0.0, min(1.0, score)), 2)


def _load_artifacts(agent_name: str) -> List[dict]:
    """Load all artifacts for an agent from store.jsonl."""
    store_path = SCIENCECLAW_DIR / "artifacts" / agent_name / "store.jsonl"
    if not store_path.exists():
        return []
    artifacts = []
    for line in store_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            artifacts.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return artifacts


def _load_global_index() -> List[dict]:
    """Load the global artifact index."""
    index_path = SCIENCECLAW_DIR / "artifacts" / "global_index.jsonl"
    if not index_path.exists():
        return []
    entries = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _discover_agents() -> List[str]:
    """Find all agent names that have artifact stores."""
    artifacts_dir = SCIENCECLAW_DIR / "artifacts"
    if not artifacts_dir.exists():
        return []
    agents = []
    for d in sorted(artifacts_dir.iterdir()):
        if d.is_dir() and (d / "store.jsonl").exists():
            agents.append(d.name)
    return agents


def _find_related_artifacts(
    artifact: dict,
    all_artifacts: List[dict],
    index_by_investigation: Dict[str, List[dict]],
) -> List[Tuple[str, str]]:
    """
    Find artifacts related to this one. Returns list of (artifact_id, relation_type).
    Relations: parent, child, sibling (same investigation), cross-agent.
    """
    related = []
    aid = artifact.get("artifact_id", "")
    inv_id = artifact.get("investigation_id", "")

    # Parents
    for pid in artifact.get("parent_artifact_ids", []):
        related.append((pid, "parent"))

    # Children (artifacts that list this as parent)
    for other in all_artifacts:
        if aid in other.get("parent_artifact_ids", []):
            related.append((other["artifact_id"], "child"))

    # Siblings (same investigation, different artifact)
    if inv_id:
        for sibling in index_by_investigation.get(inv_id, []):
            sid = sibling.get("artifact_id", "")
            if sid != aid and (sid, "sibling") not in related:
                related.append((sid, "sibling"))

    return related


def _detect_contradictions(
    artifacts: List[dict],
) -> List[Dict]:
    """
    Detect potential contradictions: artifacts from different agents on the
    same investigation_id with different result_quality or conflicting signals.
    """
    by_investigation: Dict[str, List[dict]] = defaultdict(list)
    for a in artifacts:
        inv_id = a.get("investigation_id", "")
        if inv_id:
            by_investigation[inv_id].append(a)

    contradictions = []
    for inv_id, group in by_investigation.items():
        agents = set(a.get("producer_agent", "") for a in group)
        if len(agents) < 2:
            continue
        # Check for quality disagreements
        qualities = defaultdict(list)
        for a in group:
            qualities[a.get("result_quality", "ok")].append(a)
        if len(qualities) > 1 and "irrelevant" in qualities:
            contradictions.append({
                "investigation_id": inv_id,
                "type": "quality_disagreement",
                "agents": sorted(agents),
                "details": (
                    f"Some agents found relevant results while others marked "
                    f"findings as irrelevant for investigation '{inv_id}'"
                ),
                "artifact_ids": [a["artifact_id"] for a in group],
            })

    return contradictions


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def generate_artifact_markdown(
    artifact: dict,
    related: List[Tuple[str, str]],
    artifact_filenames: Dict[str, str],
) -> str:
    """Generate a full markdown file for a single artifact."""
    aid = artifact.get("artifact_id", "")
    agent = artifact.get("producer_agent", "unknown")
    skill = artifact.get("skill_used", "unknown")
    inv_id = artifact.get("investigation_id", "")
    timestamp = artifact.get("timestamp", "")
    a_type = artifact.get("artifact_type", "raw_output")
    quality = artifact.get("result_quality", "ok")
    content_hash = artifact.get("content_hash", "")
    parent_ids = artifact.get("parent_artifact_ids", [])

    text_content = _extract_text_content(artifact)
    tags = _auto_tag(text_content)
    confidence = _compute_confidence(artifact)

    # Determine source databases from skill
    source_dbs = [skill]
    payload = artifact.get("payload", {})
    if isinstance(payload, dict) and "source" in payload:
        source_dbs.append(str(payload["source"]))

    # Related agent names
    related_agents = set()
    for rid, rtype in related:
        if rid in artifact_filenames:
            # We don't have the full artifact here, but we know about relations
            related_agents.add(rtype)

    # YAML frontmatter
    frontmatter_lines = [
        "---",
        f"artifact_id: \"{aid}\"",
        f"agent_name: \"{agent}\"",
        f"investigation_id: \"{inv_id}\"",
        f"timestamp: {timestamp}",
        f"artifact_type: \"{a_type}\"",
        f"skill_used: \"{skill}\"",
        f"result_quality: \"{quality}\"",
        f"confidence_score: {confidence}",
        f"content_hash: \"{content_hash}\"",
        f"source_databases: [{', '.join(repr(s) for s in source_dbs)}]",
        f"tags: [{', '.join(repr(t) for t in tags)}]",
        f"related_agents: [{', '.join(repr(a) for a in sorted(related_agents))}]",
        f"parent_artifact_ids: [{', '.join(repr(p) for p in parent_ids)}]",
        "---",
    ]
    frontmatter = "\n".join(frontmatter_lines)

    # Title
    title = f"# {a_type} — {skill}"
    if inv_id:
        title += f" ({inv_id})"

    # Wikilinks section
    wikilinks_section = ""
    if related:
        links = []
        for rid, rtype in related:
            fname = artifact_filenames.get(rid, rid)
            links.append(f"- {rtype}: [[{fname}]]")
        wikilinks_section = "\n## Related Artifacts\n" + "\n".join(links)

    # Metadata section (Dataview-compatible inline fields)
    dataview_section = "\n".join([
        "\n## Metadata",
        f"agent:: {agent}",
        f"investigation:: {inv_id}",
        f"skill:: {skill}",
        f"type:: {a_type}",
        f"quality:: {quality}",
        f"confidence:: {confidence}",
        f"date:: {timestamp[:10] if timestamp else 'unknown'}",
    ])

    # Tags section
    tags_section = ""
    if tags:
        tags_section = "\n## Tags\n" + " ".join(f"#{t}" for t in tags)

    # Content summary
    content_section = "\n## Content Summary\n"
    if isinstance(payload, dict):
        # Extract key information
        for key in ("title", "query", "topic", "name"):
            if key in payload and isinstance(payload[key], str):
                content_section += f"**{key.title()}**: {payload[key]}\n\n"

        # List results if present
        for key in ("results", "articles", "entries", "items"):
            items = payload.get(key, [])
            if isinstance(items, list) and items:
                content_section += f"### {key.title()} ({len(items)} found)\n\n"
                for i, item in enumerate(items[:5], 1):
                    if isinstance(item, dict):
                        item_title = item.get("title", item.get("name", f"Item {i}"))
                        content_section += f"{i}. {item_title}\n"
                if len(items) > 5:
                    content_section += f"\n*...and {len(items) - 5} more*\n"
                break
    else:
        content_section += "*No structured content available*\n"

    # Needs section (broadcast signals)
    needs = artifact.get("needs", [])
    needs_section = ""
    if needs:
        needs_section = "\n## Open Needs\n"
        for need in needs:
            if isinstance(need, dict):
                n_type = need.get("artifact_type", "unknown")
                n_query = need.get("query", "")
                needs_section += f"- **{n_type}**: {n_query}\n"

    return "\n".join(filter(None, [
        frontmatter,
        "",
        title,
        dataview_section,
        tags_section,
        wikilinks_section,
        content_section,
        needs_section,
    ]))


def generate_daily_digest(
    date_str: str,
    all_artifacts: List[dict],
    contradictions: List[Dict],
) -> str:
    """Generate a daily digest markdown summarizing all agent activity."""
    # Filter artifacts for this date
    todays = [a for a in all_artifacts if a.get("timestamp", "").startswith(date_str)]

    if not todays:
        return f"---\ndate: {date_str}\ntype: daily-digest\n---\n\n# Daily Digest — {date_str}\n\nNo agent activity recorded.\n"

    # Group by agent
    by_agent: Dict[str, List[dict]] = defaultdict(list)
    for a in todays:
        by_agent[a.get("producer_agent", "unknown")].append(a)

    # Group by investigation
    by_investigation: Dict[str, List[dict]] = defaultdict(list)
    for a in todays:
        inv_id = a.get("investigation_id", "uncategorized")
        by_investigation[inv_id].append(a)

    # Collect all tags
    all_tags: Set[str] = set()
    for a in todays:
        text = _extract_text_content(a)
        all_tags.update(_auto_tag(text))

    # Build frontmatter
    frontmatter = "\n".join([
        "---",
        f"date: {date_str}",
        "type: daily-digest",
        f"total_artifacts: {len(todays)}",
        f"active_agents: [{', '.join(repr(a) for a in sorted(by_agent.keys()))}]",
        f"investigations: [{', '.join(repr(i) for i in sorted(by_investigation.keys()))}]",
        f"tags: [{', '.join(repr(t) for t in sorted(all_tags))}]",
        f"contradictions_detected: {len(contradictions)}",
        "---",
    ])

    sections = [
        frontmatter,
        "",
        f"# Daily Digest — {date_str}",
        "",
        f"**Total artifacts**: {len(todays)}  ",
        f"**Active agents**: {len(by_agent)}  ",
        f"**Investigations**: {len(by_investigation)}",
        "",
    ]

    # Agent summaries
    sections.append("## Agent Activity\n")
    for agent_name in sorted(by_agent.keys()):
        agent_artifacts = by_agent[agent_name]
        skills_used = set(a.get("skill_used", "") for a in agent_artifacts)
        sections.append(f"### {agent_name}")
        sections.append(f"- Artifacts produced: {len(agent_artifacts)}")
        sections.append(f"- Skills used: {', '.join(sorted(skills_used))}")
        sections.append("")

    # Investigation summaries
    sections.append("## Investigations\n")
    for inv_id in sorted(by_investigation.keys()):
        inv_artifacts = by_investigation[inv_id]
        agents = sorted(set(a.get("producer_agent", "") for a in inv_artifacts))
        sections.append(f"### {inv_id}")
        sections.append(f"- Artifacts: {len(inv_artifacts)}")
        sections.append(f"- Contributing agents: {', '.join(agents)}")
        sections.append("")

    # Contradictions
    if contradictions:
        sections.append("## Contradictions Detected\n")
        for c in contradictions:
            sections.append(f"### {c['investigation_id']}")
            sections.append(f"- **Type**: {c['type']}")
            sections.append(f"- **Agents**: {', '.join(c['agents'])}")
            sections.append(f"- **Details**: {c['details']}")
            sections.append("")

    # Tags cloud
    if all_tags:
        sections.append("## Topics\n")
        sections.append(" ".join(f"#{t}" for t in sorted(all_tags)))
        sections.append("")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------

def sync_vault(
    vault_dir: Path,
    agent_filter: Optional[str] = None,
    generate_digest: bool = True,
) -> Dict[str, int]:
    """
    Sync all artifacts to the Obsidian vault directory.

    Returns dict with sync statistics.
    """
    vault_dir.mkdir(parents=True, exist_ok=True)

    agents = [agent_filter] if agent_filter else _discover_agents()
    if not agents:
        print("No agents with artifacts found.")
        return {"agents": 0, "artifacts": 0}

    # Load all artifacts across agents
    all_artifacts: List[dict] = []
    for agent_name in agents:
        all_artifacts.extend(_load_artifacts(agent_name))

    # Build investigation index
    index_by_investigation: Dict[str, List[dict]] = defaultdict(list)
    for a in all_artifacts:
        inv_id = a.get("investigation_id", "")
        if inv_id:
            index_by_investigation[inv_id].append(a)

    # Generate filenames for wikilinks
    artifact_filenames: Dict[str, str] = {}
    for a in all_artifacts:
        aid = a.get("artifact_id", "")
        agent = _safe_filename(a.get("producer_agent", "unknown"))
        skill = _safe_filename(a.get("skill_used", "unknown"))
        short_id = aid[:8]
        artifact_filenames[aid] = f"{agent}_{skill}_{short_id}"

    # Sync artifacts per agent
    total_synced = 0
    for agent_name in agents:
        agent_dir = vault_dir / _safe_filename(agent_name)
        agent_dir.mkdir(parents=True, exist_ok=True)

        agent_artifacts = _load_artifacts(agent_name)
        for artifact in agent_artifacts:
            aid = artifact.get("artifact_id", "")
            fname = artifact_filenames.get(aid, aid[:8])

            related = _find_related_artifacts(
                artifact, all_artifacts, index_by_investigation
            )

            md_content = generate_artifact_markdown(
                artifact, related, artifact_filenames
            )

            md_path = agent_dir / f"{fname}.md"
            md_path.write_text(md_content, encoding="utf-8")
            total_synced += 1

        print(f"  Synced {len(agent_artifacts)} artifacts for {agent_name}")

    # Detect contradictions
    contradictions = _detect_contradictions(all_artifacts)
    if contradictions:
        print(f"  Detected {len(contradictions)} potential contradiction(s)")

    # Generate daily digest
    if generate_digest:
        digest_dir = vault_dir / "digests"
        digest_dir.mkdir(parents=True, exist_ok=True)

        # Group by date and generate digests
        dates_seen: Set[str] = set()
        for a in all_artifacts:
            ts = a.get("timestamp", "")
            if ts:
                dates_seen.add(ts[:10])

        for date_str in sorted(dates_seen):
            digest_md = generate_daily_digest(date_str, all_artifacts, contradictions)
            digest_path = digest_dir / f"digest_{date_str}.md"
            digest_path.write_text(digest_md, encoding="utf-8")

        # Also generate today's digest even if no artifacts
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today not in dates_seen:
            digest_md = generate_daily_digest(today, all_artifacts, contradictions)
            digest_path = digest_dir / f"digest_{today}.md"
            digest_path.write_text(digest_md, encoding="utf-8")

        print(f"  Generated {len(dates_seen) + (1 if today not in dates_seen else 0)} daily digest(s)")

    return {
        "agents": len(agents),
        "artifacts": total_synced,
        "contradictions": len(contradictions),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync ScienceClaw artifacts to an Obsidian vault",
    )
    parser.add_argument(
        "--vault", "-v",
        type=Path,
        default=DEFAULT_VAULT_DIR,
        help=f"Path to Obsidian vault directory (default: {DEFAULT_VAULT_DIR})",
    )
    parser.add_argument(
        "--agent", "-a",
        help="Sync only this agent's artifacts",
    )
    parser.add_argument(
        "--digest",
        action="store_true",
        help="Generate daily digest only (skip artifact sync)",
    )
    parser.add_argument(
        "--no-digest",
        action="store_true",
        help="Skip daily digest generation",
    )

    args = parser.parse_args()

    print(f"Syncing to vault: {args.vault}")

    if args.digest:
        # Digest-only mode
        all_artifacts = []
        for agent_name in _discover_agents():
            all_artifacts.extend(_load_artifacts(agent_name))
        contradictions = _detect_contradictions(all_artifacts)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        digest_md = generate_daily_digest(today, all_artifacts, contradictions)
        digest_dir = args.vault / "digests"
        digest_dir.mkdir(parents=True, exist_ok=True)
        digest_path = digest_dir / f"digest_{today}.md"
        digest_path.write_text(digest_md, encoding="utf-8")
        print(f"Daily digest written to: {digest_path}")
        return

    stats = sync_vault(
        vault_dir=args.vault,
        agent_filter=args.agent,
        generate_digest=not args.no_digest,
    )

    print(f"\nSync complete: {stats['artifacts']} artifacts from {stats['agents']} agent(s)")
    if stats.get("contradictions"):
        print(f"  {stats['contradictions']} contradiction(s) detected — check daily digest")


if __name__ == "__main__":
    main()
