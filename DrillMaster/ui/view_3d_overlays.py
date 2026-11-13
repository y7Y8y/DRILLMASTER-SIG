"""DrillMaster — Overlays de la Vue 3D (volet 1, tranche 2, v2.9.146).

Couche PRÉSENTATION flottante extraite de ``ui/view_3d.py`` (SPEC) :
légende, gizmo d'orientation, badge d'exagération, infobulle de survol.

Règle anti-chevauchement (SPEC B-4) : les positions des overlays fixes
sont déclarées dans UNE SEULE fonction — ``overlay_layout`` — pure et
testée (collision légende ↔ gizmo évitée par décalage vertical).
Le canvas appelle ces fonctions via des délégations à une ligne.
"""

from __future__ import annotations

import math
from typing import Optional

from qgis.PyQt.QtCore import QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QFontMetrics, QPen, QPolygonF

from ..core.multi_assay import format_grade_value
from ..core.structure_classify import structure_family
from .overlay_layout import overlay_layout  # noqa: F401 — réexporté
from ..core.section import assay_ramp_rgb


def _tr(text):
    """v2.9.236 — Lot 4 : légendes 3D traduisibles (drawText)."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("View3DOverlay", text)


def _imagery_material_label(key: str) -> str:
    """Libellé du badge Imagerie (générique, traduit à l'affichage)."""
    _MAP = {
        "core": _tr("Carotte"), "rc": _tr("RC"), "auger": _tr("Auger"),
        "pit": _tr("Puits droit"), "other": _tr("Autre"),
    }
    return _MAP.get(str(key or "").casefold(), _tr("Imagerie"))


def _imagery_badge_color(canvas, dh, material_key) -> QColor:
    """Couleur de pastille Imagerie : mêmes conventions que le badge 3D.

    Gris-bleu = toutes les photos de ce matériau sont présentes ;
    orange = au moins une absente ; rouge = au moins une illisible.
    Aucune valeur/plage/nom codé en dur.
    """
    from .view_3d_renderer import _imagery_file_present
    project = getattr(canvas, "_project_ref", None)
    provider = getattr(canvas, "imagery_source_dir_provider", None)
    source = str(provider() or "") if callable(provider) else ""
    has_missing = has_unreadable = False
    for rec in (getattr(dh, "imagery", None) or []):
        if str(getattr(rec, "material_label", "") or "").casefold() != (
                str(material_key or "").casefold()):
            continue
        try:
            present = _imagery_file_present(
                canvas, project, getattr(rec, "image_path", ""), source)
        except Exception as _stat_exc:
            # Défaut prudent du badge légende : fichier interrogé mais
            # stat inconnu → considéré illisible (jamais muet).
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : légende imagerie — stat fichier",
                          _stat_exc)
            has_unreadable = True
            continue
        if not present:
            has_missing = True
    if has_unreadable:
        return QColor("#C0392B")
    if has_missing:
        return QColor("#F39C12")
    return QColor("#5D6D7E")


def _imagery_legend_entries(canvas):
    """Entrées de légende Imagerie : un badge-lettre par matériau présent.

    Générique : collecte les matériaux réellement présents sur les forages
    visibles, dans l'ordre alphabétique des libellés.  Clé affichée =
    lettre du badge 3D (C/P/O/A/R), survol = libellé complet.
    """
    from .section_imagery import _material_badge_letter
    seen = {}
    for dh in canvas._get_visible_drillholes():
        for rec in (getattr(dh, "imagery", None) or []):
            key = str(getattr(rec, "material_label", "") or "").casefold()
            if not key:
                continue
            if getattr(rec, "material_label", "") and not _material_badge_letter(key):
                # inconnu → « Autre » (même repli que le badge 3D).
                key = "other"
            label = _imagery_material_label(
                "other" if key not in (
                    "core", "rc", "auger", "pit", "other") else key)
            letter = _material_badge_letter(
                "other" if key not in (
                    "core", "rc", "auger", "pit", "other") else key) or "?"
            if label not in seen:
                seen[label] = (letter, label, _imagery_badge_color(
                    canvas, dh, key))
    if not seen:
        return []
    return [(None, [v for _k, v in sorted(seen.items(),
                                          key=lambda kv: kv[0].casefold())])]


def elide_text(fm, text: str, max_w: float):
    """Tronque ``text`` à ``max_w`` px avec « … » (tel quel si ça tient)."""
    """Tronque ``text`` à ``max_w`` px avec « … ».  Retourne tel quel si
    ça tient déjà (ou si ``max_w`` est trop petit pour 1 caractère + …).
    """
    text = str(text or "")
    if fm.horizontalAdvance(text) <= max_w:
        return text
    ell = "…"
    for i in range(len(text), 0, -1):
        if fm.horizontalAdvance(text[:i] + ell) <= max_w:
            return text[:i] + ell
    return ell

