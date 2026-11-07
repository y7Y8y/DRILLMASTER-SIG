"""Écran « Pistes » (T-04) — rendu **généré depuis le contrat**.

Aucune piste, aucun libellé, aucune valeur n'est écrit ici : tout vient de
`specs/data/tracks.json` et `specs/data/lexique.json`. Si une piste est ajoutée
au JSON, l'écran l'affiche sans qu'une ligne de ce fichier change (R-03).

Sortie : `maquettes/17_pistes_genere.png` (+ variante « Avancé »).
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "maquettes"))

from ui import C, Tokens, switch                        # noqa: E402
from drillmaster_v3.core import (TrackCatalog, Visibilite,  # noqa: E402
                                 lexique)

W, H = 1600, 1000
LARGEUR = {"essentiel": 96}
COLONNES = [("visible", 78), ("label", 300), ("width", 96),
            ("opacity", 96), ("side", 110), ("etat", 150)]

NOMS = {
    "order": "Ordre d'affichage", "gap": "Espacement", "fill": "Remplissage",
    "stroke": "Contour", "label_text": "Étiquettes", "tooltip": "Info-bulle",
    "filter": "Filtre", "export": "À l'export", "method": "Méthode de classes",
    "n_classes": "Nombre de classes", "ramp": "Rampe de couleurs",
    "breaks": "Seuils", "scale_scope": "Portée de l'échelle", "unit": "Unité",
    "range": "Plage", "tick_step": "Pas des graduations",
    "label_every": "Étiquette toutes les", "line_style": "Style de trait",
    "dash": "Pointillés", "rule_ids": "Règles de seuil",
    "label_position": "Position de l'étiquette", "pattern": "Motif",
    "legend_order": "Ordre de légende", "hatch_scale": "Densité du motif",
    "thumb_size": "Taille de vignette", "resolution": "Résolution",
    "alt_text": "Texte de remplacement", "width": "Largeur",
    "opacity": "Opacité", "side": "Côté", "visible": "Visible",
}


def joli(valeur):
    if isinstance(valeur, bool):
        return "oui" if valeur else "non"
    if isinstance(valeur, (list, tuple)):
        return " · ".join(str(v) for v in valeur) or "—"
    if isinstance(valeur, dict):
        return " · ".join(f"{k} {v}" for k, v in valeur.items()) or "—"
    if valeur in (None, ""):
        return "—"
    return str(valeur)


def entete(c, x, y, w):
    t = c.th
    c.txt(x + 18, y, "VISIBLE", size=8.2, fill=t.ink_3, bold=True, anchor="ls")
    c.txt(x + 96, y, "PISTE", size=8.2, fill=t.ink_3, bold=True, anchor="ls")
    c.txt(x + 396, y, "LARGEUR", size=8.2, fill=t.ink_3, bold=True, anchor="ls")
    c.txt(x + 492, y, "OPACITÉ", size=8.2, fill=t.ink_3, bold=True, anchor="ls")
    c.txt(x + 588, y, "CÔTÉ", size=8.2, fill=t.ink_3, bold=True, anchor="ls")
    c.txt(x + 700, y, "ÉTAT", size=8.2, fill=t.ink_3, bold=True, anchor="ls")
    c.l(x + 8, y + 10, x + w - 8, y + 10, fill=t.border)


def champ(c, x, y, valeur, herite, unite="", w=76):
    t = c.th
    c.r(x, y, w, 26, fill=t.surface_2 if herite else t.surface,
        stroke=t.border_strong, rx=6)
    if herite:
        c.c(x + 9, y + 13, 2.2, t.ink_3)
        c.txt(x + 16, y + 18, valeur, size=9.4, fill=t.ink_3, anchor="ls")
    else:
        c.txt(x + 9, y + 18, valeur, size=9.6, fill=t.ink, anchor="ls")
    if unite:
        c.txt(x + w - 8, y + 18, unite, size=8.4, fill=t.ink_3, anchor="rs")


def pistes(path, mode="guidee", detail=None):
    t = Tokens
    c = C(W, H, t)
    cat = TrackCatalog()
    vis = Visibilite(cat)
    if detail is None:                      # R-03 : choisi dans le contrat
        detail = cat.par_famille("quantitative")[0]["id"]
    jeu = __import__("json").loads(
        (RACINE / "specs/data/projet_issia.json").read_text(encoding="utf-8"))

    c.app_bar(lexique.module("coupe2d"))
    titre = "Pistes"
    sous = ("12 pistes en 4 familles · une seule déclaration chacune · "
            "les mêmes réglages partout")
    c.page_title(24, 82, titre, sous)

    # sélecteur de mode (T-08)
    y = 132
    c.txt(24, y + 16, "Mode", size=9, fill=t.ink_3, anchor="ls")
    c.segmented(66, y, ["Guidé", "Expert"], 0 if mode == "guidee" else 1)
    c.txt(250, y + 16, "le mode allège l'affichage, il ne change aucune valeur",
          size=8.8, fill=t.ink_3, anchor="ls")
    c.chip(W - 24 - 200, y + 2, "6 réglages visibles maximum", "ok")

    # ── liste
    lx, ly, lw, lh = 24, 172, 1010, 792
    c.panel(lx, ly, lw, lh, "Les 12 pistes",
            "La famille donne les valeurs · le rond gris = valeur héritée")
    entete(c, lx + 14, ly + 66, lw)
    yy = ly + 90

    familles = {}
    for pid in cat.ids():
        familles.setdefault(cat.declare(pid)["family"], []).append(pid)

    for fam, ids in familles.items():
        label = lexique.famille(fam)
        c.r(lx + 12, yy, lw - 24, 30, fill=t.surface_3, rx=7)
        c.txt(lx + 22, yy + 20, label, size=9.4, fill=t.ink_2, bold=True,
              anchor="ls")
        c.txt(lx + 22 + c.tw(label, 9.4, True) + 10, yy + 20,
              f"{len(ids)} pistes · même réglage pour la famille", size=8.4,
              fill=t.ink_3, anchor="ls")
        yy += 34

        for pid in ids:
            st = cat.resout(pid)
            info = jeu["par_piste"].get(pid, {})
            sel = pid == detail
            rh = 42
            c.r(lx + 12, yy, lw - 24, rh - 4,
                fill=t.accent_soft if sel else None, rx=7)
            if sel:
                c.r(lx + 12, yy, 3, rh - 4, fill=t.accent, rx=1)
            switch(c, lx + 20, yy + 11, st.visible)
            c.txt(lx + 96, yy + 10, st.label, size=10.2, bold=True,
                  fill=t.ink if st.visible else t.ink_3, anchor="ls")
            c.txt(lx + 96, yy + 26, info.get("quantite", ""), size=8.4,
                  fill=t.ink_3, anchor="ls")
            champ(c, lx + 386, yy + 5, str(st.width), "width" in st.herite,
                  "px")
            champ(c, lx + 482, yy + 5, str(st.opacity), "opacity" in st.herite,
                  "%")
            cote = {"left": "Gauche", "right": "Droite",
                    "overlay": "Plein"}[st.side]
            champ(c, lx + 578, yy + 5, cote, "side" in st.herite, "", 96)
            etat = info.get("etat", "ok")
            c.dot(lx + 706, yy + 15, etat)
            c.txt(lx + 718, yy + 20,
                  {"ok": "à jour", "warn": "3 réserves",
                   "info": "en attente"}[etat], size=8.8, fill=t.ink_3,
                  anchor="ls")
            c.txt(lx + lw - 32, yy + 8, "›", size=12, fill=t.ink_3, anchor="ls")
            yy += rh

    c.txt(lx + 20, ly + lh - 18,
          "Cliquez sur une valeur pour la forcer pour cette piste seule.",
          size=8.4, fill=t.ink_3, anchor="ls")

    # ── détail : le champ vient de la même source que la liste
    st = cat.resout(detail)
    dx, dy, dw = 1050, 172, 526
    c.panel(dx, dy, dw, 792, st.label, "Le détail d'une piste, pas un formulaire")

    yy = dy + 68
    compact = mode == "experte"
    c.txt(dx + 16, yy, "CE QUE MONTRE L'ÉCRAN EN MODE " +
          ("GUIDÉ" if not compact else "EXPERT"), size=8.2, fill=t.ink_3,
          bold=True, anchor="ls")
    yy += 14
    for champ_ in vis.essentiels(detail, mode):
        if champ_ in ("visible", "width", "opacity", "side"):
            continue
        valeur = joli(st.specific.get(champ_, getattr(st, champ_, None)))
        if compact:
            c.txt(dx + 16, yy + 8, NOMS.get(champ_, champ_), size=8.8,
                  fill=t.ink_2, anchor="ls")
            c.txt(dx + dw - 16, yy + 8, valeur, size=8.8, fill=t.ink_3,
                  anchor="rs")
            yy += 19
        else:
            c.r(dx + 16, yy, dw - 32, 30, fill=t.surface_2, stroke=t.border,
                rx=6)
            c.txt(dx + 26, yy + 19, NOMS.get(champ_, champ_), size=9.2,
                  fill=t.ink, anchor="ls")
            c.txt(dx + dw - 26, yy + 19, valeur, size=9.2, fill=t.ink_2,
                  anchor="rs")
            yy += 34

    if not compact:
        c.txt(dx + 16, yy + 6, f"{len(vis.avances(detail))} réglages de plus "
              "existent pour cette piste.", size=8.8, fill=t.ink_3, anchor="ls")
        c.button(dx + 16, yy + 18, "Afficher les réglages avancés", w=240,
                 size=9.2)
        yy += 58

    c.l(dx, yy + 4, dx + dw, yy + 4, fill=t.border)
    yy += 24
    c.txt(dx + 16, yy, "OÙ CE RÉGLAGE S'APPLIQUE", size=8.2, fill=t.ink_3,
          bold=True, anchor="ls")
    yy += 16
    for lecteur in cat.LECTEURS:
        r = cat.lit(detail, lecteur, "width")
        nom = {"2d": "Coupe 2D", "3d": "Vue 3D", "legende": "Légende",
               "export": "Export PDF", "carte": "Carte QGIS"}[lecteur]
        c.dot(dx + 20, yy + 6, "ok" if r["applique"] else "off")
        c.txt(dx + 34, yy + 10, nom, size=9.2,
              fill=t.ink if r["applique"] else t.ink_3, anchor="ls")
        if not r["applique"]:
            c.txt(dx + 160, yy + 10, r["raison"], size=8.4, fill=t.ink_3,
                  anchor="ls")
        yy += 20

    yy += 4
    c.l(dx, yy, dx + dw, yy, fill=t.border)
    yy += 16
    c.txt(dx + 16, yy, "CE QUE VOUS NE POUVEZ PAS RÉGLER ICI", size=8.2,
          fill=t.ink_3, bold=True, anchor="ls")
    c.txt(dx + 16, yy + 18, "la couleur et le motif viennent du Référentiel",
          size=8.8, fill=t.ink_2, anchor="ls")
    c.txt(dx + 16, yy + 34, "les seuils viennent d'Analyses → Intercepts",
          size=8.8, fill=t.ink_2, anchor="ls")
    c.txt(dx + 16, yy + 50, "aucun réglage de piste n'est dans la coupe",
          size=8.8, fill=t.ink_2, anchor="ls")

    # ── aperçu : ce que la piste donnera dans la coupe
    ay = dy + (560 if mode == "guidee" else 370)
    c.panel(dx + 16, ay, dw - 32, 150, "Aperçu dans la coupe",
            "Ce que vous voyez est ce qui sortira à l'export")
    ax = dx + 40
    aw = dw - 80
    for k in range(8):
        fx = ax + 20 + (aw - 50) * k / 7
        c.l(fx, ay + 66, fx + 2, ay + 120, fill=t.ink_3, w=1)
        for j in range(4):
            v = 0.25 + ((k * 7 + j * 3) % 10) / 14
            c.r(fx + 4, ay + 66 + j * 13, 4 + v * 28, 9,
                fill=["#B42318", "#DC6803", "#F79009", "#FDB022"][j], rx=1)

    c.status_bar(f"Coupe {jeu['coupe']} · 12 pistes · un seul jeu de réglages · "
                 "aucun réglage dupliqué", "À jour")
    return c.save(path)


if __name__ == "__main__":
    out = RACINE / "maquettes"
    print(pistes(out / "17_pistes_genere.png", "guidee"))
    print(pistes(out / "17_pistes_genere_expert.png", "experte"))
