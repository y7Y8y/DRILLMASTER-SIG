"""
DrillMaster — Topographie : ligne de sol le long de la ligne de coupe
======================================================================

v2.9.0 — cascade de sources (décision écran 22/08) :

1. RASTER MNT — échantillonné le long de la ligne par la couche UI
   (QGIS) ; la seule source qui donne une élévation CONTINUE tout le
   long de la ligne (opération standard GDAL, comme Leapfrog/Datamine) ;
2. CSV x;y;z — fourni dans le projet (mesures ponctuelles interpolées) ;
3. COLLETS SEULEMENT — filet de sécurité universel, toujours
   disponible (interpolation linéaire collet à collet).

La couche vectorielle n'est PAS un source natif : interpoler une surface
continue à partir de courbes de niveau ou de points cotés, c'est le rôle
de l'outil d'interpolation de QGIS (TIN, IDW, voisin naturel) — le
plugin guide l'utilisateur (« générez un MNT depuis votre couche, puis
chargez ce MNT ») au lieu de réimplémenter un outil mature.

Ancre aux collets (décision écran) : le MNT est un modèle interpolé
(alimentation, terrassement de plateforme, résolution de pixel) alors que
l'altitude de collet vient d'un levé précis — les deux ne coïncident
presque jamais.  La ligne de surface garde la FORME du MNT (information
topographique entre les forages) mais est recalée pour passer EXACTEMENT
par chaque collet : le collet est la donnée la plus précise de ce point.

La correction est une interpolation COSINUS des écarts (dérivée nulle au
collet et aux bornes de l'atténuation) : aucun coude visible au collet,
l'atténuation est progressive en s'éloignant des points connus.

Contrôle qualité MNT ↔ collets : l'écart entre le MNT échantillonné à la
position XY du collet et l'altitude de collet enregistrée est rapporté
pour CHAQUE collet ; au-delà d'un seuil (défaut 2 m) c'est un signal
(terrassement, erreur de saisie) — affiché, jamais masqué.

v2.9.10 — anti-escalier : densify + moyenne glissante puis
ré-ancrage collets (la ligne MNT ne « marche » plus pixel
par pixel — retour écran).

Pure Python, sans Qt ni QGIS — testable hors QGIS.
"""
from __future__ import annotations

import math


# ---------------------------------------------------------------------------
# Profil de base
# ---------------------------------------------------------------------------
def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def profile_at(profile, along) -> float | None:
    """Élévation du profil en ``along`` (interpolation linéaire).

    ``profile`` = liste ordonnée ``(along, elev)``.  None si le profil est
    vide ou si ``along`` est non fini.  En dehors de l'étendue du profil :
    valeur de l'extrémité la plus proche (profil « plat » aux bords).
    """
    if not profile or not _finite(along):
        return None
    if along <= profile[0][0]:
        return float(profile[0][1])
    if along >= profile[-1][0]:
        return float(profile[-1][1])
    for (a0, e0), (a1, e1) in zip(profile, profile[1:]):
        if a0 <= along <= a1:
            if a1 - a0 < 1e-9:
                return float(e0)
            t = (float(along) - float(a0)) / (float(a1) - float(a0))
            return float(e0) + t * (float(e1) - float(e0))
    return None  # pragma: no cover — inatteignable (bornes gérées)


