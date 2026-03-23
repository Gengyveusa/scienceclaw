#!/usr/bin/env python3
"""
Specialized agent tool profiles for the ScienceClaw multi-agent system.

Each agent has a unique configuration with:
- default_queries: Pre-configured search terms for the agent's domain
- priority_databases: Ordered list of databases the agent should consult first
- expertise_tags: Semantic tags describing the agent's specialization

These profiles are loaded by the heartbeat daemon and used by the skill
selector / deep investigation pipeline to prioritize tools and queries.

Usage:
    from agent_profiles import AGENT_TOOL_PROFILES, get_agent_profile, apply_profile_to_config

    profile = get_agent_profile("QuantumBioAgent-1")
    config = apply_profile_to_config(base_config, profile)
"""

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Agent tool profiles
# ---------------------------------------------------------------------------

AGENT_TOOL_PROFILES: Dict[str, dict] = {
    # -------------------------------------------------------------------
    # QuantumBioAgent-1 — biology specialization
    # Focus: quantum coherence in biological systems, periodontal biofilm,
    #        bacteriophage therapy
    # -------------------------------------------------------------------
    "QuantumBioAgent-1": {
        "specialization": "biology",
        "description": (
            "Quantum biology specialist investigating quantum coherence in "
            "biological systems, periodontal biofilm dynamics, and "
            "bacteriophage therapy applications."
        ),
        "default_queries": [
            "quantum coherence biological systems photosynthesis",
            "quantum tunneling enzyme catalysis proton transfer",
            "periodontal biofilm Porphyromonas gingivalis virulence",
            "bacteriophage therapy antibiotic resistant biofilm",
            "quantum biology radical pair mechanism magnetoreception",
            "exciton transport light harvesting complexes",
            "biofilm quorum sensing disruption phage",
            "quantum effects NADH electron transport chain",
            "phage therapy periodontal pathogens clinical trials",
            "quantum decoherence timescales warm wet biological",
        ],
        "default_mesh_headings": [
            "Quantum Theory",
            "Biofilms",
            "Bacteriophages",
            "Periodontitis",
            "Photosynthesis",
            "Electron Transport",
            "Energy Transfer",
            "Porphyromonas gingivalis",
            "Anti-Bacterial Agents",
            "Phage Therapy",
        ],
        "priority_databases": [
            "pubmed",
            "pubmed-database",
            "arxiv",
            "arxiv-database",
            "uniprot",
            "uniprot-database",
            "biorxiv-database",
            "blast",
            "pdb",
            "pdb-database",
            "string-database",
            "sequence",
            "gget",
            "esm",
            "websearch",
        ],
        "expertise_tags": [
            "quantum-biology",
            "quantum-coherence",
            "biofilm",
            "periodontal-biofilm",
            "bacteriophage",
            "phage-therapy",
            "photosynthesis",
            "electron-transport",
            "radical-pair-mechanism",
            "magnetoreception",
            "enzyme-tunneling",
            "exciton-dynamics",
        ],
        "preferred_tools": [
            "pubmed", "pubmed-database", "arxiv", "arxiv-database",
            "uniprot", "uniprot-database", "blast", "pdb", "pdb-database",
            "biorxiv-database", "string-database", "sequence",
            "gget", "esm", "biopython", "websearch",
        ],
        "research_focus": {
            "interests": [
                "quantum coherence in biological systems",
                "periodontal biofilm formation and disruption",
                "bacteriophage therapy for resistant infections",
                "quantum tunneling in enzyme catalysis",
                "radical pair mechanism in magnetoreception",
            ],
            "organisms": [
                "Porphyromonas gingivalis",
                "Chlorobaculum tepidum",
                "Rhodobacter sphaeroides",
                "Cryptochrome (avian)",
                "Escherichia coli",
            ],
            "proteins": [
                "FMO complex",
                "Cryptochrome",
                "Reaction center",
                "Aromatic amine dehydrogenase",
                "ATP synthase",
            ],
        },
    },

    # -------------------------------------------------------------------
    # ChemSpecAgent-1 — chemistry / spectroscopy specialization
    # Focus: NADH/FAD/ATP/GSH spectral signatures, Raman and
    #        fluorescence spectroscopy literature
    # -------------------------------------------------------------------
    "ChemSpecAgent-1": {
        "specialization": "chemistry",
        "description": (
            "Chemistry and spectroscopy specialist focused on endogenous "
            "fluorophore spectral signatures (NADH, FAD, ATP, GSH), "
            "Raman spectroscopy, and fluorescence lifetime imaging."
        ),
        "default_queries": [
            "NADH autofluorescence spectral signature excitation emission",
            "FAD flavin adenine dinucleotide fluorescence lifetime",
            "ATP bioluminescence Raman spectroscopy detection",
            "glutathione GSH Raman spectral marker oxidative stress",
            "Raman spectroscopy biofilm chemical composition",
            "fluorescence lifetime imaging microscopy FLIM metabolic",
            "NADH FAD redox ratio fluorescence imaging",
            "surface enhanced Raman spectroscopy SERS biomarker",
            "two-photon excitation fluorescence NADH tissue",
            "coherent anti-Stokes Raman scattering CARS biological",
        ],
        "default_mesh_headings": [
            "Spectrum Analysis, Raman",
            "Spectrometry, Fluorescence",
            "NAD/metabolism",
            "Flavin-Adenine Dinucleotide",
            "Adenosine Triphosphate",
            "Glutathione",
            "Microscopy, Fluorescence",
            "Optical Imaging",
            "Fluorescent Dyes",
            "Molecular Probes",
        ],
        "priority_databases": [
            "nistwebbook",
            "pubchem",
            "pubchem-database",
            "chembl",
            "chembl-database",
            "cas",
            "pubmed",
            "pubmed-database",
            "arxiv",
            "arxiv-database",
            "rdkit",
            "matchms",
            "hmdb-database",
            "websearch",
        ],
        "expertise_tags": [
            "spectroscopy",
            "raman-spectroscopy",
            "fluorescence-spectroscopy",
            "NADH",
            "FAD",
            "ATP",
            "GSH",
            "FLIM",
            "SERS",
            "autofluorescence",
            "redox-ratio",
            "metabolic-imaging",
            "endogenous-fluorophore",
        ],
        "preferred_tools": [
            "nistwebbook", "pubchem", "pubchem-database", "chembl",
            "chembl-database", "cas", "rdkit", "matchms", "datamol",
            "hmdb-database", "pubmed", "pubmed-database", "arxiv",
            "arxiv-database", "websearch",
        ],
        "research_focus": {
            "interests": [
                "NADH and FAD autofluorescence spectral characterization",
                "Raman spectroscopy for biological tissue analysis",
                "fluorescence lifetime imaging of metabolic state",
                "surface enhanced Raman spectroscopy biomarkers",
                "spectral unmixing of endogenous fluorophores",
            ],
            "compounds": [
                "NADH",
                "FAD",
                "ATP",
                "GSH (glutathione)",
                "porphyrins",
                "collagen",
                "tryptophan",
            ],
        },
    },

    # -------------------------------------------------------------------
    # SwarmSynthAgent-1 — cross-domain synthesis / linker
    # Pulls from both bio and chem agents, finds interdisciplinary
    # connections, generates bridging synthesis reports.
    # -------------------------------------------------------------------
    "SwarmSynthAgent-1": {
        "specialization": "synthesis",
        "description": (
            "Cross-domain synthesis agent that links biology and chemistry "
            "findings. Identifies interdisciplinary connections between "
            "quantum biology, spectroscopy, biofilm, and phage therapy "
            "research to generate bridging synthesis reports."
        ),
        "default_queries": [
            "quantum biology spectroscopy biofilm Raman fluorescence",
            "NADH autofluorescence biofilm metabolic activity",
            "bacteriophage biofilm Raman spectroscopy monitoring",
            "fluorescence lifetime imaging biofilm infection",
            "quantum coherence photodynamic therapy biofilm",
            "metabolic imaging periodontal disease spectroscopy",
            "phage therapy combined spectroscopic monitoring",
            "redox state NADH FAD biofilm antibiotic resistance",
            "quantum dots fluorescence biofilm detection",
            "interdisciplinary quantum biology drug delivery",
        ],
        "default_mesh_headings": [
            "Interdisciplinary Research",
            "Translational Science",
            "Biofilms/drug effects",
            "Spectrum Analysis, Raman",
            "Phage Therapy",
            "NAD/metabolism",
            "Quantum Theory",
            "Drug Delivery Systems",
            "Fluorescence",
            "Anti-Infective Agents",
        ],
        "priority_databases": [
            "pubmed",
            "pubmed-database",
            "arxiv",
            "arxiv-database",
            "websearch",
            "uniprot",
            "pubchem",
            "nistwebbook",
            "biorxiv-database",
            "openalex-database",
            "literature-review",
            "literature-deep-research",
        ],
        "expertise_tags": [
            "cross-domain-synthesis",
            "interdisciplinary",
            "quantum-biology",
            "spectroscopy",
            "biofilm",
            "phage-therapy",
            "translational-science",
            "systems-thinking",
            "meta-analysis",
            "bridging-research",
        ],
        "preferred_tools": [
            "pubmed", "pubmed-database", "arxiv", "arxiv-database",
            "websearch", "uniprot", "pubchem", "nistwebbook",
            "biorxiv-database", "openalex-database",
            "literature-review", "literature-deep-research",
            "hypothesis-generation", "scientific-brainstorming",
            "scientific-writing", "write-review-paper",
        ],
        "linked_agents": [
            "QuantumBioAgent-1",
            "ChemSpecAgent-1",
        ],
        "synthesis_config": {
            "cross_reference_mode": True,
            "bridge_domains": ["biology", "chemistry"],
            "report_format": "interdisciplinary_synthesis",
            "min_sources_per_domain": 2,
            "contradiction_detection": True,
        },
        "research_focus": {
            "interests": [
                "bridging quantum biology and spectroscopy findings",
                "translational connections between biofilm and phage research",
                "integrating metabolic imaging with infection biology",
                "cross-domain hypothesis generation",
                "meta-analysis of interdisciplinary approaches",
            ],
        },
    },
}


