"""Chantier 5 — boutons et gestes.

Le département Boutons avait 4 « bloquants » : 4 suppressions sans filet.
Vérification faite dans le code, **aucune ne détruit de donnée** : elles
retirent des couches régénérables. Le vrai défaut est ailleurs, et il est
plus grave pour un débutant : **on ne sait pas ce qu'une action va changer
avant de la déclencher**.

Ici : un geste annonce sa portée avant, propose une sortie après, et refuse
d'agir sans nom.

    g = Geste("Supprimer le projet", destructive=True)
    g.portee("le dossier du projet, et tout ce qu'il contient")
    g.perd("les fichiers importés", "les coupes enregistrées")
    g.sortie("l'action sera à confirmer par écrit")
    g.exige_motif()
    g.verifie(signe="A. Koné", motif="projet abandonné")
"""
from __future__ import annotations

from dataclasses import dataclass, field

ROLES = ("primaire", "secondaire", "discret")
VERBES = ("Ouvrir", "Importer", "Calculer", "Exporter", "Appliquer", "Fermer")
MOTS_INTERDITS_GESTE = ("ok", "valider", "exécuter", "lancer", "go", "submit",
                        "confirmer")


class GesteRefuse(Exception):
    """Un geste refusé, avec la raison en mots simples."""


@dataclass
class Geste:
    libelle: str
    role: str = "secondaire"
    destructive: bool = False
    ce_qui_change: str = ""
    pertes: tuple = ()
    sorties: tuple = ()
    motif_obligatoire: bool = False

    def __post_init__(self):
        if self.role not in ROLES:
            raise GesteRefuse(
                f"rôle « {self.role} » inconnu ; les rôles sont : "
                + ", ".join(ROLES))
        if self.libelle.strip().lower() in MOTS_INTERDITS_GESTE:
            raise GesteRefuse(
                f"« {self.libelle} » est un mot creux : un bouton dit ce qu'il "
                f"fait (« Importer les 64 forages », pas « OK »)")
        if self.destructive and self.role == "primaire":
            raise GesteRefuse(
                "une action qui peut détruire n'est jamais le bouton "
                "principal : le geste attendu n'est pas la suppression")

    # ── ce que le geste annonce ────────────────────────────────────
    def portee(self, texte):
        self.ce_qui_change = texte
        return self

    def perd(self, *elements):
        self.pertes += tuple(elements)
        return self

    def sortie(self, *issues):
        self.sorties += tuple(issues)
        return self

    def exige_motif(self):
        self.motif_obligatoire = True
        return self

    # ── avant : peut-il seulement s'afficher ? ─────────────────────
    def complet(self):
        if self.destructive and not self.pertes:
            raise GesteRefuse(
                f"« {self.libelle} » peut détruire mais ne dit pas ce qui sera "
                f"perdu : l'utilisateur doit lire la conséquence avant de "
                f"cliquer")
        if self.destructive and not self.sorties:
            raise GesteRefuse(
                f"« {self.libelle} » ne propose aucune sortie : une action "
                f"irréversible sans issue est un piège")
        return True

    def annonce(self):
        """La phrase affichée avant le clic."""
        self.complet()
        if not self.destructive:
            return self.libelle
        pertes = " et ".join(self.pertes)
        return (f"{self.libelle} — sera perdu : {pertes}. "
                f"Sortie possible : {' ; '.join(self.sorties)}.")

    # ── pendant : l'accord de l'utilisateur ────────────────────────
    def verifie(self, signe="", motif="", ecrit=False):
        """Rien ne s'exécute sans signature, et sans motif si exigé."""
        self.complet()
        if not str(signe).strip():
            raise GesteRefuse(
                f"« {self.libelle} » demande qui agit : sans nom, personne ne "
                f"peut expliquer ce qui s'est passé")
        if not str(motif).strip() and self.motif_obligatoire:
            raise GesteRefuse(
                f"« {self.libelle} » demande un motif : dans six mois, "
                f"quelqu'un se demandera pourquoi")
        if self.destructive and not ecrit:
            raise GesteRefuse(
                f"« {self.libelle} » demande une confirmation écrite : c'est "
                f"le seul moyen de distinguer un clic d'une décision")
        return True


# ── les 3 rôles, et la règle du primaire unique ────────────────────
def un_seul_primaire(gestes):
    """Une barre d'actions ne montre qu'un bouton principal."""
    primaires = [g for g in gestes if g.role == "primaire"]
    if len(primaires) > 1:
        raise GesteRefuse(
            "plusieurs boutons principaux ("
            + ", ".join(f"« {g.libelle} »" for g in primaires)
            + ") : l'utilisateur ne sait plus quelle est l'action attendue")
    return primaires[0] if primaires else None


def barre(libelle, gestes):
    """Ce qu'une barre d'actions affiche : un titre, trois poids."""
    from ..theme import theme
    principal = un_seul_primaire(gestes)
    return {
        "titre": libelle,
        "primaire": principal.libelle if principal else None,
        "secondaires": [g.libelle for g in gestes if g.role == "secondaire"],
        "discrets": [g.libelle for g in gestes if g.role == "discret"],
        "couleur_primaire": theme.accent,
        "destructifs": [g.libelle for g in gestes if g.destructive],
    }