def profile_from_collars(collars, a_min: float, a_max: float) -> list[tuple[float, float]]:
    """Profil « collets seulement » : interpolation linéaire par morceaux
    passant EXACTEMENT par les collets, plat au-delà des extrêmes.

    ``collars`` = liste ``(along, elev)`` des collets DE LA COUPE (dans le
    buffer).  La grille du profil est l'union de l'échantillonnage régulier
    (97 points) et des abscisses des collets : chaque collet est un
    SOMMET du profil — la courbe passe par lui au centimètre, pas « à
    côté » (décision écran : le collet est la donnée la plus précise du
    point).  Vide si aucun collet ou si l'étendue est nulle.
    """
    pts = sorted({(float(a), float(e)) for a, e in collars
                  if _finite(a) and _finite(e)})
    if not pts:
        return []
    a_min, a_max = float(a_min), float(a_max)
    if a_max - a_min < 1e-9:
        return [(a_min, pts[0][1])]
    base = [a_min + i * (a_max - a_min) / 96.0 for i in range(97)]
    grid = sorted(set(base) | {a for a, _ in pts if a_min <= a <= a_max})
    collar_elev = dict(pts)
    out = []
    for a in grid:
        if a in collar_elev:
            out.append((a, collar_elev[a]))
        else:
            out.append((a, profile_at(pts, a)))
    return out


# ---------------------------------------------------------------------------
# Contrôle qualité MNT ↔ collets
# ---------------------------------------------------------------------------
def collar_deviations(profile, collars) -> list[dict]:
    """Écart MNT ↔ collet, POUR CHAQUE COLLET (jamais masqué).

    ``collars`` = liste ``(along, elev, hole_id)``.  Retourne
    ``[{"hole_id", "along", "dem_elev", "collar_elev", "diff"}]`` où
    ``diff = elev_collet − elev_MNT`` (positif = le collet est AU-DESSUS
    du MNT).  Un collet dont le MNT n'a pas de valeur (NoData) n'a pas de
    ``dem_elev`` — il est signalé, pas écarté.
    """
    out = []
    for item in collars:
        if len(item) >= 3:
            along, elev, hole_id = item[0], item[1], item[2]
        else:
            along, elev = item
            hole_id = ""
        if not (_finite(along) and _finite(elev)):
            continue
        dem = profile_at(profile, along)
        out.append({
            "hole_id": str(hole_id),
            "along": float(along),
            "dem_elev": float(dem) if _finite(dem) else None,
            "collar_elev": float(elev),
            "diff": (float(elev) - dem) if _finite(dem) else None,
        })
    return out


# ---------------------------------------------------------------------------
# Ancrage aux collets
# ---------------------------------------------------------------------------
def _decay_length(collars_along) -> float:
    """Portée d'atténuation L (m) : 25 % de l'étendue collet-à-collet,
    bornée à [15, 100] m ; un seul collet → 30 m."""
    if len(collars_along) < 2:
        return 30.0
    span = max(collars_along) - min(collars_along)
    return min(max(0.25 * span, 15.0), 100.0)


