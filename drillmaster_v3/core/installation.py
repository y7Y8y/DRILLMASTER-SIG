"""Chantier 12 — un plugin qui s'installe, ou qui ne se plaint pas à tort.

Le constat de la flotte tenait en trois lignes : « le champ `email` manque »,
« la compatibilité s'arrête à 3.99 », « la désinstallation est propre ». Deux
vraies, une fausse — et il en manquait la plus coûteuse.

    from drillmaster_v3.core.installation import fiche, verifie, paquet_propre

    manquants = verifie({"name": "DrillMaster", ...})   # → ["email"]
    paquet_propre(["DrillMaster/__pycache__/x.pyc"])     # → ce qui n'a rien à faire là

Ce que ce module refuse d'inventer
----------------------------------
1. **Une compatibilité qu'on ne tient pas.** Écrire `qgisMaximumVersion=4.99`
   fait apparaître le plugin dans la liste « prêt pour QGIS 4 » : c'est une
   promesse, pas une case à cocher. Tant que le code écrit `Qt.AlignCenter`
   au lieu de `Qt.AlignmentFlag.AlignCenter`, la promesse est fausse.
2. **Un fichier que rien ne lit.** Un paquet n'embarque que ce qui sert.
3. **Une licence introuvable chez l'utilisateur.** Le chemin d'un fichier se
   vérifie **là où le plugin est installé**, pas dans le dépôt de l'auteur.
"""
from __future__ import annotations

import os

# ── 1 · la fiche d'identité qu'exige le dépôt officiel ──────────────
# Source : documentation QGIS, « Structuring Python Plugins », table des
# métadonnées. Sept champs sont obligatoires ; le plugin en fournissait six.
CHAMPS_REQUIS = ("name", "qgisMinimumVersion", "description", "about",
                 "version", "author", "email", "repository")
CHAMPS_FACULTATIFS = ("changelog", "experimental", "deprecated", "tags",
                      "homepage", "tracker", "icon", "category",
                      "plugin_dependencies", "server", "hasProcessingProvider")

# Catégories admises par la documentation. « Plugins » n'en fait pas partie :
# le champ est un conseil de menu, et le plugin se pose déjà dans le menu
# « Extensions » par `addPluginToMenu`. Mieux vaut aucune catégorie qu'une
# catégorie fausse.
CATEGORIES = ("Raster", "Vector", "Database", "Mesh", "Web")

# ── 2 · ce qui n'a rien à faire dans un paquet livré ────────────────
MOTIFS_EXCLUS = ("__pycache__", ".pyc", ".pyo", ".DS_Store", ".git/",
                 ".idea/", ".vscode/")
# Dossiers de développement : ils tournent sur le poste de l'auteur, avec
# ses chemins à lui. Livrés, ils ne servent à personne et inquiètent.
DOSSIERS_DE_DEVELOPPEMENT = ("tools/", "tests/")


def fiche(metadata: dict) -> dict:
    """La fiche lue et classée : obligatoire, facultatif, manquant."""
    bas = {str(k).strip().lower(): str(v).strip()
           for k, v in (metadata or {}).items()}
    manquants = [c for c in CHAMPS_REQUIS if not bas.get(c.lower())]
    return {
        "champs": bas,
        "requis": list(CHAMPS_REQUIS),
        "fournis": [c for c in CHAMPS_REQUIS if bas.get(c.lower())],
        "manquants": manquants,
        "complet": not manquants,
        "facultatifs_fournis": [c for c in CHAMPS_FACULTATIFS
                                if bas.get(c.lower())],
    }


def verifie(metadata: dict) -> list:
    """Les reproches, en clair. Liste vide = la fiche passe."""
    f = fiche(metadata)
    reproches = []
    for champ in f["manquants"]:
        reproches.append(f"le champ obligatoire « {champ} » manque")
    adresse = f["champs"].get("email", "")
    if adresse and ("@" not in adresse or " " in adresse):
        reproches.append(f"l'adresse de contact « {adresse} » n'en est pas une")
    categorie = f["champs"].get("category", "")
    if categorie and categorie not in CATEGORIES:
        reproches.append(
            f"la catégorie « {categorie} » n'est pas dans la liste admise "
            f"({', '.join(CATEGORIES)}) : une catégorie fausse vaut moins "
            "qu'aucune catégorie")
    for champ in ("experimental", "deprecated", "server",
                  "hasProcessingProvider"):
        valeur = f["champs"].get(champ)
        if valeur and valeur.lower() not in ("true", "false"):
            reproches.append(f"« {champ} » vaut « {valeur} » au lieu de "
                             "True ou False")
    return reproches


