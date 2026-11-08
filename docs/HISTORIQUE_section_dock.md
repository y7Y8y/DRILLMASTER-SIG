# Journal de versions de `ui/section_dock.py`

Ce journal vivait en tête du fichier de code, en docstring : 800 lignes
lues à chaque ouverture du monolithe pour comprendre un bug déjà corrigé.
Il est conservé ici, intégralement et sans réécriture — c'est un document,
pas du code. Le fichier source renvoie à cette page.

## Le journal, tel qu'il était

```

v2.9.135 (perf : gros projets / plusieurs coupes / clics) :
  - debounce style / exag / persist JSON ; cache projection par coupe ;
  - corridor : skip trajectoire si le collet ne peut pas atteindre ;
  - 1 légende par rendu (plus 3×) ; viewport BoundingRect.
v2.9.134 (Propriétés : chaque bloc à son niveau) :
  - légende Intercepts = frère de Teneurs (plus un 8 pt collé dessous) ;
  - « Épaisseur carte QGIS » hors « Piste sur la coupe » ;
  - page Intercepts = même cadre que Litho / Teneurs.
v2.9.132 (Intercepts cochable comme les autres pistes) :
  - case « Afficher les intercepts » ; décocher masque la piste
    (les règles restent) ; comme Teneurs / Litho.
v2.9.131 (Teneurs à plat ; intercepts indépendants) :
  - plus d'accordéon « Affichage » vide de sens sous Teneurs ;
  - Intercepts visibles dès qu'une règle est ON (Teneurs décochée OK).
v2.9.130 (Seuils = page de la piste Intercepts) :
  - clic Intercepts dans Pistes → règles (teneurs ET + litho OU) ;
  - plus un sous-groupe de Teneurs ; piste auto si une règle est ON.
v2.9.129 (légende Seuils = sous-groupe Teneurs, pastilles pleines) :
  - plus de titre sœur « Règle de seuil » ni de cadre pointillé ;
  - pastille = bloc intercept (plein) ; texte « cyan · Fe > 15 % ».
v2.9.128 (ouverture projet : plus de crash légende) :
  - _show_alterations rétabli dans SectionCanvas.__init__ ;
  - _update_legends / set_drillholes défensifs (getattr + try).
v2.9.125 (panneau Teneurs plat + aides partout) :
  - plus de cadre/halo autour d'Affichage Teneurs (comme Altérations) ;
v2.9.124 (teneurs propres + intercepts liés + aides repliées) :
  - plus de gutter gris Intercepts (halo le long des teneurs) ;
  - Teneurs décochée → intercepts masqués (règles conservées) ;
  - aides longues repliées « ⓘ Aide » (même pattern que Seuils).
v2.9.123 (formulaire Seuils compact + labels pistes teneurs) :
  - aide Seuils repliée par défaut (lien « ⓘ Aide ») ;
  - chaque règle repliée par défaut (en-tête + Activer + pastille) ;
  - Litho (OU) = cases à cocher (plus de multi-sélection Ctrl) ;
  - « Clause » → « Critère » dans le formulaire (vocabulaire JORC) ;
  - label « Fe % » / « Cu ppm » au-dessus de chaque piste teneur
    (dock = export, même fonction).
v2.9.122 (piste Intercepts dédiée + clic-légende anthracite) :
  - matches de seuil = blocs pleins sur une piste dédiée (même côté
    que les teneurs, à l'extérieur) — plus de contour sur Fe/Cu ;
  - piste visible dès qu'une règle est ON (même 0 match) ; disparaît
    si 0 règle ON (auto-collapse dock = export) ;
  - 2 règles / même From–To = 2 colonnes côte à côte (jamais fusion) ;
  - clic-légende = LEGEND_CLICK_COLOR anthracite (plus le cyan des règles).
v2.9.121 (seuils : valeurs réelles + traits magenta/ambre = cyan) :
  - spin valeur borné au min/max RÉEL de l'élément choisi
    (plus de 700 sur un Fe à 1–20) ;
  - magenta / ambre : même trait que cyan (dock + export) + halo
    sombre partagé (lisible sur toute rampe) ;
  - règle Fe+Cu avec seule Fe affichée → contour sur la piste Fe.
v2.9.120 (pistes chargées cochées + texte blanc bandeau) :
  - fichier importé = piste disponible et COCHÉE par défaut
    (plus de décochage fantôme des domaines déjà chargés) ;
  - bandeau nodata : texte blanc sur fond ardoise (lisible).
v2.9.118 (pages pistes verrouillées sans fichier) :
  - sans import Miné/Alt/Teneurs/Litho : page props non éditable ;
  - bandeau « Importez le fichier… » à la place des réglages.
v2.9.117 (architecture pistes + Seuils sous Teneurs) :
  - Seuils n'est PAS une piste : sous-onglet de Teneurs ;
  - pistes sans fichier importé : décochées / grisées ;
  - légende : masquée si pas de données (plus de « Aucune… » fantôme).
v2.9.116 (multi-règles seuil + couleurs) :
  - max 3 règles indépendantes (Fe cyan / Cu magenta / 3e ambre) ;
  - même _draw_selection_outline, couleur par règle.
v2.9.115 (export PNG exag. V forcée à 1.0) :
  - pendant l'export : _v_exag = 1.0 + re-render ; dock inchangé.
v2.9.114 (dock 1.85 / export 0.9 même fn) :
  - _outline_export_mode bascule pen avant scene.render.
v2.9.113 (contour seuil moins gras export) :
  - pen_w scène 0.9 (non-cosmetic) ; grades restent lisibles.
v2.9.112 (contour seuil visible export PNG) :
  - _selection_highlight_pen non-cosmetic (scale avec scene.render).
v2.9.111 (unités par clause dans légende seuil) :
  - Fe % et Cu ppm séparés ; plus de % collé sur toutes les clauses.
v2.9.110 (contour multi-pistes si ET multi-teneurs) :
  - chaque élément de la règle affiché est surligné (pas ancre seule).
v2.9.109 (multi-clauses ET teneurs) :
  - clauses 1..3 ET ; manquant=faux ; ancre=1ère clause ;
  - rétrocompat element/op/value.
v2.9.108 (multi-litho OU + trait ~1.85) :
  - litho_filter = liste (OU) ; pen_w=1.85 lisible.
v2.9.107 (anti-débord contour voisins) :
  - inset From/To + gap 0.35 + pen 1.5 ; poly only.
v2.9.106 (contour ~2 px, dock=export) :
  - pen_w=2.0 unique dans _draw_selection_outline.
v2.9.105 (HL path ligne de sol) :
  - kind path = trait cyan sur le path (pas offset tube).

v2.9.87 (motifs Qt hérités de 2.9.33 — CHEMIN ACTIF) :
  - coupe : _LITHO_BRUSH_PATTERNS + QBrush Dense* + lignes custom // axe
    (_draw_axis_aligned_pattern_lines) — PAS de paint_style partagé ;
  - légende : _lithology_symbol_pixmap_impl (traits écran / Dense brush) ;
  - référentiel : _pattern_icon (QBrush Qt) ;
  - carte QGIS : tiretés 1D (styles._LINE_DASH_PATTERNS), pas hachures bande ;
  - geo_style / pattern_paint / pattern_engine / _StyledFillItem = NON branchés
    sur ce chemin (marqueurs DEPRECATED + audit 2.9.87).

v2.9.83–86 (expériences paint_style / StyleDefinition) :
  - code encore présent mais HORS chemin actif en 2.9.87.

v2.9.82 (motifs unifiés + codes miné EN BANDE + P1–P3) :
  - codes miné : fit sur le VRAI code ; rappel si vraiment trop petit ;
  - P1–P3 référentiel/carte/stub.

v2.9.81 (fix crash légende UnboundLocal + résilience étape 3) :
  - _lithology_symbol_pixmap : plus d'import local normalise_pattern ;
  - _update_legends : pastille en try → ne bloque plus set_drillholes.

v2.9.80 (moteur motifs partagé core/pattern_engine) :
  - un seul layout paramétrique coupe + légende + futurs modules ;
  - s'adapte largeur/hauteur ; points = grille (plus Dense* Qt coupe) ;
  - encre + spacing + seuil aplat centralisés.

v2.9.79 (plus de table DEFAULT litho — flux universel) :
  - couleurs litho = biblio famille OU hash (comme altéro) ;
  - aucun code site-spécifique dans le moteur ;
  - référentiel user toujours roi.

v2.9.78 (motifs altéro lisibles + légende = coupe + codes miné égaux) :
  - encre foncée aussi sur motifs POINTS/denses (pastel) ;
  - pastille légende densifiée = même langage que la coupe ;
  - codes courts : taille uniforme par trou.

v2.9.77 (biblio sans conflit litho ≠ altéro) :
  - litho = aplats VIFS ; altération = pastels CLAIRS ;
  - 0 hex partagé ; géologue reconnaît domaine d'un coup d'œil ;
  - toujours suggestions (user décide).

v2.9.76 (motifs lisibles : densité + encre, pas gras) :
  - traits 1.0 px ; plus de hachures (espacement serré) ;
  - encre pastel #1A252F opaque ; opacité bande 80 %.

v2.9.73 (GMAG table > famille ; altéro motifs lisibles) :
  - discover litho : biblio famille (plus de table DEFAULT) ;
  - altérations : opacité 95 %, encre motifs plus foncée.

v2.9.72 (marge bas 8 m ; palettes litho+altéro reconstruites) :
  - marge bas max(8 m, 5 %) rétablie ;
  - LITHO_BASE + ALTER_BASE + DEFAULT_LITHO revus (0 doublon) ;
  - taxonomies resynchronisées sur genesis_palettes.

v2.9.71 (qtz jaune ; marge bas 3 m) :
  - Qtz vein = jaune lisible #F1C40F ;
  - marge bas max(3 m, 2.5 %) — moins de blanc sous les trous.

v2.9.70 (elev 20 m, marge bas eoh, litho contrastée, EOH = ticks) :
  - pas élévation défaut 20 m (Auto → 10 m trop serré) ;
  - marge bas ≥ 8 m pour eoh vs axe distance ;
  - DEFAULT_LITHO prioritaire (GMAG ≠ basalt) ; Qtz vein clair ;
  - chiffre EOH même graisse que 10/30/50 (plus de bold qui grossit).

v2.9.69 (défauts user : elev Auto, voies 12, litho distincte, miné 2 lettres) :
  - pas d'élévation défaut = Automatique (0), plus 20 m forcé ;
  - largeur voie miné / alté = 12 px ;
  - codes miné défaut = 2 premières lettres du code brut ;
  - palette litho familles plus contrastée.

v2.9.68 (marge altitude 2 m dans la coupe) :
  - emprise verticale ≥ +2 m bas/haut (plot + export) ;
  - ticks inchangés (data extrema) ; eoh a de l'air dans le cadre.

v2.9.67 (PNG ultra-HD, plus de SVG) :
  - export PNG seul ~20 000 px / scale 4–5 / 100 Mpx (v2.9.95) ;
  - SVG retiré du dialogue et du pipeline ;
  - marge bas conservée (protège eoh + axe) — volontaire.

v2.9.66 (titre de section centré gras) :
  - nom de coupe centré, gras, plus grand (export PNG/SVG) ;
  - plus de titre discret collé à gauche.

v2.9.65 (légende export un cran plus lisible) :
  - corps / titres SmallCaps +1–2 pt, lignes un peu plus hautes ;
  - leg_scale plancher +0.15, largeur colonne inchangée ;
  - pas d’élargissement de page ni de légende monstre.

v2.9.64 (EOH = même corps que ticks + N mini-carte) :
  - EOH en QFont identique aux cotes 10/30/50 (plus de HTML pt) ;
  - « eoh » italique même taille, collé sous le chiffre ;
  - placement bas / extérieur serré sous le fond de trou ;
  - flèche N mini-carte rentrée (plus de N coupé au bord).

v2.9.63 (topo clipée au cadre P1–P2) :
  - ligne de sol affichée uniquement dans min_along…max_along ;
  - plus de débord ±buffer hors axes (export Sec.001/002) ;
  - échantillonnage corridor inchangé (QC / ancrage collets).
  - document margin 0 ; « eoh » centré et collé sous 140.3 / 150.4 ;
  - plus de dérive vers l'axe X.

v2.9.61 (EOH = dernière graduation, même taille) :
  - même police / couleur / barreau que les autres profondeurs ;
  - chiffre gras (valeur réelle) ; « eoh » italique collé sous le chiffre.

v2.9.60 (EOH réel, gras + eoh italique) :
  - fin de trou = graduation à la profondeur RÉELLE (ex. 150.4) ;
  - chiffre en gras ; « eoh » subtil en italique juste en dessous ;
  - plus de cartouche « EOH 150 » mal placé hors trajectoire.

v2.9.59 (crash distance_step_spin) :
  - _section_style_values / apply : getattr défensif sur spins axes ;
  - construction UI sous _loading_settings pour bloquer signaux précoces.

v2.9.58 (panneau propriétés : seul « Coupe active » ouvert) :
  - Inclusion / Pistes / Topo / Légendes repliés par défaut ;
  - Légendes reste non déroulé (déjà le cas, rendu explicite).

v2.9.57 (mini-carte N+échelle, légende, EOH, elev 20) :
  - mini-carte : nord, échelle, labels anti-chevauchement ;
  - légende plus grande + phrase altérations du panneau ;
  - pas élévation défaut Auto ; topo plus visible ;
  - EOH gras en bas de trajectoire.

v2.9.56 (export page layout propre) :
  - bannir « Largeur = intensité » de la légende export (ne reflète rien
    de lisible sur la coupe exportée) ;
  - légende plus compacte (échelle plafonnée, altérations 2 colonnes) ;
  - mini-carte bas-droite alignée bas de coupe (plus de trou blanc ni
    carte qui flotte sous la page) ;
  - taille mini-carte bornée (~légende, max ~section/5).

v2.9.55 (mini-carte sous légende + collets courts) :
  - mini-carte à droite, SOUS la légende (plus sous la coupe / cartouche) ;
  - collets dans l'emprise buffer seulement, libellés courts (ex. 004) ;
  - plus de tampon bas-gauche qui chevauche NE/azimut.

v2.9.54 (légende lisible + mini-carte visible en HD) :
  - légende proportionnelle à la hauteur de coupe (plus de texte minuscule) ;
  - mini-carte ~14 % largeur coupe (plus un timbre 220 px invisible) ;
  - plafond compose aligné sur le PNG HD (ne plus jeter légende/page).

v2.9.53 (PNG toujours ~12k, sans case HD) :
  - plus d'option « haute résolution » encombrante ;
  - tout PNG exporte à ~12 000 px (défaut unique).

v2.9.52 (légende export : largeur = intensité) :
  - clé visuelle Faible / Modérée / Forte sous Altérations (PNG+SVG) ;
  - le lecteur hors plugin comprend sans ouvrir QGIS.

v2.9.51 (PNG encore plus HD) :
  - PNG normal ~6000 px ; PNG HD ~12000 px / scale↑ / plafond pixels↑ ;
  - toujours sans constBits ; export différé.

v2.9.50 (revert 2.9.49 mal compris) :
  - restaurer largeur ← intensité (AM-03) + textes d'aide ;
  - 2.9.49 avait retiré le rendu à tort (demande = texte manquant).

v2.9.49 (intensité ≠ largeur) — REVERTÉ en 2.9.50 :

  - ne plus affirmer ni appliquer « largeur = intensité » ;
  - voies à largeur FIXE ; intensité uniquement en infobulle ;
  - textes panneau / légende / référentiel alignés.

v2.9.48 (teneurs élément+unité + PNG HD option) :
  - légende teneurs : ligne « Fe — % » (élément + unité) comme panneau ;
  - option PNG haute résolution (jusqu'à ~7000 px) pour zoom plus net ;
  - note honnête : PNG HD ≈ net à zoom modéré ; SVG reste le mieux au fort zoom.

v2.9.47 (SVG + mini-carte visible) :
  - export PNG ou SVG (SVG = net au zoom ; PNG reste raster) ;
  - mini-carte collée en bas-gauche de la COUPE (plus coupée/absente) ;
  - crop bas moins agressif pour préserver pied + locator.

v2.9.46 (export plus net + moins de blanc) :
  - résolution max ~4800 px / scale ↑ (moins flou au zoom) ;
  - marges page serrées ; gap coupe|légende réduit ;
  - crop bords via QImage.pixel() (pas constBits) ;
  - emprise scène pad 4 px ; locator ne gonfle plus la largeur.

v2.9.45 (légende export = panneau plugin) :
  - symboles : forage #393939 fin, collet POINT seul, barrette, veine, sol ;
  - libellés en PETITES CAPITALES (comme panneau) ;
  - résolution export un peu plus haute (moins de flou au zoom).

v2.9.44 (légende export complète + motifs) :
  - ordre haut→bas : Symboles · Teneurs · Litho · Altérations · Miné ;
  - pastilles litho/altéro = _lithology_symbol_pixmap (motifs = coupe) ;
  - hauteur légende calculée (plus de troncature des altérations) ;
  - largeur serrée ; mini-carte conservée.

v2.9.43 (export minimal anti-segfault) :
  - SUPPRIME crop constBits/memoryview (segfault natif QGIS) ;
  - pipeline minimal : scene.render → titre/pied texte → save ;
  - légendes peintes simples ; pas de scan pixels ;
  - tout try/except + log fichier si échec.

v2.9.42 (export anti-crash QGIS) :
  - rendu APRÈS fermeture du dialogue (pas dans exec_ imbriqué) ;
  - plafonds mémoire (max 3600 px, scale ≤ 1.5) ;
  - crop rapide par scanline (plus de pixelColor × millions) ;
  - QPainter toujours end() en finally ; OOM → message, pas crash.

v2.9.41 (titre haut / méta bas, sans doublons) :
  - haut : UNIQUEMENT le nom de section ;
  - bas : projet · date · SCR (secondaire) ;
  - PAS d'azimut (déjà sur la coupe) ;
  - PAS de buffer dans le bandeau (déjà mini-carte ; H:50 m = échelle).

v2.9.40 (titre = nom de section seul) :
  - cartouche : TITRE = nom de la coupe uniquement (ex. Section_001) ;
  - projet / date / SCR / buffer = ligne secondaire discrète (pas titre).

v2.9.39 (cartouche + mini-carte + légende serrée) :
  - bandeau titre · date · SCR · buffer · azimut ;
  - mini-carte plan : ligne de coupe P1→P2, corridor buffer, collets ;
  - légendes en lecture haut→bas (1 panneau, 2 col. par bloc) ;
  - largeur légende serrée + crop (moins de blanc à droite).

v2.9.38 (légende export compacte, moins de blanc) :
  - légendes en 2 colonnes par bloc (litho / altéro / miné) ;
  - hauteur cible ≈ hauteur de la coupe (plus de bande blanche
    sous la coupe quand la légende est longue) ;
  - composition aligne en haut + crop final.

v2.9.37 (export net + légendes complètes) :
  - résolution export ×2 (min) / plafond 8000 px — moins de flou au zoom ;
  - légendes REDESSINÉES depuis les données (plus de grab widgets
    collapsés / hors layout → titres sans pastilles) ;
  - pastilles litho = _lithology_symbol_pixmap (même rendu coupe).

v2.9.36 (export PNG + légendes + rognage) :
  - option « Inclure les légendes » → image coupe | légendes ;
  - rognage du blanc : emprise utile (items) + crop pixels ;
  - plus d'union forcée avec sceneRect (viewport → marges vides).

v2.9.35 (export PNG = coupe ENTIÈRE) :
  - plus de grab viewport (zoom/pan tronquait) ;
  - rendu de la scène complète (itemsBoundingRect / sceneRect)
    → toute la coupe, pas seulement la fenêtre visible.

v2.9.34 (export PNG vue actuelle) :
  - barre globale : ↶ Annuler · ↷ Rétablir · Exporter… ;
  - PNG = canvas Coupe 2D tel qu'à l'écran (pas de composition maison).

v2.9.33 (ancre rappel plus discrète) :
  - pastille de début de rappel : 2,2 → 1,3 px (toujours visible,
    moins envahissante).

v2.9.32 (début de rappel visible) :
  - trait DI+FL (et tout rappel miné) : POINT D'ANCRAGE plein
    sur le bord externe de la bande = on voit OÙ ça commence ;
  - départ = milieu profondeur, bord outer (pas le centre flottant) ;
  - tooltip rappel : « départ · bord bande ».

v2.9.31 (motifs // axe + rappel DI+FL clair) :
  - vertical/horizontal/diagonale = RELATIF À L'AXE du forage
    (convention log), toujours — sans option utilisateur ;
  - traits custom ≥2 aussi // axe ;
  - légende = pastille trou vertical (même convention) ;
  - rappel combo DI+FL : départ bord externe des bandes.

v2.9.30 (hotfix crash clip motifs) :
  - _ClippedStrokeItem.paint : setClipPath(QPainterPath) uniquement
    (plus setClipRegion(QPolygon) → TypeError sous PyQt/QGIS 3.44).

v2.9.29 (motifs ≥2 traits + Annuler global) :
  - motifs H/V/diagonales : au moins 2 traits visibles (espacement
    réduit si bande étroite) — sinon on ne distingue pas le type ;
  - Annuler / Rétablir sortis de « Propriétés » → barre globale
    du dock Visualisation (à droite des onglets Coupe/3D).

v2.9.28 (motifs nets, plus d'option axe) :
  - option « Motifs alignés sur l'axe » SUPPRIMÉE (toujours fixes
    = légende) — évite de mélanger l'utilisateur ;
  - motifs toujours à l'échelle NATIVE 1,0 (plus de scale qui
    pixelise / gratte) ; sous ~4 px → couleur seule ;
  - antialiasing désactivé sur les remplissages hachurés (1-bit Qt
    + AA = flou gratté) ; courbes/trajectoire gardent l'AA ;
  - pastille légende identique (AA off, scale 1).

v2.9.27 (légende = coupe + axe + Annuler visible) :
  - boutons Annuler / Rétablir en TEXTE (plus seulement ↶ caché) ;
  - motifs « alignés sur l'axe » : rotation sur l'AXE du trou
    (milieu haut→bas), plus la diagonale du trapèze (qui donnait
    n'importe quoi) ; scale forcé à 1,0 avec rotation (pas de
    déformation scale+rotate) ;
  - pastille légende = même encre / sous-couche / scale natif 1,0
    que la coupe (plus d'écart motif légende vs bande).

v2.9.26 (retour arrière général — mauvaise manip) :
  - pile Annuler / Rétablir pour TOUT réglage de la coupe
    (largeurs, couleurs, opacités, pistes, teneurs, buffer,
    exagération…) — pas seulement le tracé de ligne ;
  - Ctrl+Z / Ctrl+Y (ou Ctrl+Shift+Z) dans la vue Coupe ;
  - boutons « ↶ Annuler » / « ↷ Rétablir » en tête du panneau ;
  - 40 niveaux ; coalescence des spins continus (~450 ms).

v2.9.25 (retour écran — défauts + miné + undo coupe) :
  - défauts : litho 17 px ; trajectoire #393939 / 0,5 px ;
    profondeur débord 2 px, texte 6 pt ;
  - minéralisation : SI place dans chaque bande → UN code PAR bande
    (pas « MA + FL ») ; combo « A + B » UNIQUEMENT si rappel ;
  - rappels plus visibles (encre un peu plus forte, placement dynamique
    rayon court d'abord) ;
  - tracé de ligne de coupe : Escape / clic droit = annuler ;
    refus du buffer = annuler (plus de ligne fantôme) ;
    bouton « Annuler le tracé » + Ctrl+Z dernière ligne.

v2.9.24 (motifs = légende, traits FINS) :
  - échelle motif plafonnée à 1,0 (jamais > légende) : scale>1
    grossissait les hachures en traits gras (retour écran) ;
  - bandes petites → motif plus FIN (scale < 1), pas plus gras ;
  - pastille légende et coupe partagent le même rendu natif.

v2.9.23 (motifs micro-bandes) :
  - bande très petite (&lt; 8 px) : plus de « couleur seule » —
    MICRO-MOTIF (échelle très fine) pour garder l'identité litho
    même en intervalle court / voie étroite ; sous ~3,5 px seulement
    on retombe en couleur (pixel).

v2.9.22 (légendes + motifs) :
  - libellés de légende en PETITES CAPITALES (surtout litho) ;
  - motifs adaptatifs : largeur ET hauteur de bande mesurées —
    bande trop petite → couleur seule ; sinon échelle calée sur
    min(portée, largeur) pour rester lisible en voie fine / court
    intervalle (plus de hachures illisibles).

v2.9.21 (retour écran bulle litho) :
  - bulle : plus de « sec. » sur TOUT composant sans rôle CSV —
    1er = hôte, QTZ_VEIN… = veine (même logique que le dessin D-01).

v2.9.20 (retour écran litho + pistes) :
  - PAS de codes litho sur la coupe (légende + bulle suffisent) ;
  - secondaires sans % : barrette INTERNE (plus de rail gauche) ;
  - bulle litho avec rôle court (hôte / sec. / veine) ;
  - micro-intervalles : motif abandonné plus tôt → couleur nette ;
  - légende symboles : barrette secondaire + filet veine ;
  - teneurs ↔ profondeurs un peu plus proches.

v2.9.19 (retour écran — double minéralisation) :
  - même intervalle, 2 styles (MA+DI, MA+BR…) : DEUX bandes gardées
    (voie 1 = 1ᵉʳ style, voie 2 = 2ᵉ), MAIS UN SEUL trait de rappel
    + UN code combiné « MA + DI » (plus deux rappels qui se croisent).

v2.9.18 (retour écran) :
  - bulles des ONGLETS étapes 1–4 (stepper + pastilles familles +
    badge_rendu) en format court.

v2.9.17 (retour écran) :
  - bulles du DOCK CONTROLE + DOCK VISUALISATION aussi en court
    (spins, combos, légendes, boutons) — pas seulement la coupe.

v2.9.16 (retour écran — bulles trop bavardes) :
  - TOUTES les bulles de la coupe en BLOC COURT (2–3 lignes max) :
    trou · From–To, puis code · intensité (ou teneur) — fini les
    libellés longs, préfixes Alt1, minéraux tronqués en pavé.
  - teneurs : infobulle ajoutée (trou · profondeur · élément · valeur).

v2.9.15 (retour écran) :
  - opacités défaut litho + teneurs = 100 % ;
  - bulle d'info : intensité PAR code (Alt_k / Int_k), plus l'intensité
    d'intervalle qui montrait FAIBLE sur une bande OXYDATION moyenne ;
  - bulles simplifiées (profondeur, code, intensité propre — fini le
    pavé « Ligne(s) CSV » / libellés redondants) ;
  - rappels miné : éventail plus serré, priorité rayon court + angle
    qui suit la profondeur du micro-intervalle (séquence MA/DF).

v2.9.14 (retour écran TPDD006 — séquence réelle MA/DF/MA/DF) :
  - ce n'est PAS un seul run : CSV 52–53 DF, 53–54 MA, 54–55 DF,
    55–60 MA (+ Style_2) — chacun mérite son code ;
  - déport ANGULAIRE (éventail ±15…±75° dans le plan normale×tangente)
    → rappels courts orientés, codes étagés à leur profondeur, plus
    la rangée horizontale DF–MA–DF avec longs traits ;
  - anti-collision globale OBB entre TOUS les codes (en place +
    déportés) ; se recalcule à chaque rendu (largeur de voie incluse).

v2.9.13 (retour écran — pan évident) :
  - glisser avec le clic gauche = déplacer la coupe (seuil 4 px) —
    plus besoin de Shift ni de molette (tout le monde sait glisser) ;
  - au repos : flèche (survol précis des micro-bandes / infobulles) ;
  - pendant le glisser : main fermée ; molette reste un pan bonus.

v2.9.12 (retour écran — chevauchement MA/DI + main de survol) :
  - déport minéralisation : plus de « dernier recours » qui accepte
    le chevauchement ; recherche radiale étendue + enregistrement OBB
    de chaque code déporté (les suivants l'évitent) ;
  - curseur FLÈCHE par défaut (plus la main permanente de
    ScrollHandDrag) — pan au clic molette / clic gauche+Espace ;
  - zone de hit élargie (pad invisible ~8 px) sur les bandes pour
    infobulle des micro-intervalles et doubles altérations.

v2.9.11 (retour écran 23/08/2026 — rappels mal orientés, codes qui
se chevauchent) :
  - les « boîtes » = bandes from→to (contour d'intervalle), PAS des
    cadres de label — on les garde (c'est le from–to) ;
  - beaucoup de rappels viennent d'intervalles RÉELS de 1 m dans le
    CSV (36–37, 47–48, 52–53…) — normal ;
  - placement déporté : d'abord PURE normale (rappel court
    perpendiculaire), glissement le long du trou seulement si
    collision, avec écart radial croissant — fini les piles de
    codes sur la même verticale et les rappels en diagonale longue.

v2.9.10 (retour écran 23/08/2026) :
  - TOPO anti-escalier : densify + moyenne glissante puis ré-ancrage
    collets (``refine_surface_profile``) — la ligne MNT ne « marche »
    plus pixel par pixel ;
  - codes minéralisation : si la bande devient plus étroite que le
    code à la plus petite taille lisible → déport + trait de rappel
    (plus de glyphe coincé illisible dans 2–4 px) ; dernier recours
    = code à côté avec rappel forcé, jamais écrasé dans la bande.

v2.9.9 (lecture MNT CORRIGÉE, retour écran 23/08/2026 : ligne dans
l'emprise, même SCR que le projet, source = mon MNT, et pourtant
« 0/257 points valides… hors étendue / NoData ») :
  - cause : ``result.value(0)`` lisait une clé d'ORDRE inexistante
    (les bandes QGIS sont 1-based → ``value(1)`` / ``results()[1]``) ;
    le MNT renvoyait donc TOUJOURS None, masqué en « hors étendue » ;
  - ``dataProvider().sample(pt, 1)`` est tenté EN PREMIER (API la
    plus fiable pour un MNT mono-bande) ;
  - repli ``identify`` + ``_extract_raster_sample`` robuste
    (results/value bande 1, dicts imbriqués, QVariant) ;
  - message d'échec enrichi : hors-emprise vs NoData + authids CRS.

v2.9.8 (conversion WGS84 ↔ UTM INTÉGRÉE, retour écran 25/08/2026 :
projet EPSG:32629 / MNT « DEM » EPSG:4326, message « transformation
CRS impossible » alors que c'est la paire la plus standard de la
géologie et que QgsCoordinateTransform échoue sous QGIS 3.44) :
  - nouveau module ``core/crs_math.py`` — Mercator transverse sur
    l'ellipsoïde WGS84 (formules standard, pure Python, QGIS-free,
    vérifiées à < 1 mm contre pyproj) ;
  - si la transformation QGIS est indisponible ET que la paire est
    WGS84 ↔ UTM (EPSG:4326 ↔ EPSG:326xx/327xx) : chaque point est
    converti par ce module au lieu d'écarter le MNT — le DEM
    WGS84 d'un projet UTM fonctionne SANS AUCUNE action de
    l'utilisateur ;
  - le message résiduel « transformation CRS impossible (projet :
    X / MNT : Y) » ne reste que pour les paires inconnues.

v2.9.7 (CRS identiques → aucune transformation, retour écran
25/08/2026 : « mon DEM a le même CRS que le projet (32629) » mais
message « CRS du projet ≠ CRS du MNT ») :
  - les CRS du projet et du MNT sont comparés PROPREMENT
    (``project_crs == layer_crs``, comme QGIS) — pas la chaîne
    d'authid : EPSG:32629, IGNF:ETRS89-UTM-29 ou une définition WKT
    peuvent désigner le MÊME système ;
  - si les CRS sont identiques : AUCUNE transformation n'est
    construite, on échantillonne directement (l'API
    QgsCoordinateTransform est instable sous certaines versions de
    QGIS, ex. 3.44 — c'est elle qui provoquait le « ≠ » faux) ;
  - si les CRS diffèrent et que la transformation échoue : message
    avec les DEUX authids + où vérifier chaque CRS.

v2.9.6 (diagnostic CRS par côté, retour écran 24/08/2026 : « MNT « DEM »
détecté mais non utilisé : transformation CRS impossible ») :
  - entre deux CRS VALIDES et différents, QGIS trouve toujours une
    transformation — donc « transformation impossible » = un des deux
    CRS n'est pas défini ;
  - le message dit MAINTENANT lequel :
    « CRS du projet QGIS non défini » (→ Projet → Propriétés → CRS)
    ou « MNT « nom » sans CRS valide » (→ clic droit couche → Définir
    le CRS, ou réprojeter le raster) ;
  - les deux authids sont cités dans le cas résiduel (deux CRS valides
    mais transformation introuvable).

v2.9.5 (MNT échantillonné sans QgsRasterIdentifyRequest — retour écran
24/08/2026, QGIS 3.44 : « MNT « DEM » détecté mais non utilisé :
classes QGIS manquantes : QgsRasterIdentifyRequest ») :
  - l'échantillonnage passe par l'API HAUT NIVEAU
    ``QgsRasterLayer.identify(point, QgsRaster.IdentifyValue, bande=1)``
    — elle ne REQUIERT PAS ``QgsRasterIdentifyRequest``, classe non
    exposée par qgis.core sous certaines versions (3.44) ; le DEM de
    l'utilisateur est maintenant réellement lu (le message précis de
    v2.9.4 avait permis de trouver la classe exacte).

v2.9.4 (le combo « Source MNT » ne liste QUE les rasters, retour écran
24/08/2026 — « j'ai un DEM chargé, la liste n'a que des vecteurs et
ça dit QGIS indisponible », QGIS 3.44) :
  - la détection des rasters passe de ``type() == 0`` à
    ``isinstance(lyr, QgsRasterLayer)`` (indépendant de la valeur du
    type(), qui rendait 0 pour des VECTEURS sous QGIS 3.44) avec
    ``type()`` en simple secours — le combo, le statut de détection,
    le rafraîchissement et le choix du MNT passent tous par le même
    helper ``_qgis_raster_layers()`` ;
  - le message d'indisponibilité de l'échantillonnage est précis :
    « QGIS indisponible (qgis.core non importable) » seulement si le
    module manque, sinon « classes QGIS manquantes : … » — plus de
    « QGIS indisponible » à tort dans QGIS.

v2.9.3 (MNT jamais écarté silencieusement, retour écran 23/08/2026 :
« par défaut il prend les collets ? », « il détecte les vecteurs et
non les rasters ? », « j'ai un DEM, est-ce qu'il le prend en compte ? ») :
  - un MNT détecté mais ÉCARTÉ (pas de dataProvider, transformation
    CRS impossible, < 2 points valides le long de la coupe = hors
    étendue ou NoData) est TOUJOURS expliqué : statut
    « Sol : … ⚠ MNT « nom » détecté mais non utilisé : <raison> » +
    ligne ⚠ dans l'infobulle — jamais de repli collets muet ;
  - le combo « Source MNT » suit les couches RASTER du projet QGIS
    actif à CHAQUE régénération (un DEM chargé après l'ouverture de
    la vue apparaît sans rechargement — garde sur la liste, pas de
    flicker) ;
  - statut « aucun MNT » précisé : RASTER (ni vecteur, ni maillage).

v2.9.2 (placement du groupe topographie + statut MNT détecté, retour
écran 23/08/2026) :
  - le groupe « Topographie (ligne de sol) » SORT de « Cadre, axes et
    échelle » (où il était introuvable — 2 niveaux de repli) et
    devient un groupe de 1ʳ NIVEAU du panneau « Propriétés de la
    coupe », DÉPLIÉ par défaut (c'est une couche de données avec sa
    source et son QC, pas un réglage du cadre) ;
  - STATUT « MNT chargé ou détecté » VISIBLE EN PERMANENCE (même
    avant la 1ʳᵉ génération) : « MNT détecté : « nom » » (le combo
    Source MNT liste déjà les rasters du projet par nom) / « Aucun
    MNT dans le projet QGIS → cascade CSV x;y;z / collets » / nom du
    CSV topographie du projet ; recalculé à chaque peuplement du
    combo (1 hook), et il ne masque jamais le statut ancrage+QC d'un
    rendu (garde ``_result``).

v2.9.1 (légende des symboles, retour écran 23/08/2026) :
  - CLÉ DE LECTURE : chaque symbole graphique du canvas a son entrée
    dans le groupe « Légendes » — trait FORAGE (couleur/épaisseur du
    canvas), pastille COLLET (rouge #C0392B identique au marqueur),
    LIGNE DE SOL avec le style exact qui est dessiné (trait PLEIN =
    mesurée MNT/CSV, POINTILLÉ = interpolée aux collets) — plus de
    ligne ni de point « non marqués dans la légende » ;
  - la légende suit le CANVAS : signal ``rendered`` émis à chaque
    sortie de ``_render``, la légende se resynchronise après chaque
    rendu (l'entrée ligne de sol apparaît/disparaît avec la source
    réellement dessinée, jamais un état en cache du côté widget) ;
  - entrée forage masquée quand la piste « Trajectoire » est décochée
    (règle des légendes : seules les pistes cochées figurent).

v2.9.0 (topographie, décision écran 22/08/2026) :
  - LIGNE DE SOL le long de la coupe, CASCADE avec repli automatique :
    MNT raster du projet QGIS → CSV x;y;z du projet → collets seulement
    (jamais un choix figé ; le MNT est toujours prioritaire) ;
  - ANCRE AUX COLLETS : la ligne garde la FORME du MNT (information entre
    les points connus) mais passe EXACTEMENT par chaque collet (sommet du
    profil, donnée la plus précise du point) — correction COSINUS C1,
    atténuation progressive, AUCUN COUDE au collet ;
  - DISTINCTION VISUELLE OBLIGATOIRE : trait PLEIN = source mesurée
    (MNT/CSV), POINTILLÉ = interpolation collet-à-collet ;
  - QC MNT ↔ COLLETS : écart de chaque collet vs MNT à sa position XY,
    affiché au-delà du seuil (défaut 2 m, réglable) — jamais masqué ;
  - l'étendue verticale VISUELLE inclut la surface (jamais rognée) mais
    les ticks de grille restent sur la trajectoire (contexte, pas donnée) ;
  - la coupe n'est JAMAIS bloquée par la topographie (repli silencieux).

v2.7.12.0 (CM-05 arbitrée le 21/08/2026) :
  - les couleurs de famille sont celles des palettes génétiques du
    document utilisateur (litho_palette.json / alt_palette.json, OKLCH)
    — source unique : core/genesis_palettes.py ;
  - familles composites d'altération (Propylitique, Phyllique avancée,
    Argilique avancée/intermédiaire) : remplissage en DÉGRADÉ des
    couleurs parentes, aussi bien en coupe qu'en légende — uniquement
    tant que la couleur est le défaut automatique du Référentiel ;
    un choix explicite de couleur reste un aplat.

v2.7.11.9 (retour écran 21/08/2026) :
  - JAMAIS de code tronqué en coupe : l'abréviation « … » (elide) est
    retirée du chemin de dessin des styles (la bande garde l'infobulle
    complète si aucune place pleine n'existe — seule source de vérité) ;
  - légendes : les longs libellés ne se tronquent plus (« Basalt ma… »,
    « Silicificati… ») — retour à la ligne partout.

v2.7.11.8 (capture du soir, 21/08/2026) :
  - légende Minéralisations : elle lisait seulement l'attribut canonique
    — en organisation large (Style_1/_2), les styles vivent dans les
    composants → « Aucune minéralisation disponible » réparé (le marqueur
    _wide_styles garantit AM-05 : jamais de minéraux en légende) ;
  - codes d'une intervalle à 2+ styles : UN libellé combiné
    (« MASSIVE + FILONIENNE ») par intervalle, posé sur toute l'étendue
    du groupe par la machine de placement existante — plus de rappels
    croisés ni de pile de cases ; les bandes restent côte à côte ;
  - séparateur visible entre codes d'altération : 0,6 px dès qu'un
    intervalle porte plus d'un code (0,2 px historique conservé pour un
    code seul).

v2.7.11.7 (retour écran 21/08/2026) :
  - garde anti-bruit : en-têtes de 3 lettres ou moins ne matchent qu'en
    EXACT (« Min » fuzzy-matchait « to » → une colonne de minéraux était
    lue comme profondeur TO) ; synonymes « min »/« mineral » ajoutés ;
  - minéralisation : splits délimités de STYLE marqués pour la piste
    (déclaré = permis par AM-05) ; splits de MINÉRAUX sans marqueur,
    jamais affichés comme bandes de style.

v2.7.11.6 (retour écran 21/08/2026) :
  - validation : une organisation confirmée (large/délimitée) dispense le
    champ canonique de contenu — fin du blocage « Champ requis » sur les
    fichiers Alteration_1/_2 ;
  - la cellule délimitée est lue depuis l'en-tête BRUTE quand il n'y a
    pas de mapping canonique ; l'unique intensité candidate alimente
    l'intervalle d'office ;
  - UI : « Options avancées… » existe désormais pour Altérations et
    Minéralisations (dialogue dédié avec plafonds CM-03) ; la table de
    mapping affiche le rôle structurel des colonnes absorbées ;
    infobulles lisibles (noir sur noir corrigé) ; libellé d'organisation
    nommé par colonnes lues.

v2.7.11.5 (retour écran 21/08/2026) : en cas d'ambiguïté de
  détection, le MEILLEUR candidat est proposé en tête de question
  (« ✓ suggéré ») — avant, les boutons commençaient au 2ᵉ choix
  et la bonne réponse n'était jamais cliquable.

v2.7.11.4 (retours écran 21/08/2026, défauts arbitrés) :
  - débord des graduations : 3 px par défaut (était 8) ;
  - motifs FIXES à l'écran par défaut (« alignés sur l'axe »
    reste disponible — annule la décision v2.7.10.28) ;
  - bandes d'altération et de minéralisation : 13 px par défaut.

v2.7.11.3 (retour écran 21/08/2026) :
  - filets filonien/accessoire EN DIAGONALE à travers la bande
    hôte (veine « \ », accessoire « / ») : lisibles alors que la
    polyligne de trace les masquait (z 2,9 < 5) ;
  - crash import « configure_composite_button » corrigé ;
    garde CHK-42 : tout attribut widget Qt (…_button, …_label…)
    doit être affecté dans son fichier — impossible à reproduire.

v2.7.11.2 (arbitrage CM-04 du 21/08/2026) :
  - tokens filoniens élargis aux codes EXACTS de la codification
    utilisateur (VQZ veine de quartz, STW stockwerk) : couleur « veine »
    et géométrie filet disent désormais la même chose ;
  - simplicité arbitrée : AUCUNE géométrie dédiée brèche/dyke/interlit —
    la grammaire à 5 classes (hôte plein / barrette secondaire / filet
    filonien / filet accessoire / partage proportionnel) suffit.

v2.7.11.1 (arbitrage CM-03 du 21/08/2026) :
  - plafonds d'organisation fixes par domaine (litho 4, altérations 5,
    styles de minéralisation 2, minéraux 5, intensités 5) ;
  - intensité PAR CODE (Int_k ≡ colonne k) sur la piste d'altération :
    la largeur du groupe reste celle de l'intervalle, les parts internes
    suivent l'intensité propre de chaque code (poids égaux ou absents ⇒
    dessin historique identique, aucune régression) ;
  - le rail des barrettes secondaires litho (D-01) est désormais RÉSERVÉ
    dans le plan de pistes (plus d'empiètement sur les voies voisines) ;
  - v2.7.13.0 — NOTION DE SOUS-PISTE PAR TYPE SUPPRIMÉE (retour écran) :
    chaque famille garde UNE seule bande de largeur FIXE — les codes d'un
    même intervalle se partagent cette bande (mode groupé unique), et le
    plan de pistes ne dépend plus des codes présents.

  - compact active-section selector; full history lives in Assistant step 4
  - explicit continuous/classified grade maps and separate lithology legend
  - named P1/P2 distance/elevation axes with safe margins
  - truthful section orientation and intelligent horizontal scale overlays
  - verifiable live buffer state and coherent geological terminology

v2.7.10.12 (retour écran) :
  - toutes les bandes d'intervalle (litho, teneurs, altérations,
    minéralisations) ont leurs bords from/to PERPENDICULAIRES à la trace
    réellement dessinée — la même normale scène que les barreaux de
    profondeur — donc polygones et graduations restent parfaitement
    alignés quel que soit le pendage ou l'exagération verticale ;

v2.7.10.13 (retour écran 20/08) :
  - le code de minéralisation suit la convention des logs : posé LE LONG
    de la bande (vertical sur trou vertical, pivoté avec le pendage),
    COMPLET, taille adaptative 6 → 3,5 pt mesurée sur la longueur du run
    et la largeur de la bande ; horizontal si la bande est large, « … »
    seulement en dernier recours ;
  - bande de style en PLEINE LARGEUR (l'intensité ne rétrécit plus la
    piste neutre -> fin de l'effet « exagéré » ; l'intensité reste dans
    l'infobulle) ; largeur par défaut de la piste : 14 px.

v2.7.10.15 (retour écran 20/08, suite immédiate) :
  - modèle STRICT de la piste minéralisation : style + minéraux — aucun
    facteur d'intensité (absent du fichier, rien d'inventé), bande pleine
    largeur entièrement offerte au code du style ;
  - micro-intervalles : le code est DÉPORTÉ à la première place libre de
    la piste avec un fin trait de rappel vers son intervalle, au lieu de
    disparaître (anti-chevauchement garanti par rectangles occupés).
    Altérations : jamais modifiées.
  - v2.7.10.16 : recherche « à côté » aussi — petit glissement latéral
    borné DANS la piste (jamais sur la piste voisine) + portée ±45 px le
    long du trou ; le rappel devient oblique si besoin.

v2.7.10.17 (retour écran 20/08, capture) :
  - le déport vertical d'écran superposait le code aux bâtonnets de
    teneurs dès que le trou est incliné. Nouvelle règle : « À CÔTÉ »,
    PERPENDICULAIRE à la trajectoire, TOUJOURS en premier (espace libre
    au-delà du bord externe de la piste) ; repli le long de la piste en
    suivant sa pente. Rappel perpendiculaire jusqu'à l'intervalle.

v2.7.10.18 (retour écran 20/08, capture) :
  - petits chevauchements résiduels sur les bords : l'empreinte des codes
    pivotés était une permutation naïve, sous-estimée aux pendages réels
    ; désormais enveloppe EXACTE (rotated_aabb) + marge 2 px, et les
    poses EN PLACE exigent aussi un slot libre.

v2.7.10.19 (retour écran 20/08, capture zoomée) :
  - « il va se poser sur un polygone d'un autre intervalle, c'est vilain »
    : l'anti-collision ignorait les BANDES. Désormais la place de déport
    exige l'absence de tout polygone de la piste (intersection polygonale
    exacte + 1,5 px de marge) ; le repli « le long de la piste » est
    supprimé (il posait le code SUR les bandes par construction).

v2.7.10.21 (retour écran 20/08, captures zoomées) :
  - rappel trop long : corridor perpendiculaire × glissement le long de
    la trace, place libre AU RAPPEL LE PLUS COURT (tri distance²) ;
  - intervalles qui semblaient vides : remplissage neutre 22 % -> 32 %,
    liseré 0,25 -> 0,35 px.

v2.7.10.26 (retour écran 20/08) :
  - onglets d'import : question d'organisation sans réponse -> ⚠ jaune
    (tabBar) ; réponse tardive -> invalidation de la géométrie générée
    + revalidation (synchro après coupes corrigée) ;
  - motifs : encre contrastée (blanc sur base foncée / ardoise sur
    pastel), densité = taille de l'intervalle, sous-couche 0,55 ;
    - minéralisation : bande TRANSPARENTE + contour d'encre neutre + code
    (« pas de couleur », décision écran).

v2.7.10.32 : une règle d'encre unique (_pattern_ink_colour) partagée
coupe/légende. v2.7.10.34 : l'historique des coupes n'est plus jamais
caché au reset ; un échec de génération est toujours présenté dans le
statut de l'étape 4 (ui/step4_section.py).
```