def get_agent_profile(agent_name: str) -> Optional[dict]:
    """
    Return the specialized tool profile for the given agent name.

    Returns None if no specialized profile exists (agent uses defaults).
    """
    return AGENT_TOOL_PROFILES.get(agent_name)


def list_agent_profiles() -> List[str]:
    """Return names of all agents with specialized profiles."""
    return list(AGENT_TOOL_PROFILES.keys())


def apply_profile_to_config(base_config: dict, profile: dict) -> dict:
    """
    Merge a specialized agent tool profile into an existing agent config.

    The profile's preferred_tools, research interests, and expertise tags
    are merged into the base config. Profile values take precedence for
    fields that overlap.

    Args:
        base_config: The agent's existing agent_profile.json content
        profile: A profile dict from AGENT_TOOL_PROFILES

    Returns:
        Updated config dict (does not mutate the original)
    """
    config = dict(base_config)

    # Merge preferred tools
    if "preferred_tools" in profile:
        config.setdefault("preferences", {})
        config["preferences"]["tools"] = profile["preferred_tools"]

    # Merge research focus
    if "research_focus" in profile:
        config.setdefault("research", {})
        for key, value in profile["research_focus"].items():
            config["research"][key] = value

    # Add profile-specific fields
    config["default_queries"] = profile.get("default_queries", [])
    config["default_mesh_headings"] = profile.get("default_mesh_headings", [])
    config["priority_databases"] = profile.get("priority_databases", [])
    config["expertise_tags"] = profile.get("expertise_tags", [])

    # Synthesis agent config
    if "synthesis_config" in profile:
        config["synthesis_config"] = profile["synthesis_config"]
    if "linked_agents" in profile:
        config["linked_agents"] = profile["linked_agents"]

    return config