def _geotech_legend_columns(canvas, kind):
    """v2.9.267 — légende quantitative 3D (RQD / récupération / densité).

    Même source que la coupe 2D : ``geotech_legend_scale`` pour les bornes
    et ``geotech_ramp_rgb`` pour les pastilles — la 3D ne recalcule pas son
    échelle dans son coin (règle de la v2.9.265 : une seule source).
    Une ligne = une valeur de la rampe ; dernière ligne = le gris
    « aucune mesure pour ce forage » (même constante ``GEOTECH_MISSING_COLOUR``
    que la bande hachurée 2D).
    """
    from ..core.geotech import (
        GEOTECH_MISSING_COLOUR, geotech_default_unit, geotech_kind,
        geotech_legend_scale, geotech_ramp_rgb)
    kind = geotech_kind(kind)
    if not kind:
        return []
    records = [
        record
        for hole in canvas._get_visible_drillholes()
        for record in (getattr(hole, "geotech", None) or [])
        if geotech_kind(getattr(record, "kind", "")) == kind]
    if not records:
        return []
    lo, hi, unit = geotech_legend_scale(kind, records)
    unit_text = str(unit or "").strip() or geotech_default_unit(kind)
    rows = []
    for colour, ratio in zip(
            geotech_ramp_rgb(kind, lo, hi),
            (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)):
        label = f"{lo + (hi - lo) * ratio:g} {unit_text}".strip()
        rows.append((label, label, QColor(colour)))
    # Pastille grise : clé de la bande « sans mesure » (comme en 2D).
    grey_short = _tr("Gris")
    grey_full = _tr("Gris : aucune mesure pour ce forage.")
    rows.append((grey_short, grey_full, QColor(GEOTECH_MISSING_COLOUR)))
    return [(None, rows)]


def _multi_domain_group_columns(canvas, dom):
    """v2.9.172 — colonnes de légende d'UN domaine du mode simultané.

    Retourne ``[(en-tête | None, [(clé, survol, couleur), …]), …]`` :

    - ``assays`` : UNE COLONNE PAR ÉLÉMENT avec SA rampe de bornes
      (même source ``assay_legend_columns`` que la légende simple —
      avant, le groupe « Teneurs » retombait sur les codes litho et la
      rampe disparaissait complètement : retour écran « légende teneur
      n'est pas affichée ») ;
    - ``intercepts`` : une ligne PAR RÈGLE active (libellé + couleur) ;
    - ``structure`` : les codes `type` du Référentiel (mesures
      ponctuelles — pas des intervalles) ;
    - ``imagery`` : les matériaux réellement présents (badge-lettre
      C/P/O/A/R, libellé complet au survol) ;
    - litho/altérations/minéralisations : les codes du Référentiel
      (code court affiché, libellé complet au survol).
    """
    if dom == "assays":
        try:
            from ..core.multi_assay import assay_legend_columns
            cols = assay_legend_columns(
                canvas.active_assay_elements(),
                canvas._assay_scales, canvas._assay_element_palettes,
                canvas.assay_palette)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : légende multi — colonnes de teneurs "
                          "(groupe Teneurs absent)", _exc)
            return []
        out = []
        for cap, cls_rows in cols:
            rows = []
            for b0, b1, frac, pal in cls_rows:
                col = QColor(assay_ramp_rgb(frac, pal))
                lbl = f"{format_grade_value(b0)} – {format_grade_value(b1)}"
                rows.append((lbl, f"{cap} {lbl}", col))
            if rows:
                out.append((cap, rows))
        return out
    if dom in ("rqd", "recovery", "density"):
        # v2.9.267 — géotech en domaine simultané : rampe quantitative
        # (mêmes bornes que le rendu 3D), comme en domaine principal.
        return _geotech_legend_columns(canvas, dom)
    if dom == "intercepts":
        rows = []
        try:
            from ..core.threshold_rule import active_rules, legend_label
            for r in active_rules(canvas._threshold_rules):
                col = QColor(r.get("color") or "#00E5FF")
                lbl = legend_label(
                    r, color_name=(r.get("color_name") or _tr("règle")))
                if lbl:
                    rows.append((lbl, lbl, col))
        except ImportError:
            # module seuil absent (pack réduit) — groupe vide.
            # SILENCE JUSTIFIÉ : fonctionnalité optionnelle.
            rows = []
        return [(None, rows)] if rows else []
    if dom == "structure":
        # v2.9.260 étape 3 — `structure` : les codes viennent des mesures
        # ponctuelles (``type``), pas des intervalles.
        entries = []
        seen = set()
        for dh in canvas._get_visible_drillholes():
            for rec in canvas._structure_records_for_domain(dh, "structure"):
                code = canvas._structure_record_code(rec)
                if code and code not in seen:
                    seen.add(code)
                    entries.append((
                        code,
                        canvas._resolve_code_label(code, "structure"),
                        canvas._resolve_code_color(code, "structure")))
        if not entries:
            return []
        entries.sort(key=lambda e: e[1].casefold())
        return [(None, entries)]
    if dom == "imagery":
        # v2.9.263 — Imagerie 3D : le badge-lettre doit être légendé
        # comme les autres domaines (aujourd'hui la légende multi ne
        # montrait rien pour Imagerie en Coupe/Sélection).
        return _imagery_legend_entries(canvas)
    # litho / altérations / minéralisations : codes du Référentiel
    entries = []
    seen = set()
    for dh in canvas._get_visible_drillholes():
        for iv in canvas._get_intervals_for_domain(dh, dom):
            for code in canvas._interval_codes(iv, dom):
                if code and code not in seen:
                    seen.add(code)
                    entries.append((
                        code,
                        canvas._resolve_code_label(code, dom),
                        canvas._resolve_code_color(code, dom)))
    if not entries:
        return []
    entries.sort(key=lambda e: e[1].casefold())
    return [(None, entries)]


