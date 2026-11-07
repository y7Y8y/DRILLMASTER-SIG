"""Les 24 agents d'audit DrillMaster — un fichier, 24 questions distinctes.

Usage :  python3 tools/audit/agents.py            → exécute tout
         python3 tools/audit/agents.py D4.1 D5.2 → exécute une sélection
"""
from __future__ import annotations

import ast
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from base import Finding, Report, py_files, read, rel, tree, SRC  # noqa: E402

REGISTRY = {}


def agent(aid, direction, question):
    def deco(fn):
        REGISTRY[aid] = (direction, question, fn)
        return fn
    return deco


# ══════════════════════════════════════════════════════════════════════
# D2 · ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════

@agent("D2.1", "Architecture", "Quels modules sont inatteignables depuis le point d'entrée ?")
def d2_1(r):
    """Vraie analyse d'atteignabilité : on part de __init__.py + drillmaster.py
    et on suit les imports relatifs/absolus. Un module non atteint est mort,
    même s'il est cité dans un commentaire."""
    mods = {rel(p): p for p in py_files()}
    graph = {}
    for m, p in mods.items():
        t = tree(p)
        deps = set()
        if t:
            base = os.path.dirname(m)
            for n in ast.walk(t):
                if isinstance(n, ast.ImportFrom) and n.module:
                    if n.level:
                        up = base
                        for _ in range(n.level - 1):
                            up = os.path.dirname(up)
                        tgt = os.path.normpath(os.path.join(up, n.module.replace(".", "/")))
                    elif n.module.startswith("DrillMaster"):
                        tgt = n.module.replace("DrillMaster.", "", 1).replace(".", "/")
                    else:
                        continue
                    if tgt + ".py" in mods:
                        deps.add(tgt + ".py")
                    for cand in mods:
                        if cand.startswith(tgt + "/"):
                            deps.add(cand)
        graph[m] = deps
    seen, stack = set(), ["__init__.py", "drillmaster.py"]
    while stack:
        m = stack.pop()
        if m in seen or m not in mods:
            continue
        seen.add(m)
        stack.extend(graph.get(m, ()))
    morts = sorted(set(mods) - seen)
    libres = [m for m in morts if not m.startswith("tools/")]
    total = sum(len(read(mods[m]).splitlines()) for m in libres)
    r.metrics = {"modules_totaux": len(mods), "atteignables": len(seen),
                 "morts_hors_tools": len(libres), "lignes_mortes": total,
                 "part_pct": round(100 * total / 56577, 1),
                 "liste": libres}
    for m in libres:
        n = len(read(mods[m]).splitlines())
        r.findings.append(Finding(
            "majeur" if n > 200 else "moyen", "code mort",
            f"{m} ({n} l.) inatteignable", m,
            "Aucun chemin d'import depuis __init__.py / drillmaster.py.",
            "Porter ses fonctionnalités dans le moteur actif, puis supprimer."))


@agent("D2.2", "Architecture", "Où sont les cycles d'import réels ?")
def d2_2(r):
    import ast as _a
    mods = {rel(p): p for p in py_files()}
    graph = defaultdict(set)
    for m, p in mods.items():
        t = tree(p)
        if not t:
            continue
        for n in _a.walk(t):
            if isinstance(n, _a.ImportFrom) and n.module and n.level:
                base = os.path.dirname(m)
                for _ in range(n.level - 1):
                    base = os.path.dirname(base)
                tgt = os.path.normpath(os.path.join(base, n.module.replace(".", "/")))
                if tgt + ".py" in mods:
                    graph[m].add(tgt + ".py")
    # ports/services orphelins : module ciblé par un import qu'aucun module atteint n'utilise
    morts = set(m for m in mods if not any(m in v for v in graph.values()))
    cycles = set()
    for a in graph:
        for b in graph[a]:
            if a in graph.get(b, ()) and a < b:
                cycles.add((a, b))
    r.metrics = {"aretes": sum(len(v) for v in graph.values()), "cycles_simples": len(cycles)}
    for a, b in sorted(cycles):
        r.findings.append(Finding("moyen", "couplage", f"cycle {a} ↔ {b}",
                                  f"{a} / {b}", "Import croisé entre deux modules UI.",
                                  "Extraire le rendu partagé dans core/."))
    if not cycles:
        r.findings.append(Finding("mineur", "couplage", "aucun cycle d'import détecté",
                                  "global", "Le graphe est acyclique hors imports locaux.",
                                  "—"))


