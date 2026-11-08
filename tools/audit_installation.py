"""Chantier 12 — l'installation : ce que le dépôt exige, ce que le code tient.

    python3 tools/audit_installation.py [--ecrit]

Quatre mesures, aucune impression :

1. **La fiche** — les champs obligatoires du dépôt officiel, lus dans
   `metadata.txt` comme le fait QGIS (`configparser`), avec la liste de ce
   qui manque *vraiment*.
2. **La fenêtre de compatibilité** — la version maximale déclarée confrontée
   au nombre de sites que Qt 6 refuse. Déclarer « QGIS 4 » avec 530 sites à
   l'ancienne forme est un mensonge que le dépôt ne détecte pas.
3. **Le paquet** — ce qui part réellement chez l'utilisateur : poids, cache
   compilé, bancs d'essai, fichiers exigés.
4. **Le démarrage dans un dossier isolé** — le plugin est copié seul, comme
   après une installation, et on lui demande ce qu'il trouve. C'est ainsi
   qu'on a découvert que la licence était cherchée *au-dessus* du paquet :
   présente dans le dépôt, introuvable chez tout le monde.
"""
from __future__ import annotations

import ast
import configparser
import json
import shutil
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.installation import (          # noqa: E402
    ENUMS_QT6, fiche, fenetre, paquet_propre, poids_lisible, preflight,
    verifie)

# Les types de champ de couche, dont la forme valide a changé avec QGIS 4.
FORMES_CHAMP_ANCIENNES = ("QVariant",)

CLASSES_QT = {
    "Qt", "QDialog", "QDialogButtonBox", "QMessageBox", "QPainter", "QFont",
    "QFrame", "QHeaderView", "QAbstractItemView", "QSizePolicy", "QStyle",
    "QKeySequence", "QComboBox", "QFileDialog", "QEasingCurve",
    "QGraphicsItem", "QTextCursor", "QShortcut", "QAction", "QIcon",
    "QFontMetrics", "QFontMetricsF", "QBrush", "QPen", "QColor", "QImage",
    "QPixmap", "QTextDocument", "QTabWidget", "QTabBar", "QToolButton",
    "QListView", "QTreeView", "QTableView", "QGraphicsView", "QWidget",
    "QLayout", "QSplitter", "QScrollArea", "QSlider", "QCheckBox",
    "QLineEdit", "QSpinBox", "QDoubleSpinBox", "QLabel", "QPushButton",
}
# Ne pas confondre : `QgsWkbTypes.Line` n'est pas `Qt.Line`.
PREFIXE_QGIS = "Qgs"


def lit_metadata():
    """`metadata.txt` lu comme QGIS le lit (configparser, section general)."""
    cp = configparser.ConfigParser()
    with open(PLUGIN / "metadata.txt", encoding="utf-8") as flux:
        cp.read_file(flux)
    return {k: v for k, v in cp.items("general")} if cp.has_section("general") else {}


def champs_anciens(racine=None):
    """Les types de champ à l'ancienne forme (`QVariant.String`…)."""
    base = racine or PLUGIN
    champs = []
    for f in sorted(base.rglob("*.py")):
        rel = str(f.relative_to(base)).replace("\\", "/")
        if "__pycache__" in rel:
            continue
        try:
            arbre = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for n in ast.walk(arbre):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id in FORMES_CHAMP_ANCIENNES):
                champs.append({"fichier": rel, "ligne": n.lineno,
                               "forme": f"{n.value.id}.{n.attr}",
                               "forme_qt6": "Qgis.FieldType"})
    return champs


def sites_qt6():
    """Les endroits que Qt 6 refuse : énumérations à l'ancienne + exec_()."""
    enums, exec_ = [], []
    for f in sorted(PLUGIN.rglob("*.py")):
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        if "__pycache__" in rel:
            continue
        try:
            arbre = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for n in ast.walk(arbre):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                classe = n.value.id
                qualifie = f"{classe}.{n.attr}"
                if qualifie in ENUMS_QT6:
                    enums.append({"fichier": rel, "ligne": n.lineno,
                                  "forme": qualifie,
                                  "forme_qt6": ENUMS_QT6[qualifie]})
                elif classe == "Qt" and n.attr in ENUMS_QT6:
                    enums.append({"fichier": rel, "ligne": n.lineno,
                                  "forme": f"Qt.{n.attr}",
                                  "forme_qt6": f"Qt.{ENUMS_QT6[n.attr]}."
                                               f"{n.attr}"})
            elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and n.func.attr == "exec_"):
                exec_.append({"fichier": rel, "ligne": n.lineno})

    champs = champs_anciens()
    return enums, exec_, champs


