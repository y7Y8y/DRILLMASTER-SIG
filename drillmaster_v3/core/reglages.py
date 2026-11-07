"""Chantier 2 — un réglage, un propriétaire.

Le défaut mesuré (agent F-01) : la largeur d'une piste est réglable dans
12 endroits de 5 fichiers. Ici, un seul propriétaire, et les cinq lecteurs
lisent le même objet — ils ne peuvent pas diverger (R-09).

    reglages = Reglages()
    reglages.modifie("assays", "width", 24, par="A. Koné")
    reglages.lecture("assays", "width")        # 24, pour les 5 vues
    reglages.journal()                          # qui, quand, quoi, pourquoi
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .tracks import CHAMPS, TrackCatalog

LECTEURS = ("2d", "3d", "legende", "export", "carte")

# champs qu'une vue n'utilise pas, avec la raison (R-08 : jamais silencieux)
SANS_OBJET = {
    ("3d", "side"): "la scène tourne : il n'y a pas de côté",
    ("carte", "side"): "vue de dessus : il n'y a pas de côté",
    ("carte", "opacity"): "la carte affiche un aplat, sans transparence",
}


@dataclass(frozen=True)
class Changement:
    piste: str
    champ: str
    avant: object
    apres: object
    par: str
    quand: str
    motif: str = ""

    def phrase(self):
        return (f"{self.piste}.{self.champ} : {self.avant} → {self.apres} "
                f"par {self.par}")


class RefusReglage(Exception):
    """Un réglage refusé, avec la raison en mots simples."""


class Reglages:
    """L'objet unique. Aucune vue n'en garde une copie."""

    def __init__(self, catalogue=None, horloge=None):
        self.catalogue = catalogue or TrackCatalog()
        self._surcharges = {}          # (piste, champ) -> valeur décidée
        self._journal = []
        self._abonnes = []             # les vues s'inscrivent ici
        self._horloge = horloge or self._maintenant

    @staticmethod
    def _maintenant():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    # ── sur qui j'écris ────────────────────────────────────────────
    def abonne(self, nom):
        """Une vue s'abonne pour être prévenue. Une seule source de vérité."""
        if nom not in LECTEURS:
            raise RefusReglage(
                f"« {nom} » n'est pas une vue connue ; les vues sont : "
                + ", ".join(LECTEURS))
        if nom not in self._abonnes:
            self._abonnes.append(nom)
        return nom

    # ── lecture ────────────────────────────────────────────────────
    def valeur(self, piste, champ):
        """La valeur effective : surcharge si décidée, sinon le contrat."""
        if champ not in CHAMPS:
            raise RefusReglage(f"« {champ} » n'est pas un champ de piste "
                               f"(15 champs : {', '.join(CHAMPS)})")
        if (piste, champ) in self._surcharges:
            return self._surcharges[(piste, champ)]
        return getattr(self.catalogue.resout(piste), champ)

    def lecture(self, piste, champ):
        """Ce que chaque vue obtient — la même valeur, sauf si sans objet."""
        base = self.valeur(piste, champ)
        detail = {}
        for vue in LECTEURS:
            raison = SANS_OBJET.get((vue, champ))
            detail[vue] = {"valeur": None, "raison": raison} if raison else {
                "valeur": base, "raison": None}
        return {"valeur": base, "vues": detail}

    def herite(self, piste, champ):
        """Vrai si la valeur vient de la famille, pas d'une décision."""
        return (piste, champ) not in self._surcharges

    # ── écriture : un seul chemin, jamais direct ───────────────────
    def _existe(self, piste):
        if piste not in self.catalogue.ids():
            raise RefusReglage(
                f"« {piste} » n'est pas une piste du contrat ; les 12 pistes "
                f"sont : " + ", ".join(self.catalogue.ids()))

    def modifie(self, piste, champ, valeur, par, motif=""):
        if not par or not str(par).strip():
            raise RefusReglage(
                "un réglage modifié doit dire qui l'a modifié : sans nom, "
                "personne ne peut expliquer la configuration dans six mois")
        if champ not in CHAMPS:
            raise RefusReglage(f"« {champ} » n'est pas un champ de piste")
        self._existe(piste)
        avant = self.valeur(piste, champ)
        self._verifie(piste, champ, valeur)
        if avant == valeur:
            return None                          # rien à faire, rien à écrire
        self._surcharges[(piste, champ)] = valeur
        c = Changement(piste, champ, avant, valeur, str(par),
                       self._horloge(), motif)
        self._journal.append(c)
        return c

    def _verifie(self, piste, champ, valeur):
        """Les bornes et les valeurs permises viennent du contrat (tracks.json).

        Aucune borne n'est écrite ici : une valeur par défaut inventée est un
        défaut de livraison (R-27).
        """
        regle = self.catalogue.contrat.get(champ)
        if regle is None:
            raise RefusReglage(f"« {champ} » n'est pas déclaré au contrat")
        genre = regle.get("type")
        if genre == "int":
            if not isinstance(valeur, int) or isinstance(valeur, bool):
                raise RefusReglage(f"{champ} attend un entier (reçu : "
                                   f"{valeur!r})")
            mini, maxi = regle.get("min"), regle.get("max")
            if mini is not None and valeur < mini or maxi is not None and valeur > maxi:
                raise RefusReglage(
                    f"{champ} accepte un entier de {mini} à {maxi} "
                    f"(reçu : {valeur!r})")
        elif genre == "bool":
            if not isinstance(valeur, bool):
                raise RefusReglage(f"{champ} attend vrai ou faux "
                                   f"(reçu : {valeur!r})")
        elif genre == "enum":
            permis = regle.get("valeurs", [])
            if valeur not in permis:
                raise RefusReglage(
                    f"{champ} accepte : " + ", ".join(f"« {v} »" for v in permis)
                    + f" (reçu : {valeur!r})")
        elif genre == "string" and not isinstance(valeur, str):
            raise RefusReglage(f"{champ} attend du texte (reçu : {valeur!r})")

    def retablit(self, piste, champ):
        """Revenir à la valeur héritée de la famille."""
        cle = (piste, champ)
        if cle not in self._surcharges:
            return None
        avant = self._surcharges.pop(cle)
        heritage = getattr(self.catalogue.resout(piste), champ)
        c = Changement(piste, champ, avant, heritage, "(rétablissement)",
                       self._horloge(), "retour à la valeur de la famille")
        self._journal.append(c)
        return c

    # ── preuve de partage ─────────────────────────────────────────
    def coherent(self, piste, champ):
        """Vrai si les vues qui appliquent le champ voient la même valeur."""
        lu = self.lecture(piste, champ)
        vues = [v["valeur"] for v in lu["vues"].values() if v["raison"] is None]
        return len(set(map(repr, vues))) <= 1

    def journal(self, piste=None):
        return [c for c in self._journal if piste in (None, c.piste)]

    def surcharges(self):
        return dict(self._surcharges)

    def resume(self):
        postes = {c.piste for c in self._journal}
        vues = ", ".join(self._abonnes) or "aucune vue abonnée"
        return (f"{len(self._surcharges)} réglage(s) décidé(s) sur "
                f"{len(postes)} piste(s) · {len(self._journal)} changement(s) "
                f"au journal · vues : {vues}")
