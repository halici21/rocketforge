"""The text-value excerpt rule (DB-2B Wave 1, 607230d): its preflight review before Wave 2.

A text assertion may ship some of the ``;``-separated statements its source prints. The review
found the first rule accepted any substring, so an excerpt could drop a negation, a limit, a
configuration, a value kind, an approximation, a ratio direction or a parenthetical
restriction. These tests hold the repaired rule: whole statements only, in printed order, no
dropped heading or value-less qualifier, text values only, and a recorded owner decision.
"""

from __future__ import annotations

import copy
import dataclasses
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference_engines"))
import promote_db2a  # noqa: E402

UNOWNED = "AS-DB05-US-F-1-008"  # a promoted text value no owner decision releases
OWNED = "AS-DB05-US-F-1-010"  # the owner-released qualification life


@pytest.fixture(scope="module")
def research():
    return promote_db2a.load_research()


def attempt(research, aid, printed, excerpt):
    r = dataclasses.replace(research, assertions=copy.deepcopy(research.assertions))
    r.assertions[aid]["value_as_printed"] = printed
    m = types.SimpleNamespace(**copy.deepcopy(vars(promote_db2a.load_manifest())))
    next(e for e in m.ASSERTIONS if e["db05_id"] == aid)["value"] = ("text", excerpt)
    with pytest.raises(promote_db2a.PromotionError) as caught:
        promote_db2a.build_corpus(r, m)
    return caught.value.problems


MEANING_CHANGES = [
    ("negation", "not more than 20 starts; qualification target 25", "20 starts", "is not a whole printed statement"),
    ("maximum", "maximum duration 2,250 s", "duration 2,250 s", "is not a whole printed statement"),
    ("configuration", "Block II: 500 klbf; Block IIA: 520 klbf", "500 klbf", "is not a whole printed statement"),
    ("sibling configuration", "Block II: 500 klbf; Block IIA: 520 klbf", "Block II: 500 klbf", "reads as context"),
    ("value kind", "predicted 300; measured 280", "300", "is not a whole printed statement"),
    ("approximation", "approximately 130 psia", "130 psia", "is not a whole printed statement"),
    ("ratio direction", "fuel-to-oxidizer ratio 2.3", "ratio 2.3", "is not a whole printed statement"),
    ("heading", "Qualification limits: 20 starts; 2,250 s", "2,250 s", "reads as context"),
    ("parenthetical", "20 starts (ground test only); 2,250 s", "20 starts", "is not a whole printed statement"),
    ("value-less qualifier", "Starts 20; Duration 2,250 seconds; per qualification test",
     "Starts 20; Duration 2,250 seconds", "reads as context"),
    ("order", "Starts 20; Duration 2,250 seconds", "Duration 2,250 seconds; Starts 20", "does not keep the printed order"),
    ("empty", "Starts 20; Duration 2,250 seconds", " ; ", "an empty excerpt"),
]


@pytest.mark.parametrize("aid", [UNOWNED, OWNED])
@pytest.mark.parametrize("name,printed,excerpt,why", MEANING_CHANGES, ids=[c[0] for c in MEANING_CHANGES])
def test_an_excerpt_cannot_change_what_the_source_says(research, aid, name, printed, excerpt, why):
    problems = attempt(research, aid, printed, excerpt)
    assert any(f"{aid}: " in p and why in p for p in problems), problems


def test_an_excerpt_is_for_text_values_only(research):
    r = dataclasses.replace(research, assertions=copy.deepcopy(research.assertions))
    r.assertions[OWNED]["value"] = 2250
    with pytest.raises(promote_db2a.PromotionError) as caught:
        promote_db2a.build_corpus(r, promote_db2a.load_manifest())
    assert any("an excerpt is for text values only" in p for p in caught.value.problems)


def test_an_excerpt_needs_an_owner_decision(research):
    """Whole statements in order, nothing dropped that scopes them: still the owner's call."""
    problems = attempt(research, UNOWNED, "18.4 feet tall; 12 feet wide", "18.4 feet tall")
    assert any(f"{UNOWNED}: a text excerpt needs a recorded owner decision" in p for p in problems), problems


def test_a_whole_value_text_is_unaffected(research):
    """No excerpt, no rule: the shipped text is the printed text."""
    corpus = promote_db2a.build_corpus(research, promote_db2a.load_manifest())
    a = next(x for x in corpus.assertions if x.assertion_id == UNOWNED)
    assert a.value.text == a.value_as_printed


def test_the_owner_admitted_excerpt_still_ships(research):
    corpus = promote_db2a.build_corpus(research, promote_db2a.load_manifest())
    a = next(x for x in corpus.assertions if x.assertion_id == OWNED)
    assert a.value.text == "Starts 20; Duration 2,250 seconds"
    assert a.value_as_printed == "Starts 20; Duration 2,250 seconds; mission duration 165 seconds"