# ── 3 · la fenêtre de compatibilité ─────────────────────────────────
# Forme Qt 5 d'un membre → forme Qt 6 exigée. Le plugin emploie la première
# 530 fois ; Qt 6 n'accepte que la seconde. Tant que c'est le cas, déclarer
# « compatible QGIS 4 » est un mensonge, même si le dépôt l'accepte.
ENUMS_QT6 = {
    # Qt : les énumérations qui ont quitté la classe Qt
    "AlignLeft": "AlignmentFlag", "AlignRight": "AlignmentFlag",
    "AlignCenter": "AlignmentFlag", "AlignHCenter": "AlignmentFlag",
    "AlignVCenter": "AlignmentFlag", "AlignTop": "AlignmentFlag",
    "AlignBottom": "AlignmentFlag",
    "UserRole": "ItemDataRole", "ForegroundRole": "ItemDataRole",
    "BackgroundRole": "ItemDataRole",
    "NoBrush": "BrushStyle", "SolidPattern": "BrushStyle",
    "CrossPattern": "BrushStyle", "DiagCrossPattern": "BrushStyle",
    "BDiagPattern": "BrushStyle", "FDiagPattern": "BrushStyle",
    "HorPattern": "BrushStyle", "VerPattern": "BrushStyle",
    "Dense1Pattern": "BrushStyle", "Dense3Pattern": "BrushStyle",
    "Dense5Pattern": "BrushStyle", "Dense7Pattern": "BrushStyle",
    "NoPen": "PenStyle", "SolidLine": "PenStyle", "DashLine": "PenStyle",
    "DotLine": "PenStyle", "CustomDashLine": "PenStyle",
    "RoundCap": "PenCapStyle", "FlatCap": "PenCapStyle",
    "MiterJoin": "PenJoinStyle", "RoundJoin": "PenJoinStyle",
    "Checked": "CheckState", "Unchecked": "CheckState",
    "PartiallyChecked": "CheckState",
    "LeftButton": "MouseButton", "RightButton": "MouseButton",
    "MiddleButton": "MouseButton", "MidButton": "MouseButton",
    "NoButton": "MouseButton",
    "ArrowCursor": "CursorShape", "CrossCursor": "CursorShape",
    "PointingHandCursor": "CursorShape", "ClosedHandCursor": "CursorShape",
    "WaitCursor": "CursorShape",
    "transparent": "GlobalColor", "black": "GlobalColor",
    "white": "GlobalColor",
    "Horizontal": "Orientation", "Vertical": "Orientation",
    "ItemIsUserCheckable": "ItemFlag", "ItemIsEditable": "ItemFlag",
    "ItemIsEnabled": "ItemFlag", "ItemIsSelectable": "ItemFlag",
    "NoItemFlags": "ItemFlag",
    "RichText": "TextFormat", "PlainText": "TextFormat",
    "KeepAspectRatio": "AspectRatioMode",
    "IgnoreAspectRatio": "AspectRatioMode",
    "SmoothTransformation": "TransformationMode",
    "FastTransformation": "TransformationMode",
    "TextWordWrap": "TextFlag",
    "TextSelectableByMouse": "TextInteractionFlag",
    "TextBrowserInteraction": "TextInteractionFlag",
    "ScrollBarAlwaysOff": "ScrollBarPolicy",
    "ScrollBarAsNeeded": "ScrollBarPolicy",
    "NoFocus": "FocusPolicy", "StrongFocus": "FocusPolicy",
    "WindowStaysOnTopHint": "WindowType", "FramelessWindowHint": "WindowType",
    "Dialog": "WindowType", "NonModal": "WindowModality",
    "WA_DeleteOnClose": "WidgetAttribute",
    "WA_MacShowFocusRect": "WidgetAttribute",
    "ControlModifier": "KeyboardModifier", "ShiftModifier": "KeyboardModifier",
    "AltModifier": "KeyboardModifier",
    "Key_Escape": "Key", "Key_Z": "Key", "Key_Delete": "Key",
    "RightDockWidgetArea": "DockWidgetArea",
    "LeftDockWidgetArea": "DockWidgetArea",
    "TopDockWidgetArea": "DockWidgetArea",
    "BottomDockWidgetArea": "DockWidgetArea",
    "ToolButtonTextBesideIcon": "ToolButtonStyle",
    "ToolButtonTextOnly": "ToolButtonStyle",
    "OddEvenFill": "FillRule",
    "CustomContextMenu": "ContextMenuPolicy",
    "TopRightCorner": "Corner", "BottomRightCorner": "Corner",
    "DownArrow": "ArrowType", "RightArrow": "ArrowType",
    # classes qui ont gagné une énumération
    "QDialog.Accepted": "QDialog.DialogCode.Accepted",
    "QDialog.Rejected": "QDialog.DialogCode.Rejected",
    "QDialogButtonBox.Ok": "QDialogButtonBox.StandardButton.Ok",
    "QDialogButtonBox.Cancel": "QDialogButtonBox.StandardButton.Cancel",
    "QDialogButtonBox.Close": "QDialogButtonBox.StandardButton.Close",
    "QDialogButtonBox.Apply": "QDialogButtonBox.StandardButton.Apply",
    "QDialogButtonBox.ActionRole": "QDialogButtonBox.ButtonRole.ActionRole",
    "QMessageBox.Ok": "QMessageBox.StandardButton.Ok",
    "QMessageBox.Cancel": "QMessageBox.StandardButton.Cancel",
    "QMessageBox.Yes": "QMessageBox.StandardButton.Yes",
    "QMessageBox.No": "QMessageBox.StandardButton.No",
    "QMessageBox.Save": "QMessageBox.StandardButton.Save",
    "QMessageBox.Discard": "QMessageBox.StandardButton.Discard",
    "QMessageBox.Warning": "QMessageBox.Icon.Warning",
    "QPainter.Antialiasing": "QPainter.RenderHint.Antialiasing",
    "QPainter.TextAntialiasing": "QPainter.RenderHint.TextAntialiasing",
    "QPainter.SmoothPixmapTransform":
        "QPainter.RenderHint.SmoothPixmapTransform",
    "QFont.Bold": "QFont.Weight.Bold",
    "QFont.SmallCaps": "QFont.Capitalization.SmallCaps",
    "QFrame.HLine": "QFrame.Shape.HLine",
    "QFrame.NoFrame": "QFrame.Shape.NoFrame",
    "QFrame.StyledPanel": "QFrame.Shape.StyledPanel",
    "QHeaderView.Stretch": "QHeaderView.ResizeMode.Stretch",
    "QHeaderView.ResizeToContents": "QHeaderView.ResizeMode.ResizeToContents",
    "QHeaderView.Interactive": "QHeaderView.ResizeMode.Interactive",
    "QAbstractItemView.SelectRows": "QAbstractItemView.SelectionBehavior.SelectRows",
    "QAbstractItemView.SelectItems": "QAbstractItemView.SelectionBehavior.SelectItems",
    "QAbstractItemView.SingleSelection":
        "QAbstractItemView.SelectionMode.SingleSelection",
    "QAbstractItemView.ExtendedSelection":
        "QAbstractItemView.SelectionMode.ExtendedSelection",
    "QAbstractItemView.DoubleClicked":
        "QAbstractItemView.EditTrigger.DoubleClicked",
    "QSizePolicy.Expanding": "QSizePolicy.Policy.Expanding",
    "QSizePolicy.Fixed": "QSizePolicy.Policy.Fixed",
    "QSizePolicy.Maximum": "QSizePolicy.Policy.Maximum",
    "QSizePolicy.Preferred": "QSizePolicy.Policy.Preferred",
    "QStyle.State_Selected": "QStyle.StateFlag.State_Selected",
    "QStyle.State_MouseOver": "QStyle.StateFlag.State_MouseOver",
    "QKeySequence.Save": "QKeySequence.StandardKey.Save",
    "QKeySequence.Undo": "QKeySequence.StandardKey.Undo",
    "QKeySequence.Redo": "QKeySequence.StandardKey.Redo",
    "QComboBox.AdjustToMinimumContentsLength":
        "QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLength",
}


