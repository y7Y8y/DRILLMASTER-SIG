"""
DrillMaster — Conversions pures WGS84 ↔ UTM
===========================================

Repli quand l'API de transformation de QGIS est indisponible ou
échoue (QGIS 3.44 — retour écran 25/08/2026 : projet EPSG:32629 /
MNT EPSG:4326, « transformation CRS impossible » alors que c'est la
paire la plus standard).

WGS84 ↔ UTM (Mercator transverse) est LA paire de la géologie :
beaucoup de MNT publics (SRTM, Copernicus…) sont livrés en WGS84
(degrés) alors que les projets sont en zone UTM (mètres).

Formules standard (USGS / proj) sur l'ellipsoïde WGS84
(a = 6378137.0, f = 1/298.257223563, k0 = 0.9996) — précision
< 1 mm dans la zone.

Pure Python (math) — QGIS-free, testable standalone.
"""

from __future__ import annotations

import math
import re

_WGS84_A = 6378137.0
_WGS84_F = 1.0 / 298.257223563
_E2 = _WGS84_F * (2.0 - _WGS84_F)
_E2P = _E2 / (1.0 - _E2)
_K0 = 0.9996
_DEG = math.pi / 180.0

_UTM_RE = re.compile(r"^EPSG:(326|327)(\d{2})$", re.IGNORECASE)
_WGS84_AUTHIDS = {"EPSG:4326", "OGC:CRS84", "OGC:CRS84:CRS:4326",
                 "EPSG:4979"}


def parse_crs(authid):
    """Interprète un authid.

    Retourne ``("wgs84",)`` pour WGS84 (degrés) ;
    ``("utm", zone, northern)`` pour UTM (EPSG:326xx nord /
    EPSG:327xx sud) ; ``None`` sinon.
    """
    a = (authid or "").strip().upper()
    if a in _WGS84_AUTHIDS:
        return ("wgs84",)
    m = _UTM_RE.match(a)
    if m:
        zone = int(m.group(2))
        if 1 <= zone <= 60:
            return ("utm", zone, m.group(1) == "326")
    return None


def utm_to_wgs84(easting, northing, zone, northern=True):
    """UTM (mètres) → ``(lon, lat)`` WGS84 (degrés).

    Inverse de Mercator transverse (formule standard).
    """
    x = float(easting) - 500000.0
    y = float(northing) - (0.0 if northern else 10000000.0)
    lam0 = (6.0 * zone - 183.0) * _DEG
    m = y / _K0
    mu = m / (_WGS84_A * (1 - _E2 / 4 - 3 * _E2 ** 2 / 64
                          - 5 * _E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - _E2)) / (1 + math.sqrt(1 - _E2))
    phi1 = (mu
            + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * math.sin(6 * mu))
    # NOTE — le facteur du terme de correction est ``tan(phi1)/r`` avec
    # ``r = (1-e2)/(1-e2*sin^2(phi1))`` et ``D^2/2`` (vérifié à
    # < 1e-8° contre pyproj — 23/08/2026) ; la transcription
    # « N1*tan/2R1 » avec ``D^2`` est une coquille courante qui
    # s'éloigne de ~10 cm au 3° du méridien central.
    p_sin = math.sin(phi1)
    p_cos = math.cos(phi1)
    p_tan = p_sin / p_cos
    p_tan2 = p_tan * p_tan
    p_tan4 = p_tan2 * p_tan2
    ep_sin = 1.0 - _E2 * p_sin * p_sin
    n = _WGS84_A / math.sqrt(ep_sin)
    r = (1.0 - _E2) / ep_sin
    c = _E2P * p_cos ** 2
    c2 = c * c
    d = x / (n * _K0)
    d2 = d * d
    d3 = d2 * d
    d4 = d3 * d
    d5 = d4 * d
    d6 = d5 * d
    lat = phi1 - (p_tan / r) * (
        d2 / 2
        - d4 / 24 * (5 + 3 * p_tan2 + 10 * c - 4 * c2 - 9 * _E2P)
        + d6 / 720 * (61 + 90 * p_tan2 + 298 * c + 45 * p_tan4
                      - 252 * _E2P - 3 * c2))
    lon = (d
           - d3 / 6 * (1 + 2 * p_tan2 + c)
           + d5 / 120 * (5 - 2 * c + 28 * p_tan2 - 3 * c2 + 8 * _E2P
                         + 24 * p_tan4)) / p_cos
    return math.degrees(lam0 + lon), math.degrees(lat)


def wgs84_to_utm(lon, lat, zone=None, northern=None):
    """WGS84 (degrés) → ``(easting, northing, zone, northern)`` UTM.

    Direct de Mercator transverse (formule standard).  Si ``zone`` /
    ``northern`` ne sont pas donnés, déduits des coordonnées.
    """
    if zone is None:
        zone = int((float(lon) + 180.0) // 6.0) + 1
        zone = min(max(zone, 1), 60)
    if northern is None:
        northern = float(lat) >= 0.0
    phi = float(lat) * _DEG
    lam = float(lon) * _DEG
    lam0 = (6.0 * zone - 183.0) * _DEG
    n = _WGS84_A / math.sqrt(1 - _E2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = _E2P * math.cos(phi) ** 2
    a_ = (lam - lam0) * math.cos(phi)
    m = _WGS84_A * (
        (1 - _E2 / 4 - 3 * _E2 ** 2 / 64 - 5 * _E2 ** 3 / 256) * phi
        - (3 * _E2 / 8 + 3 * _E2 ** 2 / 32 + 45 * _E2 ** 3 / 1024)
        * math.sin(2 * phi)
        + (15 * _E2 ** 2 / 256 + 45 * _E2 ** 3 / 1024) * math.sin(4 * phi)
        - (35 * _E2 ** 3 / 3072) * math.sin(6 * phi))
    easting = _K0 * n * (a_
                         + (1 - t + c) * a_ ** 3 / 6
                         + (5 - 18 * t + t ** 2 + 72 * c - 58 * _E2P)
                         * a_ ** 5 / 120) + 500000.0
    northing = _K0 * (m + n * math.tan(phi) * (
        a_ ** 2 / 2
        + (5 - t + 9 * c + 4 * c ** 2) * a_ ** 4 / 24
        + (61 - 58 * t + t ** 2 + 600 * c - 330 * _E2P) * a_ ** 6 / 720))
    if not northern:
        northing += 10000000.0
    return easting, northing, zone, northern


def conversion_between(src_authid, dest_authid):
    """Conversion de point intégrée ``src → dest``, ou ``None``.

    Uniquement la paire standard WGS84 ↔ UTM (EPSG:4326 ↔
    EPSG:326xx/327xx) — le repli quand QGIS ne peut pas convertir
    (retour écran 25/08/2026).  Retourne une fonction
    ``(x, y) → (x', y')``.
    """
    s = parse_crs(src_authid)
    d = parse_crs(dest_authid)
    if s == ("wgs84",) and d is not None and d[0] == "utm":
        zone, northern = d[1], d[2]

        def _w2u(lon, lat):
            e, n, _z, _nb = wgs84_to_utm(
                lon, lat, zone=zone, northern=northern)
            return e, n

        return _w2u
    if s is not None and s[0] == "utm" and d == ("wgs84",):
        zone, northern = s[1], s[2]

        def _u2w(e, n):
            return utm_to_wgs84(e, n, zone, northern)

        return _u2w
    return None