def contenu_paquet():
    """Tout ce que le zip embarquerait s'il était fait du dossier tel quel."""
    noms, octets = [], 0
    for f in sorted(PLUGIN.rglob("*")):
        if f.is_file():
            rel = f"DrillMaster/{f.relative_to(PLUGIN).as_posix()}"
            noms.append(rel)
            octets += f.stat().st_size
    fautifs = paquet_propre(noms)
    propre = [n for n in noms if n not in set(fautifs)]
    return {
        "fichiers_total": len(noms),
        "poids_total_ko": round(octets / 1024, 1),
        "poids_total_lisible": poids_lisible(octets),
        "a_exclure": len(fautifs),
        "exemples_a_exclure": fautifs[:12],
        "fichiers_propres": len(propre),
        "poids_propre_ko": round(sum(
            (RACINE / n).stat().st_size for n in propre) / 1024, 1),
    }


def demarrage_isole():
    """Le plugin copié seul, comme chez l'utilisateur : que trouve-t-il ?

    Une installation ne se juge pas dans le dépôt de l'auteur. On copie donc
    le paquet dans un dossier « plugins » vide, sans rien au-dessus, et on
    interroge la fiche d'identité.
    """
    resultat = {"preflight": [], "licence": "", "licence_trouvee": False}
    with tempfile.TemporaryDirectory() as tmp:
        cible = Path(tmp) / "plugins" / "DrillMaster"
        shutil.copytree(PLUGIN, cible,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        resultat["preflight"] = preflight(str(cible))
        sys.path.insert(0, str(Path(tmp) / "plugins"))
        for nom in [m for m in sys.modules if m.startswith("DrillMaster")]:
            del sys.modules[nom]
        try:
            from DrillMaster.core.about import about_info
            info = about_info(str(cible))
            resultat["licence"] = info.get("license_file", "")
            resultat["licence_trouvee"] = bool(info.get("license_installed"))
            resultat["version_lue"] = info.get("version", "")
        finally:
            sys.path.pop(0)
            for nom in [m for m in sys.modules if m.startswith("DrillMaster")]:
                del sys.modules[nom]
    return resultat


def main(argv):
    meta = lit_metadata()
    f = fiche(meta)
    reproches = verifie(meta)
    enums, exec_, champs = sites_qt6()
    fen = fenetre(meta.get("qgisminimumversion", ""),
                  meta.get("qgismaximumversion", ""),
                  len(enums), len(exec_), len(champs))
    paquet = contenu_paquet()
    isole = demarrage_isole()

    print("── la fiche d'identité (ce qu'exige le dépôt officiel)")
    print(f"  champs obligatoires fournis : {len(f['fournis'])}/{len(f['requis'])}")
    for champ in f["manquants"]:
        print(f"    MANQUE  {champ}")
    for r in reproches:
        print(f"  reproche : {r}")
    print(f"  version : {meta.get('version', '—')}")

    print("\n── la fenêtre de compatibilité")
    print(f"  minimum {fen['minimum']} · maximum déclaré "
          f"{fen['maximum'] or '(non déclaré)'}")
    print(f"  sites que Qt 6 refuse : {len(enums)} énumérations "
          f"+ {len(exec_)} exec_() + {len(champs)} types de champ")
    if fen["mensonge"]:
        print("  ATTENTION : la fenêtre déclarée couvre QGIS 4, le code non.")
    elif fen["declare_qgis4"]:
        epreuve = "faite" if fen["epreuve_reelle"] else "PAS FAITE"
        print("  la fenêtre annonce QGIS 4 ; le code n'a plus de forme")
        print("  que Qt 6 refuse.")
        print(f"  épreuve dans un QGIS 4 réel : {epreuve} — on le dit, "
              "on ne l'affirme pas")
    else:
        print("  la fenêtre déclarée ne promet pas QGIS 4 — et c'est exact")

    print("\n── le paquet")
    print(f"  {paquet['fichiers_total']} fichiers, "
          f"{paquet['poids_total_lisible']}")
    print(f"  {paquet['a_exclure']} fichier(s) n'ont rien à y faire "
          f"→ {paquet['fichiers_propres']} fichiers utiles")
    for exemple in paquet["exemples_a_exclure"][:6]:
        print(f"    {exemple}")

    print("\n── le démarrage, paquet copié seul")
    print(f"  fichiers manquants : {isole['preflight'] or 'aucun'}")
    print(f"  licence : {isole['licence'] or 'introuvable'}")
    print(f"  licence trouvée : {'oui' if isole['licence_trouvee'] else 'NON'}")

    if "--ecrit" in argv:
        sortie = {
            "fiche": {"requis": f["requis"], "fournis": f["fournis"],
                      "manquants": f["manquants"], "reproches": reproches,
                      "version": meta.get("version", ""),
                      "auteur": meta.get("author", ""),
                      "courriel": meta.get("email", "")},
            "compatibilite": {**fen, "sites": enums[:60],
                              "sites_total": len(enums),
                              "champs": champs[:60]},
            "paquet": paquet,
            "demarrage_isole": isole,
        }
        (RACINE / "specs" / "data" / "installation.json").write_text(
            json.dumps(sortie, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print("\nécrit specs/data/installation.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