def anchor_profile_to_collars(profile, collars,
                              decay: float | None = None
                              ) -> list[tuple[float, float]]:
    """Recaler le profil pour qu'il passe EXACTEMENT par chaque collet.

    La correction ``C(a)`` vaut l'écart ``Δ_j = elev_collet_j −
    profile(along_j)`` au collet j, interpolée SANS COUDE (dérivée nulle
    partout, décision écran « pas de coude visible au collet ») :

    - entre deux collets consécutifs : blend COSINUS Δ_j → Δ_{j+1}
      (dérivée nulle aux deux collets) ;
    - à l'extérieur des collets extrêmes : Δ atténué par cosine sur la
      portée L (dérivée nulle au collet ET à la borne → aucun coude) ;
    - un seul collet : atténuation des deux côtés ;
    - aucun collet (ou tous les écarts nuls) : profil inchangé.

    Le profil ancré est rééchantillonné sur la grille DU PROFIL D'ENTRÉE
    (même pas, mêmes abscisses — plus de point, pas de point perdu).

    ``collars`` = liste ``(along, elev)`` ou ``(along, elev, hole_id)``.
    Le profil ancré est la grille d'entrée ENRICHIE des abscisses des
    collets : chaque collet est un SOMMET auquel la valeur est EXACTEMENT
    l'altitude de collet (décision écran « passage exact »), quel que soit
    le pas d'échantillonnage du MNT.
    Le QC MNT ↔ collets se fait SÉPARÉMENT avec :func:`collar_deviations`
    sur le profil d'origine (les écarts sont les mêmes avant/après
    ancrage — une seule source de vérité pour les chiffres affichés).
    """
    pts = sorted({(float(a), float(e)) for a, e in
                  ((c[0], c[1]) for c in collars)
                  if _finite(a) and _finite(e)})
    if not profile or not pts:
        return list(profile or [])
    base = [(a, e) for a, e in profile if _finite(a) and _finite(e)]
    if not base:
        return []

    collar_elev = {}
    for a, e in pts:
        collar_elev.setdefault(a, e)

    # Δ_j = écart collet − MNT (None si le MNT n'a pas de valeur là —
    # collet hors couverture : pas ancrable, pas masqué non plus).
    anchors = []
    for a, e in pts:
        mnt = profile_at(base, a)
        if not _finite(mnt):
            continue
        d = e - mnt
        if d != 0.0:
            anchors.append((a, d))
    if not anchors:
        return base

    L = float(decay) if decay is not None else _decay_length(
        [a for a, _ in anchors])
    a_first = anchors[0][0]
    a_last = anchors[-1][0]

    def correction(a: float) -> float:
        if a <= a_first:
            t = (a_first - a) / L
            d = anchors[0][1]
        elif a >= a_last:
            t = (a - a_last) / L
            d = anchors[-1][1]
        else:
            # entre deux collets : blend cosine du Δ de gauche au Δ de
            # droite (dérivée nulle aux deux collets)
            for (a0, d0), (a1, d1) in zip(anchors, anchors[1:]):
                if a0 <= a <= a1:
                    u = (a - a0) / (a1 - a0) if a1 - a0 > 1e-9 else 0.0
                    return (d0 * 0.5 * (1.0 + math.cos(math.pi * u))
                            + d1 * 0.5 * (1.0 - math.cos(math.pi * u)))
            return 0.0  # pragma: no cover — inatteignable (bornes gérées)
        if t >= 1.0:
            return 0.0
        if t <= 0.0:
            return d
        return d * 0.5 * (1.0 + math.cos(math.pi * t))

    grid = sorted({a for a, _ in base} | set(collar_elev))
    out = []
    for a in grid:
        if a in collar_elev:
            out.append((a, collar_elev[a]))      # sommet EXACT au collet
        else:
            e = profile_at(base, a)
            out.append((a, e + correction(a) if _finite(e) else e))
    return out


