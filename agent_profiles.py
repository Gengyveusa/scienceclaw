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
    # QuantumBioAgent-1 — mitochondrial quantum biology
    # Focus: quantum tunneling in ETC, quantum coherence in respiratory
    #        complexes, proton tunneling in ATP synthase, mitochondrial
    #        membrane potential quantum effects, ROS quantum dynamics
    # -------------------------------------------------------------------
    "QuantumBioAgent-1": {
        "specialization": "biology",
        "description": (
            "Mitochondrial quantum biology specialist investigating quantum "
            "tunneling in the electron transport chain, quantum coherence in "
            "respiratory complexes I-IV, proton tunneling in ATP synthase, "
            "and reactive oxygen species quantum dynamics."
        ),
        "default_queries": [
            "quantum tunneling electron transport chain mitochondria",
            "quantum coherence Complex I NADH ubiquinone oxidoreductase",
            "proton tunneling ATP synthase rotary mechanism mitochondria",
            "mitochondrial membrane potential quantum effects proton motive force",
            "reactive oxygen species quantum dynamics superoxide mitochondria",
            "quantum biology Complex III cytochrome bc1 Q-cycle electron bifurcation",
            "Complex IV cytochrome c oxidase quantum tunneling oxygen reduction",
            "mitochondrial Complex II succinate dehydrogenase quantum effects",
            "mitochondrial DNA mutation rate quantum error mechanisms",
            "quantum decoherence mitochondrial inner membrane electron transfer",
        ],
        "default_mesh_headings": [
            "Mitochondria",
            "Quantum Theory",
            "Electron Transport Chain Complex Proteins",
            "Electron Transport",
            "Mitochondrial Proton-Translocating ATPases",
            "Reactive Oxygen Species",
            "Mitochondrial Membranes",
            "Proton-Motive Force",
            "DNA, Mitochondrial",
            "Oxidative Phosphorylation",
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
            "mitochondria",
            "quantum-biology",
            "quantum-tunneling",
            "electron-transport-chain",
            "ATP-synthase",
            "proton-tunneling",
            "respiratory-complex",
            "membrane-potential",
            "reactive-oxygen-species",
            "oxidative-phosphorylation",
            "mitochondrial-DNA",
            "quantum-coherence",
        ],
        "preferred_tools": [
            "pubmed", "pubmed-database", "arxiv", "arxiv-database",
            "uniprot", "uniprot-database", "blast", "pdb", "pdb-database",
            "biorxiv-database", "string-database", "sequence",
            "gget", "esm", "biopython", "websearch",
        ],
        "research_focus": {
            "interests": [
                "quantum tunneling in mitochondrial electron transport chain",
                "quantum coherence in respiratory complexes I-IV",
                "proton tunneling mechanisms in ATP synthase",
                "mitochondrial membrane potential and quantum effects",
                "reactive oxygen species generation via quantum dynamics",
                "mitochondrial DNA mutation rates and quantum error mechanisms",
            ],
            "organisms": [
                "Homo sapiens",
                "Mus musculus",
                "Saccharomyces cerevisiae",
                "Bos taurus",
            ],
            "proteins": [
                "Complex I (NADH:ubiquinone oxidoreductase)",
                "Complex II (succinate dehydrogenase)",
                "Complex III (cytochrome bc1)",
                "Complex IV (cytochrome c oxidase)",
                "ATP synthase (Complex V)",
                "Cytochrome c",
                "Ubiquinone (Coenzyme Q)",
            ],
        },
    },

    # -------------------------------------------------------------------
    # ChemSpecAgent-1 — mitochondrial spectroscopy specialization
    # Focus: NADH/FAD autofluorescence in mitochondria, cytochrome c
    #        oxidase spectral signatures, mitochondrial membrane potential
    #        probes, Raman/FLIM of mitochondrial metabolic states
    # -------------------------------------------------------------------
    "ChemSpecAgent-1": {
        "specialization": "chemistry",
        "description": (
            "Mitochondrial spectroscopy specialist focused on NADH/FAD "
            "autofluorescence in mitochondria, cytochrome c oxidase spectral "
            "signatures, mitochondrial membrane potential fluorescent probes "
            "(JC-1, TMRM, MitoTracker), and FLIM of mitochondrial metabolic states."
        ),
        "default_queries": [
            "NADH autofluorescence mitochondria two-photon excitation emission",
            "FAD fluorescence lifetime mitochondrial metabolic state FLIM",
            "cytochrome c oxidase near-infrared spectroscopy absorption spectrum",
            "JC-1 mitochondrial membrane potential fluorescent probe aggregation",
            "TMRM tetramethylrhodamine mitochondrial membrane potential imaging",
            "MitoTracker mitochondria fluorescent staining spectral properties",
            "Raman spectroscopy mitochondrial function cytochrome c resonance",
            "NADH FAD redox ratio mitochondrial oxidative phosphorylation imaging",
            "fluorescence lifetime imaging microscopy mitochondrial heterogeneity",
            "mitochondrial NADH pool free bound fluorescence lifetime components",
        ],
        "default_mesh_headings": [
            "Mitochondria/metabolism",
            "Spectrum Analysis, Raman",
            "Spectrometry, Fluorescence",
            "NAD/metabolism",
            "Flavin-Adenine Dinucleotide/metabolism",
            "Electron Transport Complex IV",
            "Membrane Potential, Mitochondrial",
            "Fluorescent Dyes",
            "Microscopy, Fluorescence",
            "Optical Imaging",
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
            "mitochondrial-spectroscopy",
            "NADH-autofluorescence",
            "FAD-fluorescence",
            "cytochrome-c-oxidase",
            "membrane-potential-probes",
            "JC-1",
            "TMRM",
            "MitoTracker",
            "raman-spectroscopy",
            "FLIM",
            "mitochondrial-redox",
            "metabolic-imaging",
            "two-photon-microscopy",
        ],
        "preferred_tools": [
            "nistwebbook", "pubchem", "pubchem-database", "chembl",
            "chembl-database", "cas", "rdkit", "matchms", "datamol",
            "hmdb-database", "pubmed", "pubmed-database", "arxiv",
            "arxiv-database", "websearch",
        ],
        "research_focus": {
            "interests": [
                "NADH and FAD autofluorescence in mitochondria",
                "cytochrome c oxidase near-infrared spectral signatures",
                "mitochondrial membrane potential fluorescent probes (JC-1, TMRM, MitoTracker)",
                "Raman spectroscopy of mitochondrial respiratory chain components",
                "FLIM of mitochondrial metabolic states and heterogeneity",
                "spectral unmixing of mitochondrial endogenous fluorophores",
            ],
            "compounds": [
                "NADH",
                "FAD",
                "Cytochrome c",
                "JC-1",
                "TMRM (tetramethylrhodamine methyl ester)",
                "MitoTracker dyes",
                "Rhodamine 123",
                "Coenzyme Q10",
            ],
        },
    },

    # -------------------------------------------------------------------
    # SwarmSynthAgent-1 — mitochondrial quantum-biology synthesis
    # Bridges mitochondrial biology with quantum physics: how quantum
    # effects in ETC relate to disease, quantum biology of aging,
    # quantum protection mechanisms in healthy vs diseased mitochondria.
    # -------------------------------------------------------------------
    "SwarmSynthAgent-1": {
        "specialization": "synthesis",
        "description": (
            "Cross-domain synthesis agent bridging mitochondrial biology "
            "with quantum physics. Connects quantum effects in the electron "
            "transport chain to disease states, investigates quantum biology "
            "of aging via mitochondrial dysfunction, and identifies quantum "
            "protection mechanisms in healthy vs diseased mitochondria."
        ),
        "default_queries": [
            "quantum effects electron transport chain mitochondrial disease",
            "mitochondrial dysfunction quantum biology aging senescence",
            "quantum tunneling efficiency Complex I deficiency neurodegeneration",
            "NADH autofluorescence mitochondrial metabolic state disease marker",
            "quantum coherence respiratory chain Parkinson Alzheimer mitochondria",
            "mitochondrial membrane potential quantum proton leak aging",
            "reactive oxygen species quantum yield mitochondrial disease",
            "spectroscopic detection mitochondrial quantum efficiency in vivo",
            "quantum protection mechanisms healthy versus diseased mitochondria",
            "mitochondrial electron transfer quantum biology translational medicine",
        ],
        "default_mesh_headings": [
            "Mitochondria/physiopathology",
            "Quantum Theory",
            "Electron Transport Chain Complex Proteins",
            "Mitochondrial Diseases",
            "Aging/metabolism",
            "Reactive Oxygen Species",
            "Neurodegenerative Diseases/metabolism",
            "Spectrometry, Fluorescence",
            "Oxidative Phosphorylation",
            "Translational Medical Research",
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
            "mitochondria",
            "quantum-biology",
            "mitochondrial-disease",
            "aging",
            "electron-transport-chain",
            "spectroscopy",
            "translational-science",
            "quantum-protection",
            "neurodegeneration",
            "metabolic-imaging",
            "systems-thinking",
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
            "bridge_domains": ["mitochondrial-biology", "quantum-physics"],
            "report_format": "interdisciplinary_synthesis",
            "min_sources_per_domain": 2,
            "contradiction_detection": True,
        },
        "research_focus": {
            "interests": [
                "how quantum effects in ETC relate to mitochondrial disease states",
                "quantum biology of aging via mitochondrial dysfunction",
                "quantum protection mechanisms in healthy vs diseased mitochondria",
                "bridging mitochondrial spectroscopy with quantum tunneling models",
                "translational implications of mitochondrial quantum efficiency",
                "meta-analysis of quantum phenomena across respiratory complexes",
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