def _draw_multi_domain_legend(canvas, painter):
    """v2.9.170 — légende MULTI-DOMAINES : groupée par domaine actif.

    Chaque domaine coché a son titre (Lithologie, Altérations…) suivi
    de SES codes avec pastilles de couleur.  Le géologue voit tout,
    comme les pistes de la coupe 2D.

    v2.9.172 — DEUX correctifs retour écran :

    1. **Plus de vide vers le bas** : la hauteur de la carte est le
       MAX des groupes (ils sont dessinés CÔTE À CÔTE), pas leur
       SOMME — avant, litho 15 codes + altérations 8 codes = carte de
       23 lignes à moitié vide.
    2. **Teneurs et intercepts légendés** : le groupe « Teneurs »
       affiche la RAMPE par élément (pas des codes), le groupe
       « Intercepts » affiche les règles de seuil actives.
    """
    visible_holes = canvas._get_visible_drillholes()
    if not visible_holes:
        return

    DOMAIN_TITLES = {
        "litho": _tr("Lithologie"),
        "alterations": _tr("Altérations"),
        "mineralizations": _tr("Minéralisations"),
        "assays": _tr("Teneurs"),
        "structure": _tr("Structures"),
        "intercepts": _tr("Intercepts (seuils)"),
        "imagery": _tr("Imagerie"),
        # v2.9.267 — géotechnique (rampe quantitative par domaine).
        "rqd": _tr("RQD"),
        "recovery": _tr("Récupération"),
        "density": _tr("Densité"),
    }

    # Collecte les groupes : (titre, domaine, colonnes)
    groups = []
    for dom in canvas.active_domains:
        if dom == "trajectory":
            continue
        cols = _multi_domain_group_columns(canvas, dom)
        if cols:
            groups.append((DOMAIN_TITLES.get(dom, dom), dom, cols))

    if not groups:
        return

    fm = painter.fontMetrics()
    font_rows = QFont("Segoe UI", 7)
    font_head = QFont("Segoe UI", 7, QFont.Bold)
    fm_rows = QFontMetrics(font_rows)
    fm_head = QFontMetrics(font_head)
    row_h = 15
    header_h = 20
    domain_h = 16  # titre de domaine
    gap_col = 6.0   # entre colonnes d'un même groupe
    gap_group = 12.0  # entre groupes

    # Pré-calcul du layout : largeur/hauteur PAR groupe et PAR colonne.
    # v2.9.172 — chaque colonne est dimensionnée avec SON domaine (le
    # code court de la litho n'a rien à voir avec celui des altérations).
    layout = []  # (titre, dom, [(header, rows, col_w, col_h)], g_w, g_h)
    for title, dom, cols in groups:
        is_code_dom = dom in (
            "litho", "alterations", "mineralizations", "structure")
        col_layout = []
        for header, rows in cols:
            longest = max(
                (fm_rows.horizontalAdvance(
                    canvas._short_code(c, dom) if is_code_dom else str(c))
                 for c, _f, _col in rows), default=0)
            w = max(72.0, float(longest) + 14 + 8)
            if header:
                w = max(w, float(fm_head.horizontalAdvance(header)) + 8)
            h = (row_h if header else 0) + len(rows) * row_h
            col_layout.append((header, rows, w, h))
        g_w = sum(c[2] for c in col_layout) + gap_col * (len(col_layout) - 1)
        g_h = domain_h + max(c[3] for c in col_layout)
        layout.append((title, dom, col_layout, g_w, g_h))

    # v2.9.172 — HAUTEUR = MAX DES GROUPES (côte à côte), pas la somme :
    # fini la carte trop haute avec un grand vide vers le bas.
    card_w = max(sum(g[3] for g in layout)
                 + gap_group * (len(layout) - 1) + 12, 150)
    card_h = header_h + max(g[4] for g in layout) + 6

    # v2.9.172 — position via le layout UNIQUE (règle B-4 : anti-
    # chevauchement légende ↔ gizmo ↔ badge, plus de gx/gy en dur qui
    # remontaient la carte trop haut).
    legend_rect = overlay_layout(
        canvas.width(), canvas.height(), card_w, card_h)["legend"]
    gx, gy = legend_rect[0], legend_rect[1]

    card_rect = QRectF(gx, gy, card_w, card_h)
    painter.setPen(QPen(QColor("#34495E"), 1))
    painter.setBrush(QBrush(QColor(23, 29, 34, 200)))
    painter.drawRoundedRect(card_rect, 4, 4)

    # Titre global
    painter.setPen(QColor("#F1C40F"))
    painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
    painter.drawText(QPointF(gx + 6, gy + 13), _tr("Domaines actifs"))
    painter.setPen(QPen(QColor("#4A5F70"), 0.8))
    painter.drawLine(QPointF(gx + 5, gy + 17), QPointF(gx + card_w - 5, gy + 17))

    # Groupes côte à côte, chacun : titre de domaine + ses colonnes
    cx = gx + 6
    for title, dom, col_layout, _g_w, _g_h in layout:
        ry = gy + header_h + 9
        painter.setFont(font_head)
        painter.setPen(QColor("#AEB6BF"))
        painter.drawText(QPointF(cx, ry), title)
        ry += domain_h
        ccx = cx
        for header, rows, col_w, _col_h in col_layout:
            ry2 = ry
            if header:
                painter.setFont(font_head)
                painter.setPen(QColor("#F1C40F"))
                painter.drawText(QPointF(ccx, ry2), header)
                ry2 += row_h
            painter.setFont(font_rows)
            max_text_w = col_w - 14 - 4
            for code, full, col in rows:
                swatch_rect = QRectF(ccx, ry2 - 9, 10, 10)
                painter.setPen(QPen(QColor(255, 255, 255, 120), 0.8))
                painter.setBrush(QBrush(col))
                painter.drawRoundedRect(swatch_rect, 2, 2)
                # v2.9.172 — la pastille RÉFLÈTE le motif (même règle
                # que la légende simple : litho/altérations).
                if dom in ("litho", "alterations"):
                    _draw_legend_pattern(canvas, painter, swatch_rect,
                                         code, col, dom)
                # v2.9.260 étape 3 — la pastille « Structures » reflète la
                # famille du symbole 3D (mini-tadpole/flèche/point).
                elif dom == "structure":
                    _draw_structure_legend_swatch(
                        canvas, painter, swatch_rect, code, col, dom)
                is_active = bool(canvas._highlight_code
                                 and canvas._highlight_code.upper() == str(code).upper())
                painter.setPen(QColor("#F1C40F") if is_active else QColor("#ECF0F1"))
                # v2.9.172 — code court avec LE domaine du groupe (avant :
                # "litho" en dur pour tous → codes d'altérations abrégés
                # en litho).
                if dom in ("litho", "alterations", "mineralizations",
                           "structure"):
                    disp_txt = canvas._elide_text(
                        fm_rows, canvas._short_code(code, dom), max_text_w)
                    hover_txt = full if (full and full.casefold() != code.casefold()) else code
                else:
                    # teneurs (bornes) / intercepts (règles) : texte tel quel
                    disp_txt = canvas._elide_text(fm_rows, str(code), max_text_w)
                    hover_txt = full
                if is_active:
                    disp_txt = f"★ {disp_txt}"
                painter.drawText(QPointF(ccx + 14, ry2), disp_txt)
                canvas._legend_rects.append(
                    (QRectF(ccx - 2, ry2 - 11, col_w, row_h), str(code), hover_txt))
                ry2 += row_h
            ccx += col_w + gap_col
        cx += _g_w + gap_group