# Le type d'un champ de couche a changé deux fois de forme : `QVariant.String`
# (Qt 5) → `QMetaType.Type.QString` (QGIS 3.38+) → `Qgis.FieldType.String`
# (QGIS 4). Le dépôt officiel valide `Qgis.FieldType`, qui n'existe pas avant
# QGIS 4 : le plugin ne peut donc pas promettre les deux à la fois.
FORMES_CHAMP_QT6 = "Qgis.FieldType"

# La quatrième condition ne se mesure pas dans un dépôt : faire tourner le
# plugin dans un QGIS 4 réel. Tant qu'elle n'est pas remplie, la fenêtre
# déclarée reste où elle est — une promesse non éprouvée reste une promesse.
EPREUVE_REELLE_QGIS4 = False


def compatible_qgis4(non_qualifies: int, exec_restants: int = 0,
                     champs: int = 0) -> bool:
    """Peut-on écrire « compatible QGIS 4 » sans mentir ?

    Trois conditions, mesurables : plus aucun membre d'énumération à la
    forme Qt 5, plus aucun `exec_()`, plus aucun type de champ à l'ancienne
    forme. La quatrième — « ça tourne sur un QGIS 4 réel » — ne se mesure
    pas dans un dépôt : elle s'éprouve chez un utilisateur, et se dit comme
    telle.
    """
    return non_qualifies == 0 and exec_restants == 0 and champs == 0