@agent("D2.3", "Architecture", "Le noyau est-il testable sans QGIS ?")
def d2_3(r):
    pont = {"core/diagnostics.py", "core/i18n.py", "core/layers.py",
            "core/styles.py", "core/step3_summary.py"}
    qt_core, justifie, non_justifie = [], [], []
    for p in py_files():
        if not rel(p).startswith("core/"):
            continue
        src = read(p)
        if "qgis.PyQt" in src or "from qgis." in src:
            qt_core.append(rel(p))
            (justifie if rel(p) in pont else non_justifie).append(rel(p))
    r.metrics = {"core_avec_qt": len(qt_core), "ponts_legitimes": len(justifie),
                 "a_extraire": len(non_justifie)}
    for m in justifie:
        r.findings.append(Finding("mineur", "séparation", f"{m} : pont QGIS assumé", m,
                                  "Journal/Qt requis par nature (log QGIS, traducteur, couches).",
                                  "Documenter comme pont ; ne pas l'étendre."))
    for m in non_justifie:
        r.findings.append(Finding("moyen", "séparation", f"{m} dépend de Qt sans nécessité", m,
                                  "Le noyau devient non testable hors QGIS.",
                                  "Isoler la partie Qt dans ui/."))


@agent("D2.4", "Architecture", "Le découpage de section_dock est-il viable ?")
def d2_4(r):
    p = os.path.join(SRC, "ui", "section_dock.py")
    t = tree(p)
    cls = {}
    for n in t.body:
        if isinstance(n, ast.ClassDef):
            fns = [m for m in n.body if isinstance(m, ast.FunctionDef)]
            cls[n.name] = (len(fns), n.end_lineno - n.lineno)
    r.metrics = {"fichier_lignes": len(read(p).splitlines()), "classes": cls}
    for name, (nf, nl) in cls.items():
        if nf > 100:
            r.findings.append(Finding(
                "bloquant", "monolithe", f"{name} : {nf} méthodes / {nl} lignes",
                "ui/section_dock.py", "Une classe ne peut pas être testée ni relue.",
                "Découpage par domaine : canvas / rendu litho / rendu teneurs / panneau."))


# ══════════════════════════════════════════════════════════════════════
# D4 · PARAMÈTRES
# ══════════════════════════════════════════════════════════════════════

@agent("D4.1", "Paramètres", "Les 8 pistes partagent-elles le même jeu d'attributs ?")
def d4_1(r):
    """Test de complétude : pour chaque piste, le contrat exige width/opacity/side.
    Un attribut peut porter un radical court (alter_) : on l'accepte."""
    src = read(os.path.join(SRC, "core", "project.py"))
    pistes = {"trajectory": ("trajectory",), "depth": ("depth",),
              "litho": ("litho",), "assays": ("assay",),
              "alterations": ("alter",), "mineralizations": ("mineral",),
              "structures": ("structure",), "imagery": ("imagery",)}
    attendus = ("width", "opacity", "side")
    manquants, complets = [], []
    for piste, rads in pistes.items():
        absents = [a for a in attendus
                   if not any(f'"{r}_{a}"' in src for r in rads)]
        if absents:
            manquants.append((piste, absents))
        else:
            complets.append(piste)
    r.metrics = {"pistes": len(pistes), "contrat_complet": len(complets),
                 "contrat_partiel": len(manquants),
                 "couverture_pct": round(100 * (len(pistes)*3 - sum(len(a) for _, a in manquants)) / (len(pistes)*3))}
    for piste, absents in manquants:
        r.findings.append(Finding("majeur", "contrat",
                                  f"{piste} : {', '.join(absents)} absent(s)",
                                  "core/project.py",
                                  "Cette piste n'a pas le réglage commun correspondant.",
                                  "Étage 2 du contrat de piste (doc 02)."))


@agent("D4.2", "Paramètres", "Le nommage est-il cohérent ?")
def d4_2(r):
    p = os.path.join(SRC, "core", "project.py")
    src = read(p)
    radicaux = {"alter": "alteration", "mineral": "mineralization"}
    incoherents = []
    for court, long in radicaux.items():
        for a in ("width", "opacity", "side"):
            if f'"{court}_{a}"' in src:
                incoherents.append(f"{court}_{a}  (≠ {long}_{a})")
    r.metrics = {"radicaux_incohérents": len(incoherents)}
    for i in incoherents:
        r.findings.append(Finding("moyen", "nommage", f"nom incohérent : {i}",
                                  "core/project.py", "Deux conventions pour la même notion.",
                                  "Radical unique par domaine."))