def _draw_legend_pattern(canvas, painter, rect, code, base_color, domain):
    """Mini-rendu du motif dans une pastille de légende (v2.9.152).

    Reproduit le LANGAGE des tubes (marques perpendiculaires à l'axe,
    encre contrastée) en 10 px : la pastille montre EXACTEMENT ce que
    le tube affiche — même source (``core.styles.tube_pattern_render``).
    Sans motif : pastille pleine, rien.
    """
    try:
        from ..core.styles import tube_pattern_render
        spec = tube_pattern_render(
            canvas._style.code_pattern(code, domain))
        if not spec:
            return
        ink = base_color.lighter(165) if base_color.lightness() < 110 \
            else base_color.darker(210)
        x, y = rect.x(), rect.y()
        w, h = rect.width(), rect.height()
        cy = y + h / 2.0
        kind = spec.get("kind")
        painter.setPen(QPen(ink, 1.1, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(QBrush(Qt.NoBrush))
        if kind == "dot":
            painter.setBrush(QBrush(ink))
            painter.setPen(QPen(Qt.NoPen))
            r = max(0.7, spec.get("radius", 0.8))
            n = max(2, int(w // max(2.6, spec.get("period", 5.0) * 0.5)))
            for i in range(n):
                dxp = x + w * (i + 1) / (n + 1)
                painter.drawEllipse(QPointF(dxp, cy), r, r)
        elif kind == "tick":
            tilt = spec.get("tilt", 0.0) * h * 0.5
            painter.drawLine(QPointF(x + w * 0.28, y + h - 1.5),
                             QPointF(x + w * 0.28 + tilt, y + 1.5))
            painter.drawLine(QPointF(x + w * 0.68, y + h - 1.5),
                             QPointF(x + w * 0.68 + tilt, y + 1.5))
        elif kind == "double_tick":
            for dxp in (x + w * 0.35, x + w * 0.60):
                painter.drawLine(QPointF(dxp, y + 1.5), QPointF(dxp, y + h - 1.5))
        elif kind == "plus":
            cxp = x + w / 2.0
            painter.drawLine(QPointF(x + 1.5, cy), QPointF(x + w - 1.5, cy))
            painter.drawLine(QPointF(cxp, y + 1.5), QPointF(cxp, y + h - 1.5))
        elif kind == "cross_x":
            painter.drawLine(QPointF(x + 2.0, y + 2.0),
                             QPointF(x + w - 2.0, y + h - 2.0))
            painter.drawLine(QPointF(x + w - 2.0, y + 2.0),
                             QPointF(x + 2.0, y + h - 2.0))
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : légende — mini-rendu du motif "
                      "(pastille pleine)", _exc)
        return


def _draw_structure_legend_swatch(canvas, painter, rect, code,
                                  base_color, domain):
    """Pastille légende 3D « Structures » fidèle au rendu réel.

    planaire/inconnu = point + courte queue (mini-tadpole) ;
    linéaire = trait + pointe (mini-flèche) ;
    composite / non-orientable = point simple.

    L'encre du glyphe est CONTRASTÉE (foncée en pastille claire, claire en
    pastille foncée) : avant, le glyphe était de la même couleur que le
    fond de pastille → invisible (retour écran « légende = juste des
    carrés »).
    """
    if domain != "structure":
        return
    try:
        family = structure_family(str(code or ""))
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : légende — famille de structure "
                      "(pastille point)", _exc)
        family = "unknown"
    ink = (base_color.lighter(210)
           if int(base_color.lightness()) < 128
           else base_color.darker(235))
    x, y = rect.x(), rect.y()
    w, h = rect.width(), rect.height()
    cx, cy = x + w / 2.0, y + h / 2.0
    ex, ey = x + w - 1.5, y + h - 1.5
    if family in ("planar", "unknown"):
        painter.setPen(QPen(ink, 1.3))
        painter.drawLine(QPointF(cx, cy), QPointF(ex, ey))
    elif family == "linear":
        painter.setPen(QPen(ink, 1.3))
        painter.drawLine(QPointF(cx, cy), QPointF(ex, ey))
        vx, vy = ex - cx, ey - cy
        norm = math.hypot(vx, vy) or 1.0
        ux, uy = vx / norm, vy / norm
        bx, by = ex - ux * 3.0, ey - uy * 3.0
        painter.setBrush(QBrush(ink))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawPolygon(QPolygonF([
            QPointF(ex, ey),
            QPointF(bx - uy * 1.6, by + ux * 1.6),
            QPointF(bx + uy * 1.6, by - ux * 1.6)]))
    if family != "linear":
        painter.setBrush(QBrush(ink))
        painter.setPen(QPen(ink, 0.4))
        painter.drawEllipse(QPointF(cx, cy), 2.2, 2.2)


def draw_floating_legend(canvas, painter):
    """Légende flottante — colonnes par élément pour les teneurs (v2.9.142+)."""
    """Légende flottante in-canvas — v2.9.142 : teneurs par colonne.

    Teneurs : UNE COLONNE PAR ÉLÉMENT (même principe que la légende
    de la coupe 2D) — en-tête « Cu ppm » puis les bornes SEULES.
    Fini le nom d'élément répété sur chaque ligne (« Cu ppm 5 – 10 »,
    « Cu ppm 10 – 20 »…) qui chargeait visuellement la légende.
    Autres domaines : comportement v2.9.141 (codes courts, 2 colonnes
    si plus de 12 entrées, survol = nom complet).
    """
    canvas._legend_rects = []
    domain = canvas.geo_domain
    if domain == "trajectory":
        return

    visible_holes = canvas._get_visible_drillholes()
    if not visible_holes:
        return

    # Colonnes de légende : (en-tête | None, lignes).
    # ligne = (texte affiché, texte de survol, couleur).
    columns: list[tuple[Optional[str], list[tuple[str, str, QColor]]]] = []
    title = ""

    def _flat_columns(rows):
        """Découpe une liste plate en 1–2 colonnes (règle v2.9.141)."""
        if not rows:
            return []
        use_columns = 2 if len(rows) > 12 else 1
        n_rows = math.ceil(len(rows) / use_columns)
        out = []
        for i in range(use_columns):
            chunk = rows[i * n_rows:(i + 1) * n_rows]
            if chunk:
                out.append((None, chunk))
        return out

    # v2.9.170 — LÉGENDE MULTI-DOMAINES : groupée par domaine actif.
    # Le géologue voit TOUS les codes de TOUS les domaines cochés,
    # chacun sous son titre de domaine (comme les pistes 2D).
    # v2.9.172 — INTERCEPTS principal inclus : avant, le mode
    # « intercepts + litho » dessinait les tubes litho SANS les
    # légender (la légende multi était refusée quand le principal
    # était intercepts) — retour écran : « je vois des mélanges ».
    _multi_domains = [d for d in
                      (getattr(canvas, "active_domains", None) or [domain])
                      if d != "trajectory"]
    if len(_multi_domains) > 1:
        return _draw_multi_domain_legend(canvas, painter)

    if domain == "intercepts":
        title = _tr("Intercepts (seuils)")
        rows = []
        try:
            from ..core.threshold_rule import active_rules, legend_label
            for r in active_rules(canvas._threshold_rules):
                col = QColor(r.get("color") or "#00E5FF")
                lbl = legend_label(
                    r, color_name=(r.get("color_name") or _tr("règle")))
                rows.append((lbl, lbl, col))
        except ImportError:
            # module seuil absent (pack réduit) — légende intercepts vide.
            # SILENCE JUSTIFIÉ : fonctionnalité optionnelle.
            rows = []
        columns = _flat_columns(rows)
    elif domain == "assays":
        # v2.9.142 — éléments affichés = choix unitaire du combo OU
        # miroir de la coupe 2D (1–3 éléments) ; UNE COLONNE par
        # élément avec en-tête, chaque élément garde SA rampe.
        title = _tr("Teneurs")
        elems = canvas.active_assay_elements()
        try:
            from ..core.multi_assay import assay_legend_columns
            cols = assay_legend_columns(
                elems, canvas._assay_scales, canvas._assay_element_palettes,
                canvas.assay_palette)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : légende — colonnes de teneurs "
                          "(légende teneurs vide)", _exc)
            cols = []
        for cap, cls_rows in cols:
            col_rows = []
            for b0, b1, frac, pal in cls_rows:
                col = QColor(assay_ramp_rgb(frac, pal))
                lbl = f"{format_grade_value(b0)} – {format_grade_value(b1)}"
                col_rows.append((lbl, f"{cap} {lbl}", col))
            if col_rows:
                columns.append((cap, col_rows))
    elif domain == "structure":
        # v2.9.260 étape 3 — mesures ponctuelles : codes `type` des
        # structures, libellés/couleurs du Référentiel (domaine structure).
        title = _tr("Structures")
        seen = set()
        entries = []
        for dh in visible_holes:
            for rec in canvas._structure_records_for_domain(dh, "structure"):
                code = canvas._structure_record_code(rec)
                if code and code not in seen:
                    seen.add(code)
                    full = canvas._resolve_code_label(code, "structure")
                    col = canvas._resolve_code_color(code, "structure")
                    entries.append((code, full, col))
        entries = sorted(entries, key=lambda e: e[1].casefold())
        columns = _flat_columns(entries)
    elif domain in ("rqd", "recovery", "density"):
        # v2.9.267 — géotechnique : échelle QUANTITATIVE (pastilles de la
        # rampe + bornes réellement observées), jamais une liste de codes.
        from ..core.geotech import geotech_label
        title = _tr("{domain} — échelle quantitative").format(
            domain=_tr(geotech_label(domain)))
        columns = _geotech_legend_columns(canvas, domain)
    elif domain == "imagery":
        # v2.9.263 — Imagerie 3D : même sans autre domaine coché, le badge
        # doit avoir sa légende (matériaux présents, couleur du badge).
        title = _tr("Imagerie")
        entries = []
        group = _imagery_legend_entries(canvas)
        for _hdr, rows in group:
            entries.extend(rows)
        columns = _flat_columns(entries)
    else:
        domain_titles = {
            "litho": _tr("Lithologie"),
            "alterations": _tr("Altérations"),
            "mineralizations": _tr("Minéralisations"),
        }
        title = domain_titles.get(domain, _tr("Légende"))
        seen = set()
        entries = []
        for dh in visible_holes:
            invs = canvas._get_intervals_for_domain(dh, domain)
            for iv in invs:
                for code in canvas._interval_codes(iv, domain):
                    if code and code not in seen:
                        seen.add(code)
                        full = canvas._resolve_code_label(code, domain)
                        col = canvas._resolve_code_color(code, domain)
                        entries.append((code, full, col))

        # Tri par libellé lisible (plus de tri par code brut).
        entries = sorted(entries, key=lambda e: e[1].casefold())
        columns = _flat_columns(entries)

    if not columns:
        return

    fm = painter.fontMetrics()
    # v2.9.141 — légende compacte : on affiche les CODES (courts), le nom
    # complet apparaît au survol.
    row_h = 15
    header_h = 20
    font_rows = QFont("Segoe UI", 7)
    font_head = QFont("Segoe UI", 7, QFont.Bold)
    fm_rows = QFontMetrics(font_rows)
    fm_head = QFontMetrics(font_head)

    # v2.9.142 — largeur ADAPTATIVE PAR COLONNE : calée sur le texte
    # réellement affiché (bornes seules pour les teneurs → colonnes
    # étroites ; en-tête d'élément pris en compte).
    def _col_width(header, rows):
        longest = max((fm_rows.horizontalAdvance(canvas._short_code(c, domain))
                       for c, _f, _c in rows), default=0)
        w = max(72.0, float(longest) + 14 + 8)
        if header:
            w = max(w, float(fm_head.horizontalAdvance(header)) + 8)
        return w

    col_widths = [_col_width(h, rows) for h, rows in columns]
    n_rows_max = max(
        (len(rows) + (1 if h else 0) for h, rows in columns), default=0)
    card_w = max(sum(col_widths) + 12, fm.horizontalAdvance(title) + 20, 100)
    card_h = header_h + n_rows_max * row_h + 6

    # v2.9.146 — position venant du layout UNIQUE (ui/overlay_layout,
    # règle B-4 : anti-chevauchement testé, plus de gx/gy en dur).
    legend_rect = overlay_layout(
        canvas.width(), canvas.height(), card_w, card_h)["legend"]
    gx, gy = legend_rect[0], legend_rect[1]

    card_rect = QRectF(gx, gy, card_w, card_h)
    painter.setPen(QPen(QColor("#34495E"), 1))
    painter.setBrush(QBrush(QColor(23, 29, 34, 200)))
    painter.drawRoundedRect(card_rect, 4, 4)

    # Title (clean without emoji)
    painter.setPen(QColor("#F1C40F"))
    painter.setFont(font_head)
    painter.drawText(QPointF(gx + 6, gy + 13), title)

    # Title separation line
    painter.setPen(QPen(QColor("#4A5F70"), 0.8))
    painter.drawLine(QPointF(gx + 5, gy + 17), QPointF(gx + card_w - 5, gy + 17))

    # v2.9.142 — dessin COLONNE PAR COLONNE : en-tête d'élément
    # (teneurs) puis les entrées.  La largeur de texte ne mord plus
    # sur le libellé le plus long (marge droite conservée).
    cx = gx + 6
    for (header, rows), col_w in zip(columns, col_widths):
        ry = gy + header_h + 9
        if header:
            painter.setFont(font_head)
            painter.setPen(QColor("#F1C40F"))
            painter.drawText(QPointF(cx, ry), header)
            ry += row_h
        painter.setFont(font_rows)
        max_text_w = col_w - 14 - 4  # décalage texte (14) + marge (4)
        for code, full, col in rows:
            swatch_rect = QRectF(cx, ry - 9, 10, 10)
            painter.setPen(QPen(QColor(255, 255, 255, 120), 0.8))
            painter.setBrush(QBrush(col))
            painter.drawRoundedRect(swatch_rect, 2, 2)
            # v2.9.152 — la pastille RÉFLÈTE le motif (retour écran :
            # « si y a motifs, la légende doit refléter cela, sinon à
            # quoi ça sert ? ») : mini-rendu des MÊMES marques que les
            # tubes (source unique core.styles.tube_pattern_render).
            if domain in ("litho", "alterations"):
                _draw_legend_pattern(canvas, painter, swatch_rect, code, col, domain)
            # v2.9.260 étape 3 — la pastille « Structures » reflète sa
            # famille (mini-tadpole/flèche/point), comme le symbole 3D.
            elif domain == "structure":
                _draw_structure_legend_swatch(
                    canvas, painter, swatch_rect, code, col, domain)

            is_active_code = bool(
                canvas._highlight_code and canvas._highlight_code.upper() == code.upper())
            painter.setPen(QColor("#F1C40F") if is_active_code else QColor("#ECF0F1"))
            # v2.9.141 — code COURT pour tous les domaines (miné/alté
            # compris) ; teneurs = libellé numérique tel quel.
            disp_txt = canvas._elide_text(fm_rows, canvas._short_code(code, domain), max_text_w)
            if is_active_code:
                disp_txt = f"★ {disp_txt}"
            painter.drawText(QPointF(cx + 14, ry), disp_txt)

            # v2.9.141 — survol : UNIQUEMENT le nom complet (pas
            # « nom · code »).  v2.9.142 teneurs : « Cu ppm 5 – 10 ».
            hover_txt = full if (full and full.casefold() != code.casefold()) else code
            canvas._legend_rects.append(
                (QRectF(cx - 2, ry - 11, col_w, row_h), code, hover_txt))
            ry += row_h
        cx += col_w

def draw_gizmo(canvas, painter):
    """Gizmo d'orientation (triède E/N/Z) en bas à gauche."""
    """Draw 3D orientation indicator triad in bottom-left corner."""
    gx, gy, glen = 45.0, canvas.height() - 35.0, 24.0
    yaw_rad = math.radians(canvas.yaw_deg)
    pitch_rad = math.radians(canvas.pitch_deg)

    def proj_g(dx, dy, dz):
        rx = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
        ry = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)
        px = rx
        py = ry * math.sin(pitch_rad) + dz * math.cos(pitch_rad)
        return QPointF(gx + px * glen, gy - py * glen)

    painter.setPen(QPen(QColor("#E74C3C"), 2.2))
    painter.drawLine(QPointF(gx, gy), proj_g(1, 0, 0))
    painter.drawText(proj_g(1.35, 0, 0), _tr("E"))

    painter.setPen(QPen(QColor("#2ECC71"), 2.2))
    painter.drawLine(QPointF(gx, gy), proj_g(0, 1, 0))
    painter.drawText(proj_g(0, 1.35, 0), _tr("N"))

    painter.setPen(QPen(QColor("#3498DB"), 2.2))
    painter.drawLine(QPointF(gx, gy), proj_g(0, 0, 1))
    painter.drawText(proj_g(0, 0, 1.35), _tr("Z"))