# ---------------------------------------------------------------------------
# Lissage / densification (anti-escalier MNT)
# ---------------------------------------------------------------------------
def densify_profile(profile, step: float | None = None,
                    max_points: int = 2000) -> list[tuple[float, float]]:
    """Ré-échantillonne le profil sur une grille régulière plus fine.

    ``step`` en mètres d'abscisse (along) ; défaut = 1/4 du pas médian
    d'origine (borné à [0,5 ; 5] m).  Plafond ``max_points`` pour ne
    jamais exploser mémoire / dessin.  Interpolation linéaire entre
    sommets — les abscisses d'origine sont CONSERVÉES (union) pour ne
    pas perdre un collet / un pic exact.
    """
    base = [(float(a), float(e)) for a, e in (profile or [])
            if _finite(a) and _finite(e)]
    if len(base) < 2:
        return list(base)
    base.sort(key=lambda p: p[0])
    # unique along (keep last elev on ties)
    uniq = {}
    for a, e in base:
        uniq[a] = e
    base = sorted(uniq.items())
    a0, a1 = base[0][0], base[-1][0]
    span = a1 - a0
    if span < 1e-9:
        return list(base)
    if step is None:
        gaps = [base[i + 1][0] - base[i][0]
                for i in range(len(base) - 1)
                if base[i + 1][0] - base[i][0] > 1e-12]
        med = sorted(gaps)[len(gaps) // 2] if gaps else 2.0
        step = max(0.5, min(5.0, med * 0.25))
    step = max(float(step), span / max(int(max_points) - 1, 1))
    n = int(round(span / step)) + 1
    n = max(n, 2)
    n = min(n, int(max_points))
    grid = [a0 + i * (span / (n - 1)) for i in range(n)]
    # conserver les sommets d'origine (collets, pics)
    grid = sorted(set(grid) | {a for a, _ in base})
    return [(a, profile_at(base, a)) for a in grid]


def smooth_profile(profile, half_window: int = 3,
                   passes: int = 2) -> list[tuple[float, float]]:
    """Lissage moyenne glissante (anti-escalier pixel MNT).

    v2.9.10 — un MNT échantillonné pixel par pixel produit une ligne
    « en escalier » (retour écran) : chaque pixel = un palier.  On
    lisse par moyenne glissante centré (fenêtre ``2*half_window+1``),
    ``passes`` fois.  Les EXTRÉMITÉS sont figées (pas de dérive hors
    corridor).  Les sommets ne sont PAS forcés aux collets ici —
    :func:`anchor_profile_to_collars` reste la passe qui ancre.
    Profil < 3 points : renvoyé tel quel.
    """
    base = [(float(a), float(e)) for a, e in (profile or [])
            if _finite(a) and _finite(e)]
    if len(base) < 3:
        return list(base)
    base.sort(key=lambda p: p[0])
    hw = max(int(half_window), 1)
    n_pass = max(int(passes), 1)
    elevs = [e for _, e in base]
    alongs = [a for a, _ in base]
    n = len(elevs)
    for _ in range(n_pass):
        out = elevs[:]
        for i in range(n):
            if i == 0 or i == n - 1:
                continue  # extrémités figées
            lo = max(0, i - hw)
            hi = min(n, i + hw + 1)
            window = elevs[lo:hi]
            out[i] = sum(window) / len(window)
        elevs = out
    return list(zip(alongs, elevs))


def refine_surface_profile(profile, collars=None) -> list[tuple[float, float]]:
    """Pipeline anti-escalier : densifier → lisser → ré-ancrer collets.

    Ordre voulu (v2.9.10) :
      1. densify — plus de points entre pixels MNT ;
      2. smooth  — casse les paliers d'un pixel ;
      3. anchor  — repasse EXACTEMENT par chaque collet (priorité
         levé terrain, décision écran inchangée).

    Sans collets, s'arrête après le lissage.  Entrée vide → [].
    """
    if not profile:
        return []
    dense = densify_profile(profile)
    smooth = smooth_profile(dense, half_window=3, passes=2)
    pts = []
    for c in (collars or []):
        try:
            pts.append((c[0], c[1]))
        except (TypeError, IndexError):
            continue
    if pts:
        return anchor_profile_to_collars(smooth, pts)
    return smooth


# ---------------------------------------------------------------------------
# Étendue verticale
# ---------------------------------------------------------------------------

def merge_surface_into_range(min_elev: float, max_elev: float,
                             surface) -> tuple[float, float]:
    """Bornes VERTICALES visuelles : trajectoire ∪ surface + respiration.

    v2.9.72 — marge bas 8 m (demande user) pour eoh vs axe distance :
    - bas  : max(8 m, 5 % span) ;
    - haut : max(2 m, 2 % span) pour la topo.
    Les ticks restent sur data_min/max_elev (pas dans la marge).
    """
    lo, hi = float(min_elev), float(max_elev)
    elevs = [float(e) for _, e in (surface or []) if _finite(e)]
    if elevs:
        lo = min(lo, min(elevs))
        hi = max(hi, max(elevs))
    span = max(hi - lo, 1.0)
    pad_lo = max(8.0, span * 0.05)   # air sous fonds de trou / eoh
    pad_hi = max(2.0, span * 0.02)
    return lo - pad_lo, hi + pad_hi


# ---------------------------------------------------------------------------
# Surface 3D : grille interpolée + isocontours (v2.9.141 — P1 / P2)
# ---------------------------------------------------------------------------
# La vue 3D a besoin d'une SURFACE (pas d'un simple profil) : on interpole
# des points épars (MNT échantillonné, CSV, ou collets) sur une grille
# régulière (X, Y), puis on en tire des courbes de niveau par marching
# squares.  Pure Python, testable hors QGIS — l'échantillonnage du raster
# QGIS vit dans la couche UI (ui/raster_surface.py), comme pour la coupe 2D.
# ---------------------------------------------------------------------------

def bounds_from_points(points, pad_ratio: float = 0.1,
                       min_span: float = 15.0):
    """Emprise (min_x, max_x, min_y, max_y) avec marge, ou None.

    ``points`` = itérable de ``(x, y, ...)``.  La marge est un ratio de la
    plus grande portée (jamais moins de ``min_span`` pour une zone réduite).
    """
    pts = []
    for p in points:
        try:
            x, y = p[0], p[1]
        except (TypeError, IndexError):
            continue
        if _finite(x) and _finite(y):
            pts.append((float(x), float(y)))
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, float(min_span))
    span_y = max(max_y - min_y, float(min_span))
    pad_x = span_x * float(pad_ratio)
    pad_y = span_y * float(pad_ratio)
    return (min_x - pad_x, max_x + pad_x, min_y - pad_y, max_y + pad_y)


