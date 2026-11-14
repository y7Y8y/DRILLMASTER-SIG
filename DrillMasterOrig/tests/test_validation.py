"""Tests validation par nature (socle, codé, quantitatif)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from DrillMasterOrig.core.model import Interval
from DrillMasterOrig.core.validation import (
    ElementSpec, validate_assays, validate_coded_log,
    validate_depth_anchored)


def _iv(hid="DDH-001", a=0.0, b=10.0, code="LST", row=1, domain="litho"):
    return Interval(hid, a, b, domain, code, row)


def test_socle_unknown_hole_and_bounds():
    report = validate_depth_anchored(
        [_iv("NOPE"), _iv(a=5.0, b=5.0), _iv(a=-1.0)], {"DDH-001"})
    assert len(report.errors) == 3
    assert report.blocking


def test_socle_overlap_is_warning():
    report = validate_depth_anchored(
        [_iv(a=0.0, b=10.0), _iv(a=5.0, b=15.0)], {"DDH-001"})
    assert not report.blocking
    assert any("recouvrement" in w for w in report.warnings)


def test_coded_log_unknown_code():
    report = validate_coded_log(
        [_iv(code="XYZ")], {"LST", "SHL"}, {"DDH-001"})
    assert any("référentiel" in e for e in report.errors)
    ok = validate_coded_log([_iv(code="LST")], {"LST"}, {"DDH-001"})
    assert not ok.blocking and not ok.warnings


def test_assays_numeric_and_qaqc():
    elements = {"Au": ElementSpec("Au", "ppm", lower_dl=0.005)}
    records = [_iv(row=1), _iv(row=2), _iv(row=3), _iv(row=4)]
    values = {
        1: {"Au": "1,25"},
        2: {"Au": "abc"},
        3: {"Au": "-0.1"},
        4: {"Au": "0.001"},
    }
    report = validate_assays(records, elements, values, {"DDH-001"})
    assert any("non numérique" in e for e in report.errors)
    assert any("négative" in e for e in report.errors)
    assert any("limite de détection" in w for w in report.warnings)
    assert not any("1,25" in e for e in report.errors)


def test_assays_undeclared_element():
    report = validate_assays(
        [_iv(row=1)], {"Au": ElementSpec("Au", "ppm")},
        {1: {"Ag": "10"}}, {"DDH-001"})
    assert any("non déclaré" in e for e in report.errors)


def test_empty_assay_value_is_accepted():
    report = validate_assays(
        [_iv(row=1)], {"Au": ElementSpec("Au", "ppm")}, {1: {"Au": ""}},
        {"DDH-001"})
    assert not report.blocking