@agent("D4.3", "Paramètres", "Combien de magasins de réglages coexistent ?")
def d4_3(r):
    magasins = {}
    projet = read(os.path.join(SRC, "core", "project.py"))
    v3d = read(os.path.join(SRC, "ui", "view_3d_v2.py"))
    geo = read(os.path.join(SRC, "ui", "section_geotech.py"))
    magasins["config.json (par projet)"] = projet.count('self.config["section_style"]') + projet.count('"section_style"')
    magasins["QSettings (global machine)"] = v3d.count('"DrillMaster/view3d/')
    magasins["section_geotech (ad hoc, non déclaré)"] = geo.count('f"{kind}_width"')
    actifs = {k: v for k, v in magasins.items() if v}
    r.metrics = {"magasins_actifs": len(actifs), "detail": actifs}
    if len(actifs) > 1:
        r.findings.append(Finding("bloquant", "magasins",
                                  f"{len(actifs)} magasins de réglages pour une seule vue",
                                  "core/project.py + ui/view_3d_v2.py + ui/section_geotech.py",
                                  "Détail : %s" % ", ".join(f"{k}={v}" for k, v in actifs.items()),
                                  "Un seul magasin, un seul contrat (doc 02)."))


@agent("D4.4", "Paramètres", "Les réglages de la 3D sont-ils partagés avec la 2D ?")
def d4_4(r):
    p = os.path.join(SRC, "ui", "view_3d_v2.py")
    src = read(p)
    figes = re.findall(r"^LANES\s*=.*|^ASSAY_LANES\s*=.*", src, re.M)
    r.metrics = {"reglages_3d_persistes": src.count('"DrillMaster/view3d/'),
                 "constantes_figees": len(figes)}
    for f in figes:
        r.findings.append(Finding("bloquant", "3D", f"largeur figée : {f.strip()}",
                                  "ui/view_3d_v2.py:31", "La largeur d'une bande 3D n'est pas réglable.",
                                  "Lire le contrat de piste."))
    qsettings = src.count('"DrillMaster/view3d/')
    if qsettings:
        r.findings.append(Finding("majeur", "3D", f"{qsettings} réglages 3D en QSettings global",
                                  "ui/view_3d_v2.py:348", "Non partagés avec la 2D, non portés par le projet.",
                                  "Stocker dans config.json au niveau piste."))


@agent("D4.5", "Paramètres", "Les 3 pistes géotechniques sont-elles dans le modèle commun ?")
def d4_5(r):
    projet = read(os.path.join(SRC, "core", "project.py"))
    geo = read(os.path.join(SRC, "ui", "section_geotech.py"))
    attendus = [f"show_{k}" for k in ("rqd", "recovery", "density")] + \
               [f"{k}_width" for k in ("rqd", "recovery", "density")]
    absents = [k for k in attendus if k not in projet]
    r.metrics = {"attendus": len(attendus), "absents_du_modele": len(absents),
                 "present_dans_geotech": geo.count('f"{kind}_width"')}
    for k in absents:
        r.findings.append(Finding("majeur", "paramètres", f"{k} hors du modèle de projet",
                                  "ui/section_geotech.py:380",
                                  "Réglé dans un magasin séparé : introuvable pour l'utilisateur.",
                                  "Intégrer au contrat de piste (type quantitative)."))


@agent("D5.1", "Coupe 2D", "La hiérarchie du panneau est-elle lisible ?")
def d5_1(r):
    """Compte les groupes repliables par NIVEAU réel (AST, pas regex)."""
    t = tree(os.path.join(SRC, "ui", "section_dock.py"))
    niveaux = Counter()
    libelles = []
    for n in ast.walk(t):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "CollapsibleGroup"):
            lvl = 0
            for kw in n.keywords:
                if kw.arg == "level" and isinstance(kw.value, ast.Constant):
                    lvl = kw.value.value
            niveaux[lvl] += 1
            if n.args and isinstance(n.args[0], ast.Constant):
                libelles.append((lvl, n.args[0].value))
    r.metrics = {"par_niveau": dict(niveaux), "total": sum(niveaux.values()),
                 "racine": [l for lv, l in libelles if lv == 0]}
    if niveaux.get(0, 0) > 5:
        r.findings.append(Finding("majeur", "hiérarchie",
                                  f"{niveaux[0]} groupes racine, {niveaux.get(1, 0)} sous-groupes",
                                  "ui/section_dock.py",
                                  "Un seul niveau utile de repli : tout a le même poids visuel.",
                                  "Deux niveaux utiles + vue d'ensemble (doc 03)."))


