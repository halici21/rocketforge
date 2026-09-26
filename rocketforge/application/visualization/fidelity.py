"""What a picture is allowed to claim.

Four kinds of thing can appear in an engineering view, and a reader must be
able to tell them apart:

* ``SUPPLIED`` -- geometry the case itself carries (an area distribution the
  user supplied, a throat and exit area);
* ``DERIVED`` -- geometry produced deterministically from solved or supplied
  quantities, e.g. a radius distribution revolved into a surface;
* ``SCHEMATIC`` -- a concept illustration with no claim to shape;
* ``QUALITATIVE_FLOW`` -- a cue for direction or phase presence, with no claim
  to a resolved flow field.

The labels are short on purpose: a viewport says which one it is in one line,
not in a disclaimer card.
"""
from __future__ import annotations

from enum import StrEnum

__all__ = ["Fidelity", "label", "FLOW_LABEL", "PLAYBACK_NOTE"]


class Fidelity(StrEnum):
    SUPPLIED = "supplied"
    DERIVED = "derived"
    SCHEMATIC = "schematic"
    QUALITATIVE_FLOW = "qualitative-flow"


_LABELS = {
    Fidelity.SUPPLIED: "Supplied geometry",
    Fidelity.DERIVED: "Derived presentation geometry",
    Fidelity.SCHEMATIC: "Schematic geometry",
    Fidelity.QUALITATIVE_FLOW: "Qualitative flow cues",
}

#: What the animated tracers are, stated once.
FLOW_LABEL = "QUALITATIVE FLOW CUES — DIRECTION ONLY, NOT A FLOW FIELD"

#: What the playback control means.
PLAYBACK_NOTE = "Visualization playback speed, not a physical time scale."


def label(kind: Fidelity | str) -> str:
    """The one-line name of a fidelity class."""
    return _LABELS[Fidelity(kind)]