def draw_exag_badge(canvas, painter):
    """Badge d'exagération verticale (haut droite) quand elle est active."""
    """Display vertical exaggeration badge when active."""
    badge_rect = QRectF(canvas.width() - 85, 45, 75, 22)
    painter.setBrush(QBrush(QColor(0, 0, 0, 160)))
    painter.setPen(QPen(QColor("#F39C12"), 1))
    painter.drawRoundedRect(badge_rect, 3, 3)

    painter.setPen(QColor("#F39C12"))
    painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
    painter.drawText(badge_rect, Qt.AlignCenter, _tr("Z × {}").format(f"{canvas.v_exag:.1f}"))

# v2.9.188 — l'infobulle : L'ESSENTIEL, replié (retour écran : « doit
# revenir à la ligne pour éviter qu'elle soit trop longue — que
# l'essentiel, partout dans le plugin »).
HOVER_TIP_MAX_W = 300.0     # largeur maxi avant retour à la ligne
HOVER_TIP_MAX_LINES = 10    # plafond de lignes


def _wrap_tooltip_lines(lines, fm, max_w=HOVER_TIP_MAX_W,
                        max_lines=HOVER_TIP_MAX_LINES):
    """Replie les lignes longues (mots entiers, jamais coupés au milieu)
    et plafonne le nombre de lignes — la bulle reste petite, l'essentiel
    reste lisible."""
    wrapped = []
    for text in lines:
        text = str(text or "").strip()
        if not text:
            continue
        if fm.horizontalAdvance(text) <= max_w:
            wrapped.append(text)
            continue
        words = text.split()
        cur = words[0] if words else text
        for word in words[1:]:
            trial = cur + " " + word
            if fm.horizontalAdvance(trial) <= max_w:
                cur = trial
            else:
                wrapped.append(cur)
                cur = word
        wrapped.append(cur)
    if len(wrapped) > max_lines:
        extra = len(wrapped) - max_lines
        wrapped = wrapped[:max_lines] + [
            _tr("… +{} ligne(s)").format(extra)]
    return wrapped