def _idw_z(pts, x: float, y: float, power: float = 2.0,
           smoothing: float = 1.0) -> float:
    """Élévation IDW (inverse-distance) d'un point ``(x, y)``.

    Un échantillon EXACTEMENT sur le nœud (distance ~0) reprend sa valeur
    (pas de lissage du MNT échantillonné) ; sinon moyenne pondérée en
    1/(d^power + smoothing), repli plus proche voisin si dénominateur nul.
    """
    total = 0.0
    wsum = 0.0
    nearest = None
    nearest_d = None
    for px, py, pz in pts:
        dx = px - x
        dy = py - y
        d2 = dx * dx + dy * dy
        if d2 < 1e-12:
            return float(pz)  # échantillon exact : valeur exacte
        if nearest_d is None or d2 < nearest_d:
            nearest_d = d2
            nearest = pz
        d = math.sqrt(d2)
        w = 1.0 / (d ** float(power) + float(smoothing))
        total += w * pz
        wsum += w
    if wsum > 0:
        return total / wsum
    return float(nearest) if nearest is not None else 0.0


def build_surface_grid(points, bounds=None, nx: int = 24, ny: int = 24,
                       power: float = 2.0, smoothing: float = 1.0):
    """Interpole des points épars ``(x, y, z)`` sur une grille régulière.

    Retourne une liste de ``(ny+1)`` lignes de ``(nx+1)`` tuples
    ``(x, y, z)``, ou None si < 3 points valides / emprise nulle.

    ATTENTION — coût O(n²·m) : pour chaque nœud, on parcourt TOUS les points.
    Pour des échantillons DÉJÀ régulièrement espacés (raster), préférer
    :func:`grid_from_gridded_samples` (O(n²)).
    """
    pts = [(float(x), float(y), float(z)) for x, y, z in points
           if _finite(x) and _finite(y) and _finite(z)]
    if len(pts) < 3:
        return None
    if bounds is None:
        bounds = bounds_from_points(pts)
    if bounds is None:
        return None
    min_x, max_x, min_y, max_y = bounds
    if max_x - min_x <= 0 or max_y - min_y <= 0:
        return None
    nx = max(int(nx), 2)
    ny = max(int(ny), 2)
    rows = []
    for i in range(ny + 1):
        gy = min_y + (max_y - min_y) * i / ny
        row = []
        for j in range(nx + 1):
            gx = min_x + (max_x - min_x) * j / nx
            row.append((gx, gy, _idw_z(pts, gx, gy, power, smoothing)))
        rows.append(row)
    return rows


