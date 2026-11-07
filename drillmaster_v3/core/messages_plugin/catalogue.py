"""Les 30 fenêtres d'alerte du plugin, converties en messages à 5 champs.

Chaque entrée est identifiée par `fichier:ligne` de l'appel d'origine — c'est
la preuve qu'aucune n'a été oubliée, et le lien avec le code à modifier.

Règles tenues :
  · **information()** ne s'emploie pas pour dire qu'une action a réussi :
    on ne dérange pas l'utilisateur pour lui annoncer que tout va bien.
  · un **blocage** propose au moins deux sorties (R-22).
  · toute phrase est vérifiée par le lexique : aucun mot interdit.
"""
from __future__ import annotations

from ..messages import (Message, Niveau, avertissement, blocage, information,
                        question)

# (identifiant, fabrique) — l'identifiant est `fichier:ligne` d'origine
_ENTREES = [
    # ── éditeur de table : la perte de travail ───────────────────────
    ("csv_editor.py:559", lambda: question(
        "Enregistrer avant de fermer ?",
        "des modifications ne sont pas enregistrées dans la copie du projet",
        "la table ouverte",
        ("enregistrer la copie du projet", "fermer sans enregistrer",
         "revenir à la table"),
        "la copie du projet")),
    ("csv_editor.py:521", lambda: avertissement(
        "La copie du projet n'a pas pu être enregistrée",
        "le dossier du projet n'est plus accessible en écriture",
        ("le dossier du projet",),
        ("vérifier le dossier du projet", "exporter la table en fichier"),
        "la copie du projet")),
    ("csv_editor.py:497", lambda: blocage(
        "Impossible d'enregistrer",
        "la table n'a pas pu être écrite : aucune modification n'a été perdue",
        ("la table ouverte",),
        ("enregistrer sous un autre fichier", "copier le détail pour le support"),
        "la table ouverte")),

    # ── organisation des lithologies ─────────────────────────────────
    ("lithology_structure_dialog.py:221", lambda: information(
        "Organisation des lithologies",
        "chaque colonne de code doit représenter un seul composant",
        "le Référentiel du projet")),
    ("lithology_structure_dialog.py:332", lambda: avertissement(
        "Organisation incomplète",
        "un des composants n'a pas de colonne de code, donc il ne serait "
        "jamais rattaché à la bonne ligne",
        ("les composants de la lithologie",),
        ("choisir une colonne de code pour chaque composant",
         "retirer le composant inutile"),
        "l'organisation des lithologies")),
    ("lithology_structure_dialog.py:337", lambda: avertissement(
        "Deux composants pointent la même colonne",
        "une même colonne ne peut pas représenter deux composants : la "
        "couleur affichée serait fausse pour l'un des deux",
        ("les composants de la lithologie",),
        ("donner une colonne différente à chaque composant",
         "retirer le composant en double"),
        "l'organisation des lithologies")),
    ("lithology_structure_dialog.py:342", lambda: avertissement(
        "Aucune colonne de lithologie choisie",
        "sans colonne de code, aucune lithologie ne peut être affichée dans "
        "les coupes",
        ("la lithologie",),
        ("choisir la colonne qui contient la lithologie",
         "importer les lithologies plus tard"),
        "la lithologie")),
    ("lithology_structure_dialog.py:352", lambda: avertissement(
        "Colonne incompatible",
        "la colonne choisie ne contient pas les codes attendus",
        ("la colonne sélectionnée",),
        ("choisir une autre colonne", "vérifier les codes du fichier"),
        "la lithologie")),
    ("lithology_structure_dialog.py:360", lambda: avertissement(
        "Séparateur invalide",
        "un code composé doit être séparé par un signe unique : avec "
        "plusieurs signes, le découpage devient imprévisible",
        ("les codes composés",),
        ("choisir un seul séparateur", "utiliser des codes simples"),
        "les codes de lithologie")),

    # ── projet : création, ouverture, suppression ────────────────────
    ("main_dock.py:475", lambda: question(
        "Un projet de ce nom existe déjà",
        "créer un second projet au même nom écraserait le premier",
        "le projet à créer",
        ("ouvrir le projet existant", "choisir un autre nom"),
        "la création du projet")),
    ("main_dock.py:491", lambda: blocage(
        "Le dossier du projet n'a pas pu être créé",
        "le dossier choisi interdit l'écriture : rien n'a été créé",
        ("le dossier choisi",),
        ("choisir un autre dossier", "vérifier les droits d'écriture"),
        "la création du projet")),
    ("main_dock.py:730", lambda: avertissement(
        "Le dossier du projet n'a pas été supprimé",
        "un fichier du dossier est ouvert ailleurs : la suppression a été "
        "interrompue, rien n'est perdu",
        ("le dossier du projet",),
        ("fermer les fichiers ouverts", "supprimer le dossier à la main"),
        "le projet")),
    ("step1_config.py:311", lambda: blocage(
        "Ce dossier n'est pas un projet DrillMaster",
        "il ne contient pas la fiche du projet : l'ouvrir donnerait des "
        "coupes vides",
        ("le dossier choisi",),
        ("choisir le bon dossier", "créer un nouveau projet ici"),
        "l'ouverture du projet")),

    # ── Référentiel : retirer, compléter, enregistrer, fermer ───────
    ("reference_dialog.py:892", lambda: information(
        "Aucune entrée non utilisée dans ce domaine",
        "tous les codes de ce domaine servent déjà dans les données : il n'y "
        "avait rien à retirer, rien n'a été modifié",
        "le Référentiel")),
    ("reference_dialog.py:899", lambda: question(
        "Retirer les entrées non utilisées ?",
        "ces codes n'apparaissent dans aucune donnée ; ils reviendront tout "
        "seuls s'ils réapparaissent dans un fichier",
        "les codes non utilisés du domaine",
        ("retirer ces codes", "les garder"),
        "le Référentiel")),
    ("reference_dialog.py:954", lambda: question(
        "Donner un motif automatique aux codes qui n'en ont pas ?",
        "chaque code recevra un motif distinct ; ceux que vous avez déjà "
        "choisis ne changent pas",
        "les codes sans motif",
        ("donner les motifs", "les laisser sans motif"),
        "les motifs du Référentiel")),
    ("reference_dialog.py:1018", lambda: question(
        "Donner une couleur distincte aux styles qui n'en ont pas ?",
        "chaque style recevra une couleur différente ; celles que vous avez "
        "choisies à la main ne changent pas",
        "les styles sans couleur choisie",
        ("donner les couleurs", "les laisser sans couleur choisie"),
        "les couleurs du Référentiel")),
    ("reference_dialog.py:1096", lambda: blocage(
        "Le Référentiel n'a pas pu être enregistré",
        "le fichier du Référentiel n'est plus accessible en écriture : aucune "
        "de vos modifications n'a été perdue",
        ("le fichier du Référentiel",),
        ("enregistrer sous un autre emplacement",
         "vérifier les droits du dossier du projet"),
        "le Référentiel")),
    ("reference_dialog.py:1125", lambda: question(
        "Fermer sans enregistrer les modifications ?",
        "vos changements de couleurs, motifs et libellés seront perdus",
        "le Référentiel",
        ("fermer sans enregistrer", "revenir et enregistrer"),
        "le Référentiel")),

    # ── Référentiel : ce qui est déjà fait ──────────────────────────
    ("reference_dialog.py:926", lambda: information(
        "Les motifs s'appliquent aux lithologies et aux altérations",
        "les autres domaines n'ont pas de motif : ils gardent leur couleur",
        "le Référentiel")),
    ("reference_dialog.py:937", lambda: information(
        "Tous les codes de ce domaine ont déjà un motif",
        "il n'y avait rien à compléter : rien n'a été modifié",
        "le Référentiel")),
    ("reference_dialog.py:978", lambda: information(
        "Les couleurs distinctes concernent les styles de minéralisation",
        "les autres domaines gardent les couleurs du Référentiel",
        "le Référentiel")),
    ("reference_dialog.py:998", lambda: information(
        "Tous les styles ont déjà une couleur choisie",
        "il n'y avait rien à compléter : rien n'a été modifié",
        "le Référentiel")),

    # ── export ───────────────────────────────────────────────────────
    ("section_export.py:55", lambda: avertissement(
        "Rien à exporter",
        "la coupe n'est pas encore calculée : le fichier serait vide",
        ("la coupe",),
        ("calculer la coupe avant d'exporter", "choisir une autre coupe"),
        "l'export de la coupe")),
    ("section_export.py:59", lambda: information(
        "Rien à exporter sur cette coupe",
        "aucune piste n'est visible : le fichier ne contiendrait que le cadre",
        "la coupe")),
    ("section_export.py:154", lambda: avertissement(
        "Le dossier d'export n'existe pas",
        "le fichier ne peut pas être écrit à cet emplacement",
        ("le dossier choisi",),
        ("créer le dossier", "choisir un autre emplacement"),
        "l'export de la coupe")),
    ("section_export.py:158", lambda: avertissement(
        "L'export de la coupe a échoué",
        "le fichier n'a pas pu être écrit : rien n'a été produit",
        ("le fichier d'export",),
        ("choisir un autre emplacement", "fermer le fichier s'il est ouvert"),
        "l'export de la coupe")),
    ("section_export_scaled.py:485", lambda: information(
        "Export en page : dossier manquant",
        "le dossier où écrire la page n'existe pas encore",
        "l'export de la coupe en page")),
    ("section_export_scaled.py:620", lambda: avertissement(
        "L'export en page a échoué",
        "le fichier n'a pas pu être écrit à l'emplacement choisi",
        ("le fichier d'export",),
        ("choisir un autre emplacement", "fermer le fichier s'il est ouvert"),
        "l'export de la coupe")),

    # ── vue 3D ───────────────────────────────────────────────────────
    ("view_3d_canvas.py:344", lambda: information(
        "Aide de la vue 3D",
        "les gestes disponibles sont : tourner, rapprocher, revenir à la vue "
        "de dessus",
        "la vue 3D")),
]

CATALOGUE = {ident: fabrique for ident, fabrique in _ENTREES}
MESSAGES: dict[str, Message] = {}


def _construit():
    for ident, fabrique in CATALOGUE.items():
        try:
            MESSAGES[ident] = fabrique()
        except Exception as e:                      # noqa: BLE001
            raise RuntimeError(f"{ident} : message impossible à construire "
                               f"({e})") from e
    return MESSAGES


_construit()


def par_id(ident):
    if ident not in MESSAGES:
        raise KeyError(f"{ident} n'est pas un message du plugin converti "
                       f"({len(MESSAGES)} convertis)")
    return MESSAGES[ident]
