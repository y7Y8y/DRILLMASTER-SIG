"""Les gestes du plugin, réécrits avec les règles du chantier 5.

Chaque geste est celui d'un bouton réel. Ce qui change par rapport au plugin :
il annonce sa portée, ce qu'il fait perdre, et la sortie possible.
"""
from __future__ import annotations

from .gestes import Geste, barre


def gestes_projet():
    return [
        Geste("Ouvrir un projet existant", role="primaire")
        .portee("le projet choisi remplace celui qui est ouvert"),
        Geste("Réinitialiser le projet", role="secondaire", destructive=True)
        .portee("l'état de travail, pas les fichiers")
        .perd("les coupes non enregistrées", "la sélection en cours")
        .sortie("les fichiers du projet sont conservés")
        .exige_motif(),
        Geste("Fermer le projet", role="discret")
        .portee("les fichiers restent sur le disque"),
        Geste("Supprimer définitivement le projet", role="discret",
              destructive=True)
        .portee("le dossier du projet et tout ce qu'il contient")
        .perd("les fichiers importés", "les coupes enregistrées",
              "l'historique du projet")
        .sortie("confirmer par écrit", "choisir « fermer » pour conserver")
        .exige_motif(),
    ]


def gestes_donnees():
    return [
        Geste("Importer un fichier", role="primaire")
        .portee("une source de plus ; rien n'est remplacé"),
        Geste("Recalculer les trajectoires", role="secondaire")
        .portee("les forages dont la trajectoire est incomplète"),
        Geste("Voir la fiche d'un problème", role="discret"),
        Geste("Écarter un forage", role="discret", destructive=True)
        .portee("ce forage, partout : coupe, 3D, export, carte")
        .perd("sa place dans les coupes et les calculs (réversible)")
        .sortie("le réintégrer à tout moment")
        .exige_motif(),
    ]


def gestes_coupe():
    return [
        Geste("Calculer la coupe", role="primaire")
        .portee("la coupe affichée ; les réglages ne changent pas"),
        Geste("Exporter la coupe", role="secondaire")
        .portee("un fichier image ou PDF à l'emplacement choisi"),
        Geste("Changer de coupe", role="discret")
        .portee("l'affichage seulement ; aucune donnée n'est modifiée"),
    ]


BARRES = {
    "projet": lambda: barre("Actions du projet", gestes_projet()),
    "donnees": lambda: barre("Actions sur les données", gestes_donnees()),
    "coupe": lambda: barre("Actions de la coupe", gestes_coupe()),
}