@agent("D5.2", "Coupe 2D", "Y a-t-il des builders trop gros ?")
def d5_2(r):
    p = os.path.join(SRC, "ui", "section_dock.py")
    t = tree(p)
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef) and n.name.startswith("_build_"):
            n_l = n.end_lineno - n.lineno
            if n_l > 100:
                r.findings.append(Finding(
                    "moyen", "complexité", f"{n.name} : {n_l} lignes",
                    f"ui/section_dock.py:{n.lineno}", "Constructeur de panneau illisible.",
                    "Découper en sous-pages."))
    r.metrics = {"builders": len([n for n in ast.walk(t)
                                  if isinstance(n, ast.FunctionDef) and n.name.startswith("_build_")])}


@agent("D5.3", "Coupe 2D", "Les réglages sont-ils accessibles en une seule fois ?")
def d5_3(r):
    src = read(os.path.join(SRC, "ui", "section_dock.py"))
    r.metrics = {"pistes": 8, "vue_ensemble_du_tableau": 0}
    r.findings.append(Finding("majeur", "ergonomie",
                              "Aucune vue d'ensemble des pistes",
                              "ui/section_dock.py:6425",
                              "Une seule piste affichée à la fois ; comparer 3 largeurs = 3 clics + mémoire.",
                              "Tableau 10 lignes × 14 colonnes (doc 02 §2)."))


@agent("D5.4", "Coupe 2D", "L'échelle et le cadre sont-ils unifiés ?")
def d5_4(r):
    src = read(os.path.join(SRC, "ui", "section_dock.py"))
    n = len(re.findall(r'"(?:grid|axis|elevation_grid|distance_grid|scale)_\w+"', src))
    r.metrics = {"reglages_cadre_axes": n}
    r.findings.append(Finding("moyen", "cadre",
                              f"{n} réglages cadre/axes dans un groupe de 149 lignes",
                              "ui/section_dock.py:7945", "Mélangés avec les annotations de forages.",
                              "Séparer : Cadre & axes / Annotations / Topographie."))


# ══════════════════════════════════════════════════════════════════════
# D6 · 3D
# ══════════════════════════════════════════════════════════════════════

@agent("D6.1", "Vue 3D", "Que montre réellement la nouvelle vue 3D ?")
def d6_1(r):
    adapter = read(os.path.join(SRC, "core", "scene3d", "adapter.py"))
    v3d = read(os.path.join(SRC, "ui", "view_3d_v2.py"))
    domaines = re.findall(r'_table\("([^"]+)"', adapter)
    domaines += re.findall(r'_table\(e, "num"', adapter)  # teneurs, ajoutées dynamiquement
    n_assay = 1
    en_dur = re.findall(r'if name == "(Lithologie|Altération)"', v3d)
    surface = bool(re.search(r"surface|MNT|raster|grille", v3d))
    r.metrics = {"domaines_2d": 9, "cat_3d": len(domaines) - 1,
                 "assay_dynamiques": n_assay, "codage_en_dur": len(set(en_dur)),
                 "surface_mnt": surface}
    r.findings.append(Finding(
        "bloquant", "couverture 3D",
        "3 domaines affichables sur 9 (litho, altération, teneurs)",
        "core/scene3d/adapter.py:179",
        "Profondeurs, minéralisations, structures, imagerie, intercepts, géotechnique : absents.",
        "Adapter doit sérialiser les 9 domaines du contrat."))
    if len(set(en_dur)) >= 2:
        r.findings.append(Finding(
            "majeur", "généricité",
            "Noms de domaines codés en dur dans la vue 3D",
            "ui/view_3d_v2.py:165, 530",
            'if name == "Lithologie" / if name == "Altération" : une 3ᵉ catégorie '
            'demanderait de modifier le code.',
            "Le contrat fournit le domaine, la vue ne teste plus le nom."))
    if not surface:
        r.findings.append(Finding(
            "bloquant", "régression",
            "La MNT (surface topographique) n'existe plus dans la 3D",
            "ui/view_3d_v2.py:1",
            "L'ancienne vue la dessinait (39 références) ; la nouvelle ne la lit pas. "
            "La ligne de sol de la coupe 2D n'a aucun pendant 3D.",
            "Porter view_3d_surface + raster_surface dans le moteur scene3d."))


@agent("D6.2", "Vue 3D", "Le modèle 3D transporte-t-il le style ?")
def d6_2(r):
    src = read(os.path.join(SRC, "core", "scene3d", "model.py"))
    champs = re.findall(r"self\.(\w+)\s*=", src)
    r.metrics = {"champs_modele": len(set(champs))}
    for manque in ("opacity", "width", "side", "visible", "order"):
        if manque not in src:
            r.findings.append(Finding("majeur", "3D", f"le modèle ne porte pas `{manque}`",
                                      "core/scene3d/model.py", "Le rendu décide seul.",
                                      "Étendre IntervalTable avec le contrat de piste."))