def fenetre(minimum: str, maximum: str, non_qualifies: int,
            exec_restants: int = 0, champs: int = 0) -> dict:
    """La fenêtre déclarée, confrontée à ce que le code tient vraiment."""
    tient = compatible_qgis4(non_qualifies, exec_restants, champs)
    maxi = (maximum or "").strip()
    couvre_qgis4 = maxi.split(".")[0].isdigit() and int(maxi.split(".")[0]) >= 4
    return {
        "minimum": minimum, "maximum": maxi,
        "declare_qgis4": couvre_qgis4,
        "tient_qgis4": tient,
        "mensonge": couvre_qgis4 and not tient,
        "sites_a_migrer": non_qualifies,
        "exec_a_migrer": exec_restants,
        "champs_a_migrer": champs,
        "forme_champ_qt6": FORMES_CHAMP_QT6,
        "epreuve_reelle": EPREUVE_REELLE_QGIS4,
    }


# ── 4 · un paquet ne contient que ce qui sert ──────────────────────
def paquet_propre(noms: list) -> list:
    """Les chemins qui n'ont rien à faire dans le paquet, tels quels.

    On ne renomme rien et on ne décide pas à la place de l'auteur : on
    nomme. Un `.pyc` compilé sur sa machine ne sert à personne ; un banc
    d'essai qui pointe vers `/home/claude/dm` non plus.
    """
    fautifs = []
    for nom in noms:
        chemin = str(nom).replace("\\", "/")
        if chemin.startswith("DrillMaster/"):
            chemin = chemin[len("DrillMaster/"):]
        if any(m in chemin for m in MOTIFS_EXCLUS):
            fautifs.append(nom)
            continue
        if any(chemin.startswith(d) for d in DOSSIERS_DE_DEVELOPPEMENT):
            fautifs.append(nom)
    return fautifs


def poids_lisible(octets: float) -> str:
    """Un poids qu'un humain lit sans calculatrice."""
    if octets >= 1_048_576:
        return f"{octets / 1_048_576:.1f} Mo"
    return f"{octets / 1024:.0f} Ko"


# ── 5 · la licence, cherchée là où le plugin est installé ──────────
def cherche_licence(dossier_plugin: str) -> str:
    """Le `LICENSE` livré avec le plugin, sinon celui du dépôt.

    Avant : le module cherchait **au-dessus** du dossier du plugin. Dans le
    dépôt, cela tombait sur le `LICENSE` de la racine — donc « trouvé » pour
    l'auteur et **introuvable pour tout le monde** : une fois installé,
    `plugins/DrillMaster/` n'a rien au-dessus de lui. La fenêtre « À propos »
    annonçait alors « Fichier LICENSE introuvable » à chaque utilisateur.
    """
    ici = os.path.join(dossier_plugin, "LICENSE")
    if os.path.isfile(ici):
        return ici
    dessus = os.path.join(os.path.dirname(os.path.abspath(dossier_plugin)),
                          "LICENSE")
    return dessus if os.path.isfile(dessus) else ""


def preflight(dossier_plugin: str) -> list:
    """Ce qui manque pour que le plugin démarre, dit en clair.

    Aucune exception : la liste vide veut dire « rien à signaler ».
    """
    manques = []
    for nom in ("__init__.py", "metadata.txt"):
        if not os.path.isfile(os.path.join(dossier_plugin, nom)):
            manques.append(nom)
    if not cherche_licence(dossier_plugin):
        manques.append("LICENSE")
    return manques
