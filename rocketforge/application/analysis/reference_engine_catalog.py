"""The reference-engine catalog, read-only: the shipped seed corpus, as questions about one configuration.

DB-2A ships an initial verified seed corpus of three engine configurations
(``rocketforge/data/evidence/engines/reference_engines.json``). This module
finds that file, loads it through the DB-1 engine-evidence loader, refuses it
if it breaks a shipping rule (:func:`~rocketforge.evidence.engines.admission.admission_violations`),
and answers questions about it:

* which configurations there are (:meth:`ReferenceEngineCatalog.entries`) and
  which ones a name refers to (:meth:`~ReferenceEngineCatalog.find`);
* what is recorded *for* a configuration (its own assertions, operating
  points and topology graphs) and what is recorded only for its variant or
  family (``context``) -- the two are never merged;
* what the record can support, per use (:meth:`~ReferenceEngineCatalog.capabilities`).

Deliberately not here: no Qt, no provider, no CEA, no network, no solve, no
unit conversion, and no design recommendation. A reference record is evidence
about a real engine; nothing in this module turns it into an input for
designing one. It reads one file, which is never research material: the
catalog does not know ``docs/research`` exists.
"""

from __future__ import annotations

import pathlib
import re
import unicodedata
from dataclasses import dataclass

from rocketforge.evidence import EvidenceError, Missing
from rocketforge.evidence.engines import (
    Assertion,
    EngineEvidenceCorpus,
    EngineSource,
    OperatingPoint,
    SubjectKind,
    TopologyGraph,
    corpus_fingerprint,
    corpus_from_json,
)
from rocketforge.evidence.engines.admission import admission_violations
from rocketforge.evidence.engines.capabilities import (
    Capability,
    CapabilityResult,
    configuration_assertions,
    configuration_capabilities,
    configuration_topologies,
    context_assertions,
    evaluate_capability,
)

from ..data_paths import data_root

__all__ = [
    "REFERENCE_ENGINE_FILE", "reference_engine_path", "load_reference_engines",
    "CatalogEntry", "ReferenceEngineCatalog",
]

REFERENCE_ENGINE_FILE = "reference_engines.json"


def reference_engine_path() -> pathlib.Path:
    """Where the shipped seed corpus lives, in a source tree or a frozen build."""
    return data_root() / "evidence" / "engines" / REFERENCE_ENGINE_FILE


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """One configuration, as a list row names it."""

    configuration_id: str
    label: str
    variant_id: str
    designation: str
    family_id: str
    family_name: str
    effective: str | Missing
    operating_points: tuple[OperatingPoint, ...]


_DASHES = re.compile(r"[‐-―−\s_]+")


def _key(name: str) -> str:
    return _DASHES.sub("-", unicodedata.normalize("NFKC", name).casefold()).strip("-")


@dataclass(frozen=True, slots=True)
class ReferenceEngineCatalog:
    """A loaded, admitted seed corpus. Frozen; every answer is a tuple."""

    corpus: EngineEvidenceCorpus
    fingerprint: str

    def entries(self) -> tuple[CatalogEntry, ...]:
        """Every configuration, sorted by id."""
        return tuple(self.entry(c.configuration_id)
                     for c in sorted(self.corpus.configurations, key=lambda c: c.configuration_id))

    def entry(self, configuration_id: str) -> CatalogEntry:
        config = next((c for c in self.corpus.configurations if c.configuration_id == configuration_id), None)
        if config is None:
            raise EvidenceError(f"unknown configuration {configuration_id!r}")
        variant = next(v for v in self.corpus.variants if v.variant_id == config.variant_id)
        family = next(f for f in self.corpus.families if f.family_id == variant.family_id)
        points = tuple(p for p in self.corpus.operating_points if p.configuration_id == configuration_id)
        return CatalogEntry(config.configuration_id, config.label, variant.variant_id, variant.designation,
                            family.family_id, family.name, config.effective, points)

    def find(self, name: str) -> tuple[CatalogEntry, ...]:
        """Configurations a name refers to: a family name, a variant designation or an alias.

        A name that is not recorded finds nothing; there is no fuzzy match.
        """
        key = _key(name)
        variants: set[str] = set()
        for v in self.corpus.variants:
            family = next(f for f in self.corpus.families if f.family_id == v.family_id)
            if key in (_key(v.designation), _key(family.name)):
                variants.add(v.variant_id)
        for a in self.corpus.aliases:
            if _key(a.name) == key:
                if a.target.kind is SubjectKind.VARIANT:
                    variants.add(a.target.id)
                elif a.target.kind is SubjectKind.FAMILY:
                    variants |= {v.variant_id for v in self.corpus.variants if v.family_id == a.target.id}
                elif a.target.kind is SubjectKind.CONFIGURATION:
                    variants.add(next(c.variant_id for c in self.corpus.configurations
                                      if c.configuration_id == a.target.id))
        return tuple(e for e in self.entries() if e.variant_id in variants)

    def assertions(self, configuration_id: str) -> tuple[Assertion, ...]:
        """What is recorded for this configuration, its operating points and its components."""
        return configuration_assertions(self.corpus, configuration_id)

    def context(self, configuration_id: str) -> tuple[Assertion, ...]:
        """What is recorded only for its variant or family. Context, never its values."""
        return context_assertions(self.corpus, configuration_id)

    def topologies(self, configuration_id: str) -> tuple[TopologyGraph, ...]:
        return configuration_topologies(self.corpus, configuration_id)

    def capabilities(self, configuration_id: str) -> tuple[CapabilityResult, ...]:
        return configuration_capabilities(self.corpus, configuration_id)

    def capability(self, configuration_id: str, capability: Capability) -> CapabilityResult:
        return evaluate_capability(self.corpus, configuration_id, capability)

    def sources(self, configuration_id: str) -> tuple[EngineSource, ...]:
        """The sources this configuration's record cites: its assertions, context, graphs and their drawings."""
        cited = {a.source_id for a in (*self.assertions(configuration_id), *self.context(configuration_id))}
        schematics = {s.schematic_id: s.source_id for s in self.corpus.schematics}
        for graph in self.topologies(configuration_id):
            cited |= set(graph.text_source_ids)
            cited |= {schematics[s] for s in graph.schematic_ids}
        return tuple(s for s in self.corpus.sources if s.source_id in cited)


def load_reference_engines(path: pathlib.Path | None = None) -> ReferenceEngineCatalog:
    """Load and admit the shipped seed corpus. A file that breaks a rule is refused, not trimmed."""
    path = reference_engine_path() if path is None else pathlib.Path(path)
    if not path.is_file():
        raise EvidenceError(f"no reference-engine corpus at {path}")
    corpus = corpus_from_json(path.read_text(encoding="utf-8"))
    violations = admission_violations(corpus)
    if violations:
        raise EvidenceError(f"{path.name} may not ship as reference data: " + "; ".join(violations))
    return ReferenceEngineCatalog(corpus, corpus_fingerprint(corpus))
