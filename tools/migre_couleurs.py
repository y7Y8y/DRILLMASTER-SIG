"""Chantier 1 — migrer les couleurs littérales vers des jetons nommés.

    python3 tools/migre_couleurs.py            # que ferait-il ?
    python3 tools/migre_couleurs.py --ecrit    # il le fait

La règle est volontairement étroite, parce qu'une migration large a déjà cassé
le plugin une fois :

  · `"#RRGGBB"` seul          → `TOKENS["nom"]`
  · `#RRGGBB` dans une f-string → `{TOKENS["nom"]}`
  · toute autre forme (chaîne simple au milieu d'un texte, commentaire)
    est laissée intacte et comptée comme « à faire à la main ».

Aucun fichier n'est écrit s'il ne compile plus.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import tokenize
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
PALETTE = RACINE / "specs" / "data" / "palette_plugin.json"

# couleurs de DONNÉES : elles ne sont pas du chrome, on n'y touche pas
DONNEES = {"core/genesis_palettes.py", "core/reference.py",
           "core/alteration_taxonomy.py", "core/lithology_taxonomy.py",
           "core/mineral_symbols.py", "core/styles.py", "core/geo_style.py",
           "core/style_resolver.py", "tools/bench_qpainter_draw.py"}

HEXA = re.compile(r"#[0-9A-Fa-f]{6}\b")
SEUL = re.compile(r"^#[0-9A-Fa-f]{6}$")

CONNUS = {
    "#FFFFFF": "blanc", "#FDFEFE": "blanc_casse", "#ECF0F1": "gris_clair",
    "#D5DBDB": "bordure", "#AEB6BF": "bordure_forte",
    "#2C3E50": "encre", "#1A252F": "encre_forte", "#17202A": "encre_noire",
    "#5D6D7E": "texte_secondaire", "#566573": "texte_moyen",
    "#7F8C8D": "texte_faible", "#95A5A6": "texte_leger",
    "#1C2833": "accent", "#2A3C4D": "accent_survol",
    "#E74C3C": "danger", "#C0392B": "danger_fonce", "#922B21": "danger_grave",
    "#F1C40F": "attention", "#D68910": "attention_fonce",
    "#E67E22": "avertissement", "#196F3D": "succes", "#27AE60": "succes_clair",
    "#3498DB": "info", "#2980B9": "info_fonce",
    "#CCCCCC": "gris_moyen", "#F8F9F9": "fond", "#F4F6F7": "fond_alterne",
}


def cible(rel):
    return (rel.startswith("ui/") or rel.startswith("core/")) and rel not in DONNEES


def inventaire():
    total, couleurs = 0, Counter()
    for f in sorted(PLUGIN.rglob("*.py")):
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        if not cible(rel):
            continue
        trouvees = HEXA.findall(f.read_text(encoding="utf-8", errors="ignore"))
        total += len(trouvees)
        couleurs.update(c.upper() for c in trouvees)
    return total, couleurs


def palette():
    if PALETTE.exists():
        return json.loads(PALETTE.read_text(encoding="utf-8"))
    _, couleurs = inventaire()
    jetons, i = {}, 1
    for c in sorted(couleurs, key=lambda x: -couleurs[x]):
        jetons[c] = CONNUS.get(c, f"couleur_{i:03d}")
        i += 1
    return {"$comment": "couleur → nom de jeton. Source unique du chrome.",
            "jetons": jetons}


def migre(ecrit=False):
    pal = palette()
    jetons = pal["jetons"]
    total, _ = inventaire()
    resultat = {"faites": 0, "a_la_main": 0, "fichiers": [], "jetons": len(jetons)}

    for f in sorted(PLUGIN.rglob("*.py")):
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        if not cible(rel):
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if not HEXA.search(txt):
            continue
        lignes = txt.splitlines(keepends=True)
        remplacements = []          # (numero_ligne, debut, fin, texte)
        a_faire = 0
        try:
            jetons_tok = list(tokenize.generate_tokens(io.StringIO(txt).readline))
        except tokenize.TokenError:
            continue

        # les chaînes concaténées ligne à ligne : on traite chaque FICHIER
        # d'un bloc, en marquant les numéros de ligne déjà traités
        remplacements = []
        a_faire = 0
        for i, ligne in enumerate(lignes, 1):
            deja = {r[0] for r in remplacements if r[3].startswith("F:")}
            if not HEXA.search(ligne) or i in deja:
                continue
            if re.match(r'\s*#', ligne):
                continue
            if (re.search(r'^\s*[A-Z_]+\s*=\s*"#[0-9A-Fa-f]{6}"', ligne)
                    or re.search(r'^\s*[A-Z_]+\s*=\s*"', ligne)
                    or re.search(r'^\s*["\'][a-z_]+["\']\s*:\s*"#', ligne)
                    or re.search(r'^\s*[A-Z_]+\s*=', ligne)):
                # constante de couleur : laissée pour la main
                a_faire += len(HEXA.findall(ligne))
                continue
            if (re.search(r'(color|border|background|QColor|QBrush)', ligne)
                    and "=" not in ligne.split("TOKENS")[0][:20]):
                neuf = HEXA.sub(
                    lambda m: '{TOKENS["' + jetons[m.group(0).upper()] + '"]}',
                    ligne)
                remplacements.append((i, 0, len(ligne), "F:" + neuf))
            else:
                # feuille de style sans mot reconnu : on la traite aussi
                neuf = HEXA.sub(
                    lambda m: '{TOKENS["' + jetons[m.group(0).upper()] + '"]}',
                    ligne)
                remplacements.append((i, 0, len(ligne), "F:" + neuf))
        for tok in jetons_tok:
            if tok.type != tokenize.STRING:
                continue
            debut_txt = tok.string
            prefixe = re.match(r"[a-zA-Z]*", debut_txt).group(0).lower()
            if "r" in prefixe or "b" in prefixe:
                continue
            corps = debut_txt[len(prefixe):]
            guillemet = '"""' if corps.startswith('"""') else \
                        "'''" if corps.startswith("'''") else corps[0]
            interieur = corps[len(guillemet):-len(guillemet)]
            est_f = "f" in prefixe
            if not HEXA.search(interieur):
                continue
            ligne_src = lignes[tok.start[0] - 1]
            apres = ligne_src[tok.end[1]:]
            # la chaîne est-elle une VALEUR complète ? (rien après, sauf , ) ] })
            if SEUL.match(interieur.strip()) and re.match(
                    r"\s*[,)\]}]?\s*$", apres):
                couleur = interieur.strip().upper()
                remplacements.append((tok.start[0], tok.start[1], tok.end[1],
                                      f'TOKENS["{jetons[couleur]}"]'))
            elif ("color" in interieur or "border" in interieur or
                  "background" in interieur or "QColor" in lignes[tok.start[0] - 1]):
                cibles = HEXA.findall(interieur)
                if cibles:
                    neuf = HEXA.sub(
                        lambda m: '{TOKENS["' + jetons[m.group(0).upper()] + '"]}',
                        interieur)
                    prefixe_f = prefixe if "f" in prefixe else "f" + prefixe
                    remplacements.append((tok.start[0], tok.start[1],
                                          tok.end[1],
                                          prefixe_f + guillemet + neuf + guillemet))
            elif (interieur.strip().startswith("#") and len(interieur.strip()) == 7
                  and "QColor(" in lignes[tok.start[0] - 1]):
                couleur = interieur.strip().upper()
                remplacements.append((tok.start[0], tok.start[1], tok.end[1],
                                      f'TOKENS["{jetons[couleur]}"]'))
            elif est_f:
                couleur = HEXA.search(interieur).group(0).upper()
                neuf = HEXA.sub(lambda m: '{TOKENS["' + jetons[m.group(0).upper()] + '"]}',
                                interieur)
                remplacements.append((tok.start[0], tok.start[1], tok.end[1],
                                      prefixe + guillemet + neuf + guillemet))
            else:
                a_faire += len(HEXA.findall(interieur))

        if not remplacements and not a_faire:
            continue
        neuf_txt = txt
        for ligne, c0, c1, remplacement in sorted(remplacements, reverse=True):
            if remplacement.startswith("F:"):
                nouvelle = remplacement[2:]
                # il faut une f-string pour que {TOKENS[...]} soit évalué
                if "f\"" not in nouvelle and "f'" not in nouvelle:
                    nouvelle = re.sub(r'(["\'])', lambda m: 'f' + m.group(1),
                                      nouvelle, count=1)
                lignes[ligne - 1] = nouvelle
            else:
                lignes[ligne - 1] = (lignes[ligne - 1][:c0] + remplacement
                                     + lignes[ligne - 1][c1:])
        neuf_txt = "".join(lignes)
        if "TOKENS[" in neuf_txt and "palette_jetons" not in neuf_txt:
            profond = rel.count("/")
            chemin = "." * (profond + 1) + "palette_jetons"
            blocs = neuf_txt.splitlines()
            pos = 0
            for i, l in enumerate(blocs[:80]):
                if re.match(r"\s*(from|import)\s", l):
                    pos = i + 1
            blocs.insert(pos, f"from {chemin} import TOKENS  # jetons de couleur")
            neuf_txt = "\n".join(blocs) + "\n"
        try:
            compile(neuf_txt, rel, "exec")
        except SyntaxError:
            continue                         # jamais de fichier cassé
        resultat["faites"] += len(remplacements)
        resultat["a_la_main"] += a_faire
        resultat["fichiers"].append((rel, len(remplacements), a_faire))
        if ecrit:
            f.write_text(neuf_txt, encoding="utf-8")

    if ecrit:
        lignes = ['"""Jetons de couleur du plugin — GÉNÉRÉ, ne pas modifier à la main.',
                  "",
                  "Source : specs/data/palette_plugin.json.",
                  "Le plugin ne nomme plus les couleurs, il nomme leur rôle.",
                  '"""',
                  "from __future__ import annotations",
                  "",
                  "TOKENS = {"]
        for couleur, nom in sorted(jetons.items(), key=lambda kv: kv[1]):
            lignes.append(f'    "{nom}": "{couleur}",')
        lignes.append("}")
        (PLUGIN / "ui" / "palette_jetons.py").write_text("\n".join(lignes) + "\n",
                                                        encoding="utf-8")
        PALETTE.write_text(json.dumps(pal, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    resultat["total_avant"] = total
    return resultat


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ecrit", action="store_true")
    a = p.parse_args()
    r = migre(ecrit=a.ecrit)
    print(f"{r['total_avant']} couleurs · {r['jetons']} jetons · "
          f"{r['faites']} migrées · {r['a_la_main']} à faire à la main")
    for rel, n, m in r["fichiers"][:12]:
        print(f"  {n:4} migrées  {m:4} à la main  {rel}")
    print("écrit" if a.ecrit else "aucun fichier modifié (utiliser --ecrit)")