def grid_from_gridded_samples(samples, bounds, n: int):
    """Construit la grille DIRECTEMENT depuis des échantillons réguliers.

    ``samples`` = liste ``(x, y, z)`` issue de l'échantillonnage d'un raster
    sur une grille ``(n+1)×(n+1)`` (lignes = y, colonnes = x).  Chaque
    échantillon est placé dans SA cellule (par coordonnée), les trous
    (NoData) sont comblés par le plus proche échantillon présent.

    O(n²) — évite l'interpolation IDW O(n⁴) de :func:`build_surface_grid`
    quand les points sont déjà sur une grille (le cas du MNT raster 3D).
    Retourne la même structure que ``build_surface_grid``, ou None.
    """
    min_x, max_x, min_y, max_y = bounds
    if max_x - min_x <= 0 or max_y - min_y <= 0:
        return None
    n = max(int(n), 2)
    cell = {}
    for (x, y, z) in samples:
        if not (_finite(x) and _finite(y) and _finite(z)):
            continue
        j = int(round((x - min_x) / (max_x - min_x) * n))
        i = int(round((y - min_y) / (max_y - min_y) * n))
        j = max(0, min(n, j))
        i = max(0, min(n, i))
        cell[(i, j)] = float(z)
    if not cell:
        return None

    # Recherche du plus proche échantillon présent (pour combler les trous).
    def _nearest(i, j):
        best = None
        best_d = None
        for (ci, cj), z in cell.items():
            d = (ci - i) ** 2 + (cj - j) ** 2
            if best_d is None or d < best_d:
                best_d = d
                best = z
        return best if best is not None else 0.0

    rows = []
    for i in range(n + 1):
        gy = min_y + (max_y - min_y) * i / n
        row = []
        for j in range(n + 1):
            gx = min_x + (max_x - min_x) * j / n
            z = cell[(i, j)] if (i, j) in cell else _nearest(i, j)
            row.append((gx, gy, z))
        rows.append(row)
    return rows


def smooth_surface_grid(grid, passes: int = 1, center: float = 4.0):
    """Lissage LÉGER d'une grille de surface (v2.9.146 — « naturel »).

    Retour écran MNT : « trop pixelisé, mais ne lisse pas trop, je veux
    du naturel ».  Un seul passage par défaut d'un noyau gaussien 3×3
    (poids centre ``center``, bords 1, croix 2 — normalisés) :

    - un RAMP linéaire reste linéaire (le noyau préserve les plans) ;
    - un pic isolé est amorti (fini l'effet « marches d'escalier » du
      maillage, sans écraser le relief) ;
    - les bords sont conservés TELS QUELS (pas de rétrécissement).

    Purement cosmétique (rendu 3D) : la ligne de sol 2D et les valeurs
    du DEM ne sont PAS modifiées.
    """
    if not grid or not grid[0]:
        return grid
    passes = max(0, int(passes))
    if passes <= 0:
        return grid
    ny = len(grid) - 1
    nx = len(grid[0]) - 1
    if nx < 2 or ny < 2:
        return grid

    def _kernel(zs):
        # zs = [z00, z10, z11, z01, centre] — noyau gaussien 3×3.
        w = (1.0, 2.0, 1.0, 2.0, float(center), 2.0, 1.0, 2.0, 1.0)
        total = 0.0
        wsum = 0.0
        for z, weight in zip(zs, w):
            total += z * weight
            wsum += weight
        return total / wsum if wsum else zs[4]

    out = [row[:] for row in grid]
    for _ in range(passes):
        src = [row[:] for row in out]
        for i in range(1, ny):
            for j in range(1, nx):
                zs = (
                    src[i - 1][j - 1][2], src[i - 1][j][2], src[i - 1][j + 1][2],
                    src[i][j - 1][2], src[i][j][2], src[i][j + 1][2],
                    src[i + 1][j - 1][2], src[i + 1][j][2], src[i + 1][j + 1][2],
                )
                x, y, _z = out[i][j]
                out[i][j] = (x, y, _kernel(zs))
    return out


