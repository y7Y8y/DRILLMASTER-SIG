"""DrillMaster — Journal de diagnostic (audit C, v2.9.161).

**Règle** (SPEC de restructuration, audit C) : une exception avalée doit
laisser une TRACE.  Avant, ~250 ``except Exception:`` silencieux
cachaient les échecs — impossible de diagnostiquer un bug qui ne laisse
aucune preuve qu'il a eu lieu (retour écran : « bugs incessants »).

Trois destins possibles pour chaque handler, tranchés explicitement :
1. **journaliser** via :func:`log_swallowed` (échec inattendu → trace) ;
2. **restreindre** à un type précis (seule une erreur *prévue et nommée*
   peut être ignorée — ex. ``ImportError`` pour un module optionnel) ;
3. **commenter** pourquoi le silence est acceptable à CET endroit précis.

Pur Python (``logging`` stdlib) : utilisable dans ``core/`` comme dans
``ui/``.  Sous QGIS, un handler pousse aussi dans le journal QGIS
(``QgsMessageLog``, onglet « Messages ») — l'utilisateur voit l'erreur
SANS popup bloquante.
"""

from __future__ import annotations

import logging

_LOGGER_NAME = "DrillMaster"

# Niveau de la trace des exceptions avalées : DEBUG = discret (visible
# dans le journal QGIS et le log Python, jamais à l'écran).
_SWALLOWED_LEVEL = logging.DEBUG


def _logger() -> logging.Logger:
    """Logger « DrillMaster » (créé paresseusement, handler QGIS inclus)."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers and not getattr(logger, "_dm_configured", False):
        logger._dm_configured = True  # type: ignore[attr-defined]
        try:
            handler = _QgisLogHandler()
            logger.addHandler(handler)
        except Exception:
            pass  # hors QGIS (tests) : logging stdlib suffit
        logger.setLevel(logging.DEBUG)
    return logger


class _QgisLogHandler(logging.Handler):
    """Handler qui pousse les enregistrements dans QgsMessageLog."""

    def __init__(self):
        super().__init__()
        self.setLevel(_SWALLOWED_LEVEL)
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record):
        try:
            from qgis.core import QgsMessageLog, Qgis
            level = (Qgis.MessageLevel.Warning
                     if record.levelno >= logging.WARNING
                     else Qgis.MessageLevel.Info)
            QgsMessageLog.logMessage(
                self.format(record), _LOGGER_NAME, level)
        except Exception:
            # QGIS indisponible (tests hors QGIS) — logging stdlib seul.
            # SILENCE JUSTIFIÉ : le handler de QGIS est un BONUS, jamais
            # une dépendance ; hors QGIS, le log stdlib suffit.
            pass


def log_swallowed(context: str, exc: BaseException):
    """Journalise une exception avalée, avec son contexte.

    ``context`` décrit CE QUI échouait (ex. « MNT raster : échantillonnage
    de la couche X ») — c'est lui qui fait gagner une heure de diagnostic.
    Niveau DEBUG (discret) : jamais de popup, juste une trace consultable.
    """
    try:
        _logger().log(
            _SWALLOWED_LEVEL, "%s — %s: %s",
            context, type(exc).__name__, exc)
    except Exception:
        # le journal ne doit JAMAIS faire planter l'appelant
        pass


def log_warning(context: str, exc: BaseException):
    """Journalise en AVERTISSEMENT (visible dans l'onglet Messages QGIS)."""
    try:
        _logger().warning("%s — %s: %s",
                          context, type(exc).__name__, exc)
    except Exception:
        # SILENCE JUSTIFIÉ : le journal ne doit JAMAIS faire planter
        # l'appelant — c'est sa raison d'être (garde-fou absolu).
        pass


# ── v2.9.334 — MÉTROLOGIE (audit architecte) ─────────────────────────
# « très lent / bloque QGIS » : sans mesure on corrige à l'aveugle.
# Chaque point chaud enregistre sa durée ; au-delà de 250 ms le journal
# QGIS prévient (Warning) — l'utilisateur SAIT où ça fige.
_TIMINGS: list = []
_TIMINGS_MAX = 50
_SLOW_MS = 250.0


def record_timing(label: str, seconds: float) -> None:
    """Enregistre une durée (s) ; WARNING journalisé si >= 250 ms."""
    try:
        ms = float(seconds) * 1000.0
    except Exception:
        return
    if ms < 0.0:
        return
    _TIMINGS.append((str(label), ms))
    if len(_TIMINGS) > _TIMINGS_MAX:
        del _TIMINGS[: len(_TIMINGS) - _TIMINGS_MAX]
    if ms >= _SLOW_MS:
        _logger().warning(
            "DrillMaster lent : %.0f ms — %s", ms, label)
    else:
        _logger().debug("DrillMaster timing : %.0f ms — %s", ms, label)


def timing_summary() -> list:
    """Copie du tampon [(étiquette, ms)] — 50 dernières mesures."""
    return list(_TIMINGS)