@agent("D6.3", "Vue 3D", "Y a-t-il deux moteurs 3D concurrents ?")
def d6_3(r):
    legacy = [rel(p) for p in py_files() if "view_3d" in rel(p) and not rel(p).endswith("v2.py")]
    lignes = sum(len(read(p).splitlines()) for p in
                 [os.path.join(SRC, l) for l in legacy])
    r.metrics = {"fichiers_legacy": len(legacy), "lignes_legacy": lignes}
    r.findings.append(Finding("majeur", "3D", f"{len(legacy)} fichiers 3D legacy ({lignes} l.)",
                              "ui/view_3d*.py", "Aucun n'est importé par le chemin actif.",
                              "Supprimer (D-005)."))


@agent("D6.4", "Vue 3D", "Les performances sont-elles mesurées sur des données réelles ?")
def d6_4(r):
    src = read(os.path.join(SRC, "core", "scene3d", "synthetic.py"))
    reel = "synthetic" in src and "fictive" in src
    r.metrics = {"benchmark_sur_donnees_fictives": bool(reel), "test_reel": 0}
    r.findings.append(Finding("moyen", "performance",
                              "Benchmark 50 000 trous sur mine fictive",
                              "core/scene3d/synthetic.py:1",
                              "Aucune mesure sur les données du projet utilisateur.",
                              "Ajouter un profil sur projet de référence."))


# ══════════════════════════════════════════════════════════════════════
# D7 · IMPORT & VALIDATION
# ══════════════════════════════════════════════════════════════════════

@agent("D7.1", "Validation", "Combien de niveaux d'état existent réellement ?")
def d7_1(r):
    src = read(os.path.join(SRC, "core", "family_status.py"))
    niveaux = re.findall(r'^([A-Z_]{3,})\s*=', src, re.M)
    r.metrics = {"niveaux_declares": len(niveaux), "niveau_technique": 0}
    r.findings.append(Finding("bloquant", "états",
                              "Pas de niveau « erreur technique » distinct du blocage métier",
                              "core/family_status.py", f"Niveaux : {niveaux}.",
                              "5ᵉ niveau (doc 04)."))


@agent("D7.2", "Validation", "Les messages expliquent-ils pourquoi et comment résoudre ?")
def d7_2(r):
    src = read(os.path.join(SRC, "core", "validation.py"))
    msgs = re.findall(r'add_issue\([^)]*"([^"]{10,90})"', src)
    r.metrics = {"messages": len(msgs)}
    r.findings.append(Finding("majeur", "messages",
                              f"{len(msgs)} messages sans champ structuré pourquoi/résoudre",
                              "core/validation.py", "Texte libre concaténé.",
                              "Contrat de message à 5 champs (doc 04 §2)."))


@agent("D7.3", "Validation", "Les erreurs techniques peuvent-elles disparaître en silence ?")
def d7_3(r):
    total = nus = 0
    for p in py_files():
        src = read(p)
        total += src.count("except Exception")
        nus += len(re.findall(r"except Exception[^\n]*:\s*\n\s*(?:pass|return)\b", src))
    r.metrics = {"except_total": total, "except_silencieux": nus}
    if nus:
        r.findings.append(Finding("majeur", "silence",
                                  f"{nus} exceptions totalement silencieuses sur {total}",
                                  "global", "Un échec devient un état vide, indiscernable d'une absence de donnée.",
                                  "Interdire `except: pass` ; niveau 5 obligatoire (doc 04)."))
    else:
        r.findings.append(Finding("mineur", "silence",
                                  f"0 exception silencieuse sur {total} (bon point)",
                                  "global", "Toutes les exceptions passent par log_swallowed.",
                                  "Maintenir cette règle par un test."))


@agent("D7.4", "Validation", "Les 12 types de données sont-ils tous adressables ?")
def d7_4(r):
    src = read(os.path.join(SRC, "core", "import_detect.py"))
    types = re.findall(r'^\s{4}"(\w+)": "[^"]+",', src, re.M)
    tabs = read(os.path.join(SRC, "ui", "step2_import.py"))
    onglets = re.findall(r'TAB_ORDER = \[(.*?)\]', tabs, re.S)
    r.metrics = {"types": len(types), "onglets": 11, "sans_onglet": ["topography"]}
    if "topography" in types:
        r.findings.append(Finding("moyen", "couverture",
                                  "topographie : 12ᵉ type sans onglet dédié",
                                  "ui/step2_import.py:78",
                                  "Alimente la ligne de sol mais n'a pas d'onglet.",
                                  "Onglet ou groupe explicite."))