def grid_z_at(grid, x: float, y: float):
    """Élévation par interpolation bilinéaire sur la grille ; None hors
    emprise.  ``grid`` = structure de :func:`build_surface_grid`.
    """
    if not grid or not grid[0]:
        return None
    ny = len(grid) - 1
    nx = len(grid[0]) - 1
    if nx < 1 or ny < 1:
        return None
    x0, y0 = grid[0][0][0], grid[0][0][1]
    x1, y1 = grid[ny][nx][0], grid[ny][nx][1]
    if x < x0 or x > x1 or y < y0 or y > y1:
        return None
    fx = (x - x0) / (x1 - x0) * nx
    fy = (y - y0) / (y1 - y0) * ny
    i = max(0, min(nx - 1, int(math.floor(fx))))
    j = max(0, min(ny - 1, int(math.floor(fy))))
    tx = fx - i
    ty = fy - j
    z00 = grid[j][i][2]
    z10 = grid[j][i + 1][2]
    z01 = grid[j + 1][i][2]
    z11 = grid[j + 1][i + 1][2]
    z0 = z00 + (z10 - z00) * tx
    z1 = z01 + (z11 - z01) * tx
    return z0 + (z1 - z0) * ty


def _grid_decay_length(anchors) -> float:
    """Portée d'atténuation L (m) pour l'ancrage grille : 25 % de la plus
    grande étendue des ancres, bornée à [15, 100] m ; une seule ancre → 30 m.
    """
    if len(anchors) < 2:
        return 30.0
    xs = [a[0] for a in anchors]
    ys = [a[1] for a in anchors]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
    return min(max(0.25 * span, 15.0), 100.0)


def anchor_grid_to_collars(grid, collars, decay=None):
    """Recale une grille (lignes de ``(x, y, z)``) pour passer EXACTEMENT par
    chaque collet — même philosophie que :func:`anchor_profile_to_collars`,
    mais en 2D (X, Y) pour la surface 3D.

    La correction est un champ radial COSINUS (dérivée nulle au collet et à la
    portée ``L``) : aucun coude, atténuation progressive.  Un nœud exactement
    sur un collet reprend son altitude.  Loin des collets (> L), la grille
    garde la valeur du MNT (interpolation fiable entre les forages).

    ``collars`` = liste ``(x, y, z)``.  Retourne une nouvelle grille (l'entrée
    n'est pas modifiée).
    """
    if not grid or not collars:
        return grid
    anchors = []
    for (cx, cy, cz) in collars:
        if not (_finite(cx) and _finite(cy) and _finite(cz)):
            continue
        gz = grid_z_at(grid, cx, cy)
        if gz is None or not _finite(gz):
            continue
        d = float(cz) - gz
        if abs(d) > 1e-9:
            anchors.append((float(cx), float(cy), d))
    if not anchors:
        return grid

    L = float(decay) if decay is not None else _grid_decay_length(anchors)

    def _correction(x, y):
        num = 0.0
        den = 0.0
        for ax, ay, d in anchors:
            dist = math.hypot(x - ax, y - ay)
            t = dist / L
            if t >= 1.0:
                continue
            w = 0.5 * (1.0 + math.cos(math.pi * t))
            num += w * d
            den += w
        return num / den if den > 1e-9 else 0.0

    out = []
    for row in grid:
        new_row = []
        for (x, y, z) in row:
            new_row.append((x, y, z + _correction(x, y)))
        out.append(new_row)
    return out


