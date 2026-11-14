"""Tests du cœur pur ORIG — tournent sans QGIS."""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from DrillMasterOrig.core.model import Collar, SurveyStation
from DrillMasterOrig.core.trajectory import (
    compute_trajectory, build_hole, point_at_depth, validate_surveys)
from DrillMasterOrig.core.units import circular_mean_azimuth, direction_vector


def _collar():
    return Collar("DDH-001", 1000.0, 2000.0, 500.0, 300.0)


def test_direction_vector_conventions():
    dx, dy, dz = direction_vector(0.0, 0.0)
    assert (round(dx, 9), round(dy, 9), round(dz, 9)) == (0.0, 1.0, 0.0)
    dx, dy, dz = direction_vector(90.0, 0.0)
    assert (round(dx, 9), round(dy, 9)) == (1.0, 0.0)
    dx, dy, dz = direction_vector(0.0, 90.0)
    assert (round(dx, 9), round(dy, 9), round(dz, 9)) == (0.0, 0.0, -1.0)
    dx, dy, dz = direction_vector(0.0, -90.0)
    assert round(dz, 9) == 1.0


def test_circular_mean_azimuth():
    assert round(circular_mean_azimuth(359.0, 1.0), 6) == 0.0
    assert round(circular_mean_azimuth(10.0, 30.0), 6) == 20.0


def test_straight_down_hole():
    collar = _collar()
    surveys = [SurveyStation("DDH-001", 100.0, 0.0, 90.0)]
    traj = compute_trajectory(collar, surveys)
    assert len(traj) == 2
    end = traj[-1]
    assert round(end.x, 6) == 1000.0
    assert round(end.y, 6) == 2000.0
    assert round(end.z, 6) == 400.0
    assert round(end.depth, 6) == 100.0


def test_average_angle_matches_v2_formula():
    collar = _collar()
    surveys = [
        SurveyStation("DDH-001", 50.0, 10.0, 20.0),
        SurveyStation("DDH-001", 100.0, 30.0, 40.0),
    ]
    traj = compute_trajectory(collar, surveys, method="average_angle")
    x, y, z = collar.x, collar.y, collar.elevation
    for dl, az, dip in ((50.0, 10.0, 20.0), (50.0, 20.0, 30.0)):
        horiz = dl * math.cos(math.radians(dip))
        x += horiz * math.sin(math.radians(az))
        y += horiz * math.cos(math.radians(az))
        z -= dl * math.sin(math.radians(dip))
    end = traj[-1]
    assert round(end.x, 6) == round(x, 6)
    assert round(end.y, 6) == round(y, 6)
    assert round(end.z, 6) == round(z, 6)


def test_minimum_curvature_constant_build_arc():
    b = math.radians(0.5)
    collar = _collar()
    surveys = [
        SurveyStation("DDH-001", d, 0.0, math.degrees(b * d))
        for d in (0.0, 25.0, 50.0, 75.0, 100.0)
    ]
    traj = compute_trajectory(collar, surveys, method="minimum_curvature")
    end = traj[-1]
    expected_y = collar.y + math.sin(b * 100.0) / b
    expected_z = collar.elevation - (1.0 - math.cos(b * 100.0)) / b
    assert round(end.x, 6) == 1000.0
    assert abs(end.y - expected_y) < 1e-6
    assert abs(end.z - expected_z) < 1e-6


def test_point_at_depth_interpolates():
    collar = _collar()
    surveys = [SurveyStation("DDH-001", 100.0, 0.0, 90.0)]
    traj = compute_trajectory(collar, surveys)
    mid = point_at_depth(traj, 50.0)
    assert round(mid.z, 6) == 450.0
    assert point_at_depth(traj, 150.0) is None
    assert point_at_depth([], 10.0) is None


def test_validate_surveys():
    surveys = [
        SurveyStation("DDH-001", 10.0, 400.0, 90.0),
        SurveyStation("DDH-001", -5.0, 10.0, 90.0),
        SurveyStation("DDH-001", 10.0, 20.0, 90.0),
    ]
    errors = validate_surveys(surveys)
    assert any("profondeur négative" in e for e in errors)
    assert any("azimut hors" in e for e in errors)
    assert any("dupliquées" in e for e in errors)


def test_build_hole_sorted_and_trajectory():
    collar = _collar()
    surveys = [
        SurveyStation("DDH-001", 100.0, 20.0, 60.0),
        SurveyStation("DDH-001", 50.0, 10.0, 30.0),
        SurveyStation("DDH-001", 0.0, 0.0, 0.0),
    ]
    hole = build_hole(collar, surveys)
    assert [s.depth for s in hole.surveys] == [0.0, 50.0, 100.0]
    assert len(hole.trajectory) == 3
    assert hole.trajectory[0].depth == 0.0