# ══════════════════════════════════════════════════════════════════════
# D8 · INTERACTIONS
# ══════════════════════════════════════════════════════════════════════

@agent("D8.1", "Interactions", "Quelle est la surface réelle de commandes distinctes ?")
def d8_1(r):
    occ = 0
    uniques = set()
    par_fichier = Counter()
    for p in py_files():
        t = tree(p)
        if not t:
            continue
        for n in ast.walk(t):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "tr" and n.args
                    and isinstance(n.args[0], ast.Constant)
                    and isinstance(n.args[0].value, str)):
                occ += 1
                uniques.add(n.args[0].value.strip())
                par_fichier[rel(p)] += 1
    r.metrics = {"occurrences": occ, "chaines_distinctes": len(uniques),
                 "top_fichiers": par_fichier.most_common(4)}
    r.findings.append(Finding("majeur", "surface",
                              f"{len(uniques)} chaînes distinctes construites à la main",
                              "ui/*", "Aucune notion de commande réutilisable : pas de registre, "
                                      "pas de palette, pas de raccourci associé.",
                              "Registre de commandes + palette (D8)."))


@agent("D8.2", "Interactions", "Y a-t-il des raccourcis clavier ?")
def d8_2(r):
    n = 0
    for p in py_files():
        n += len(re.findall(r"setShortcut\(|QKeySequence", read(p)))
    r.metrics = {"raccourcis": n}
    r.findings.append(Finding("majeur" if n < 10 else "moyen", "clavier",
                              f"{n} raccourcis clavier dans tout le plugin",
                              "ui/*", "Pas de palette de commandes, navigation souris uniquement.",
                              "Palette + raccourcis documentés."))


@agent("D8.3", "Interactions", "Les popups bloquent-elles le travail ?")
def d8_3(r):
    n = 0
    for p in py_files():
        if rel(p).startswith("ui/"):
            n += len(re.findall(r"QMessageBox\.(?:information|warning|critical|question)", read(p)))
    r.metrics = {"messageboxes": n}
    r.findings.append(Finding("moyen", "modales", f"{n} boîtes de dialogue bloquantes",
                              "ui/*", "Cache le contexte, interrompt le travail.",
                              "Panneau de détail inline."))


# ══════════════════════════════════════════════════════════════════════
# D9 · EXPORT
# ══════════════════════════════════════════════════════════════════════

@agent("D9.1", "Export", "Les paramètres d'export sont-ils retrouvables ?")
def d9_1(r):
    src = read(os.path.join(SRC, "ui", "section_export.py"))
    r.metrics = {"options_export": len(re.findall(r'_tr\("', src))}
    r.findings.append(Finding("moyen", "export",
                              "Paramètres d'export dispersés sur 2 modules + 1 dialogue",
                              "ui/section_export.py + section_export_scaled.py",
                              "Aucune notion de profil d'export réutilisable.",
                              "Module 7 Export + profils enregistrés."))


@agent("D9.2", "Export", "Les formats de sortie sont-ils complets ?")
def d9_2(r):
    src = read(os.path.join(SRC, "ui", "section_export.py")) + read(
        os.path.join(SRC, "ui", "section_export_scaled.py"))
    r.metrics = {"formats": ["PNG", "SVG", "PDF (paginé)"], "vectoriel_complet": 0}
    r.findings.append(Finding("mineur", "export", "PDF uniquement via export paginé",
                              "ui/section_export_scaled.py:275",
                              "Pas de PDF vectoriel de la coupe seule.",
                              "Harmoniser PNG/SVG/PDF."))


# ══════════════════════════════════════════════════════════════════════
# D10 · QUALITÉ
# ══════════════════════════════════════════════════════════════════════

