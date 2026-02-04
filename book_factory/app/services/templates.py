"""Default chapter templates."""
from __future__ import annotations

DEFAULT_SILO_TEMPLATES = {
    1: {
        "title": "The Why Now Brief",
        "sections": [
            "What changed recently",
            "Why this matters now",
            "Who should care",
            "Key signal or proof point",
        ],
    },
    2: {
        "title": "The 1-Hour Quick Start",
        "sections": [
            "Prerequisites",
            "Install/setup",
            "First success",
            "Common first mistakes",
        ],
    },
    3: {
        "title": "Core Concepts Without the Fluff",
        "sections": [
            "Key terms",
            "Mental model",
            "How it works under the hood",
        ],
    },
    4: {
        "title": "Step-By-Step Build",
        "sections": [
            "End-to-end workflow",
            "Decision points",
            "Default recommendations",
        ],
    },
    5: {
        "title": "Real-World Use Cases",
        "sections": [
            "3-7 concrete use cases",
            "When to use / when not to",
            "Implementation sketch",
        ],
    },
    6: {
        "title": "Gotchas, Fail States, Troubleshooting",
        "sections": [
            "Common mistakes",
            "Warning signs",
            "Fixes",
        ],
    },
    7: {
        "title": "Security, Privacy, Risks, Compliance",
        "sections": [
            "Threat model",
            "Data handling",
            "Compliance risks",
        ],
    },
    8: {
        "title": "Performance, Scale, Cost Control",
        "sections": [
            "Latency/throughput",
            "Scaling tactics",
            "Cost traps",
        ],
    },
    9: {
        "title": "Tooling, Templates, Checklists",
        "sections": [
            "Copy-paste configs",
            "Checklist",
            "Before you ship",
        ],
    },
    10: {
        "title": "Roadmap, What's Next, Series Hooks",
        "sections": [
            "What’s coming",
            "Adjacent topics",
            "Series hooks",
        ],
    },
}
