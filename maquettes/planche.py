"""Planche contact : tous les écrans de la refonte sur une seule image."""
import os
from PIL import Image, ImageDraw, ImageFont

S = 2
OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ECRANS = [
    ("01_projet", "1 · Projet", "identité, référentiel, bibliothèques, santé"),
    ("02_donnees", "2 · Données", "87 contrôles, 5 niveaux d'état, détail pourquoi/concerné/résoudre"),
    ("03_geometrie", "3 · Géométrie", "méthode, cache signé, contrôles de trajectoire"),
    ("04_coupe_2d", "4 · Coupe 2D", "l'écran clé : pistes unifiées, largeur/opacité éditables"),
    ("05_vue_3d", "5 · Vue 3D", "surface MNT, forages, corridor, arbre de calques"),
    ("06_analyses", "6 · Analyses", "rose des directions, stéréonet, intercepts, distribution"),
    ("07_referentiel", "7 · Référentiel", "codes, couleurs, motifs, règles de gamme"),
    ("08_export", "8 · Export", "profils réutilisables, aperçu A1 avant production"),
    ("09_guide", "9 · Mode Guidé", "4 étapes, couverture des 12 types, blocages expliqués"),
    ("04_coupe_2d_sombre", "Variante sombre — Coupe 2D", "même structure, jetons inversés"),
    ("05_vue_3d_sombre", "Variante sombre — Vue 3D", "aucune couleur métier ne dépend du thème"),
]


def run(path):
    cols, tw = 2, 760
    pad, gap, cap = 34, 26, 62
    th = int(tw * 0.625)
    rows = (len(ECRANS) + cols - 1) // cols
    W = pad * 2 + tw * cols + gap * (cols - 1)
    head = 108
    H = head + pad + rows * (th + cap) + (rows - 1) * gap + pad
    canvas = Image.new("RGB", (W * S, H * S), "#EEF0F4")
    d = ImageDraw.Draw(canvas)
    f_title = ImageFont.truetype(FONT_B, 24 * S)
    f_sub = ImageFont.truetype(FONT, 12 * S)
    f_cap = ImageFont.truetype(FONT_B, 12 * S)
    f_note = ImageFont.truetype(FONT, 10 * S)

    d.text((pad * S, 34 * S), "DrillMaster — refonte de l'interface",
           font=f_title, fill="#101828")
    d.text((pad * S, 66 * S),
           "9 écrans · thème clair et sombre · plugin QGIS, format dock 1600 × 1000",
           font=f_sub, fill="#667085")
    d.line([(pad * S, 92 * S), ((W - pad) * S, 92 * S)], fill="#D0D5DD", width=S)

    for i, (name, title, note) in enumerate(ECRANS):
        r, cc = divmod(i, cols)
        x = pad + cc * (tw + gap)
        y = head + pad + r * (th + cap + gap)
        img = Image.open(os.path.join(OUT, f"{name}.png")).convert("RGB")
        img = img.resize((tw * S, th * S), Image.LANCZOS)
        canvas.paste(img, (x * S, y * S))
        d.rectangle([x * S, y * S, (x + tw) * S, (y + th) * S],
                    outline="#C9CFD8", width=S)
        d.text((x * S, (y + th + 14) * S), title, font=f_cap, fill="#101828")
        d.text((x * S, (y + th + 34) * S), note, font=f_note, fill="#667085")

    canvas = canvas.resize((W, H), Image.LANCZOS)
    canvas.save(path)
    return path


if __name__ == "__main__":
    print(run(os.path.join(OUT, "00_planche_contact.png")))