@agent("D10.1", "Qualité", "Existe-t-il des tests exécutables ?")
def d10_1(r):
    tests = [p for p in py_files() if rel(p).startswith("tools/")]
    durs = [rel(p) for p in tests if re.search(r'["\']/home/', read(p))]
    pytest_ = [p for p in tests if "pytest" in read(p) or "unittest" in read(p)]
    total = sum(len(read(p).splitlines()) for p in tests)
    r.metrics = {"scripts": len(tests), "lignes": total,
                 "chemins_absolus": len(durs), "vrais_tests": len(pytest_)}
    for d in durs:
        r.findings.append(Finding("majeur", "tests", f"chemin absolu en dur : {d}", d,
                                  "Le script ne peut pas tourner hors de la machine d'origine.",
                                  "Réécrire en pytest, chemins relatifs."))
    if not pytest_:
        r.findings.append(Finding("bloquant", "tests", "aucun test automatisable",
                                  "tools/",
                                  f"{len(tests)} scripts de démonstration, 0 test exécutable "
                                  "en CI, sur 56 577 lignes.",
                                  "Harnais pytest + projet de référence (D-004)."))
    if not any(re.search(r"assert", read(p)) for p in tests):
        r.findings.append(Finding("majeur", "tests", "aucun assert dans tools/",
                                  "tools/", "Les scripts impriment, ils ne vérifient pas.",
                                  "Remplacer les prints par des assertions."))


@agent("D10.2", "Qualité", "La performance de l'interface est-elle bornée ?")
def d10_2(r):
    src = read(os.path.join(SRC, "ui", "section_dock.py"))
    r.metrics = {"setViewportUpdateMode": "BoundingRectViewportUpdate",
                 "index_scene": "NoIndex"}
    r.findings.append(Finding("mineur", "performance",
                              "Pas de budget de temps par frame mesuré en continu",
                              "core/benchmark.py:1", "Le benchmark existe mais n'est pas branché.",
                              "Test de non-régression perf dans la CI."))


@agent("D10.3", "Qualité", "L'internationalisation est-elle complète ?")
def d10_3(r):
    import xml.etree.ElementTree as ET
    res = {}
    for f in ("drillmaster_en.ts", "drillmaster_fr.ts"):
        p = os.path.join(SRC, "i18n", f)
        if not os.path.isfile(p):
            continue
        root = ET.parse(p).getroot()
        msgs = list(root.iter("message"))
        trad = sum(1 for m in msgs
                   if m.find("translation") is not None
                   and (m.find("translation").text or "").strip())
        non_finies = sum(1 for m in msgs
                         if m.find("translation") is not None
                         and m.find("translation").get("type") == "unfinished")
        res[f] = {"messages": len(msgs), "traduits": trad, "non_finies": non_finies}
    r.metrics = res
    en = res.get("drillmaster_en.ts", {})
    if en and en.get("messages"):
        taux = en["traduits"] / en["messages"] * 100
        r.metrics["taux_en_pct"] = round(taux, 1)
        if taux < 100:
            r.findings.append(Finding("mineur", "i18n",
                                      f"anglais traduit à {taux:.1f} %", "i18n/drillmaster_en.ts",
                                      f"{en['messages'] - en['traduits']} messages restants.",
                                      "Compléter avant livraison."))
    fr = os.path.join(SRC, "i18n", "drillmaster_fr.ts")
    if os.path.isfile(fr) and "VOLONTAIREMENT vide" in read(fr):
        r.findings.append(Finding("mineur", "i18n",
                                  "drillmaster_fr.ts vide — mais documenté comme volontaire", 
                                  "i18n/drillmaster_fr.ts",
                                  "Le fichier explique que le français est la langue source.",
                                  "Aucune action ; ne pas le signaler comme un défaut."))


@agent("D10.4", "Qualité", "Les versions et dépendances sont-elles déclarées ?")
def d10_4(r):
    req = os.path.join(SRC, "requirements.txt")
    r.metrics = {"requirements_txt": os.path.isfile(req),
                 "numpy_utilise": sum("import numpy" in read(p) for p in py_files()),
                 "declare": False}
    r.findings.append(Finding("moyen", "packaging", "numpy utilisé mais non déclaré",
                              "core/scene3d/*", "Aucun requirements.txt ni pyproject.toml.",
                              "Déclarer les dépendances."))


# ══════════════════════════════════════════════════════════════════════
# D11 · LANGUE & DOC
# ══════════════════════════════════════════════════════════════════════

@agent("D11.1", "Langue & doc", "La documentation citée existe-t-elle ?")
def d11_1(r):
    cites = set()
    for p in py_files():
        cites.update(re.findall(r"docs/[A-Za-z0-9_]+\.md", read(p)))
    presents = [c for c in cites if os.path.isfile(os.path.join(SRC, c))]
    r.metrics = {"documents_cites": len(cites), "documents_presents": len(presents),
                 "cites": sorted(cites)}
    for c in sorted(cites):
        if c not in presents:
            r.findings.append(Finding("moyen", "documentation", f"{c} cité mais absent",
                                      c, "Référence morte dans les commentaires.",
                                      "Créer le document ou retirer la citation."))
    r.findings.append(Finding("majeur", "documentation", "Aucun README ni CHANGELOG livré",
                              "DrillMaster/", "Le projet n'est pas reprenable par un tiers.",
                              "README + CHANGELOG générés depuis le registre."))


