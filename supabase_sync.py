#!/usr/bin/env python3
"""
Supabase persistence layer for ScienceClaw artifacts.

Mirrors artifacts to Supabase in real-time (dual-write alongside local JSONL)
and supports backfilling existing local artifacts.

Required environment variables:
    SUPABASE_URL  — Supabase project URL (e.g., https://xxx.supabase.co)
    SUPABASE_KEY  — Supabase service role or anon key

Tables (auto-created if they don't exist):
    agents           — Agent registry with configs
    investigations   — Investigation tracking
    artifacts        — Full artifact records with metadata
    cross_references — Links between related artifacts

Usage:
    # As a module (dual-write from ArtifactStore):
    from supabase_sync import SupabaseSync
    sync = SupabaseSync()
    sync.upsert_artifact(artifact_dict)

    # CLI — backfill existing artifacts:
    python3 supabase_sync.py backfill
    python3 supabase_sync.py backfill --agent QuantumBioAgent-1

    # CLI — sync a single agent's config:
    python3 supabase_sync.py register --agent QuantumBioAgent-1

Author: ScienceClaw Team
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCIENCECLAW_DIR = Path(os.path.expanduser("~/.scienceclaw"))

# SQL for table creation (Supabase runs PostgreSQL)
TABLE_DEFINITIONS = {
    "agents": """
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            expertise TEXT,
            config JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """,
    "investigations": """
        CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY,
            agent_id TEXT REFERENCES agents(id),
            topic TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """,
    "artifacts": """
        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
            investigation_id TEXT,
            agent_id TEXT REFERENCES agents(id),
            artifact_type TEXT NOT NULL,
            skill_used TEXT,
            content JSONB DEFAULT '{}'::jsonb,
            metadata JSONB DEFAULT '{}'::jsonb,
            tags TEXT[] DEFAULT '{}',
            source_db TEXT,
            confidence FLOAT DEFAULT 0.5,
            content_hash TEXT,
            result_quality TEXT DEFAULT 'ok',
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """,
    "cross_references": """
        CREATE TABLE IF NOT EXISTS cross_references (
            id SERIAL PRIMARY KEY,
            artifact_id_1 TEXT REFERENCES artifacts(id),
            artifact_id_2 TEXT REFERENCES artifacts(id),
            relationship_type TEXT NOT NULL,
            strength FLOAT DEFAULT 0.5,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(artifact_id_1, artifact_id_2, relationship_type)
        );
    """,
}


# ---------------------------------------------------------------------------
# Supabase client wrapper
# ---------------------------------------------------------------------------

class SupabaseSync:
    """
    Thin REST wrapper around Supabase PostgREST API.

    Uses plain HTTP requests to avoid requiring the supabase-py SDK,
    keeping dependencies minimal. Falls back gracefully if Supabase
    is not configured.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ):
        self.url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.key = supabase_key or os.environ.get("SUPABASE_KEY", "")
        self.enabled = bool(self.url and self.key)

        if self.enabled:
            try:
                import requests  # noqa: F401
                self._requests = requests
            except ImportError:
                print("Warning: 'requests' package not installed. Supabase sync disabled.")
                self.enabled = False

    @property
    def rest_url(self) -> str:
        return f"{self.url}/rest/v1"

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    def _post(self, table: str, data: dict, upsert: bool = False) -> bool:
        """POST a row to a table. Returns True on success."""
        if not self.enabled:
            return False
        headers = dict(self._headers)
        if upsert:
            headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
        try:
            resp = self._requests.post(
                f"{self.rest_url}/{table}",
                headers=headers,
                json=data,
                timeout=10,
            )
            return resp.status_code in (200, 201, 204)
        except Exception as e:
            print(f"Supabase POST to {table} failed: {e}")
            return False

    def _get(self, table: str, params: Optional[Dict] = None) -> List[dict]:
        """GET rows from a table."""
        if not self.enabled:
            return []
        try:
            headers = dict(self._headers)
            headers["Prefer"] = "return=representation"
            resp = self._requests.get(
                f"{self.rest_url}/{table}",
                headers=headers,
                params=params or {},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            print(f"Supabase GET from {table} failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Agent operations
    # ------------------------------------------------------------------

    def upsert_agent(self, agent_name: str, config: dict) -> bool:
        """Register or update an agent in Supabase."""
        expertise = config.get("expertise_preset", config.get("specialization", "mixed"))
        data = {
            "id": agent_name,
            "name": agent_name,
            "expertise": expertise,
            "config": json.loads(json.dumps(config, default=str)),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return self._post("agents", data, upsert=True)

    # ------------------------------------------------------------------
    # Investigation operations
    # ------------------------------------------------------------------

    def upsert_investigation(
        self,
        investigation_id: str,
        agent_name: str,
        topic: str,
        status: str = "active",
    ) -> bool:
        """Register or update an investigation."""
        data = {
            "id": investigation_id,
            "agent_id": agent_name,
            "topic": topic,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return self._post("investigations", data, upsert=True)

    # ------------------------------------------------------------------
    # Artifact operations
    # ------------------------------------------------------------------

    def upsert_artifact(self, artifact: dict) -> bool:
        """
        Upsert a single artifact to Supabase.

        Accepts the same dict format as stored in store.jsonl.
        """
        # Import auto-tagging from vault_sync if available
        tags = []
        try:
            from vault_sync import _extract_text_content, _auto_tag, _compute_confidence
            text = _extract_text_content(artifact)
            tags = _auto_tag(text)
            confidence = _compute_confidence(artifact)
        except ImportError:
            confidence = 0.5

        data = {
            "id": artifact.get("artifact_id", ""),
            "investigation_id": artifact.get("investigation_id", ""),
            "agent_id": artifact.get("producer_agent", ""),
            "artifact_type": artifact.get("artifact_type", "raw_output"),
            "skill_used": artifact.get("skill_used", ""),
            "content": json.loads(json.dumps(artifact.get("payload", {}), default=str)),
            "metadata": {
                "schema_version": artifact.get("schema_version", "1.0"),
                "parent_artifact_ids": artifact.get("parent_artifact_ids", []),
                "needs": artifact.get("needs", []),
                "timestamp": artifact.get("timestamp", ""),
            },
            "tags": tags,
            "source_db": artifact.get("skill_used", ""),
            "confidence": confidence,
            "content_hash": artifact.get("content_hash", ""),
            "result_quality": artifact.get("result_quality", "ok"),
            "created_at": artifact.get("timestamp", datetime.now(timezone.utc).isoformat()),
        }
        return self._post("artifacts", data, upsert=True)

    # ------------------------------------------------------------------
    # Cross-reference operations
    # ------------------------------------------------------------------

    def add_cross_reference(
        self,
        artifact_id_1: str,
        artifact_id_2: str,
        relationship_type: str,
        strength: float = 0.5,
    ) -> bool:
        """Add a cross-reference between two artifacts."""
        data = {
            "artifact_id_1": artifact_id_1,
            "artifact_id_2": artifact_id_2,
            "relationship_type": relationship_type,
            "strength": strength,
        }
        return self._post("cross_references", data, upsert=True)

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def backfill_agent(self, agent_name: str) -> Dict[str, int]:
        """
        Backfill all local artifacts for an agent to Supabase.

        Returns stats dict with counts of synced items.
        """
        stats = {"artifacts": 0, "investigations": 0, "cross_refs": 0, "errors": 0}

        # Load agent profile
        profile_path = SCIENCECLAW_DIR / "agent_profile.json"
        per_agent_path = SCIENCECLAW_DIR / "profiles" / agent_name / "agent_profile.json"
        if per_agent_path.exists():
            profile_path = per_agent_path

        if profile_path.exists():
            try:
                config = json.loads(profile_path.read_text(encoding="utf-8"))
                if self.upsert_agent(agent_name, config):
                    print(f"  Registered agent: {agent_name}")
            except (json.JSONDecodeError, OSError) as e:
                print(f"  Warning: Could not load profile for {agent_name}: {e}")

        # Load artifacts
        store_path = SCIENCECLAW_DIR / "artifacts" / agent_name / "store.jsonl"
        if not store_path.exists():
            print(f"  No artifacts found for {agent_name}")
            return stats

        artifacts = []
        for line in store_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                artifacts.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        # Track investigations
        investigations_seen = set()

        for artifact in artifacts:
            # Upsert investigation if new
            inv_id = artifact.get("investigation_id", "")
            if inv_id and inv_id not in investigations_seen:
                investigations_seen.add(inv_id)
                if self.upsert_investigation(inv_id, agent_name, inv_id):
                    stats["investigations"] += 1

            # Upsert artifact
            if self.upsert_artifact(artifact):
                stats["artifacts"] += 1
            else:
                stats["errors"] += 1

            # Create cross-references for parent relationships
            for parent_id in artifact.get("parent_artifact_ids", []):
                if self.add_cross_reference(
                    parent_id,
                    artifact["artifact_id"],
                    "parent_child",
                    strength=0.9,
                ):
                    stats["cross_refs"] += 1

        return stats

    def backfill_all(self) -> Dict[str, Any]:
        """Backfill all agents' artifacts to Supabase."""
        artifacts_dir = SCIENCECLAW_DIR / "artifacts"
        if not artifacts_dir.exists():
            print("No artifacts directory found.")
            return {"agents": 0}

        total_stats: Dict[str, Any] = {"agents": 0, "artifacts": 0, "investigations": 0, "cross_refs": 0, "errors": 0}

        for d in sorted(artifacts_dir.iterdir()):
            if d.is_dir() and (d / "store.jsonl").exists():
                agent_name = d.name
                print(f"Backfilling {agent_name}...")
                stats = self.backfill_agent(agent_name)
                total_stats["agents"] += 1
                for key in ("artifacts", "investigations", "cross_refs", "errors"):
                    total_stats[key] += stats.get(key, 0)
                print(f"  Done: {stats['artifacts']} artifacts, {stats['investigations']} investigations, {stats['cross_refs']} cross-refs")

        return total_stats

    def get_table_sql(self) -> str:
        """Return SQL statements to create all required tables."""
        return "\n\n".join(TABLE_DEFINITIONS.values())


# ---------------------------------------------------------------------------
# Dual-write integration hook
# ---------------------------------------------------------------------------

def create_dual_write_store(agent_name: str):
    """
    Create an ArtifactStore wrapper that dual-writes to both local JSONL
    and Supabase.

    Usage:
        store = create_dual_write_store("QuantumBioAgent-1")
        artifact = store.create_and_save(skill_used="pubmed", payload={...})
        # Artifact is now in both local store.jsonl AND Supabase
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from artifacts.artifact import ArtifactStore, Artifact

    class DualWriteArtifactStore(ArtifactStore):
        """ArtifactStore that also writes to Supabase on every save."""

        def __init__(self, agent_name: str):
            super().__init__(agent_name)
            self._supabase = SupabaseSync()
            if self._supabase.enabled:
                print(f"Supabase dual-write enabled for {agent_name}")

        def save(self, artifact: Artifact) -> str:
            """Save to local JSONL, then mirror to Supabase."""
            artifact_id = super().save(artifact)

            if self._supabase.enabled:
                self._supabase.upsert_artifact(artifact.to_dict())
                # Create cross-references for parent relationships
                for parent_id in artifact.parent_artifact_ids:
                    self._supabase.add_cross_reference(
                        parent_id,
                        artifact.artifact_id,
                        "parent_child",
                        strength=0.9,
                    )

            return artifact_id

    return DualWriteArtifactStore(agent_name)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ScienceClaw Supabase sync and backfill",
    )
    subparsers = parser.add_subparsers(dest="command")

    # backfill command
    backfill_parser = subparsers.add_parser("backfill", help="Backfill local artifacts to Supabase")
    backfill_parser.add_argument("--agent", "-a", help="Backfill only this agent")

    # register command
    register_parser = subparsers.add_parser("register", help="Register an agent in Supabase")
    register_parser.add_argument("--agent", "-a", required=True, help="Agent name to register")

    # schema command
    subparsers.add_parser("schema", help="Print SQL table definitions")

    args = parser.parse_args()

    if args.command == "schema":
        sync = SupabaseSync()
        print(sync.get_table_sql())
        return

    if args.command == "backfill":
        sync = SupabaseSync()
        if not sync.enabled:
            print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment.")
            print("See .env.example for configuration.")
            sys.exit(1)

        if args.agent:
            print(f"Backfilling {args.agent}...")
            stats = sync.backfill_agent(args.agent)
            print(f"\nDone: {stats['artifacts']} artifacts, {stats['investigations']} investigations")
        else:
            print("Backfilling all agents...")
            stats = sync.backfill_all()
            print(f"\nDone: {stats['agents']} agents, {stats['artifacts']} artifacts total")

        if stats.get("errors"):
            print(f"  {stats['errors']} error(s) occurred during backfill")
        return

    if args.command == "register":
        sync = SupabaseSync()
        if not sync.enabled:
            print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment.")
            sys.exit(1)

        # Try to load profile
        profile_path = SCIENCECLAW_DIR / "profiles" / args.agent / "agent_profile.json"
        if not profile_path.exists():
            profile_path = SCIENCECLAW_DIR / "agent_profile.json"

        if not profile_path.exists():
            print(f"No profile found for {args.agent}")
            sys.exit(1)

        config = json.loads(profile_path.read_text(encoding="utf-8"))

        # Also merge specialized profile if available
        try:
            from agent_profiles import get_agent_profile, apply_profile_to_config
            specialized = get_agent_profile(args.agent)
            if specialized:
                config = apply_profile_to_config(config, specialized)
        except ImportError:
            pass

        if sync.upsert_agent(args.agent, config):
            print(f"Registered {args.agent} in Supabase")
        else:
            print(f"Failed to register {args.agent}")
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