# Tables de marching squares (Bourke) — coins BL=0, BR=1, TR=2, TL=3.
_MS_EDGE_TABLE = (0, 9, 3, 10, 6, 15, 5, 12, 12, 5, 15, 6, 10, 3, 9, 0)
_MS_LINE_TABLE = (
    (), (0, 3), (0, 1), (1, 3), (1, 2), (0, 1, 2, 3), (0, 2), (2, 3),
    (2, 3), (0, 2), (0, 3, 1, 2), (1, 2), (1, 3), (0, 1), (0, 3), (),
)
_MS_EDGES = ((0, 1), (1, 2), (2, 3), (3, 0))  # edge i relie les coins


def _march_cell(xs, ys, zs, level):
    """Segments (x0, y0, x1, y1) traversés par ``level`` dans une cellule.

    ``xs``/``ys``/``zs`` = 4 coins (BL, BR, TR, TL).  La table standard de
    Bourke résout les cas ambigus (sellle) en deux segments sans croisement.
    """
    which = 0
    if zs[0] > level:
        which |= 1
    if zs[1] > level:
        which |= 2
    if zs[2] > level:
        which |= 4
    if zs[3] > level:
        which |= 8
    lines = _MS_LINE_TABLE[which]
    if not lines:
        return []

    def interp(a, b):
        za, zb = zs[a], zs[b]
        if zb - za == 0:
            t = 0.5
        else:
            t = (level - za) / (zb - za)
        t = max(0.0, min(1.0, t))
        return (xs[a] + (xs[b] - xs[a]) * t,
                ys[a] + (ys[b] - ys[a]) * t)

    out = []
    for k in range(0, len(lines), 2):
        e0, e1 = lines[k], lines[k + 1]
        p0 = interp(*_MS_EDGES[e0])
        p1 = interp(*_MS_EDGES[e1])
        out.append((p0[0], p0[1], p1[0], p1[1]))
    return out


def contour_segments(grid, levels):
    """Isocontours par marching squares sur une grille.

    Retourne ``{niveau: [(x0, y0, x1, y1), ...]}`` en coordonnées RÉELLES
    (plan XY).  Le rendu 3D projette chaque extrémité à l'altitude du
    niveau.  ``grid`` = structure de :func:`build_surface_grid`.
    """
    if not grid or not grid[0]:
        return {}
    ny = len(grid) - 1
    nx = len(grid[0]) - 1
    if nx < 1 or ny < 1:
        return {}
    out = {float(lv): [] for lv in levels}
    for j in range(ny):
        for i in range(nx):
            # coins BL, BR, TR, TL
            c = [grid[j][i], grid[j][i + 1],
                 grid[j + 1][i + 1], grid[j + 1][i]]
            xs = [p[0] for p in c]
            ys = [p[1] for p in c]
            zs = [p[2] for p in c]
            for lv in levels:
                out[lv].extend(_march_cell(xs, ys, zs, lv))
    return out


def contour_levels(zmin: float, zmax: float, step: float | None = None,
                   max_levels: int = 20):
    """Niveaux d'isocontours réguliers dans ``[zmin, zmax]``.

    ``step`` explicite (m) sinon pas « joli » auto (≈ étendue / 8), borné à
    ``max_levels`` lignes.
    """
    lo, hi = float(zmin), float(zmax)
    if hi <= lo:
        return []
    if step is None:
        raw = (hi - lo) / 8.0
        pw = 10.0 ** math.floor(math.log10(raw)) if raw > 0 else 1.0
        frac = raw / pw
        if frac < 1.5:
            step = 1.0 * pw
        elif frac < 3.5:
            step = 2.0 * pw
        elif frac < 7.5:
            step = 5.0 * pw
        else:
            step = 10.0 * pw
    step = float(step)
    if step <= 0:
        return []
    first = math.ceil(lo / step) * step
    levels = []
    v = first
    while v <= hi + 1e-9 and len(levels) < max_levels:
        levels.append(round(v, 9))
        v += step
    return levels