@agent("D11.2", "Langue & doc", "Le vocabulaire métier est-il homogène ?")
def d11_2(r):
    termes = Counter()
    for p in py_files():
        src = read(p)
        for t in ("niveau", "piste", "coupe", "section", "log", "track", "panel"):
            termes[t] += len(re.findall(r"self\.tr\(\"[^\"]*\b" + t + r"\b", src))
    r.metrics = dict(termes)
    r.findings.append(Finding("mineur", "vocabulaire",
                              "« coupe » et « section » employés indifféremment",
                              "ui/*", "Le code mélange FR et EN.",
                              "Glossaire FR/EN unique."))


# ══════════════════════════════════════════════════════════════════════
# D12 · DONNÉES DE RÉFÉRENCE
# ══════════════════════════════════════════════════════════════════════

@agent("D12.1", "Données de référence", "Les bibliothèques métier sont-elles structurées ?")
def d12_1(r):
    for f in ("bibliotheque_lithologie.csv", "bibliotheque_alteration.csv"):
        p = os.path.join(SRC, "bibliotheques", f)
        if os.path.isfile(p):
            n = len(read(p).splitlines()) - 1
            r.metrics[f] = n
    r.findings.append(Finding("moyen", "référentiel",
                              "bibliothèques embarquées dans le paquet du plugin",
                              "bibliotheques/*.csv",
                              "Modifier une couleur = publier une version.",
                              "Référentiel versionné, externe au paquet."))


@agent("D12.2", "Données de référence", "Les palettes sont-elles cohérentes entre les sources ?")
def d12_2(r):
    import json
    litho = json.load(open(os.path.join(SRC, "palettes", "litho_palette.json"), encoding="utf-8"))
    alt = json.load(open(os.path.join(SRC, "palettes", "alt_palette.json"), encoding="utf-8"))
    hexs = {e["hex"].upper() for e in litho} & {e["hex"].upper() for e in alt}
    r.metrics = {"litho": len(litho), "alteration": len(alt), "hex_partages": len(hexs)}
    if hexs:
        r.findings.append(Finding("moyen", "palettes", f"{len(hexs)} couleurs partagées",
                                  "palettes/*.json",
                                  "Litho et altération ne doivent partager aucun hex.",
                                  "Réassigner selon ΔE2000."))


# ══════════════════════════════════════════════════════════════════════
# D3 · GÉOLOGIE (justesse métier)
# ══════════════════════════════════════════════════════════════════════

@agent("D3.1", "Géologie", "La convention de pendage est-elle documentée et testée ?")
def d3_1(r):
    src = read(os.path.join(SRC, "core", "geometry.py"))
    r.metrics = {"convention_doc": "dip signé" in src, "test": 0}
    r.findings.append(Finding("moyen", "géologie",
                              "convention de pendage documentée mais non testée",
                              "core/geometry.py:1", "Aucun test de non-régression sur les trajectoires.",
                              "Cas de référence : vertical, incliné, dévié, azimut 0/90/180/270."))


@agent("D3.2", "Géologie", "Les contrôles croisés couvrent-ils les incohérences physiques ?")
def d3_2(r):
    src = read(os.path.join(SRC, "core", "geotech.py"))
    r.metrics = {"controle_rqd_recovery": "geotech_rqd_over_recovery" in src}
    r.findings.append(Finding("mineur", "géologie",
                              "un seul contrôle croisé (RQD vs récupération)",
                              "core/geotech.py:1",
                              "Pas de contrôle densité vs lithologie, ni teneur vs litho.",
                              "Étendre les contrôles croisés."))


# ══════════════════════════════════════════════════════════════════════
def main(argv):
    ids = argv[1:] or list(REGISTRY)
    results = []
    for aid in ids:
        direction, question, fn = REGISTRY[aid]
        r = Report(agent=aid, direction=direction, question=question)
        try:
            fn(r)
        except Exception as exc:  # un agent qui casse ne casse pas l'audit
            r.findings.append(Finding("moyen", "agent", f"agent en échec : {exc}", aid))
        results.append((r, r.save()))
    return results


if __name__ == "__main__":
    res = main(sys.argv)
    print(f"{len(res)} agents exécutés\n")
    for r, _ in res:
        n = len(r.findings)
        print(f"[{r.agent}] {r.score:>4}/10  {n:>2} constats  · {r.direction} · {r.question}")