def draw_hover_tooltip(canvas, painter):
    """Infobulle de survol — police unique, bornée au canvas."""
    """Infobulle au survol — propre, police unique, bornée au canvas."""
    if not canvas._hover_text or not canvas._hover_pos:
        return
    lines = [l for l in canvas._hover_text.strip().split("\n") if l]
    if not lines:
        return

    # v2.9.141 — UNE seule police, corps 8 pt, gras seulement pour le
    # header.  Largeur mesurée avec la police GRASSE (la plus large) pour
    # ne jamais déborder.
    # v2.9.184 — PETITES MAJUSCULES aussi sur l'infobulle CUSTOM de la
    # 3D (dessinée au QPainter : la police QToolTip ne s'y applique
    # pas — retour écran : « partout, je dis bien partout »).
    f_body = QFont("Segoe UI", 8)
    f_body.setCapitalization(QFont.SmallCaps)
    f_head = QFont("Segoe UI", 8)
    f_head.setBold(True)
    f_head.setCapitalization(QFont.SmallCaps)
    fm_body = QFontMetrics(f_body)
    fm_head = QFontMetrics(f_head)
    # v2.9.188 — RETOUR À LA LIGNE + plafond : la bulle ne dépasse
    # jamais ~300 px de large ni 10 lignes (+ « … +N » si besoin).
    lines = _wrap_tooltip_lines(lines, fm_body)
    if not lines:
        return
    line_h = fm_body.height() + 3

    max_avail = float(canvas.width() - 24)
    w = max(fm_head.horizontalAdvance(lines[0]),
            max((fm_body.horizontalAdvance(l) for l in lines[1:]), default=0)) + 22
    w = min(w, max_avail)
    h = len(lines) * line_h + 12
    h = min(h, float(canvas.height() - 20))

    px = canvas._hover_pos.x() + 14
    py = canvas._hover_pos.y() + 14
    if px + w > canvas.width() - 8:
        px = canvas._hover_pos.x() - w - 14
    if py + h > canvas.height() - 8:
        py = canvas._hover_pos.y() - h - 14
    px = max(8, min(px, canvas.width() - w - 8))
    py = max(8, min(py, canvas.height() - h - 8))

    painter.setPen(QPen(QColor(170, 180, 190), 1.0))
    painter.setBrush(QBrush(QColor(255, 255, 255, 246)))
    painter.drawRoundedRect(QRectF(px, py, w, h), 4, 4)

    divider_y = py + line_h + 5
    painter.setPen(QPen(QColor(220, 225, 230), 0.8))
    painter.drawLine(QPointF(px + 8, divider_y), QPointF(px + w - 8, divider_y))

    content_w = w - 20
    for i, line in enumerate(lines):
        y_offset = py + line_h - 3 + i * line_h + (3 if i > 0 else 0)
        if i == 0:
            painter.setPen(QColor("#1A5276"))
            painter.setFont(f_head)
            elided = canvas._elide_text(fm_head, line, content_w)
        else:
            painter.setPen(QColor("#2C3E50"))
            painter.setFont(f_body)
            elided = canvas._elide_text(fm_body, line, content_w)
        painter.drawText(QPointF(px + 10, y_offset), elided)
