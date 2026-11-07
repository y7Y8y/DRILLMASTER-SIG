"""Planche des corrections : ce qui répond aux cinq reproches."""
import os
from PIL import Image, ImageDraw, ImageFont

S = 2
OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ECRANS = [
    ("11_pistes", "1 · Les 12 pistes, en 4 familles",
     "une déclaration chacune, valeurs héritées de la famille"),
    ("12_partages", "2 · Un réglage, cinq lecteurs",
     "chaque réglage a un propriétaire ; aucune copie dans une vue"),
    ("13_donnees_rangs", "3 · 12 types, 3 rangs",
     "les catégories restent avec leur type, jamais ailleurs"),
    ("14_message", "4 · Une erreur qu'on comprend",
     "ce que j'ai vu, pourquoi, trois sorties, aucune décision automatique"),
    ("15_etats", "5 · Les 5 états, en deux voix",
     "même vocabulaire au mode Guidé et au mode Expert"),
    ("16_validation", "6 · Est-ce que ça tient ?",
     "17 cas d'usage rejoués, dont les cas limites réels"),
    ("04_coupe_2d", "7 · La coupe, corrigée",
     "3 familles + 4 réglages de coupe : plus de liste plate de 12 lignes"),
]


def run(path):
    cols, tw = 2, 760
    pad, gap, cap = 34, 26, 62
    th = int(tw * 0.625)
    rows = (len(ECRANS) + cols - 1) // cols
    W = pad * 2 + tw * cols + gap * (cols - 1)
    head = 112
    H = head + pad + rows * (th + cap) + (rows - 1) * gap + pad
    canvas = Image.new("RGB", (W * S, H * S), "#EEF0F4")
    d = ImageDraw.Draw(canvas)
    f_title = ImageFont.truetype(FONT_B, 24 * S)
    f_sub = ImageFont.truetype(FONT, 12 * S)
    f_cap = ImageFont.truetype(FONT_B, 12 * S)
    f_note = ImageFont.truetype(FONT, 10 * S)

    d.text((pad * S, 32 * S), "DrillMaster — les corrections", font=f_title,
           fill="#101828")
    d.text((pad * S, 64 * S),
           "cinq reproches, cinq réponses · ce qui change dans l'interface",
           font=f_sub, fill="#667085")
    d.line([(pad * S, 92 * S), ((W - pad) * S, 92 * S)], fill="#D0D5DD",
           width=S)

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
    print(run(os.path.join(OUT, "10_planche_corrections.png")))
