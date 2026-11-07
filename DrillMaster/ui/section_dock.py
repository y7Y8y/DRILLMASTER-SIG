"""
DrillMaster — Section View Widget V2.9.62
============================================

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
"""
from __future__ import annotations

from pathlib import Path

import csv
import math
import os
from typing import Optional

from qgis.PyQt.QtCore import Qt, QPointF, QRectF, QRect, QSize, pyqtSignal, QTimer, QEvent, QCoreApplication
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QGraphicsView, QGraphicsScene, QPushButton, QToolButton, QShortcut,
    QSlider, QLabel, QDoubleSpinBox, QSpinBox, QCheckBox,
    QGraphicsEllipseItem, QGraphicsPolygonItem, QComboBox, QMenu,
    QSplitter, QFrame, QScrollArea, QLineEdit, QColorDialog,
    QStackedWidget, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSizePolicy, QFileDialog, QMessageBox, QDialog,
    QDialogButtonBox, QGroupBox, QTabWidget,
)
from qgis.PyQt.QtGui import (
    QColor, QPen, QBrush, QFont, QFontMetrics, QFontMetricsF, QPainter, QPolygonF,
    QPixmap, QImage, QTransform, QPainterPath, QPainterPathStroker, QKeySequence)

from ..core.section import (
    compass16,  # 337 — rose 16 partagée (core)
    SectionResult, SectionLine, generate_section, get_litho_color,
    get_litho_style, compute_assay_scale, classify_assay, assay_ramp_rgb,
    assay_scale_classes, get_all_litho_codes, compute_buffer_diagnostics,
    group_shared_collars, compute_isotropic_scales, grid_tick_values,
    generated_litho_color, CLASSIFICATION_METHODS, ASSAY_RAMPS,
    project_point_onto_section, drillhole_buffer_status,
)
# v2.9.0 — topographie : cascade MNT → CSV → collets, ancrage, QC.
from ..core.topography import (
    anchor_profile_to_collars, collar_deviations, profile_from_collars,
    refine_surface_profile)
# v2.9.8 — repli intégré WGS84 ↔ UTM si la transform QGIS échoue.
from ..core.crs_math import conversion_between
from ..core.track_bands import (
    component_band_layout, intensity_factor,
    LANE_WIDTH_PX, lane_slots, reduced_rail_fraction)
from ..core import multi_assay as multi_assay_mod
from ..core import threshold_rule as threshold_rule_mod
from ..core.reference import PATTERN_UNDERLAY_ALPHA_RATIO, normalise_pattern
from ..core.data_model import DrillHole
from .styles_qt import (
    COLORS, BUTTON_SECONDARY, INPUT_STYLE, TABLE_STYLE, TOOLTIP_STYLE,
    suppress_button_focus_rects, make_collapsible_help)



# ---------------------------------------------------------------------------
# v2.9.90 — UNIQUE source couleur de sélection légende → coupe
# Toute surbrillance (contour scène + chrome panneau) lit CETTE constante.
# ---------------------------------------------------------------------------
SELECTION_HIGHLIGHT_COLOR = "#00E5FF"  # cyan vif = règle 1 (slot)
# v2.9.122 — clic-légende ≠ couleur de règle (cyan/magenta/ambre).
LEGEND_CLICK_COLOR = "#34495E"  # anthracite / ardoise (interaction UI)

# v2.9.114 — largeurs scène (pen non-cosmetic) : dock lisible, export HD fin
SELECTION_OUTLINE_PEN_DOCK = 1.85
SELECTION_OUTLINE_PEN_EXPORT = 0.9


def _selection_highlight_pen(width: float = 2.0,
                             color: str = None) -> "QPen":
    """Pinceau pointillé de sélection.

    v2.9.112 — **non-cosmetic** : largeur en unités scène.
    v2.9.116 — ``color`` optionnelle (multi-règles) ; défaut =
    SELECTION_HIGHLIGHT_COLOR (légende HL reste cyan unique).
    """
    hex_c = str(color or SELECTION_HIGHLIGHT_COLOR).strip() or SELECTION_HIGHLIGHT_COLOR
    if not hex_c.startswith("#"):
        hex_c = "#" + hex_c
    pen = QPen(QColor(hex_c), float(width), Qt.DashLine)
    pen.setCosmetic(False)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen

def _selection_chrome_stylesheet() -> str:
    """Style row légende sélectionnée — bordure = LEGEND_CLICK_COLOR."""
    base = QColor(LEGEND_CLICK_COLOR)
    # fond clair dérivé (mélange blanc) — pas une 2e couleur magique
    fill = QColor(
        (base.red() + 255 * 2) // 3,
        (base.green() + 255 * 2) // 3,
        (base.blue() + 255 * 2) // 3,
    )
    return (
        f"QWidget {{ background: {fill.name()}; "
        f"border: 1px dashed {LEGEND_CLICK_COLOR}; "
        f"border-radius: 3px; }}"
    )

# v2.7.5 — one unmistakable Qt style per offered key (see core/reference
# PATTERN_KEYS).  Existing key→style assignments are kept for saved
# projects; "dots" is now genuinely SPARSE points and legacy "dense"
# reads as the same sparse look (they were indiscernible by design).
_LITHO_BRUSH_PATTERNS = {
    "": Qt.SolidPattern,
    "diagonal": Qt.FDiagPattern,
    "backward_diagonal": Qt.BDiagPattern,
    "cross": Qt.CrossPattern,
    "diagonal_cross": Qt.DiagCrossPattern,
    "horizontal": Qt.HorPattern,
    "vertical": Qt.VerPattern,
    "dots": Qt.Dense1Pattern,
    "dense": Qt.Dense1Pattern,  # legacy alias, reads as sparse dots
# v2.7.8.2 — trois densités de pointillés discernables sur 8 px
    "dots_moyen": Qt.Dense3Pattern,
    "dots_fin": Qt.Dense5Pattern,
    "dots_dense": Qt.Dense7Pattern,
}


# v2.7.10.27/32 — les motifs à LIGNES seuls reçoivent une encre
# contrastée ; les motifs DENSES (Qt.Dense* = remplissage) gardent la
# couleur de base, sinon la bande entière vire au gris.
_LINE_BRUSH_STYLES = (Qt.FDiagPattern, Qt.BDiagPattern, Qt.CrossPattern,
                      Qt.DiagCrossPattern, Qt.HorPattern, Qt.VerPattern)


def _pattern_ink_colour(base_colour: QColor, brush_style=None) -> QColor:
    """v2.9.33/87 — ENCRE unique coupe=légende.

    Lignes : blanc sur foncé, ardoise sur clair.
    Dense* : couleur de base (remplissage Qt, pas encre grise).
    """
    if brush_style in _LINE_BRUSH_STYLES:
        return (QColor("#FFFFFF") if base_colour.lightness() < 130
                else QColor("#4A4A4A"))
    return QColor(base_colour)


def _export_smallcaps_font(point_size: int = 8, bold: bool = False) -> "QFont":
    """Police export en petites capitales (même intention que le panneau)."""
    f = QFont("Segoe UI", max(6, int(point_size)))
    f.setBold(bool(bold))
    try:
        f.setCapitalization(QFont.SmallCaps)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : _export_smallcaps_font", _exc)
        # SmallCaps indisponible — casse logicielle plus bas
        pass
    return f


def _export_sc_text(text) -> str:
    """Texte pour petite-capitale : Qt SmallCaps + filet upper poli."""
    s = str(text or "")
    # SmallCaps Qt affiche les minuscules en petites caps ; on garde
    # le libellé tel quel si possible, sinon upper léger en secours.
    return s


def _legend_label(text: str) -> "QLabel":
    """v2.9.22 — libellé de légende en petites capitales (lisibilité codes)."""
    label = QLabel(QCoreApplication.translate(
        "SectionWidget", str(text or "")))
    label.setWordWrap(True)
    font = label.font()
    try:
        font.setCapitalization(QFont.SmallCaps)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Légende : _legend_label", _exc)
        # SmallCaps indisponible sur certains backends Qt — CSS en secours.
        pass
    font.setPointSize(max(8, font.pointSize()))
    label.setFont(font)
    # filet CSS en secours (thèmes Qt qui ignorent SmallCaps)
    label.setStyleSheet(
        (label.styleSheet() or "")
        + "QLabel { font-variant: small-caps; letter-spacing: 0.3px; "
        "background: transparent; }")
    return label







class CollapsibleGroup(QWidget):
    """Accordion with visually distinct main (0) and nested (1) levels."""

    def __init__(self, title, content, expanded=False, parent=None, level=0):
        super().__init__(parent)
        self.level = level
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14 if level else 0, 2 if level else 0, 0, 2 if level else 0)
        layout.setSpacing(0)
        self.header = QToolButton()
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(expanded)
        self.header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        # v2.7.12.14 — REVUE ÉCRAN (onglet Coupe 2D) : la politique
        # horizontale de QToolButton est Fixed (taille sizeHint) — les
        # titres « flottent » à moitié dans le panneau (barre bleue et
        # fond tronqués). En Expanding, le titre fait toute la largeur :
        # un vrai accordéon, lisible et cohérent partout (panneau coupes
        # ET historique de l'étape 4).
        self.header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if level == 0:
            self.header.setStyleSheet(f"""
                QToolButton {{
                    background: #EAF0F4; color: {COLORS['primary']};
                    border: none; border-left: 3px solid {COLORS['accent']};
                    border-bottom: 1px solid {COLORS['border_dark']};
                    padding: 8px 7px; font-size: 9pt; font-weight: bold;
                    text-align: left;
                }}
            """)
        else:
            self.header.setStyleSheet(f"""
                QToolButton {{
                    background: #F7F9F9; color: {COLORS['text_medium']};
                    border: 1px solid {COLORS['border']};
                    padding: 5px 6px; font-size: 8pt; font-weight: normal;
                    text-align: left;
                }}
            """)
        self.content = content
        self.content.setVisible(expanded)
        self.header.toggled.connect(self._toggle)
        layout.addWidget(self.header)
        # v2.7.12.13 — le contenu absorbe l'espace restant : à l'étape 4
        # (sans défilement) la table d'historique remplit l'étape ; dans
        # les panneaux (sous QScrollArea) aucun effet, la hauteur reste
        # la sizeHint.
        layout.addWidget(self.content, 1)

    def _toggle(self, expanded):
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.content.setVisible(expanded)
        # v2.7.12.14 — REVUE ÉCRAN (onglet Coupe 2D) : changer la
        # visibilité change la sizeHint du groupe — sans
        # updateGeometry(), Qt ne re-propage PAS la nouvelle taille :
        # le panneau gardait la hauteur dépliée et chaque groupe replié
        # réservait son espace fantôme (les grands vides entre les
        # titres constatés à l'écran).
        self.updateGeometry()



class _PatternPolygonItem(QGraphicsPolygonItem):
    """v2.9.28 — polygone hachuré SANS antialiasing.

    Les motifs Qt (FDiag, Dense…) sont des bitmaps 1-bit : l'AA du
    QGraphicsView les floute en « gratté pixelisé ».  On coupe l'AA
    uniquement pour cet item ; le reste de la scène garde l'AA.
    """

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        super().paint(painter, option, widget)
        painter.restore()


class _ClippedStrokeItem(QGraphicsPolygonItem):
    """v2.9.29 — traits de motif clipés au polygone, AA off, ≥2 traits."""

    def __init__(self, poly, strokes_path, pen, parent=None):
        super().__init__(poly, parent)
        self._strokes = strokes_path
        self._pen = pen
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(Qt.NoBrush))

    def paint(self, painter, option, widget=None):
        # v2.9.30 — NE PAS passer un QPolygon à setClipRegion (TypeError
        # sous PyQt6 / QGIS 3.44 : attend un QRegion).  setClipPath avec
        # QPainterPath est le chemin portable et précis.
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        try:
            from qgis.PyQt.QtGui import QPainterPath, QRegion
            clip = QPainterPath()
            clip.addPolygon(self.polygon())
            painter.setClipPath(clip)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : paint", _exc)
            # repli : QRegion construit depuis le polygone (pas QPolygon nu)
            try:
                from qgis.PyQt.QtGui import QRegion
                painter.setClipRegion(QRegion(self.polygon().toPolygon()))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : paint", _exc)
                # pas de clip — traits un peu hors bande, mieux que crash
                pass
        painter.setPen(self._pen)
        painter.setBrush(QBrush(Qt.NoBrush))
        painter.drawPath(self._strokes)
        painter.restore()


class _ClippedFillItem(QGraphicsPolygonItem):
    """v2.9.80 — points / fills de motif clipés au polygone (pattern_engine)."""

    def __init__(self, poly, fill_path, ink_colour, parent=None):
        super().__init__(poly, parent)
        self._fill = fill_path
        self._ink = QColor(ink_colour)
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(Qt.NoBrush))

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        try:
            from qgis.PyQt.QtGui import QPainterPath
            clip = QPainterPath()
            clip.addPolygon(self.polygon())
            painter.setClipPath(clip)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : paint", _exc)
            # pas de clip — points un peu hors bande, mieux que crash
            pass
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(self._ink))
        painter.drawPath(self._fill)
        painter.restore()



class _StyledFillItem(QGraphicsPolygonItem):
    """DEPRECATED (audit 2.9.87) — non utilisé sur le chemin actif.

    Expérience v2.9.84 paint_style.  Rendu courant = _add_patterned_poly
    (brush Qt 2.9.33).  Ne pas réactiver sans décision produit.
    Conservé pour éviter de casser un import / test caché.
    """

    def __init__(self, poly, style_def, border_pen, axis_dx=0.0, axis_dy=1.0,
                 parent=None):
        super().__init__(poly, parent)
        self._style_def = style_def
        self._axis_dx = float(axis_dx)
        self._axis_dy = float(axis_dy)
        self.setPen(border_pen if border_pen is not None else QPen(Qt.NoPen))
        self.setBrush(QBrush(Qt.NoBrush))

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        try:
            from ..core.pattern_paint import paint_style
            poly = self.polygon()
            pts = [(float(poly.at(i).x()), float(poly.at(i).y()))
                   for i in range(poly.size())]
            paint_style(
                painter, self._style_def,
                polygon_points=pts,
                axis_dx=self._axis_dx,
                axis_dy=self._axis_dy,
                draw_underlay=True,
                draw_border=False,
            )
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : paint", _exc)
            c = QColor(getattr(self._style_def, "fill_color", None) or "#CCC")
            painter.setPen(QPen(Qt.NoPen))
            painter.setBrush(QBrush(c))
            painter.drawPolygon(self.polygon())
        if self.pen().style() != Qt.NoPen:
            painter.setPen(self.pen())
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawPolygon(self.polygon())
        painter.restore()


class SectionCanvas(QGraphicsView):
    hole_clicked = pyqtSignal(str)
    # v2.9.1 — rendu terminé : la légende se resynchronise avec ce qui
    # est réellement dessiné (ligne de sol, collets).
    rendered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 352 — APRÈS super().__init__ (la 351 appelait self.tr()
        # avant : RuntimeError « super-class __init__() never called »
        # au démarrage du dock).  Le geste « trou devant » annoncé.
        self.setToolTip(self.tr(
            "Double-clic sur un trou : le fait passer devant · "
            "clic droit : menu du trou"))
        # v2.9.28 — AA pour courbes/textes ; les hachures Qt (bitmaps)
        # sont dessinées SANS AA (sinon flou « gratté »).  SmoothPixmap
        # off pour ne pas interpoler les pastilles de motif.
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, False)
        # v2.9.13 — pan ÉVIDENT : glisser clic gauche = déplacer
        # (seuil 4 px pour ne pas voler le clic / le survol).
        # Au repos : flèche (viser micro-bandes + infobulles).
        # ScrollHandDrag permanent était trop agressif (main partout).
        self.setDragMode(QGraphicsView.NoDrag)
        self.viewport().setCursor(Qt.ArrowCursor)
        self._panning = False
        self._pan_last = None
        self._pan_press = None          # pos au press (seuil)
        self._pan_button = None
        # v2.9.179 — forages exclus par l'utilisateur (proposition
        # validée) : exclus = absents du résultat.
        self._excluded_hole_ids: set = set()
        # v2.9.135 — FullViewportUpdate repeignait TOUTE la vue à chaque
        # item (lent dès que la coupe a beaucoup de bandes).
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        # v2.7.13.1 — REVUE ÉCRAN : « les bulles d'info sur la coupe,
        # c'est du blanc sur du blanc ». Le canvas a sa PROPRE feuille de
        # style : en Qt, un widget stylé en propre COUPE le cascade des
        # ancêtres pour son sous-arbre — c'est donc le CONTEXTE de style
        # de toutes ses infobulles (bandes, codes, forages). Sans la règle
        # QToolTip ici, elles retombaient sur le thème QGIS (blanc sur
        # blanc). Architecture styles_qt.py : chaque contexte stylé porte
        # la règle TOOLTIP_STYLE.
        self.setStyleSheet(
            TOOLTIP_STYLE
            + f"background-color: {COLORS['bg_card']}; "
              f"border: 1px solid {COLORS['border']};")
        self.scene = QGraphicsScene(self)
        # v2.9.135 — NoIndex : le BSP se reconstruit à chaque addItem
        # (centaines/milliers de bandes). Scène surtout statique.
        try:
            self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : __init__", _exc)
            # enum Qt5/Qt6 selon QGIS
            pass
        self.setScene(self.scene)
        self._result: Optional[SectionResult] = None
        self._proj_cache = {}
        self._proj_cache_order = []
        self._rendering = False
        self._elems_cache = None
        self._elems_fp = None
        self._drillholes: list[DrillHole] = []
        self._line: Optional[SectionLine] = None
        self._hole_items: dict = {}
        # 359 — ordre EXPLICITE de superposition : premier = devant.
        # Le z de sélection (71) restait invisible dès qu'un redraw
        # passait derrière ; l'ordre vit ici et survit aux redraws.
        self._hole_z_order: list = []
        self._selected: Optional[str] = None
        self._interval_selection_items: list = []
        # v2.9.89 — légende → surbrillance (lot isolé, voir section dédiée)
        self._legend_band_registry: list = []  # (domain, code_norm, QPolygonF)
        # 350 — défaut : rien n'est estompé (rien ne s'applique à ce
        # qui n'a rien demandé) ; l'estompage est un choix explicite.
        self._legend_fade_enabled = False     # 349 : panneau
        # 355 — « trop de chevauchements, fatigant pour l'œil » :
        # mode confort = moins de décor (rappels, rims, 2× moins de
        # chiffres de profondeur).  Débrayable au panneau.
        self._comfort_mode = True
        self._legend_highlight_keys = set()   # 348 : MULTI
        # (domain, code_norm) — la surbrillance légende accepte
        # plusieurs codes (Ctrl+clic), pas un seul.
        self._legend_highlight_items: list = []
        self._show_grid = True
        self._show_elevation_values = True
        self._show_distance_values = True
        self._show_axis_titles = True
        self._grid_color = "#D5DBDB"
        self._grid_width = 0.7
        self._grid_style = "dash"
        self._grid_opacity = 70
        self._elevation_grid_step = 20.0  # v2.9.70 défaut 20 m
        self._distance_grid_step = 0.0
        self._axis_value_font_size = 7
        self._axis_value_color = "#7F8C8D"
        self._axis_value_bold = False
        self._axis_value_decimals = 0
        self._axis_title_font_size = 8
        self._axis_title_color = "#566573"
        self._axis_title_bold = True
        self._show_litho = True
        self._show_assays = True
        self._show_intercepts = True
        self._show_depth = True
        self._show_collar_labels = True
        self._show_collar_info = True
        self._depth_step = 20.0
        self._v_exag = 1.0
        self._buffer = 50.0
        self._buffer_mode = "collar"
        self._distance_unit = "m"
        self._element: Optional[str] = None
        # v2.9.92 — multi-teneurs (max 3) ; _element = premier (rétrocompat)
        self._assay_elements: list = []
        self._assay_element_palettes: dict = {}
        self._assay_scales: dict = {}  # element -> scale
        # v2.9.102 — règle de seuil (affichage) ; jamais dans sources
        self._threshold_rule: dict = {}
        self._threshold_rules: list = []  # v2.9.116 multi-règles
        self._threshold_outline_items: list = []
        # v2.9.114 — True pendant export PNG → pen plus fin (même fn dessin)
        self._outline_export_mode = False
        self._classification = "jenks"
        self._n_classes = 7
        self._manual_breaks = []
        # 370 — seuils manuels PAR ÉLÉMENT {code: [vals]} ("" = sans code)
        self._manual_breaks_by_elem = {}
        self._round_breaks = True
        self._scale_scope = "project"
        self._assay_palette = "grade"
        self._assay_opacity = 100
        self._assay_scale: Optional[dict] = None  # scale du 1er élément
        self._litho_styles = None
        self._collar_id_font_size = 8
        self._collar_info_font_size = 7
        self._collar_id_position = "top"
        self._collar_info_position = "top"
        self._collar_id_offset_x = 0.0
        self._collar_id_offset_y = 0.0
        self._collar_info_offset_x = 0.0
        self._collar_info_offset_y = 0.0
        self._collar_marker_size = 6.0
        self._shared_collar_tolerance = 0.1
        self._show_trajectory = True
        self._trajectory_color = "#393939"
        self._trajectory_width = 0.5
        self._depth_font_size = 6
        # v2.7.8.2 — « débord des graduations » : combien le barreau
        # dépasse au-delà de la litho (convention du barreau centré).
        # v2.7.8.3 — défauts renforcés : débord 8 px, épaisseur 1 px,
        # opacité 80 % (le trait porte visiblement son étiquette).
        # v2.7.11.4 — retour écran 21/08 : le barreau déborde de 3 px
        # (8 px mangeait trop de couloir).
        self._depth_tick_length = 2.0
        self._depth_tick_width = 1.0
        # v2.7.8.2 — opacité commune des traits et des chiffres.
        self._depth_opacity = 80
        self._depth_side = "left"
        # v2.7.7 — backbone de profondeur : étiquettes toutes les N
        # graduations (défaut 2 : graduations 10 m, étiquettes 20 m).
        self._depth_label_every = 2
        # v2.9.278 — retour écran : bandes litho « trop grosses/larges ».
        # La largeur était fixe à 17 px (indépendante de l'espacement des
        # trous et du zoom) → colonnes épaisses.  Défaut plus fin ; le
        # spinner « largeur de voie » permet toujours d'ajuster.
        self._litho_width = 10.0
        self._litho_opacity = 100
        # v2.7.2 — Altérations & Minéralisations (AM-01 à AM-03).
        # v2.8.0 — le spinner règle la largeur de VOIE (pas la piste :
        # la piste = nb voies observées × largeur de voie).
        # v2.9.128 — _show_alterations était avalé par un commentaire
        # cassé → crash à l'ouverture d'un projet (légende).
        self._show_alterations = True
        self._alter_width = LANE_WIDTH_PX
        self._alter_opacity = 80
        self._show_mineralizations = True
        # v2.8.0 — idem : largeur de voie par défaut.
        self._mineral_width = LANE_WIDTH_PX
        self._mineral_opacity = 80
        # v2.9.260 (étape 2) — piste des mesures de structure.
        self._show_structures = True
        self._structure_width = LANE_WIDTH_PX
        self._structure_opacity = 90
        self._structure_side = "right"
        self._structure_marker_size = 5.0
        # Densité (règle explicite étape 2) : espacement minimal des
        # pastilles en px le long de la piste ; sous cet espacement, les
        # mesures sont empilées dans la voie (pas de cluster qui masque
        # l'identité native), chaque infobulle/détail reste disponible.
        self._structure_min_spacing = 9.0
        # v2.9.262 (Chantier 2 E2) — piste « Imagerie ».
        self._show_imagery = True
        self._imagery_width = 10.0
        self._imagery_side = "right"
        self._imagery_opacity = 100
        # v2.9.264 — géotechnique : trois pistes cochables, rampe continue.
        from .section_geotech import init_geotech_defaults as _init_geotech
        _init_geotech(self)
        # v2.9.262 — fournisseur project (déposé par SectionWidget) pour
        # résoudre les chemins relatifs d'image sans logique dans le canvas.
        self.imagery_project_provider = None
        self.imagery_source_dir_provider = None
        self._imagery_source_dir = ""
        self._style_resolver = None
        self._style_cache = {}
        self._assay_max_width = 15.0
        self._assay_width_mode = "proportional"
        # v2.9.123 — unités par élément pour les libellés de piste (« Fe % »)
        self._assay_element_units: dict = {}
        # v2.7.7 — positions des pistes (AUDIT_V2.7.7.md) : teneurs à gauche,
        # altérations et minéralisations à droite ; offsets calculés par
        # core.track_layout.plan_tracks (auto-collapse).
        self._assay_side = "left"
        self._alter_side = "right"
        self._mineral_side = "right"
        self._track_plan = None
        # v2.7.8.3 — hachures alignées sur l'axe des forages (convention
        # log) ; décoché = motifs fixes à l'écran. Persisté par projet.
        # v2.7.9.6 — défaut décoché (décision écran).
        # v2.7.10.28 — « suivre la trajectoire » redevient le défaut
        # (décision écran du jour, qui annule v2.7.9.6).
        # v2.7.11.4 — retour écran 21/08 : motifs FIXES à l'écran par
        # défaut (décision « alignés sur l'axe » de la v2.7.10.28
        # renversée par l'utilisateur).
        self._patterns_follow_hole_axis = False  # v2.9.28 : option retirée
        self._show_orientation = True
        self._orientation_position = "auto"
        # v2.9.321 — cartouche « moins petite » : défaut 10 pt (était 9)
        self._orientation_font_size = 10
        # v2.9.321 — commentaire libre imprimé dans le cartouche
        self._orientation_note = ""
        # v2.9.321 — cadrage carte en plan (export) : slider + glisser
        self._locator_zoom = 1.0
        self._locator_off = (0.0, 0.0)
        self._show_scale_bar = True
        self._scale_position = "auto"
        self._scale_size = "medium"
        self._margin_left = 96.0
        self._margin_right = 70.0
        self._margin_top = 70.0
        self._margin_bottom = 135.0
        self._sx = 1.0
        self._sy = 1.0
        # 386 — export À L'ÉCHELLE : px scène / unité imposé (None = écran).
        self._fixed_sx = None
        self._scale_ratio_text = ""
        self._content_left = 0.0
        self._content_top = 0.0
        # v2.9.0 — topographie : profil de sol (along, elev) ancré aux
        # collets, sa source ("dem" | "csv" | "collars") et son infobulle.
        self._surface = None
        self._surface_source = ""
        self._surface_tooltip = ""
        self._surface_color = "#8B6F52"
        self._show_surface = True
        # Le widget fournit le profil à chaque régénération (la surface
        # dépend de la ligne, du buffer et du choix de source — jamais
        # d'état en cache).  None en test/hors widget : pas de surface.
        self.surface_provider = None

    # ------------------------------------------------------------------
    # Data & parameters
    # ------------------------------------------------------------------
    def set_data(self, drillholes, line, buffer, v_exag, element=None,
                 buffer_mode="collar"):
        self._drillholes = drillholes
        self._line = line
        self._buffer = buffer
        self._buffer_mode = buffer_mode
        self._v_exag = v_exag
        # v2.9.92 fix — ne PAS écraser _assay_elements multi déjà posés
        # par _generate_and_display / update_params.  element = 1er seulement
        # (rétrocompat) ; si multi vide, dériver de element.
        if element is not None:
            self._element = element
        existing = multi_assay_mod.normalize_elements(
            getattr(self, "_assay_elements", None) or [])
        if existing:
            # garder multi ; aligner _element sur le 1er
            self._assay_elements = existing
            self._element = existing[0]
        elif element:
            self._assay_elements = multi_assay_mod.normalize_elements([element])
            self._element = element
        self._regenerate()

    def update_params(self, buffer=None, v_exag=None, element=None,
                      classification=None, n_classes=None,
                      manual_breaks=None, scale_scope=None, palette=None,
                      buffer_mode=None, round_breaks=None,
                      threshold_rule=None,
                      threshold_rules=None,
                      elements=None, element_palettes=None,
                      excluded_hole_ids=None):  # v2.9.179
        need_recompute = False
        need_rescale = False
        need_rerender = False
        if buffer is not None and buffer != self._buffer:
            self._buffer = buffer
            need_recompute = True
        if buffer_mode is not None and buffer_mode != self._buffer_mode:
            self._buffer_mode = buffer_mode
            need_recompute = True
        if excluded_hole_ids is not None:
            ids = {str(h) for h in (excluded_hole_ids or []) if h}
            if ids != set(self._excluded_hole_ids or set()):
                self._excluded_hole_ids = ids
                need_recompute = True
        if v_exag is not None and v_exag != self._v_exag:
            self._v_exag = v_exag
            need_rerender = True
        if elements is not None:
            elems = multi_assay_mod.normalize_elements(elements)
            if elems != list(self._assay_elements or []):
                self._assay_elements = elems
                self._element = elems[0] if elems else None
                need_rescale = True
        elif element is not None and element != self._element:
            self._element = element
            self._assay_elements = multi_assay_mod.normalize_elements(
                [element] if element else [])
            need_rescale = True
        if element_palettes is not None:
            pals = dict(element_palettes or {})
            if pals != dict(self._assay_element_palettes or {}):
                self._assay_element_palettes = pals
                need_rerender = True
        if classification is not None and classification != self._classification:
            self._classification = classification
            need_rescale = True
        if n_classes is not None and n_classes != self._n_classes:
            self._n_classes = int(n_classes)
            need_rescale = True
        if manual_breaks is not None:
            if isinstance(manual_breaks, dict):
                by = {str(k): sorted(set(float(v) for v in (vs or [])))
                      for k, vs in (manual_breaks or {}).items() if vs}
                if by != getattr(self, "_manual_breaks_by_elem", {}):
                    self._manual_breaks_by_elem = by
                    need_rescale = True
                lst = list(by.get(self._element or "") or by.get("") or [])
            else:
                lst = list(manual_breaks)
            if lst != self._manual_breaks:
                self._manual_breaks = lst
                need_rescale = True
        if round_breaks is not None and bool(round_breaks) != self._round_breaks:
            self._round_breaks = bool(round_breaks)
            need_rescale = True
        if scale_scope is not None and scale_scope != self._scale_scope:
            self._scale_scope = scale_scope
            need_rescale = True
        if palette is not None and palette != self._assay_palette:
            self._assay_palette = palette
            need_rerender = True
        # v2.9.116 — multi-règles prioritaire ; threshold_rule = miroir
        if threshold_rules is not None:
            nr_list = threshold_rule_mod.normalize_rules(threshold_rules)
            cur = threshold_rule_mod.normalize_rules(
                getattr(self, "_threshold_rules", None) or [])
            if nr_list != cur:
                self._threshold_rules = nr_list
                mig = threshold_rule_mod.migrate_threshold_payload({
                    "threshold_rules": nr_list})
                self._threshold_rule = mig.get("threshold_rule") or {}
                need_rerender = True
        elif threshold_rule is not None:
            nr = threshold_rule_mod.normalize_rule(threshold_rule)
            if nr != threshold_rule_mod.normalize_rule(
                    getattr(self, "_threshold_rule", None)):
                self._threshold_rule = nr
                self._threshold_rules = threshold_rule_mod.normalize_rules([nr])
                need_rerender = True
        if need_recompute and self._drillholes and self._line:
            self._regenerate()
        elif need_rescale and self._result:
            self._compute_assay_scale()
            self._render()
        elif need_rerender and self._result:
            self._render()
    def set_visibility(self, litho, assays, depth, collars=True, grid=True):
        self._show_litho = litho
        self._show_assays = assays
        self._show_depth = depth
        self._show_collar_labels = collars
        self._show_grid = grid
        if self._result:
            self._render()

    def set_display_style(self, **style):
        """Apply annotation/layer properties and redraw without regeneration."""
        mapping = {
            "show_grid": "_show_grid",
            "show_elevation_values": "_show_elevation_values",
            "show_distance_values": "_show_distance_values",
            "show_axis_titles": "_show_axis_titles",
            "grid_color": "_grid_color",
            "grid_width": "_grid_width",
            "grid_style": "_grid_style",
            "grid_opacity": "_grid_opacity",
            "elevation_grid_step": "_elevation_grid_step",
            "distance_grid_step": "_distance_grid_step",
            "axis_value_font_size": "_axis_value_font_size",
            "axis_value_color": "_axis_value_color",
            "axis_value_bold": "_axis_value_bold",
            "axis_value_decimals": "_axis_value_decimals",
            "axis_title_font_size": "_axis_title_font_size",
            "axis_title_color": "_axis_title_color",
            "axis_title_bold": "_axis_title_bold",
            "show_collar_labels": "_show_collar_labels",
            "show_collar_info": "_show_collar_info",
            "collar_id_font_size": "_collar_id_font_size",
            "collar_info_font_size": "_collar_info_font_size",
            "collar_id_position": "_collar_id_position",
            "collar_info_position": "_collar_info_position",
            "collar_id_offset_x": "_collar_id_offset_x",
            "collar_id_offset_y": "_collar_id_offset_y",
            "collar_info_offset_x": "_collar_info_offset_x",
            "collar_info_offset_y": "_collar_info_offset_y",
            "collar_marker_size": "_collar_marker_size",
            "shared_collar_tolerance": "_shared_collar_tolerance",
            "show_trajectory": "_show_trajectory",
            "trajectory_color": "_trajectory_color",
            "trajectory_width": "_trajectory_width",
            "show_depth": "_show_depth",
            "depth_step": "_depth_step",
            "depth_label_every": "_depth_label_every",
            "depth_font_size": "_depth_font_size",
            "depth_tick_length": "_depth_tick_length",
            "depth_tick_width": "_depth_tick_width",
            "depth_opacity": "_depth_opacity",
            "depth_side": "_depth_side",
            "show_litho": "_show_litho",
            "litho_width": "_litho_width",
            "litho_opacity": "_litho_opacity",
            "patterns_follow_hole_axis": "_patterns_follow_hole_axis",
            "show_alterations": "_show_alterations",
            "alter_width": "_alter_width",
            "alter_opacity": "_alter_opacity",
            "alter_side": "_alter_side",
            "show_mineralizations": "_show_mineralizations",
            "mineral_width": "_mineral_width",
            "mineral_opacity": "_mineral_opacity",
            "mineral_side": "_mineral_side",
            "show_structures": "_show_structures",
            "structure_width": "_structure_width",
            "structure_opacity": "_structure_opacity",
            "structure_side": "_structure_side",
            "structure_marker_size": "_structure_marker_size",
            "structure_min_spacing": "_structure_min_spacing",
            "show_imagery": "_show_imagery",
            "imagery_width": "_imagery_width",
            "imagery_side": "_imagery_side",
            "imagery_opacity": "_imagery_opacity",
            "show_assays": "_show_assays",
            "show_intercepts": "_show_intercepts",
            "assay_opacity": "_assay_opacity",
            "assay_max_width": "_assay_max_width",
            "assay_width_mode": "_assay_width_mode",
            "assay_side": "_assay_side",
            "show_orientation": "_show_orientation",
            "orientation_position": "_orientation_position",
            "orientation_font_size": "_orientation_font_size",
            "orientation_note": "_orientation_note",
            "show_scale_bar": "_show_scale_bar",
            "scale_position": "_scale_position",
            "scale_size": "_scale_size",
            "show_surface": "_show_surface",
            "surface_color": "_surface_color",
        }
        from .section_geotech import geotech_display_attrs
        mapping.update(geotech_display_attrs())
        redraw = bool(style.pop("redraw", True))
        changed = False
        for key, value in style.items():
            attr = mapping.get(key)
            if not attr:
                continue
            if getattr(self, attr, None) != value:
                setattr(self, attr, value)
                changed = True
        if redraw and changed and self._result:
            self._render()

    def set_depth_step(self, step):
        self._depth_step = step
        if self._result:
            self._render()


    # ==================================================================
    # v2.9.89/90 — LÉGENDE → SURBRILLANCE COUPE (lot isolé)
    # ------------------------------------------------------------------
    # Clic item légende panneau (litho / altéro / miné / symboles) →
    # contour pointillé cyan des géométries matchées.
    # Simple sélection ; re-clic = clear ; autre = remplace.
    # JAMAIS dans l'export PNG.  Pas d'édition symbole (RENDU-07).
    # Couleur : SELECTION_HIGHLIGHT_COLOR uniquement (module-level).
    # ==================================================================

    @staticmethod
    def _legend_norm_code(code) -> str:
        return str(code or "").strip().casefold()

    def _legend_register_band(self, domain: str, code, poly,
                              fill=None) -> None:
        """Enregistre un polygone de bande pour la surbrillance légende.
        342 : fill = couleur d'origine de la bande — la surbrillance la
        REDESSINE au-dessus des chevauchements."""
        self._legend_register_geom(domain, code, "poly", poly, fill)

    def _legend_register_geom(self, domain: str, code, kind: str, payload,
                              fill=None) -> None:
        """Enregistre une géométrie (poly | path | ellipse) sélectionnable."""
        d = str(domain or "").strip()
        c = self._legend_norm_code(code)
        if not d or not c or payload is None:
            return
        kind = str(kind or "poly")
        try:
            if kind == "poly":
                poly_copy = QPolygonF(payload)
                if poly_copy.isEmpty():
                    return
                payload = poly_copy
            elif kind == "path":
                # QPainterPath — copie
                path = QPainterPath(payload)
                if path.isEmpty():
                    return
                payload = path
            elif kind == "ellipse":
                # payload = (cx, cy, radius)
                cx, cy, radius = payload
                payload = (float(cx), float(cy), float(radius))
            else:
                return
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Légende : _legend_register_geom", _exc)
            # géométrie invalide — ignorer
            return
        self._legend_band_registry.append((d, c, kind, payload, fill))

    def legend_highlight_keys(self):
        """348 — ensemble des clés (domain, code_norm) en exergue."""
        return set(self._legend_highlight_keys)

    def legend_highlight_key(self):
        """Compat : première clé ou None."""
        return next(iter(self._legend_highlight_keys), None)

    def set_legend_highlight(self, domain: str, code: str) -> None:
        """Active la surbrillance pour UN code (remplace tout)."""
        d = str(domain or "").strip()
        c = self._legend_norm_code(code)
        if not d or not c:
            self.clear_legend_highlight()
            return
        self._legend_highlight_keys = {(d, c)}
        self._legend_highlight_apply()

    def toggle_legend_highlight(self, domain: str, code: str) -> None:
        """348 — Ctrl+clic : ajoute/retire un code à l'exergue."""
        d = str(domain or "").strip()
        c = self._legend_norm_code(code)
        if not d or not c:
            return
        key = (d, c)
        if key in self._legend_highlight_keys:
            self._legend_highlight_keys.discard(key)
        else:
            self._legend_highlight_keys.add(key)
        self._legend_highlight_apply()

    def clear_legend_highlight(self) -> None:
        """Désélectionne (retire contours + estompage)."""
        self._legend_highlight_keys = set()
        self._legend_highlight_clear_items()
        self._legend_fade_apply()

    def _legend_highlight_clear_items(self) -> None:
        for item in list(self._legend_highlight_items):
            try:
                if item.scene() is self.scene:
                    self.scene.removeItem(item)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Légende : _legend_highlight_clear_items", _exc)
                # item déjà retiré (rebuild scène)
                pass
        self._legend_highlight_items = []

    def _draw_selection_outline(self, kind, payload, *, z_value=80.0,
                                tooltip: str = "",
                                color: str = None):
        """UNIQUE dessin de contour de surbrillance (dock + export PNG).

        v2.9.102 — une seule fonction pour légende-highlight ET règle de
        seuil.

        v2.9.103+ — trait EXTERIEUR latéral + fill none ; pointillé.

        v2.9.105 — kind "path" (ligne de sol, trajectoire) : path direct
        (pas de tube offset).

        v2.9.106/107 — gap latéral 0.35 px ; inset From/To ~1.0 px
        (anti-débord voisins).  Dock == export (même fonction).

        v2.9.108+ — multi-litho OU ; pen non-cosmetic (v2.9.112).
        v2.9.113/114 — largeur selon contexte :
          dock   = SELECTION_OUTLINE_PEN_DOCK (1.85, lisible à l'écran)
          export = SELECTION_OUTLINE_PEN_EXPORT (0.9, net en PNG HD)
        v2.9.116 — ``color`` optionnelle (multi-règles Fe cyan / Cu magenta) ;
          défaut = SELECTION_HIGHLIGHT_COLOR (légende HL reste cyan).
        Une seule fonction ; le mode export bascule la largeur.
        Retourne l'item scène ou None.
        """
        # Stroke only, non-cosmetic (unités scène). Largeur dock ≠ export.
        if getattr(self, "_outline_export_mode", False):
            pen_w = float(SELECTION_OUTLINE_PEN_EXPORT)
        else:
            pen_w = float(SELECTION_OUTLINE_PEN_DOCK)
        gap = 0.3  # extérieur latéral serré (anti-débord + moins d'encre)
        depth_inset = 1.0  # rentre From/To avant expand → moins d'empiètement voisins
        pen = _selection_highlight_pen(pen_w, color=color)
        # v2.9.121 — halo sombre IDENTIQUE pour cyan / magenta / ambre
        # (dock + export) : les 3 couleurs restent lisibles sur toute rampe.
        halo_pen = _selection_highlight_pen(pen_w + 0.55, color="#1A252F")
        no_fill = QBrush(Qt.NoBrush)
        item = None
        halo_item = None
        try:
            if kind == "poly":
                outline = self._exterior_outline_path_from_poly(
                    payload, gap=gap, pen_w=pen_w, depth_inset=depth_inset)
                if outline is not None and not outline.isEmpty():
                    halo_item = self.scene.addPath(outline, halo_pen, no_fill)
                    item = self.scene.addPath(outline, pen, no_fill)
                else:
                    # repli : polygone brut (mieux que rien)
                    halo_item = self.scene.addPolygon(payload, halo_pen, no_fill)
                    item = self.scene.addPolygon(payload, pen, no_fill)
            elif kind == "path":
                # Polyligne ouverte (surface / trajectoire) : path tel quel.
                halo_item = self.scene.addPath(payload, halo_pen, no_fill)
                item = self.scene.addPath(payload, pen, no_fill)
            elif kind == "ellipse":
                cx, cy, radius = payload
                expand = float(gap) + float(pen_w) * 0.5
                r = max(float(radius) + expand, 4.0)
                halo_item = self.scene.addEllipse(
                    cx - r, cy - r, 2 * r, 2 * r, halo_pen, no_fill)
                item = self.scene.addEllipse(
                    cx - r, cy - r, 2 * r, 2 * r, pen, no_fill)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("État/sélection : _draw_selection_outline", _exc)
            # géométrie hors scène / stroker indisponible
            item = None
        if item is None:
            return None
        if halo_item is not None:
            try:
                halo_item.setParentItem(item)
                halo_item.setAcceptedMouseButtons(Qt.NoButton)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("État/sélection : _draw_selection_outline", _exc)
                # parentage optionnel — halo orphelin mieux que crash
                pass
        item.setZValue(float(z_value))
        item.setAcceptedMouseButtons(Qt.NoButton)
        try:
            item.setFlag(item.GraphicsItemFlag.ItemIsSelectable, False)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("État/sélection : _draw_selection_outline", _exc)
            # flag API varie selon PyQt/bindings
            pass
        if tooltip:
            try:
                item.setToolTip(str(tooltip))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("État/sélection : _draw_selection_outline", _exc)
                # tooltip optionnel
                pass
        return item

    @staticmethod
    def _inset_band_depth_ends(poly, inset: float = 1.0):
        """Rentre les bords From/To d'une bande trapèze (anti-débord voisins).

        Winding historique band_trapezoid :
        [top_inner, top_outer, bottom_outer, bottom_inner].
        Les côtés latéraux (inner/outer) restent ; seuls les bouts
        profondeur sont décalés vers l'intérieur avant l'expand extérieur.
        """
        if poly is None or inset <= 0:
            return poly
        try:
            n = int(poly.size()) if hasattr(poly, "size") else len(poly)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste lithologie : _inset_band_depth_ends", _exc)
            return poly
        if n < 4:
            return poly
        try:
            pts = [poly.at(i) for i in range(n)]
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste lithologie : _inset_band_depth_ends", _exc)
            try:
                pts = list(poly)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Piste lithologie : _inset_band_depth_ends", _exc)
                return poly
        ti, to, bo, bi = pts[0], pts[1], pts[2], pts[3]
        mid_tx = 0.5 * (float(ti.x()) + float(to.x()))
        mid_ty = 0.5 * (float(ti.y()) + float(to.y()))
        mid_bx = 0.5 * (float(bi.x()) + float(bo.x()))
        mid_by = 0.5 * (float(bi.y()) + float(bo.y()))
        dx = mid_bx - mid_tx
        dy = mid_by - mid_ty
        length = math.hypot(dx, dy)
        if length < 1e-6:
            return poly
        # bande trop courte : inset proportionnel (ne pas inverser)
        max_in = max(0.0, 0.35 * length)
        ins = min(float(inset), max_in)
        if ins <= 1e-9:
            return poly
        ux, uy = dx / length, dy / length

        def _mv(p, s):
            return QPointF(float(p.x()) + ux * s, float(p.y()) + uy * s)

        new_pts = [_mv(ti, ins), _mv(to, ins), _mv(bo, -ins), _mv(bi, -ins)]
        for extra in pts[4:]:
            new_pts.append(extra)
        try:
            return QPolygonF(new_pts)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste lithologie : _inset_band_depth_ends", _exc)
            return poly

    @staticmethod
    def _exterior_outline_path_from_poly(poly, *, gap: float = 0.35,
                                         pen_w: float = 1.5,
                                         depth_inset: float = 1.0):
        """Contour extérieur autour d'un QPolygonF (bandes litho / teneurs).

        v2.9.107 — inset From/To puis expand latéral : le trait ne mange
        plus les intervalles voisins en profondeur.
        """
        if poly is None:
            return None
        try:
            poly2 = SectionCanvas._inset_band_depth_ends(
                poly, inset=float(depth_inset))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _exterior_outline_path_from_poly", _exc)
            # inset optionnel
            poly2 = poly
        path = QPainterPath()
        try:
            path.addPolygon(poly2 if poly2 is not None else poly)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _exterior_outline_path_from_poly", _exc)
            # poly invalide
            return None
        return SectionCanvas._exterior_outline_path(
            path, gap=gap, pen_w=pen_w)

    @staticmethod
    def _exterior_outline_path(path, *, gap: float = 0.35,
                               pen_w: float = 1.5):
        """Élargit un QPainterPath vers l'extérieur (gap + demi-trait).

        Le chemin retourné est la région élargie : le stroke du pen est
        centré sur son contour extérieur → le trait reste hors de la
        bande (gap libre latéral). Fill = none à l'appelant.
        """
        if path is None:
            return None
        try:
            src = QPainterPath(path)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _exterior_outline_path", _exc)
            # copie path impossible
            return None
        if src.isEmpty():
            return None
        # expand jusqu'au centre du trait = gap + pen_w/2
        expand = max(float(gap) + float(pen_w) * 0.5, 0.35)
        try:
            stroker = QPainterPathStroker()
            stroker.setWidth(expand * 2.0)
            stroker.setJoinStyle(Qt.MiterJoin)
            stroker.setCapStyle(Qt.FlatCap)
            rim = stroker.createStroke(src)
            outer = src.united(rim)
            if outer is None or outer.isEmpty():
                return src
            return outer
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _exterior_outline_path", _exc)
            # stroker indisponible — pas d'offset
            return src

    # 348 — opacité des bandes NON en exergue quand un exergue est
    # actif : le reste s'estompe, l'interprétation ressort.
    LEGEND_FADE_OPACITY = 0.35

    def _legend_fade_apply(self) -> None:
        """348 : estompe les bandes hors exergue (1.0 sinon)."""
        keys = self._legend_highlight_keys
        for items in self._hole_items.values():
            for item in items:
                if not getattr(item, "_is_band", False):
                    continue
                try:
                    if not keys or not self._legend_fade_enabled:
                        item.setOpacity(1.0)
                        continue
                    tags = getattr(item, "_legend_tags", None) or []
                    item.setOpacity(
                        1.0 if any(t in keys for t in tags)
                        else self.LEGEND_FADE_OPACITY)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Légende : estompage", _exc)

    def _legend_highlight_apply(self) -> None:
        """348 — surbrillance pour TOUTES les clés en exergue."""
        self._legend_highlight_clear_items()
        keys = self._legend_highlight_keys
        if not keys or not self._legend_band_registry:
            self._legend_fade_apply()
            return
        for entry in self._legend_band_registry:
            # 343 — compat 3/4/5 champs (le 5e = couleur d'origine,
            # ajoutée en 342 ; l'unpack 4 champs crashait dessus).
            d, c = entry[0], entry[1]
            if len(entry) == 3:
                kind, payload, fill = "poly", entry[2], None
            elif len(entry) == 4:
                kind, payload, fill = entry[2], entry[3], None
            else:
                kind, payload, fill = entry[2], entry[3], entry[4]
            if (d, c) not in keys:
                continue
            # 342 — « peg sélectionné sur trou 5, on ne le voit pas à
            # cause du chevauchement » : la bande sélectionnée est
            # REDESSINÉE au-dessus de TOUS les forages (z 79) avec sa
            # couleur d'origine, avant le contour pointillé (z 80).
            if kind == "poly" and fill is not None:
                try:
                    top = self.scene.addPolygon(
                        payload, QPen(Qt.NoPen), QBrush(fill))
                    top.setZValue(79.0)
                    top.setAcceptedMouseButtons(Qt.NoButton)
                    self._legend_highlight_items.append(top)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Légende : bande au-dessus", _exc)
            item = self._draw_selection_outline(
                kind, payload, z_value=80.0, color=LEGEND_CLICK_COLOR)
            if item is not None:
                self._legend_highlight_items.append(item)
        self._legend_fade_apply()

    def fade_opacity_for_export(self, suppress: bool):
        """348 : neutralise/rétablit l'estompage pendant l'export."""
        if suppress:
            for items in self._hole_items.values():
                for item in items:
                    if getattr(item, "_is_band", False):
                        try:
                            item.setOpacity(1.0)
                        except Exception as _exc:
                            from ..core.diagnostics import log_swallowed
                            log_swallowed("Export : estompage off", _exc)
        else:
            self._legend_fade_apply()

    def hide_legend_highlight_for_export(self):
        """Masque la surbrillance pendant l'export PNG. Retourne l'état."""
        key = self.legend_highlight_key()
        items_state = []
        for item in self._legend_highlight_items:
            try:
                items_state.append((item, item.isVisible()))
                item.setVisible(False)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export : hide_legend_highlight_for_export", _exc)
                # item déjà détruit (rebuild scène pendant export)
                pass
        return key, items_state

    def restore_legend_highlight_after_export(self, state) -> None:
        """Restaure la surbrillance après export PNG."""
        if not state:
            return
        _key, items_state = state
        for item, was_visible in items_state:
            try:
                item.setVisible(bool(was_visible))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export : restore_legend_highlight_after_export", _exc)
                # item déjà détruit — ignore
                pass

    def set_outline_export_mode(self, enabled: bool) -> None:
        """Bascule largeur contour seuil/légende pour export PNG.

        v2.9.114 — dock 1.85 / export 0.9 (même _draw_selection_outline).
        Re-applique les contours pour que le pen prenne effet avant render.
        """
        on = bool(enabled)
        if bool(getattr(self, "_outline_export_mode", False)) == on:
            return
        self._outline_export_mode = on
        if self._result is None:
            return
        try:
            self._legend_highlight_apply()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : set_outline_export_mode", _exc)
            # légende HL optionnelle
            pass
        # v2.9.122 — intercepts = aplats identiques dock/export (pas de re-pen)

    # ==================================================================
    # fin lot v2.9.89/90 légende → surbrillance
    # ==================================================================


    def set_threshold_rule(self, rule: dict) -> None:
        """Règle unique (rétrocompat) → multi via set_threshold_rules."""
        self.set_threshold_rules([rule] if rule else [])

    def set_threshold_rules(self, rules) -> None:
        """Multi-règles de seuil (affichage only). Max 3, couleurs de slot."""
        nr_list = threshold_rule_mod.normalize_rules(rules)
        self._threshold_rules = nr_list
        mig = threshold_rule_mod.migrate_threshold_payload({
            "threshold_rules": nr_list})
        self._threshold_rule = mig.get("threshold_rule") or {}
        if self._result is not None:
            # v2.9.122 — largeur de piste intercepts change → replan
            self._render()

    def _clear_threshold_outlines(self) -> None:
        for item in list(getattr(self, "_threshold_outline_items", []) or []):
            try:
                if item.scene() is self.scene:
                    self.scene.removeItem(item)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Intercepts/seuils : _clear_threshold_outlines", _exc)
                # item déjà retiré (rebuild scène)
                pass
        self._threshold_outline_items = []

    def _draw_intercept_track(self, sr=None) -> None:
        """v2.9.122 — SEUL dessin des matches de seuil (piste dédiée).

        Dock et export : même fonction (aplats, pas de pen dock/export).
        Apparition gérée par le plan de pistes (règle ON), pas par les matchs.
        """
        self._apply_threshold_outlines()

    def _apply_threshold_outlines(self) -> None:
        """Blocs intercepts (une colonne par règle active).

        v2.9.122 — plus de contour sur les teneurs / litho.
        v2.9.104 — matchs adjacents → un bloc/groupe.
        v2.9.116 — itère threshold_rules (max 3) ; couleur par slot.
        """
        self._clear_threshold_outlines()
        rules = threshold_rule_mod.active_rules(
            getattr(self, "_threshold_rules", None)
            or ([getattr(self, "_threshold_rule", None)]
                if getattr(self, "_threshold_rule", None) else []))
        if not rules:
            return
        if not self._result or not self._track_plan:
            return
        lane = self._track_plan.by_key.get("intercepts")
        if lane is None:
            return
        slots = threshold_rule_mod.intercept_slot_layout(
            len(rules), float(lane.inner_edge), float(lane.width),
            side=lane.side)
        if not slots:
            return
        hole_by_id = {str(ph.hole_id): ph for ph in self._result.holes}
        # v2.9.124 — plus de gutter gris (halo le long des teneurs).
        # Piste réservée dans le layout ; seuls les blocs colorés se voient.

        for rule_idx, (rule, slot) in enumerate(zip(rules, slots)):
            self._apply_one_threshold_rule(
                rule, rule_idx=rule_idx, slot=slot, hole_by_id=hole_by_id)

    def _apply_one_threshold_rule(
            self, rule, *, rule_idx=0, slot=None, hole_by_id=None,
            elems=None, subs=None, scales=None, bars_mode=False,
            sign=1.0, unit=""):
        """Dessine les blocs d'UNE règle sur SA colonne intercepts."""
        rule_n = threshold_rule_mod.normalize_rule(rule, slot_index=rule_idx)
        color = rule_n.get("color") or SELECTION_HIGHLIGHT_COLOR
        cname = rule_n.get("color_name") or "cyan"
        clause_elems = []
        for cl in (rule_n.get("clauses") or []):
            el = str(cl.get("element") or "").strip()
            if el and el not in clause_elems:
                clause_elems.append(el)
        if not clause_elems:
            return
        if not slot:
            return
        hole_by_id = hole_by_id or {}
        off_inner = float(slot["inner"])
        off_outer = float(slot["outer"])
        matches = []
        for ph in self._result.holes:
            for iv in ph.assays:
                attrs = dict(getattr(iv, "attributes", None) or {})
                if not threshold_rule_mod.interval_matches(
                        rule_n, attributes=attrs, hole=ph,
                        from_depth=float(iv.from_depth),
                        to_depth=float(iv.to_depth)):
                    continue
                matches.append({
                    "hole_id": str(ph.hole_id),
                    "element": f"rule{int(rule_idx)}",
                    "from_depth": float(iv.from_depth),
                    "to_depth": float(iv.to_depth),
                    "value": attrs.get(clause_elems[0]),
                    "attributes": attrs,
                    "off_inner": off_inner,
                    "off_outer": off_outer,
                })

        groups = threshold_rule_mod.group_contiguous_matches(matches)
        z_base = 4.6 + 0.05 * float(rule_idx)
        block_pen = QPen(
            QColor(threshold_rule_mod.INTERCEPT_BLOCK_STROKE), 0.45)
        fill = QColor(str(color))
        for group in groups:
            if not group:
                continue
            ph = hole_by_id.get(str(group[0].get("hole_id")))
            if ph is None:
                continue
            elem = clause_elems[0] if clause_elems else ""
            g_from = min(float(m["from_depth"]) for m in group)
            g_to = max(float(m["to_depth"]) for m in group)
            poly = self._band_poly(ph, g_from, g_to, off_inner, off_outer)
            if poly is None:
                continue

            if len(group) == 1:
                m0 = group[0]
                tip_core = threshold_rule_mod.explain_match(
                    rule_n, attributes=m0.get("attributes") or {},
                    element=elem,
                    value=float(m0["value"]) if m0.get("value") is not None else 0.0,
                    unit=unit)
                tip = (
                    f"{ph.hole_id} · {m0['from_depth']:g}–"
                    f"{m0['to_depth']:g} m\n[{cname}] {tip_core}")
            else:
                tip_core = threshold_rule_mod.legend_label(
                    rule_n, color_name=cname, units={})
                tip = (
                    f"{ph.hole_id} · {g_from:g}–{g_to:g} m\n"
                    f"{len(group)} intervalles · {tip_core or elem}")

            item = self.scene.addPolygon(poly, block_pen, QBrush(fill))
            if item is None:
                continue
            item.setZValue(z_base)
            try:
                item.setAcceptedMouseButtons(Qt.NoButton)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Intercepts/seuils : _apply_one_threshold_rule", _exc)
                # flag souris optionnel
                pass
            try:
                item.setToolTip(str(tip))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Intercepts/seuils : _apply_one_threshold_rule", _exc)
                # tooltip optionnel
                pass
            self._threshold_outline_items.append(item)
            # v2.9.124 — pas de hit-pad (halo) autour des blocs intercepts.


    # 344 — le trou sélectionné passe DEVANT tous les autres :
    # aux chevauchements, ses bandes/tennes/étiquettes restent
    # lisibles (retour écran : « 9 domine sur 05, or les infos de 05
    # doivent être sur le 9 sinon 9 cache ça »).
    # 353 — « bring to front » doit VRAIMENT passer devant : +71
    # (bandes ≈ 75) au lieu de +60 (64), car à 64 les TENEURS de
    # l'autre trou (z 70, règle 345) recouvraient encore la litho du
    # trou mis devant au croisement.  75 > 70 (teneurs) et < 79/80
    # (exergue légende).  Sans sélection : règle 345 intacte
    # (teneurs au-dessus des bandes).
    SELECTED_HOLE_Z_OFFSET = 71.0

    def highlight_hole(self, hid):
        self._selected = hid
        if not self._result:
            return
        has_interval = bool(getattr(self, "_interval_selection_items", None))
        for h, items in self._hole_items.items():
            sel = (h == hid or h in (hid if isinstance(
                hid, (list, tuple, set)) else ()))
            for item in items:
                if hasattr(item, '_is_trace'):
                    pen = item.pen()
                    pen.setColor(
                        QColor(COLORS['danger']) if (sel and not has_interval)
                        else QColor(self._trajectory_color))
                    pen.setWidthF(
                        max(2.5, self._trajectory_width + 1.0) if (sel and not has_interval)
                        else self._trajectory_width)
                    item.setPen(pen)
                elif hasattr(item, '_is_label'):
                    f = item.font()
                    f.setBold(sel)
                    item.setFont(f)
                    item.setDefaultTextColor(QColor(COLORS['danger']) if sel else QColor(COLORS['primary']))
                elif hasattr(item, '_is_info_label'):
                    item.setDefaultTextColor(
                        QColor(COLORS['danger']) if sel
                        else QColor(COLORS['text_medium']))
                elif hasattr(item, '_is_leader'):
                    pen = item.pen()
                    pen.setColor(
                        QColor(COLORS['danger']) if sel
                        else QColor(COLORS['text_light']))
                    item.setPen(pen)
                # 346 — l'offset z (trou devant) ne porte QUE sur les
                # bandes litho/alté/miné, et APRÈS le style ci-dessus
                # (la 345 plaçait le `continue` avant : plus aucune
                # trace rouge / étiquette grasse = « rien ne se passe »).
                # Les teneurs (z 70, données dures) restent au-dessus.
                if getattr(item, "_is_band", False):
                    if not hasattr(item, "_base_z"):
                        try:
                            item._base_z = item.zValue()
                        except Exception as _exc:
                            from ..core.diagnostics import log_swallowed
                            log_swallowed("section : z de base", _exc)
                            item._base_z = 0.0
                    try:
                        item.setZValue(
                            item._base_z
                            + (self.SELECTED_HOLE_Z_OFFSET
                               if sel else 0.0))
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed(
                            "section : z trou sélectionné", _exc)

    # 359 — « classe qui passe devant qui » : ordre explicite, appliqué
    # sur les bandes litho/alté/miné.  Offset max +40 (bande 4 → 44) :
    # sous les teneurs (70, données dures) et sous l'exergue (79/80).
    HOLE_STACK_Z_FRONT = 40.0


    def _hole_draw_rank(self, ph):
        """363 — rang de DESSIN du trou : à z égal, le dernier item
        ajouté couvre les autres → le trou « devant » est dessiné en
        DERNIER.  Seconde méthode, infaillible celle-là (retour :
        « l'onglet superposition ne change rien »)."""
        order = list(getattr(self, "_hole_z_order", []) or [])
        if not order:
            return (0, 0)
        try:
            r = order.index(str(getattr(ph, "hole_id", ph)))
        except ValueError:
            return (0, 0)
        return (1, len(order) - r)

    def set_hole_z_order(self, order):
        """359/369 — ordre de superposition (premier = devant).
        369 — rendu complet IMMÉDIAT : l'ordre de dessin ne prenait
        effet qu'au prochain redraw (« ça prend en compte quand je
        change de section et je reviens »)."""
        self._hole_z_order = [str(h) for h in (order or [])]
        self._apply_hole_z_order()
        try:
            self._render()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section : rendu immédiat ordre", _exc)

    def _apply_hole_z_order(self):
        order = list(getattr(self, "_hole_z_order", []) or [])
        items_map = getattr(self, "_hole_items", None)
        if not items_map:
            return
        # 359 — trou HORS ordre (ou ordre vidé) : z de base restauré
        # (« il rend la place » doit VRAIMENT rendre la place).
        for hid, items in items_map.items():
            if hid in order:
                continue
            for item in items:
                if getattr(item, "_is_band", False) \
                        and hasattr(item, "_base_z"):
                    try:
                        item.setZValue(item._base_z)
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("section : z rendu", _exc)
        if not order:
            return
        n = len(order)
        for rank, hid in enumerate(order):
            off = self.HOLE_STACK_Z_FRONT * (1.0 - float(rank) / float(n))
            for item in items_map.get(hid, []):
                if not getattr(item, "_is_band", False):
                    continue
                if not hasattr(item, "_base_z"):
                    try:
                        item._base_z = item.zValue()
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("section : z de base (ordre)", _exc)
                        item._base_z = 0.0
                try:
                    item.setZValue(item._base_z + off)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("section : z ordre trous", _exc)
                # 360 — le z seul ne passait pas sur tous les postes
                # (« ne rien passer devant ») : on force AUSSI l'ordre
                # de scène (retire/rajoute = dessus garanti).
                try:
                    sc = getattr(self, "scene", None)
                    if sc is not None:
                        sc.removeItem(item)
                        sc.addItem(item)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("section : ordre scène", _exc)

    def bring_hole_to_front(self, hid):
        """359 — le trou passe DEVANT (premier de l'ordre explicite)."""
        hid = str(hid)
        order = [h for h in getattr(self, "_hole_z_order", []) if h != hid]
        order.insert(0, hid)
        self.set_hole_z_order(order)

    def send_hole_to_back(self, hid):
        """359 — le trou rend la place (sort de l'ordre explicite)."""
        hid = str(hid)
        self.set_hole_z_order(
            [h for h in getattr(self, "_hole_z_order", []) if h != hid])

    def highlight_interval(self, hid: str, from_m: float, to_m: float,
                           domain: Optional[str] = None):
        """Highlight a specific interval on the 2D section (synced with 3D).

        v2.9.260 — une sélection de MESURE `structure` est ponctuelle
        (from == to) : la bande litho serait vide.  On dessine alors un
        contour autour du/des marqueurs de structure du forage à cette
        profondeur (identique depuis 2D → 3D et 3D → 2D).
        """
        self.clear_interval_highlight()
        if not self._result or not hid:
            return
        if str(domain or "") == "structure" or abs(float(from_m) - float(to_m)) < 1e-3:
            from .section_structure import highlight_structure_point
            if highlight_structure_point(self, hid, float(from_m)):
                return
        ph = next((h for h in self._result.holes if h.hole_id == hid), None)
        if not ph:
            return
        # v2.9.278 — plancher abaissé (8→4 px) pour autoriser des voies
        # réellement fines.
        half = max(self._litho_width * 0.5, 4.0)
        poly = self._band_poly(ph, from_m, to_m, -half, half)
        if poly is not None:
            try:
                item = self._draw_selection_outline("poly", poly, color=SELECTION_HIGHLIGHT_COLOR)
                if item:
                    self._interval_selection_items.append(item)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : highlight_interval", _exc)
                # Tracé d'outline d'intervalle optionnel
                pass

    def clear_interval_highlight(self):
        """Clear active interval outline highlight.

        v2.9.196 — ANTI-DANGLING : on ne retire que les items
        vivants et dans CETTE scène (item détruit par scene.clear() =
        pointeur C++ mort → removeItem segfaulte).
        """
        scene = self.scene
        for it in list(getattr(self, "_interval_selection_items", [])):
            try:
                if it.scene() is scene:
                    scene.removeItem(it)
            except RuntimeError:
                pass   # SILENCE JUSTIFIÉ : wrapper C++ déjà détruit
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : clear_interval_highlight", _exc)
        self._interval_selection_items = []

    def get_available_elements(self) -> list[str]:
        dhs = self._drillholes or []
        fp = (id(dhs), len(dhs))
        if fp == getattr(self, "_elems_fp", None) and self._elems_cache is not None:
            return list(self._elems_cache)
        elems = set()
        for dh in dhs:
            for iv in dh.assays:
                for k in iv.attributes:
                    if k not in ("hole_id", "from", "to", "lithology", "alteration"):
                        if isinstance(iv.attributes[k], (int, float)):
                            elems.add(k)
        out = sorted(elems)
        self._elems_fp = fp
        self._elems_cache = out
        return list(out)

    # ------------------------------------------------------------------
    # Regeneration & scaling
    # ------------------------------------------------------------------
    def _proj_cache_key(self):
        line = self._line
        dhs = self._drillholes or []
        if line is None:
            return None
        return (
            id(dhs),
            len(dhs),
            round(float(line.x1), 3), round(float(line.y1), 3),
            round(float(line.x2), 3), round(float(line.y2), 3),
            round(float(self._buffer), 3),
            str(self._buffer_mode),
            str(getattr(self, "_surface_choice", "") or ""),
            tuple(sorted(self._excluded_hole_ids or ())),  # v2.9.179
            repr((getattr(getattr(getattr(getattr(self, "_parent_section", None), "main_dock", None), "project", None), "config", None) or {}).get("display_profiles")),  # v2.9.297 RACINE : SectionCanvas n'a PAS main_dock → _parent_section
        )

    def _regenerate(self):
        if not self._drillholes or not self._line:
            return
        key = self._proj_cache_key()
        cache = getattr(self, "_proj_cache", None)
        if not isinstance(cache, dict):
            cache = {}
            self._proj_cache = cache
            self._proj_cache_order = []
        hit = cache.get(key) if key is not None else None
        if hit is not None:
            (self._result, self._surface, self._surface_source,
             self._surface_tooltip) = hit
            self._compute_assay_scale()
            self._render()
            return
        # v2.9.0 — la surface est recalculée À CHAQUE régénération : elle
        # dépend de la ligne, du buffer (collets ancrés) et du choix de
        # source.  Le provider (widget) peut lever une exception — la
        # coupe ne doit JAMAIS être bloquée par la topographie : repli
        # silencieux sans surface, la cause est dans le statut du widget.
        surface, source, tooltip = None, "", ""
        if self.surface_provider is not None:
            try:
                surface, source, tooltip = self.surface_provider()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : _regenerate", _exc)
                surface, source, tooltip = None, "", ""
        self._surface = surface
        self._surface_source = source
        self._surface_tooltip = tooltip
        import time as _t334
        _t0 = _t334.perf_counter()
        self._result = generate_section(
            self._drillholes, self._line,
            buffer=self._buffer,
            vertical_exaggeration=self._v_exag,
            buffer_mode=self._buffer_mode,
            surface=surface,
            surface_source=source,
            excluded_hole_ids=self._excluded_hole_ids,  # v2.9.179
            display_config=(getattr(getattr(getattr(getattr(self, "_parent_section", None), "main_dock", None), "project", None), "config", None) or {}).get("display_profiles"),  # v2.9.297 RACINE : via _parent_section (le canvas n'a pas main_dock) — sans cela None = profils JAMAIS appliqués
        )
        from ..core.diagnostics import record_timing as _rt334
        _rt334("section: interpolation + projection",
               _t334.perf_counter() - _t0)

        if key is not None:
            cache[key] = (
                self._result, self._surface, self._surface_source,
                self._surface_tooltip)
            order = getattr(self, "_proj_cache_order", None)
            if not isinstance(order, list):
                order = []
            order.append(key)
            while len(order) > 8:
                old = order.pop(0)
                cache.pop(old, None)
            self._proj_cache_order = order
        self._compute_assay_scale()
        self._render()

    def _compute_assay_scale(self):
        """Rebuild assay scales — one independent scale per active element.

        Logic lives in core.multi_assay (v2.9.92).  ``_assay_scale`` remains
        the primary element's scale for legacy callers / map style.
        """
        self._assay_scale = None
        self._assay_scales = {}
        elems = multi_assay_mod.normalize_elements(
            self._assay_elements or ([self._element] if self._element else []))
        self._assay_elements = elems
        self._element = elems[0] if elems else None
        if not elems or not self._result:
            return
        if self._scale_scope == "project":
            intervals = [
                iv for dh in self._drillholes for iv in dh.assays
            ]
        else:
            intervals = [
                iv for ph in self._result.holes for iv in ph.assays
            ]
        self._assay_scales = multi_assay_mod.build_scales(
            elems,
            intervals_for_scope=intervals,
            compute_scale=compute_assay_scale,
            method=self._classification,
            n_classes=self._n_classes,
            manual_breaks=self._manual_breaks,
            round_breaks=self._round_breaks,
            manual_breaks_by_element=self._manual_breaks_by_elem,
        )
        if self._element and self._element in self._assay_scales:
            self._assay_scale = self._assay_scales[self._element]

    def _compute_scale(self):
        """Use horizontal pixels/unit as reference; sy/sx is exactly exag."""
        if not self._result:
            return
        sr = self._result
        w = max(sr.max_along - sr.min_along, 1.0)
        fx = getattr(self, "_fixed_sx", None)
        if fx:
            # 386 — échelle imposée (export 1:N) : indépendante de l'écran.
            self._sx = float(fx)
            self._sy = float(fx) * max(float(self._v_exag), 0.01)
            return
        n_common = self._common_ratio()
        if n_common:
            # 391 — ÉCHELLE DE PROJET : la même 1:N pour toutes les coupes
            # (comparables / corrélables, comme la 3D), au lieu de remplir
            # la largeur de la fenêtre coupe par coupe.
            from ..core.section_scale import sx_for_ratio, unit_factor
            self._sx = sx_for_ratio(n_common, unit_factor(self._distance_unit))
            self._sy = self._sx * max(float(self._v_exag), 0.01)
            return
        vw = max(
            self.viewport().width() - self._margin_left - self._margin_right,
            100)
        self._sx, self._sy = compute_isotropic_scales(
            vw, w, self._v_exag)

    def _layout_content(self, scene_w, scene_h):
        """Centre the (possibly exaggerated) content block in the scene."""
        sr = self._result
        w = max(sr.max_along - sr.min_along, 1.0)
        h = max(sr.max_elev - sr.min_elev, 1.0)
        content_w = w * self._sx + self._margin_left + self._margin_right
        content_h = h * self._sy + self._margin_top + self._margin_bottom
        self._content_left = (
            max((scene_w - content_w) / 2, 0) + self._margin_left)
        self._content_top = (
            max((scene_h - content_h) / 2, 0) + self._margin_top)

    def _to_scene(self, along, real_elev):
        sr = self._result
        x = self._content_left + (along - sr.min_along) * self._sx
        y = self._content_top + (sr.max_elev - real_elev) * self._sy
        return QPointF(x, y)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self):
        if getattr(self, "_rendering", False):
            return
        self._rendering = True
        import time as _t334
        _t0 = _t334.perf_counter()
        try:
            self._render_impl()
        finally:
            self._rendering = False
            from ..core.diagnostics import record_timing
            record_timing("2D section render (_render_impl)",
                          _t334.perf_counter() - _t0)

    def _render_impl(self):
        self.scene.clear()
        self._hole_items.clear()
        # v2.9.89 — registre bandes légende (scène rebuild)
        self._legend_band_registry = []
        self._legend_highlight_items = []
        self._threshold_outline_items = []
        # v2.9.196 — FIX SEGFAULT : scene.clear() détruit les C++ ;
        # _interval_selection_items était la seule liste non vidée →
        # un removeItem ultérieur sur item MORT = access violation.
        self._interval_selection_items = []
        if not self._result:
            self.rendered.emit()
            return

        vw = max(self.viewport().width(), 200)
        vh = max(self.viewport().height(), 200)

        # Scene size follows the content: with exaggeration > 1 the content
        # becomes taller than the viewport and the view becomes scrollable.
        sr = self._result
        # 363 — ordre de DESSIN : le trou « devant » passe en dernier
        # (à z égal le dernier ajouté couvre) — ne dépend d'aucune
        # subtilité de zValue selon les postes.
        if getattr(self, "_hole_z_order", None):
            sr.holes.sort(key=self._hole_draw_rank)
        self._compute_scale()
        self._apply_common_elev_window(sr)
        self._reserve_assay_label_room(sr)
        content_w = (max(sr.max_along - sr.min_along, 1.0) * self._sx
                     + self._margin_left + self._margin_right)
        content_h = (max(sr.max_elev - sr.min_elev, 1.0) * self._sy
                     + self._margin_top + self._margin_bottom)
        sw = max(vw, content_w)
        sh = max(vh, content_h)
        if getattr(self, "_fixed_sx", None):
            # 386 — emprise = contenu, MAIS assez large pour que la barre
            # d'échelle (+ « 1:N ») ne passe jamais sur le cartouche
            # d'orientation du bas-gauche (coupe étroite à petite échelle).
            sw, sh = max(content_w, 560.0), content_h
        self.scene.setSceneRect(0, 0, sw, sh)
        self._layout_content(sw, sh)

        if not sr.holes:
            f = QFont("Segoe UI", 11)
            f.setBold(True)
            lbl = self.scene.addText(
                self.tr("Aucun forage dans le buffer ({} {}).\nAugmentez le buffer ou retracez la ligne de coupe.")
                .format(f"{self._buffer:.0f}", self._distance_unit), f)
            lbl.setDefaultTextColor(QColor(COLORS['text_light']))
            lbl.setPos(sw / 2 - 150, sh / 2 - 20)
            return

        if (self._show_grid or self._show_elevation_values
                or self._show_distance_values or self._show_axis_titles):
            self._draw_grid(sr)
        # v2.9.0 — ligne de sol (topographie) : contexte, sous toutes les
        # pistes de données.
        if self._show_surface and sr.surface:
            self._draw_surface_profile(sr)
        # v2.7.7 — une seule passe de plan de pistes pour tout le rendu :
        # positions, gaps et auto-collapse viennent de core.track_layout.
        self._track_plan = self._build_track_plan(sr)
        if self._show_litho: self._draw_litho(sr)
        self._assay_labels_pending = None
        if self._show_assays: self._draw_assays(sr)
        if self._show_alterations: self._draw_alterations(sr)
        if self._show_mineralizations: self._draw_mineralizations(sr)
        self._draw_structures(sr)
        if self._show_imagery:
            self._draw_imagery(sr)
        from .section_geotech import draw_geotech as _geotech_draw
        self._geotech_legend_ranges.clear()
        for _kind in ("rqd", "recovery", "density"):
            if getattr(self, f"_{_kind}", False):
                _geotech_draw(self, sr, _kind)
        self._draw_traces(sr)
        if self._show_depth:
            self._draw_depth_markers(sr)
            self._draw_eoh_labels(sr)
        self._flush_assay_labels()
        if self._show_collar_labels: self._draw_labels(sr)
        if self._show_orientation: self._draw_orientation(sr)
        if self._show_scale_bar: self._draw_scale_bar(sr)
        if self._show_orientation: self._draw_north_badge()
        if self._selected:
            self.highlight_hole(self._selected)
        # 359 — l'ordre explicite survit au rebuild (avant : le z de
        # sélection disparaissait au premier redraw = « ça ne fait
        # absolument pas cela »).
        self._apply_hole_z_order()
        # v2.9.89 — resynchronise surbrillance légende après rebuild scène
        self._legend_highlight_apply()
        # v2.9.102 — contours règle de seuil (dock + export : même dessin)
        self._apply_threshold_outlines()
        self.rendered.emit()

    def _draw_surface_profile(self, sr):
        """v2.9.0 — ligne de sol le long de la coupe (core.topography).

        La source pilote le style du trait (décision écran : présenter les
        deux avec la même confiance visuelle serait trompeur) :
        - PLEIN    : source mesurée (MNT raster, CSV x;y;z) ;
        - POINTILLÉ : collets seulement (interpolation — la forme entre
          les forages est déduite, pas mesurée).

        Le profil est ancré aux collets (passe EXACTEMENT par chacun —
        sommet du polygone, voir core.topography.anchor_profile_to_
        collars).  z 3.5 : au-dessus des remplissages d'intervalle (3),
        sous toutes les pistes de données (4+).  L'infobulle détaille la
        source, l'ancrage et le QC MNT ↔ collets.

        v2.9.63 — le profil MNT peut être échantillonné sur le corridor
        ±buffer pour l'ancrage/QC, mais le TRAIT affiché est coupé à
        l'emprise du cadre (min_along…max_along = P1–P2) : plus de
        « moustaches » topo hors axes (retour écran export Sec.001/002).
        """
        a0 = float(sr.min_along)
        a1 = float(sr.max_along)
        if a1 - a0 < 1e-9:
            return
        # conserver uniquement le segment dans le cadre + 1 pt de
        # chaque côté pour interpoler pile sur les bords P1/P2
        raw = [(float(a), float(e)) for a, e in (sr.surface or [])
               if a is not None and e is not None]
        if len(raw) < 2:
            return

        def _elev_at(along):
            if along <= raw[0][0]:
                return raw[0][1]
            if along >= raw[-1][0]:
                return raw[-1][1]
            for (x0, y0), (x1, y1) in zip(raw, raw[1:]):
                if x0 <= along <= x1:
                    if x1 - x0 < 1e-12:
                        return y0
                    t = (along - x0) / (x1 - x0)
                    return y0 + t * (y1 - y0)
            return raw[-1][1]

        clipped = [(a, e) for a, e in raw if a0 <= a <= a1]
        # bornes exactes du cadre (évite un trou / un débord d'1 pixel)
        if not clipped or clipped[0][0] > a0 + 1e-9:
            clipped.insert(0, (a0, _elev_at(a0)))
        if clipped[-1][0] < a1 - 1e-9:
            clipped.append((a1, _elev_at(a1)))
        # dédoublonner abscisses croissantes
        cleaned = []
        for a, e in clipped:
            if cleaned and abs(a - cleaned[-1][0]) < 1e-9:
                cleaned[-1] = (a, e)
            else:
                cleaned.append((a, e))
        pts = [self._to_scene(a, e) for a, e in cleaned]
        if len(pts) < 2:
            return
        source = sr.surface_source
        style = (Qt.DashLine if source == "collars" else Qt.SolidLine)
        pen = QPen(QColor(self._surface_color), 2.0, style)  # v2.9.57 lisible
        # Une SEULE item QGraphicsPathItem (addPath) : polyligne OUVERTE
        # (QPainterPath, pas de segment de fermeture), un seul pinceau,
        # une seule infobulle.  addPolyline/setClosed ne sont pas exposés
        # par PyQt5.
        path = QPainterPath(pts[0])
        for point in pts[1:]:
            path.lineTo(point)
        item = self.scene.addPath(path, pen, QBrush(Qt.NoBrush))
        item.setZValue(3.5)
        if self._surface_tooltip:
            item.setToolTip(self._surface_tooltip)
        # v2.9.90 — symbole légende « ligne de sol »
        self._legend_register_geom("symbol", "surface", "path", path)

    def _draw_grid(self, sr):
        grid_colour = QColor(self._grid_color)
        grid_colour.setAlpha(round(255 * self._grid_opacity / 100.0))
        line_styles = {
            "solid": Qt.SolidLine, "dash": Qt.DashLine, "dot": Qt.DotLine,
        }
        pen = QPen(
            grid_colour, float(self._grid_width),
            line_styles.get(self._grid_style, Qt.DashLine))
        axis_pen = QPen(QColor(self._axis_title_color),
                        max(float(self._grid_width), 0.8), Qt.SolidLine)
        value_font = QFont("Segoe UI", int(self._axis_value_font_size))
        value_font.setBold(bool(self._axis_value_bold))
        value_colour = QColor(self._axis_value_color)
        title_font = QFont("Segoe UI", int(self._axis_title_font_size))
        title_font.setBold(bool(self._axis_title_bold))
        title_colour = QColor(self._axis_title_color)
        decimals = int(self._axis_value_decimals)

        plot_left = self._to_scene(sr.min_along, sr.max_elev).x()
        plot_right = self._to_scene(sr.max_along, sr.max_elev).x()
        plot_top = self._to_scene(sr.min_along, sr.max_elev).y()
        plot_bottom = self._to_scene(sr.min_along, sr.min_elev).y()
        # Nominal lanes: title 24 px | 6 px | values 24 px | 12 px | axis.
        elevation_values_right = 54.0
        elevation_axis_x = elevation_values_right + 12.0
        self.scene.addLine(
            elevation_axis_x, plot_top, elevation_axis_x, plot_bottom, axis_pen)
        self.scene.addLine(
            elevation_axis_x, plot_bottom, plot_right, plot_bottom, axis_pen)

        er = max(sr.data_max_elev - sr.data_min_elev, 1.0)
        es = (self._elevation_grid_step if self._elevation_grid_step > 0
              else self._nice(er / 8))
        n_eff = self._effective_ratio()
        if n_eff:
            # 391 — pas VERTICAL lié à l'échelle seule (jamais plus dense que
            # 15 mm papier) : même graduation sur toutes les coupes.
            from ..core.section_scale import grid_step_for_ratio, unit_factor
            es = max(es, grid_step_for_ratio(
                n_eff, unit_factor(self._distance_unit), self._v_exag))
        # Only ticks inside exact data extrema; visual 2% padding has no ticks.
        for e in grid_tick_values(sr.data_min_elev, sr.data_max_elev, es):
            y = self._to_scene(sr.min_along, e).y()
            self.scene.addLine(
                elevation_axis_x - 6, y, elevation_axis_x, y, axis_pen)
            if self._show_grid:
                self.scene.addLine(elevation_axis_x, y, plot_right, y, pen)
            if self._show_elevation_values:
                label = self.scene.addText(f"{e:.{decimals}f}", value_font)
                label.setDefaultTextColor(value_colour)
                label.setPos(
                    elevation_values_right - label.boundingRect().width(),
                    y - label.boundingRect().height() / 2)

        dr = sr.max_along - sr.min_along
        ds = (self._distance_grid_step if self._distance_grid_step > 0
              else self._nice(dr / 8))
        if n_eff and not self._distance_grid_step > 0:
            # 391 — pas HORIZONTAL lié à l'échelle seule, pas à la longueur
            # de la coupe (avant : 10 / 20 / 50 m selon la coupe).
            ds = grid_step_for_ratio(n_eff, unit_factor(self._distance_unit))
        # Identical axis spacing: graph | 12 px | values | 6 px | title.
        distance_values_y = plot_bottom + 12
        for d in grid_tick_values(sr.min_along, sr.max_along, ds):
            x = self._to_scene(d, sr.min_elev).x()
            self.scene.addLine(x, plot_bottom, x, plot_bottom + 6, axis_pen)
            if self._show_grid:
                self.scene.addLine(x, plot_top, x, plot_bottom, pen)
            if self._show_distance_values:
                label = self.scene.addText(f"{d:.{decimals}f}", value_font)
                label.setDefaultTextColor(value_colour)
                label.setPos(
                    x - label.boundingRect().width() / 2,
                    distance_values_y)

        if self._show_axis_titles:
            distance_title = self.scene.addText(
                self.tr("Distance le long de la coupe depuis P1 ({})")
                .format(self._distance_unit), title_font)
            distance_title.setDefaultTextColor(title_colour)
            distance_title.setPos(
                plot_left + max(
                    (plot_right - plot_left
                     - distance_title.boundingRect().width()) / 2, 0),
                distance_values_y + QFontMetrics(value_font).height() + 6)
            elevation_title = self.scene.addText(
                self.tr("Élévation ({})").format(self._distance_unit),
                title_font)
            elevation_title.setDefaultTextColor(title_colour)
            elevation_title.setRotation(-90)
            elevation_title.setPos(0, 0)
            rotated = elevation_title.sceneBoundingRect()
            # Column 1 title (24 px), 6 px gap, then values ending at x=54.
            target_center = QPointF(12, (plot_top + plot_bottom) / 2.0)
            delta = target_center - rotated.center()
            elevation_title.moveBy(delta.x(), delta.y())

        endpoint_y = plot_bottom - QFontMetrics(value_font).height() - 3
        endpoint_values = (
            (0.0, "P1 (0)"),
            (self._line.length,
             f"P2 ({self._line.length:.{decimals}f} {self._distance_unit})"),
        )
        for value, text in endpoint_values:
            x = self._to_scene(value, sr.min_elev).x()
            if plot_left - 1 <= x <= plot_right + 1:
                endpoint = self.scene.addText(text, value_font)
                endpoint.setDefaultTextColor(QColor(COLORS['primary']))
                endpoint.setPos(
                    x - endpoint.boundingRect().width() / 2, endpoint_y)

    _ROLE_LABELS = {
        "primary": "principal", "secondary": "secondaire",
        "vein": "veine", "accessory": "accessoire"}

    def _style_for(self, domain, code):
        """Resolved label/colour/pattern for any referential domain.

        The lithology domain keeps its proven legacy stack (référentiel +
        geological palette).  Other domains go through the live resolver
        injected by the main dock; without a project, a stable generated
        colour keeps every code drawable.
        """
        if domain == "lithology":
            return get_litho_style(code, self._litho_styles)
        code = str(code)
        cache_key = (domain, code)
        cached = self._style_cache.get(cache_key)
        if cached is not None:
            return cached
        resolved_style = None
        resolved = None  # v2.7.13.2 — sans resolver injecté, jamais d'UnboundLocalError
        resolver = getattr(self, "_style_resolver", None)
        if resolver is not None:
            try:
                resolved = resolver(domain, code)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : _style_for", _exc)
                resolved = None
        if resolved is not None and (resolved.color or resolved.label):
            resolved_style = {
                "color": resolved.color or generated_litho_color(code),
                "pattern": resolved.pattern or "",
                "label": resolved.label or code,
                # v2.7.9.2 — le symbole du Référentiel voyage jusqu'ici :
                # la coupe dessine EXACTEMENT ce que le Référentiel dit.
                "symbol_id": getattr(resolved, "symbol_id", "") or "",
                # v2.7.9.7 — la visibilité aussi : une entrée décochée
                # disparaît de la coupe et des légendes.
                "visible": getattr(resolved, "visible", True),
            }
            # v2.7.12.0 — CM-05 : famille composite = dégradé des parents
            # (document utilisateur).  Seulement tant que la couleur est
            # le défaut AUTOMATIQUE — un choix explicite reste un aplat.
            if (domain == "alteration"
                    and getattr(resolved, "automatic", False)):
                from ..core.alteration_taxonomy import (
                    suggest_alteration_family)
                family = suggest_alteration_family(code)
                if family:
                    from ..core.genesis_palettes import composite_stops
                    stops = composite_stops("alteration", family["key"])
                    if stops:
                        resolved_style["gradient"] = stops
        if resolved_style is None:
            resolved_style = {
                "color": generated_litho_color(code),
                "pattern": "",
                "label": code,
                "symbol_id": "",
                "visible": True,
            }
        self._style_cache[cache_key] = resolved_style
        return resolved_style

    def _add_litho_band(self, items, tooltip, ph, iv, center, width_fraction,
                        style, z_value, diagonal=0, select_code="",
                        symbol_tag=""):
        c = QColor(style["color"])
        c.setAlpha(round(255 * self._litho_opacity / 100.0))
        half = max(width_fraction * self._litho_width, 0.6) / 2.0
        off = center * self._litho_width
        if diagonal:
            # v2.7.11.3 — filets filonien/accessoire EN DIAGONALE (retour
            # écran : le filet centré sur la trace était masqué par la
            # polyligne du forage, z 2,9 < 5).  La bandelette balaie la
            # bande hôte d'un bord à l'autre entre from et to — bord
            # from tangente l'arête interne, bord to l'arête externe —
            # convention de lecture des veines sur les logs.  Veine « \ »
            # et accessoire « / » de sens opposés : deux structures
            # présentes ensemble se croisent au lieu de se confondre.
            from ..core.track_layout import diagonal_filet_polygon
            top = self._depth_tick_anchor(ph, iv.from_depth)
            bottom = self._depth_tick_anchor(ph, iv.to_depth)
            if top is None or bottom is None:
                return
            sp_t, tdx_t, tdy_t = top
            sp_b, tdx_b, tdy_b = bottom
            host_half = self._litho_width / 2.0
            slant = max(host_half - abs(off) - half, 0.0)
            corners = diagonal_filet_polygon(
                (float(sp_t.x()), float(sp_t.y())), (tdx_t, tdy_t),
                (float(sp_b.x()), float(sp_b.y())), (tdx_b, tdy_b),
                width_px=half * 2.0, slant_px=slant, direction=diagonal)
            poly = QPolygonF([QPointF(cx, cy) for cx, cy in corners])
        else:
            # v2.7.10.12 — bords from/to perpendiculaires à la trace
            # (comme les graduations), plus jamais horizontaux par
            # construction.
            poly = self._band_poly(
                ph, iv.from_depth, iv.to_depth, off - half, off + half)
        if poly is None:
            return
        # v2.9.89 — enregistrement pour clic légende (contour pointillé)
        # code brut uniquement (même clé que la légende), jamais le label.
        code_key = str(select_code or "").strip()
        if not code_key:
            code_key = str(iv.attributes.get("lithology", "") or "").strip()
        tags348 = []
        if code_key:
            self._legend_register_band("lithology", code_key, poly, c)
            tags348.append(("lithology", self._legend_norm_code(code_key)))
        # v2.9.90 — symboles de coupe (barrette / veine)
        if symbol_tag:
            self._legend_register_band("symbol", symbol_tag, poly, c)
            tags348.append(("symbol", self._legend_norm_code(symbol_tag)))
        self._add_patterned_poly(
            items, tooltip, poly, c, style.get("pattern", ""), z_value,
            QPen(QColor("#566573"), 0.3),
            legend_tags=tags348 or None)

    def _add_patterned_poly(self, items, tooltip, poly, colour, pattern_key,
                            z_value, border_pen, pattern_map=None,
                            gradient=None, legend_tags=None):
        """v2.9.87 — système motifs 2.9.33 (Qt brush + lignes // axe).

        Origine v2.7.5 — two-layer fill : a soft SOLID underlay keeps the colour
        identity readable, the chosen motif rides on top as strokes.

        v2.7.10.26 (retour écran) :
        - le motif n'est plus dessiné en couleur de base (qui la changeait
          à l'œil) : ENCRE CONTRASTÉE — blanche sur base foncée (ex. bleu
          pur), ardoise foncée sur base claire/pastel — posée SUR la
          couleur de base conservée (sous-couche elle-même renforcée) ;
        - la DENSITÉ du motif suit la TAILLE de l'intervalle (échelle du
          pinceau = portée/28 px, bornée 0,55–2,0) : on sent le motif
          — quadrillage ou diagonale — même sur un intervalle fin.

        Without the underlay a patterned band is only made of thin strokes
        over transparency : two different colours then look identical
        (feedback 18/08/2026).  Never needed for the plain solid fill."""
        brush_style = (pattern_map or _LITHO_BRUSH_PATTERNS).get(
            normalise_pattern(pattern_key) or pattern_key, Qt.SolidPattern)
        # v2.7.12.0 — CM-05 : famille composite → remplissage en DÉGRADÉ
        # horizontal des couleurs parentes (décision utilisateur), le motif
        # éventuel reste dessiné dessus, bordure inchangée.  Ne s'active
        # que si l'appelant a joint ``gradient`` (couleur automatique).
        fill_brush = None
        if gradient and len(gradient) >= 2:
            from qgis.PyQt.QtGui import QLinearGradient
            rect = poly.boundingRect()
            grad = QLinearGradient(rect.left(), rect.center().y(),
                                   rect.right(), rect.center().y())
            n = len(gradient)
            for i, hexs in enumerate(gradient):
                stop_colour = QColor(hexs)
                stop_colour.setAlpha(colour.alpha())
                grad.setColorAt(i / (n - 1), stop_colour)
            fill_brush = QBrush(grad)
        if brush_style != Qt.SolidPattern:
            underlay = QColor(colour)
            underlay.setAlpha(round(
                colour.alpha() * PATTERN_UNDERLAY_ALPHA_RATIO))
            if fill_brush is None:
                base_brush = QBrush(underlay, Qt.SolidPattern)
            else:
                # Sous-couche : le dégradé atténué sous le motif.
                from qgis.PyQt.QtGui import QLinearGradient
                rect = poly.boundingRect()
                grad = QLinearGradient(rect.left(), rect.center().y(),
                                       rect.right(), rect.center().y())
                n = len(gradient)
                for i, hexs in enumerate(gradient):
                    stop_colour = QColor(hexs)
                    stop_colour.setAlpha(underlay.alpha())
                    grad.setColorAt(i / (n - 1), stop_colour)
                base_brush = QBrush(grad)
            base_item = self.scene.addPolygon(
                poly, QPen(Qt.NoPen), base_brush)
            base_item.setZValue(z_value - 0.05)
            base_item._is_band = True  # 345 : monté si trou sélectionné
            if legend_tags:
                base_item._legend_tags = list(legend_tags)  # 348
            if tooltip:
                base_item.setToolTip(tooltip)
            items.append(base_item)
        # v2.7.10.26/27/32 — encre contrastée réservée aux motifs À LIGNES
        # (les motifs denses = remplissage gardent la couleur de base) ;
        # UNE SEULE règle d'encre, partagée avec la légende
        # (_pattern_ink_colour) : la coupe et la légende ne peuvent plus
        # afficher le même motif dans deux couleurs différentes.
        dense_pattern = (brush_style not in _LINE_BRUSH_STYLES
                         and brush_style != Qt.SolidPattern)
        # v2.7.10.28 — « on doit VOIR le motif complet » (retour écran) :
        # une maille de motif vaut ~10 px à l'échelle 1 ; l'échelle est
        # choisie pour loger au moins ~2 mailles dans la portée de la
        # bande (règle span/20). v2.7.10.30 — PLAFOND PROPRE par famille :
        # jamais de traits épais ni de points géants « agrandis » à plus
        # de 1,4×/1,0× leur forme native — pas de désordre quand la bande
        # est immense ; en dessous du seuil lisible (~7 px) : couleur
        # seule, l'honnêteté avant le motif.
        # v2.9.31 — motifs RELATIFS À L'AXE du forage (convention log) :
        # « vertical » = // trajectoire, « horizontal » = ⊥ trajectoire.
        # Toujours (plus d'option).  Échelle native 1,0 ; sous ~4 px →
        # couleur seule.  ≥2 traits si bande étroite.
        axis_dx = axis_dy = 0.0
        if len(poly) >= 4:
            top_mx = (float(poly[0].x()) + float(poly[1].x())) / 2.0
            top_my = (float(poly[0].y()) + float(poly[1].y())) / 2.0
            bot_mx = (float(poly[3].x()) + float(poly[2].x())) / 2.0
            bot_my = (float(poly[3].y()) + float(poly[2].y())) / 2.0
            axis_dx, axis_dy = bot_mx - top_mx, bot_my - top_my
        axis_len = math.hypot(axis_dx, axis_dy)

        motif_ok = False
        span_px = width_px = 0.0
        if brush_style != Qt.SolidPattern and len(poly) >= 3:
            span_px = math.hypot(
                float(poly[2].x() - poly[1].x()),
                float(poly[2].y() - poly[1].y()))
            width_px = math.hypot(
                float(poly[1].x() - poly[0].x()),
                float(poly[1].y() - poly[0].y()))
            if width_px < 0.5:
                width_px = span_px
            if span_px < 0.5:
                span_px = width_px
            if min(span_px, width_px) >= 4.0:
                motif_ok = True
        if brush_style != Qt.SolidPattern and not motif_ok:
            item = self.scene.addPolygon(
                poly, border_pen,
                QBrush(fill_brush if fill_brush is not None
                       else QColor(colour)))
            item.setZValue(z_value)
            item._is_band = True  # 345 : monté si trou sélectionné
            if legend_tags:
                item._legend_tags = list(legend_tags)  # 348
            if tooltip:
                item.setToolTip(tooltip)
            items.append(item)
            if tooltip and poly is not None:
                self._add_tooltip_hit_pad(
                    items, poly, tooltip, z_value=float(z_value) + 0.2)
            return item

        ink_colour = _pattern_ink_colour(colour, brush_style)
        if brush_style in _LINE_BRUSH_STYLES:
            ink_colour.setAlpha(min(max(colour.alpha(), 180), 230))
        else:
            ink_colour.setAlpha(max(colour.alpha(), 200))

        # Lignes : toujours traits custom // axe (≥2), jamais brush Qt
        # écran-fixe (qui ne suit pas le pendage).
        if brush_style in _LINE_BRUSH_STYLES:
            item = _PatternPolygonItem(poly)
            item.setPen(border_pen)
            item.setBrush(QBrush(Qt.NoBrush))
            item.setZValue(z_value)
            self.scene.addItem(item)
            if tooltip:
                item.setToolTip(tooltip)
            items.append(item)
            self._draw_axis_aligned_pattern_lines(
                items, poly, brush_style, ink_colour, z_value,
                axis_dx, axis_dy)
        else:
            # Dots / dense : brush natif + rotation axe (scale 1)
            item_brush = QBrush(ink_colour, brush_style)
            if axis_len >= 0.5:
                from ..core.track_layout import pattern_rotation_degrees
                transform = QTransform()
                transform.rotate(pattern_rotation_degrees(axis_dx, axis_dy))
                item_brush.setTransform(transform)
            item = _PatternPolygonItem(poly)
            item.setPen(border_pen)
            item.setBrush(item_brush)
            item.setZValue(z_value)
            self.scene.addItem(item)
            if tooltip:
                item.setToolTip(tooltip)
            items.append(item)
        if tooltip and poly is not None:
            self._add_tooltip_hit_pad(
                items, poly, tooltip, z_value=float(z_value) + 0.2)

        return item


    def _draw_axis_aligned_pattern_lines(
            self, items, poly, brush_style, ink_colour, z_value,
            axis_dx, axis_dy):
        """v2.9.31 — ≥2 traits H/V/diag RELATIFS À L'AXE du forage.

        Repère local :
          û = axe (from→to le long du trou) ;
          n̂ = normale droite (vers l'extérieur de bande).
        « vertical »   = // û  (suit la trajectoire) ;
        « horizontal » = // n̂  (⊥ trajectoire) ;
        FDiag / BDiag  = ±45° dans ce repère.
        """
        from qgis.PyQt.QtGui import QPainterPath
        al = math.hypot(float(axis_dx), float(axis_dy))
        if al < 0.5:
            # trou quasi-point : repli écran
            axis_dx, axis_dy, al = 0.0, 1.0, 1.0
        ux, uy = float(axis_dx) / al, float(axis_dy) / al
        # normale droite (scène y-down)
        nx, ny = -uy, ux
        # centre + demi-axes via bbox corners projected
        br = poly.boundingRect()
        cx = br.center().x()
        cy = br.center().y()
        # étendues le long de û et n̂ (max projection des 4 coins)
        corners = [
            (float(poly[i].x()), float(poly[i].y()))
            for i in range(min(4, len(poly)))]
        if len(corners) < 2:
            return
        projs_u = [(x - cx) * ux + (y - cy) * uy for x, y in corners]
        projs_n = [(x - cx) * nx + (y - cy) * ny for x, y in corners]
        u_min, u_max = min(projs_u), max(projs_u)
        n_min, n_max = min(projs_n), max(projs_n)
        len_u = max(u_max - u_min, 1.0)
        len_n = max(n_max - n_min, 1.0)

        def _n_lines(length):
            return max(2, min(5, int(float(length) / 3.5)))

        strokes = QPainterPath()

        def _seg(u0, n0, u1, n1):
            x0 = cx + u0 * ux + n0 * nx
            y0 = cy + u0 * uy + n0 * ny
            x1 = cx + u1 * ux + n1 * nx
            y1 = cy + u1 * uy + n1 * ny
            strokes.moveTo(x0, y0)
            strokes.lineTo(x1, y1)

        kinds = []
        if brush_style in (Qt.HorPattern, Qt.CrossPattern):
            kinds.append("H")  # // normale = « horizontal » log
        if brush_style in (Qt.VerPattern, Qt.CrossPattern):
            kinds.append("V")  # // axe = « vertical » log
        if brush_style in (Qt.FDiagPattern, Qt.DiagCrossPattern):
            kinds.append("FD")
        if brush_style in (Qt.BDiagPattern, Qt.DiagCrossPattern):
            kinds.append("BD")

        for kind in kinds:
            if kind == "V":
                # traits // axe : espacés le long de la normale
                n = _n_lines(len_n)
                for i in range(1, n + 1):
                    nn = n_min + (n_max - n_min) * i / (n + 1.0)
                    _seg(u_min, nn, u_max, nn)
            elif kind == "H":
                # traits ⊥ axe : espacés le long de l'axe
                n = _n_lines(len_u)
                for i in range(1, n + 1):
                    uu = u_min + (u_max - u_min) * i / (n + 1.0)
                    _seg(uu, n_min, uu, n_max)
            elif kind == "FD":
                # diagonale u+n = const
                span = len_u + len_n
                count = max(2, min(6, int(span / 4.0)))
                for i in range(1, count + 1):
                    c = (u_min + n_min) + span * i / (count + 1.0)
                    # u+n=c intersect rectangle [u_min,u_max]×[n_min,n_max]
                    pts = []
                    for u in (u_min, u_max):
                        nn = c - u
                        if n_min - 1e-6 <= nn <= n_max + 1e-6:
                            pts.append((u, nn))
                    for nn in (n_min, n_max):
                        u = c - nn
                        if u_min - 1e-6 <= u <= u_max + 1e-6:
                            pts.append((u, nn))
                    uniq = []
                    for pt in pts:
                        if all(abs(pt[0]-q[0]) > 1e-4 or abs(pt[1]-q[1]) > 1e-4
                               for q in uniq):
                            uniq.append(pt)
                    if len(uniq) >= 2:
                        _seg(uniq[0][0], uniq[0][1], uniq[1][0], uniq[1][1])
            elif kind == "BD":
                # diagonale u-n = const
                span = len_u + len_n
                count = max(2, min(6, int(span / 4.0)))
                c_min = u_min - n_max
                c_max = u_max - n_min
                for i in range(1, count + 1):
                    c = c_min + (c_max - c_min) * i / (count + 1.0)
                    pts = []
                    for u in (u_min, u_max):
                        nn = u - c
                        if n_min - 1e-6 <= nn <= n_max + 1e-6:
                            pts.append((u, nn))
                    for nn in (n_min, n_max):
                        u = c + nn
                        if u_min - 1e-6 <= u <= u_max + 1e-6:
                            pts.append((u, nn))
                    uniq = []
                    for pt in pts:
                        if all(abs(pt[0]-q[0]) > 1e-4 or abs(pt[1]-q[1]) > 1e-4
                               for q in uniq):
                            uniq.append(pt)
                    if len(uniq) >= 2:
                        _seg(uniq[0][0], uniq[0][1], uniq[1][0], uniq[1][1])

        if strokes.isEmpty():
            return
        pen = QPen(ink_colour, 1.0)
        pen.setCosmetic(True)
        pen.setCapStyle(Qt.FlatCap)
        clip_item = _ClippedStrokeItem(poly, strokes, pen)
        clip_item.setZValue(float(z_value) + 0.01)
        self.scene.addItem(clip_item)
        items.append(clip_item)



    def _add_tooltip_hit_pad(self, items, poly, tooltip, z_value=4.2):
        """v2.9.12 — zone de survol élargie pour infobulle.

        Les micro-intervalles (1 m) et les voies d'une double altération
        font des polygones trop fins pour la souris.  Un pad invisible
        (~8 px de demi-largeur) reprend le même tooltip, au-dessus du
        remplissage mais sous les codes (z 15).
        """
        if not tooltip or poly is None:
            return
        try:
            path = QPainterPath()
            path.addPolygon(poly)
            stroker = QPainterPathStroker()
            stroker.setWidth(8.0)
            stroker.setJoinStyle(Qt.RoundJoin)
            stroker.setCapStyle(Qt.RoundCap)
            fat = stroker.createStroke(path)
            # united with original so the interior still hits
            fat = fat.united(path)
            # brush quasi-invisible mais « solide » pour le hit-test
            brush = QBrush(QColor(0, 0, 0, 1))
            hit = self.scene.addPath(fat, QPen(Qt.NoPen), brush)
            hit.setZValue(float(z_value))
            hit.setToolTip(tooltip)
            # ne pas voler les clics de sélection de forage
            hit.setAcceptedMouseButtons(Qt.NoButton)
            items.append(hit)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _add_tooltip_hit_pad", _exc)
            # stroker/path indisponible : pas de pad, tooltip polygone seul
            pass

    def _tip_header(self, ph, iv):
        """v2.9.16 — 1ʳᵉ ligne commune à toutes les bulles d'intervalle."""
        return f"{ph.hole_id} · {iv.from_depth:g}–{iv.to_depth:g} m"

    def _litho_tooltip(self, ph, iv):
        """v2.9.21 — bloc court + rôle aligné sur le DESSIN (D-01).

        Bug retour écran : QMAG + QTZ_VEIN affichaient tous deux « sec. »
        parce que le CSV n'a souvent PAS de colonne rôle (role="") et
        ``draw_role("", code)`` ne normalisait pas — le layout, lui,
        traite le 1er diviseur comme hôte et les codes veine en filet.
        Même règle ici.
        """
        from ..core.track_bands import (
            KNOWN_ROLES, ROLE_PRIMARY, ROLE_SECONDARY, draw_role)
        lines = [self._tip_header(ph, iv)]
        role_short = {
            "primary": self.tr("hôte"),
            "secondary": self.tr("sec."),
            "vein": self.tr("veine"),
            "accessory": self.tr("access."),
        }
        if iv.components:
            comps = [c for c in iv.components
                     if str(getattr(c, "raw_code", "") or "").strip()]
            has_primary = any(
                str(getattr(c, "role", "") or "").strip() == ROLE_PRIMARY
                for c in comps)
            for index, comp in enumerate(comps):
                code = str(comp.raw_code or "").strip()
                raw_role = str(getattr(comp, "role", "") or "").strip()
                if raw_role not in KNOWN_ROLES:
                    # Comme _role_and_proportion : inconnu → secondary,
                    # SAUF 1er composant s'il n'y a aucun primary explicite
                    # → hôte (base du layout D-01).
                    if not has_primary and index == 0:
                        raw_role = ROLE_PRIMARY
                    else:
                        raw_role = ROLE_SECONDARY
                role = draw_role(raw_role, code)
                tag = role_short.get(role, "sec.")
                if comp.proportion is not None:
                    lines.append(f"{code} · {comp.proportion:g} % · {tag}")
                else:
                    lines.append(f"{code} · {tag}")
        else:
            code = str(iv.attributes.get("lithology", "") or "").strip()
            if code:
                lines.append(code)
        return "\n".join(lines)


    def _draw_litho_overflow_marker(self, items, ph, iv, count, codes, tooltip):
        """v2.9.91 — annotation visible « +N » (coupe + export, pas une bulle).

        Posée au milieu de l'intervalle, bord externe de la piste litho.
        Aucun nouveau renderer de motif : texte scène uniquement.
        """
        try:
            n = int(count or 0)
        except (TypeError, ValueError):
            n = 0
        if n <= 0:
            return
        mid = 0.5 * (float(iv.from_depth) + float(iv.to_depth))
        anchor = self._depth_tick_anchor(ph, mid)
        if anchor is None:
            return
        sp, tdx, tdy = anchor
        # bord externe droit de la piste litho (offset = +half width)
        half = float(self._litho_width) / 2.0
        # normale droite déjà dans tdx/tdy (track_layout)
        x = float(sp.x()) + float(tdx) * half + 2.0
        y = float(sp.y()) + float(tdy) * half
        label = f"+{n}"
        font = QFont("Segoe UI", 7)
        font.setBold(True)
        text_item = self.scene.addText(label, font)
        text_item.setDefaultTextColor(QColor("#1A252F"))
        # fond clair pour lisibilité export
        br = text_item.boundingRect()
        bg = self.scene.addRect(
            0, 0, br.width() + 2, br.height(),
            QPen(QColor("#566573"), 0.4),
            QBrush(QColor(255, 255, 255, 220)))
        bg.setZValue(12.0)
        text_item.setZValue(12.1)
        bg.setPos(x, y - br.height() / 2.0)
        text_item.setPos(x + 1.0, y - br.height() / 2.0)
        tip_codes = ", ".join(str(c) for c in (codes or ()) if c)
        tip = tooltip or ""
        extra = (self.tr("Litho non dessinées : {}").format(tip_codes)
                 if tip_codes else
                 self.tr("{} litho(s) secondaire(s) non dessinées")
                 .format(n))
        full_tip = (tip + "\n" + extra).strip() if tip else extra
        text_item.setToolTip(full_tip)
        bg.setToolTip(full_tip)
        items.append(bg)
        items.append(text_item)

    def _draw_litho(self, sr):
        """Lithology track : the primary band plus every declared component.

        D-01/D-02/D-05 are implemented by component_band_layout; without
        components the historical single-code band is kept exactly.
        """
        for ph in sr.holes:
            items = self._hole_items.setdefault(ph.hole_id, [])
            for iv in ph.litho:
                tooltip = self._litho_tooltip(ph, iv)
                # v2.7.13.2 — AUCUNE BANDE MUETTE : un composant décoché
                # dans le Référentiel ne réserve plus sa part de la
                # subdivision (un split 70/30 dont le 30 % est décoché
                # laissait 30 % de vide) — la subdivision est recalculée
                # sur les composants VISIBLES seuls, la bande se remplit.
                visible_components = [
                    c for c in (iv.components or [])
                    if get_litho_style(
                        c.raw_code, self._litho_styles
                    ).get("visible", True) is not False]
                bands = (component_band_layout(visible_components)
                         if visible_components else [])
                if not bands:
                    style = get_litho_style(
                        iv.attributes.get("lithology", ""), self._litho_styles)
                    # v2.7.9.7 — entrée décochée du Référentiel : pas de
                    # bande dans la coupe.
                    if style.get("visible") is False:
                        continue
                    self._add_litho_band(
                        items, tooltip, ph, iv, 0.0, 1.0, style, 2.0,
                        select_code=str(
                            iv.attributes.get("lithology", "") or ""))
                    continue
                overflow_n = 0
                overflow_codes = ()
                for spec in bands:
                    style = get_litho_style(spec.raw_code, self._litho_styles)
                    if style.get("visible") is False:
                        continue
                    z_value = {"base": 2.0, "split": 2.0,
                               "reduced": 2.6, "overlay": 2.9}[spec.kind]
                    # v2.7.11.3 — les filets filoniens traversent la bande
                    # en diagonale (lisibles malgré la trace) ; l'accessoire
                    # prend le sens opposé pour ne jamais coïncider.
                    diagonal = 0
                    if spec.kind == "overlay":
                        diagonal = 1 if spec.role == "vein" else -1
                    _sym = ""
                    if spec.kind == "overlay":
                        _sym = "litho_vein"
                    elif spec.kind == "reduced":
                        _sym = "litho_secondary"
                    self._add_litho_band(
                        items, tooltip, ph, iv, spec.center, spec.width,
                        style, z_value, diagonal=diagonal,
                        select_code=str(spec.raw_code or ""),
                        symbol_tag=_sym)
                    # v2.9.91 — overflow secondaries → annotation « +N »
                    if spec.kind == "base":
                        overflow_n = int(getattr(spec, "overflow_count", 0) or 0)
                        overflow_codes = tuple(
                            getattr(spec, "overflow_codes", ()) or ())
                if overflow_n > 0:
                    self._draw_litho_overflow_marker(
                        items, ph, iv, overflow_n, overflow_codes, tooltip)

    # --- v2.7.2 — Altérations & Minéralisations tracks (AM-01 à AM-03) ---

    @staticmethod
    def _interval_codes(iv, attribute, use_components=True):
        """Codes carried by one interval : declared components first, then
        the untouched raw value.

        v2.7.10.37 — CM-01/AM-05 : en minéralisations, les composants nés
        de la colonne « Minéraux » (split explicite) ne sont JAMAIS des
        styles de bande ; seuls les composants du mode large (colonnes de
        style, marque « _wide_styles ») alimentent la piste — il reste
        impossible qu'un minéral devienne un style par accident."""
        if use_components and iv.components:
            if attribute == "mineralization_style":
                codes = ([c.raw_code for c in iv.components if c.raw_code]
                         if iv.attributes.get("_wide_styles") else [])
            else:
                codes = [c.raw_code for c in iv.components if c.raw_code]
            if codes:
                return codes
        value = iv.attributes.get(attribute)
        return [value] if value not in (None, "") else []

    def _domain_has_data(self, sr, hole_attribute, attribute,
                         use_components=True):
        """v2.7.13.0 — le domaine porte-t-il au moins un code dans la
        section ?  Sert au plan de pistes : une famille sans donnée ne
        laisse aucun trou (auto-collapse), comme avant le mode
        sous-pistes dont elle reprend la sonde (mêmes ``use_components``)."""
        return any(
            self._interval_codes(iv, attribute, use_components)
            for ph in sr.holes for iv in getattr(ph, hole_attribute))

    def _lane_fill_fraction(self, iv, code):
        """v2.8.0 — fraction de remplissage d'UNE voie (AM-03 propre).

        L'intensité PROPRIÈTE du code (sa colonne Int_k appariée, CM-03)
        est la référence ; sans intensité propre, repli sur l'intensité
        de l'intervalle.  Une voie ne regarde jamais l'intensité d'une
        voisine (le groupe partagé est retiré).

        v2.9.15 — match casefold (OXYDATION == Oxydation) pour ne pas
        retomber à tort sur Int d'intervalle / Int_1.
        """
        target = str(code).strip().casefold()
        for c in (getattr(iv, "components", None) or []):
            raw = str(getattr(c, "raw_code", "") or "").strip()
            if raw.casefold() == target:
                own = str(getattr(c, "intensity", "") or "").strip()
                if own:
                    return intensity_factor(own)
                # composant trouvé sans intensité propre → neutre
                return intensity_factor("")
        return intensity_factor(iv.attributes.get("intensity", ""))

    def _compute_lane_count(self, sr, hole_attribute, domain_attribute,
                            attribute, domain):
        """v2.8.1 — nb de voies de la piste = le plus grand nombre de
        codes VISIBLES d'un même intervalle.  La voie 1 porte TOUJOURS
        le code de la 1ʳ colonne ; les autres voies n'existent que parce
        qu'un intervalle porte 2 ou 3 codes (« si jamais un intervalle
        a deux ou trois, c'est là que l'autre voie vient » — décision
        écran 22/08).  Un code décoché ne crée jamais de voie.
        """
        best = 0
        holes = getattr(sr, hole_attribute, None) or []
        for ph in holes:
            for iv in getattr(ph, domain_attribute, None) or []:
                visible = 0
                for c in self._interval_codes(iv, attribute, True) or []:
                    text = str(c).strip()
                    if not text:
                        continue
                    if (self._style_for(domain, text)
                            .get("visible", True) is False):
                        continue
                    visible += 1
                best = max(best, visible)
        return best

    def _draw_alterations(self, sr):
        lane = self._track_plan.by_key.get("alterations") \
            if self._track_plan else None
        if lane is None:
            return
        self._draw_domain_track(
            sr, "alterations", "alteration", "alteration",
            self._alter_opacity,
            lane.inner_edge, self.tr("Altération"), side=lane.side)
        # v2.7.10.29 — PAS de codes texte sur les altérations (correction
        # écran : la demande « code dans l'intervalle » visait la
        # MINÉRALISATION, déjà couverte par _draw_style_identity_track).
        # L'altération reste : couleur de famille + largeur d'intensité.

    def _draw_mineralizations(self, sr):
        # Lanes follow the mineralization STYLE; split minerals remain a
        # tooltip detail (AM-05), never an automatic band.
        lane = self._track_plan.by_key.get("mineralizations") \
            if self._track_plan else None
        if lane is None:
            return
        self._draw_domain_track(
            sr, "mineralizations", "mineralization_style",
            "mineralization_style",
            self._mineral_opacity, lane.inner_edge, self.tr("Minéralisation"),
            side=lane.side, use_components=True,
            extra_attribute="minerals",
            extra_label=self.tr("Minéraux"),
            pattern_identity=True)

    def _draw_structures(self, sr):
        """v2.9.260 — piste des mesures de structure (étape 2)."""
        from .section_structure import draw_structures
        draw_structures(self, sr)

    def _draw_imagery(self, sr):
        """v2.9.262 — piste 2D « Imagerie » (Chantier 2 E2)."""
        from .section_imagery import draw_imagery, imagery_project_and_source
        project, source_dir = imagery_project_and_source(self)
        draw_imagery(self, sr, project=project, source_dir=source_dir)

    def _structure_tooltip(self, ph, record, code):
        """Infobulle du point de structure (compacte, données réelles)."""
        from .section_structure import structure_tooltip
        return structure_tooltip(self, ph, record, code)

    def _draw_domain_track(self, sr, hole_attribute, attribute, domain,
                           opacity, base_offset,
                           singular, side="right", use_components=True,
                           extra_attribute="", extra_label="",
                           pattern_identity=False):
        """One coded track (AM-01 à AM-03).

        v2.8.0/2.8.1 — VOIES PAR POSITION (décision écran 22/08) : la
        voie 1 porte TOUJOURS le code de la 1ʳ colonne ; la voie k n'existe
        que parce qu'un intervalle porte k codes (``lane_slots`` calcule
        le nb de voies, largeur constante ``LANE_WIDTH_PX``, voies
        COLLÉES).  Le trait fin GRAS entre deux voies n'est JAMAIS une
        grille permanente : il n'est tracé QUE sur les intervalles qui
        portent 2+ codes, entre les voies qui y coexistent
        (``_draw_interval_lane_lines``).  Le remplissage d'une voie =
        l'intensité PROPRIÈTE du code qu'elle contient (colonne Int_k
        appariée, repli sur l'intensité d'intervalle) — une voie ne
        regarde jamais les autres codes du même intervalle (le groupe
        partagé CM-03 est retiré : plus d'Intense_1, plus de sous-bandes).

        v2.7.7 — ``side`` mirrors the geometry : ``base_offset`` is the
        inner edge (closest to the trace) and bands extend outward, left or
        right, according to the track plan (core.track_layout).

        v2.7.8 — ``pattern_identity`` (minéralisations) : la piste est
        codée par MOTIF sur une encre neutre, plus jamais par couleur —
        fin du conflit visuel avec lithologie / altérations / teneurs.
        """
        if not any(
                self._interval_codes(iv, attribute, use_components)
                for ph in sr.holes for iv in getattr(ph, hole_attribute)):
            return
        if pattern_identity:
            # v2.7.10.9 — chemin dédié : trapèzes neutres + un code par
            # RUN d'intervalles consécutifs de même style, posé seulement
            # s'il tient (jamais de chevauchement).
            self._draw_style_identity_track(
                sr, hole_attribute, attribute, domain,
                opacity, base_offset, singular, side=side,
                use_components=use_components, extra_attribute=extra_attribute,
                extra_label=extra_label)
            return
        alpha = round(255 * opacity / 100.0)
        sign = 1.0 if side == "right" else -1.0
        slots = getattr(self, "_lane_slots", {}).get(attribute, [])
        for ph in sr.holes:
            items = self._hole_items.setdefault(ph.hole_id, [])
            for iv in getattr(ph, hole_attribute):
                # v2.8.1 — les codes VISIBLES de l'intervalle occupent
                # les voies 1..k DANS L'ORDRE : le code de la 1ʳ colonne
                # est toujours dans la voie 1, le 2ᵉ dans la voie 2…
                # (jamais de voie attribuée à un code par son identité).
                visible_codes = []
                seen_here = set()
                for raw in (codes := self._interval_codes(
                        iv, attribute, use_components) or []):
                    code = str(raw).strip()
                    if not code or code in seen_here:
                        continue
                    seen_here.add(code)
                    # v2.7.13.2 — AUCUNE BANDE MUETTE : un code décoché
                    # dans le Référentiel ne dessine rien (ni bande, ni
                    # remplissage) et ne pousse pas les suivants.
                    if (self._style_for(domain, code)
                            .get("visible", True) is False):
                        continue
                    visible_codes.append(code)
                for index, code in enumerate(visible_codes):
                    if index >= len(slots):
                        continue  # garde d'invariant (jamais atteint)
                    r0, r1 = slots[index]
                    # v2.8.0 — le remplissage de CETTE voie ne dépend que
                    # de l'intensité de CE code (sa propre colonne Int_k,
                    # repli sur l'intensité d'intervalle).
                    frac = self._lane_fill_fraction(iv, code)
                    poly = self._band_poly(
                        ph, iv.from_depth, iv.to_depth,
                        base_offset + sign * r0,
                        base_offset + sign * (r0 + frac * (r1 - r0)))
                    if poly is None:
                        continue
                    tooltip = self._domain_tooltip(
                        ph, iv, [code], domain, singular,
                        extra_attribute, extra_label)
                    style = self._style_for(domain, code)
                    c = QColor(style["color"])
                    c.setAlpha(alpha)
                    rim_pen = (QPen(Qt.NoPen) if getattr(
                        self, "_comfort_mode", True)
                        else QPen(QColor("#566573"), 0.2))  # 355
                    # v2.9.89 — registre légende (altération / domaine)
                    self._legend_register_band(domain, code, poly, c)
                    tags348 = [(domain, self._legend_norm_code(code))]
                    # v2.7.12.0 — CM-05 : dégradé des parents pour les
                    # familles composites (automatique uniquement).
                    self._add_patterned_poly(
                        items, tooltip, poly, c, style.get("pattern", ""), 4,
                        rim_pen, legend_tags=tags348,
                        gradient=style.get("gradient") or None)
                # v2.8.1 — les traits fins GRAS apparaissent SEULEMENT
                # ici : intervalle à 2+ codes → frontières entre les
                # voies qui coexistent, sur la longueur de l'intervalle
                # seulement (jamais de grille sur toute la coupe).
                if len(visible_codes) > 1 and len(slots) > 1:
                    k = min(len(visible_codes), len(slots))
                    self._draw_interval_lane_lines(
                        items, ph, iv, base_offset, sign,
                        [slots[i][1] for i in range(1, k)])

    def _draw_interval_lane_lines(self, items, ph, iv, base_offset, sign,
                                  r_values):
        """v2.8.1 — traits fins GRAS entre voies d'UN intervalle.

        Plus de grille permanente (décision écran : « je veux pas voir
        les parallèles — seulement si y'a deux altérations sur un même
        intervalle ») : chaque frontière ``r`` est tracée segment par
        segment, parallèlement à la trace (mêmes normales que les bandes
        et les graduations), UNIQUEMENT sur la portion du segment qui
        tombe dans ``[iv.from_depth, iv.to_depth]``.  Z 4,5 : au-dessus
        des remplissages (4), sous les codes (15,5).
        """
        from ..core.track_layout import rightward_normal
        pen = QPen(QColor("#566573"), 0.8)
        f = min(iv.from_depth, iv.to_depth)
        t = max(iv.from_depth, iv.to_depth)
        pts = ph.points
        for r in r_values:
            offset = base_offset + sign * r
            for i in range(1, len(pts)):
                p0, p1 = pts[i - 1], pts[i]
                d0, d1 = p0.depth, p1.depth
                lo = max(f, min(d0, d1))
                hi = min(t, max(d0, d1))
                if hi - lo < 1e-9:
                    continue
                s0 = self._to_scene(p0.along, p0.elevation)
                s1 = self._to_scene(p1.along, p1.elevation)
                nx, ny = rightward_normal(
                    float(s1.x()) - float(s0.x()),
                    float(s1.y()) - float(s0.y()))
                span = max(abs(d1 - d0), 1e-9)
                u0 = (lo - d0) / span
                u1 = (hi - d0) / span
                item = self.scene.addLine(
                    s0.x() + (s1.x() - s0.x()) * u0 + nx * offset,
                    s0.y() + (s1.y() - s0.y()) * u0 + ny * offset,
                    s0.x() + (s1.x() - s0.x()) * u1 + nx * offset,
                    s0.y() + (s1.y() - s0.y()) * u1 + ny * offset, pen)
                item.setZValue(4.5)
                items.append(item)

    # --- v2.7.10.9 — piste de style : trapèzes neutres + code par run -------

    @staticmethod
    def _code_font_ladder():
        """Échelle de polices mesurées (6 pt → 3,5 pt, pas 0,25) pour les
        codes écrits dans les bandes : la plus grande taille respectant
        LES DEUX contraintes gagne ; 3,5 pt (vs 4 pt) donne au code
        complet une dernière chance de tenir dans une bande très fine
        avant toute abréviation.  QFont(famille, taille) n'accepte qu'un
        int : pour les tailles en 0,25 pt, on passe par setPointSizeF
        (v2.7.10.11)."""
        sizes = [round(6.0 - index * 0.25, 2)
                 for index in range(11)]  # 6.0 … 3.5
        fonts = {}
        for size in sizes:
            font = QFont("Segoe UI")
            font.setPointSizeF(size)
            font.setBold(True)
            fonts[size] = (font, QFontMetrics(font))
        return sizes, fonts

    def _draw_style_identity_track(self, sr, hole_attribute, attribute,
                                   domain, opacity, base_offset,
                                   singular, side="right", use_components=True,
                                   extra_attribute="", extra_label=""):
        """Piste minéralisation : mêmes trapèzes from→to que les autres
        pistes, remplissage neutre au lieu de couleur, et un CODE par
        RUN d'intervalles consécutifs de même style — DANS SA VOIE.

        v2.8.0/2.8.1 — VOIES PAR POSITION (décision écran 22/08) :
        ``Style_1`` porte TOUJOURS la voie 1, la voie 2 n'existe que
        parce qu'un intervalle porte 2 styles (``lane_slots``,
        ``LANE_WIDTH_PX``, voies COLLÉES).  La bande d'un style = le slot
        ENTIER de sa voie (remplissage transparent + contour 0,5 px
        d'encre neutre) : sa largeur ne dépend ni d'une intensité (le
        fichier n'en a pas — rien d'inventé) ni des autres styles — plus
        de groupe partagé.  v2.9.19 — les bandes restent une par voie ;
        le CODE est combiné « A + B » avec UN rappel quand 2+ styles
        coexistent sur le même intervalle (retour écran double MA/DI).
        Le trait fin GRAS entre deux voies
        n'apparaît QUE sur les intervalles à 2+ styles, sur leur longueur
        seulement (jamais de grille permanente — ``_draw_interval_lane_lines``).

        Règles anti-chevauchement (décision écran) — inchangées :
        - MODÈLE STRICT (v2.7.10.15) : style + minéraux, point ;
        - TEXTE LE LONG DE LA BANDE (v2.7.10.13) : le code suit l'axe du
          trou (jamais à l'envers, pivot centré), la LONGUEUR du run
          porte le texte ;
        - MICRO-INTERVALLES (v2.7.10.17→19) : code DÉPORTÉ perpendiculaire
          avec trait de rappel fin, jamais sur un autre code (rectangles
          occupés) ni sur un polygone de la piste ;
        - PLACE EN PLACE (v2.8.2) : le test est EXACT — la boîte serrée
          PIVOTÉE du candidat (OBB, théorème de l'axe séparateur) ne doit
          toucher aucun autre code en place (séparation 1 px).  L'ancien
          AABB + 2 px rejetait le code de la voie 2 à cause du code de la
          voie 1 (voies collées de 10 px, codes pivotés à 55–65° : l'AABB
          gonfle l'étendue horizontale d'environ 4 px de chaque côté) —
          rappel injustifié sur une bande qui recevait le code (retour
          écran 22/08) ; les codes déportés gardent le test AABB
          conservateur (ils flottent en espace libre) ; un micro-run ne
          reçoit le code en place que s'il y tient PHYSIQUEMENT
          (plus grande taille sans marge, 3,5 pt en dernière chance) —
          le rappel est réservé aux runs qui ne reçoivent vraiment pas
          le code ;
        - BANDES PERPENDICULAIRES (v2.7.10.12) : mêmes ancres et normales
          que les graduations de profondeur ;
        - abréviation « … » en tout dernier recours ; des intervalles
          consécutifs de même style dans la même voie ne posent qu'un
          seul code, centré sur le run.
        """
        from ..core.mineral_symbols import style_display_code
        from ..core.reference import MINERALIZATION_INK
        from ..core.track_layout import (
            angled_depot_candidates, band_edge_x, first_free_position,
            fit_code_to_band, label_rotation_degrees, obb_intersects,
            rightward_normal, rotated_aabb)
        if not any(
                self._interval_codes(iv, attribute, use_components)
                for ph in sr.holes for iv in getattr(ph, hole_attribute)):
            return
        alpha = round(255 * opacity / 100.0)
        # v2.7.10.26 — « pas de couleur » (décision écran explicite) : la
        # bande est TRANSPARENTE, seuls le contour fin et le code portent
        # le style.  L'encre neutre #5D6D7E (MINERALIZATION_INK) reste
        # celle du texte et du contour.
        neutral_fill = QColor(0, 0, 0, 0)
        ink = QColor(MINERALIZATION_INK)
        ink.setAlpha(max(0, min(255, int(round(alpha * 0.9)))))
        _font_sizes, _fonts = self._code_font_ladder()

        sign = 1.0 if side == "right" else -1.0
        # v2.8.0 — voies fixes par style observé (ordre de première
        # occurrence, stable pour toute la section).
        slots = getattr(self, "_lane_slots", {}).get(attribute, [])
        # v2.7.10.15 — rectangles (x0, y0, x1, y1) déjà pris par les codes
        # posés : l'anti-chevauchement vaut pour toute la coupe, déport
        # compris.
        occupied = []
        # v2.8.2 — boîtes SERRÉES PIVOTÉES (cx, cy, w, h, rot) des codes
        # posés EN PLACE : le test de place en place est EXACT (OBB,
        # th. de l'axe séparateur) — plus l'enveloppe AABB + 2 px qui
        # rejetait un code de la voie 2 à cause du code de la voie 1
        # voisine (voies collées de 10 px, codes pivotés à 55–65°) et
        # l'envoyait en rappel alors que sa bande le recevait (retour
        # écran 22/08).
        in_place_rects = []
        # v2.7.10.19 — polygones de TOUTES les bandes dessinées ici : un
        # code déporté ne doit jamais se poser dessus (autre intervalle
        # voisin compris) — retour écran « vilain ».
        band_polys = []

        def _rotated_label_poly(cx, cy, w, h, rotation):
            poly = QPolygonF([
                QPointF(-w / 2, -h / 2), QPointF(w / 2, -h / 2),
                QPointF(w / 2, h / 2), QPointF(-w / 2, h / 2)])
            if rotation:
                poly = QTransform().rotate(rotation).map(poly)
            return poly.translated(cx, cy)

        for ph in sr.holes:
            items = self._hole_items.setdefault(ph.hole_id, [])
            intervals = sorted(
                getattr(ph, hole_attribute),
                key=lambda iv: (iv.from_depth, iv.to_depth))
            runs = []       # runs terminés de ce forage (posés ci-dessous)
            open_runs = {}  # (index voie, style) -> run en cours
            for iv in intervals:
                codes = self._interval_codes(iv, attribute, use_components)
                if not codes:
                    continue
                # v2.8.1 — les styles VISIBLES de l'intervalle occupent
                # les voies 1..k DANS L'ORDRE : Style_1 toujours dans la
                # voie 1, Style_2 dans la voie 2… (jamais de voie
                # attribuée à un style par son identité).
                visible_styles = []
                seen_here = set()
                for raw in (codes or []):
                    code = str(raw).strip()
                    if not code or code in seen_here:
                        continue
                    seen_here.add(code)
                    # v2.7.13.2 — AUCUNE BANDE MUETTE : un style décoché
                    # ne dessine rien (ni bande, ni polygone invisible,
                    # ni réservation de largeur).
                    if (self._style_for(domain, code)
                            .get("visible", True) is False):
                        continue
                    visible_styles.append(code)
                # Parts pour le CODE (label) — les bandes se dessinent
                # toujours une par voie ; le libellé est décidé après.
                label_parts = []  # (index, code, display, poly, o0, o1)
                for index, code in enumerate(visible_styles):
                    if index >= len(slots):
                        continue  # garde d'invariant (jamais atteint)
                    style = self._style_for(domain, code)
                    r0, r1 = slots[index]
                    o0 = base_offset + sign * r0
                    o1 = base_offset + sign * r1
                    # v2.7.10.12 — trapèze perpendiculaire à la trace
                    # dessinée, sur le slot ENTIER de la voie.
                    poly = self._band_poly(
                        ph, iv.from_depth, iv.to_depth, o0, o1)
                    if poly is None:
                        continue
                    # Bande (toujours, par intervalle) : remplissage
                    # TRANSPARENT + contour d'encre neutre 0,5 px (v2.7.10.26).
                    # v2.9.15 — bulle PAR style (pas tous les codes de
                    # l'intervalle) : même logique que les altérations.
                    tooltip = self._domain_tooltip(
                        ph, iv, [code], domain, singular,
                        extra_attribute, extra_label)
                    band_item = self.scene.addPolygon(
                        poly, (QPen(Qt.NoPen) if getattr(
                            self, "_comfort_mode", True)
                            else QPen(QColor(MINERALIZATION_INK), 0.5)),
                        QBrush(neutral_fill))  # 355
                    band_item.setZValue(4)
                    band_item._is_band = True  # 345
                    band_item._legend_tags = [
                        (domain, self._legend_norm_code(code))]  # 348
                    if tooltip:
                        band_item.setToolTip(tooltip)
                    items.append(band_item)
                    self._add_tooltip_hit_pad(items, poly, tooltip, z_value=4.2)
                    band_polys.append(poly)
                    # v2.9.89 — registre légende minéralisation
                    self._legend_register_band(
                        domain, code, poly, QColor(style["color"]))
                    display_code = style_display_code(
                        code, style.get("symbol_id"), style.get("pattern"))
                    if display_code:
                        label_parts.append(
                            (index, code, display_code, poly, o0, o1))

                # v2.9.25 — LABEL par BANDE si place, combo seulement en rappel :
                #   chaque style a TOUJOURS sa bande ;
                #   si chaque bande a assez de place pour SON code →
                #     un run mono par voie (MA dans voie 1, FL dans voie 2) ;
                #   sinon (bandes trop étroites / courtes) → un seul run
                #     combo « MA + FL » qui ira en rappel (phase 2).
                #   Plus de « MA + FL » collé dans une bande qui aurait
                #   pu porter les codes séparément.
                def _open_or_extend_run(label_key, payload, from_depth, to_depth):
                    # même règle qu'avant : abs(run["to"] - iv.from_depth) < 1e-6
                    run = open_runs.get(label_key)
                    if (run is not None
                            and abs(run["to"] - from_depth) < 1e-6):
                        run["bottom"] = payload["bottom"]
                        run["inner_bottom"] = payload["inner_bottom"]
                        run["outer_bottom"] = payload["outer_bottom"]
                        run["to"] = to_depth
                    else:
                        if run is not None:
                            runs.append(run)
                        open_runs[label_key] = dict(payload)
                        open_runs[label_key]["to"] = to_depth

                active_keys = set()
                if len(label_parts) >= 1:
                    # Estimer si CHAQUE bande peut porter son code
                    # (largeur de voie − 2 px ≥ largeur min du code).
                    _min_sz = min(float(s) for s in _font_sizes)
                    _, _mf = _fonts[_min_sz] if _min_sz in _fonts else (
                        None, None)
                    can_per_band = True
                    if len(label_parts) >= 2 and _mf is not None:
                        for _idx, _code, disp, poly, o0, o1 in label_parts:
                            # largeur de bande ≈ |o1-o0|
                            band_w = abs(float(o1) - float(o0)) - 2.0
                            # portée along
                            span_est = math.hypot(
                                float(poly[2].x() - poly[1].x()),
                                float(poly[2].y() - poly[1].y()))
                            code_w = float(
                                _mf.tightBoundingRect(disp).width())
                            code_h = float(
                                _mf.tightBoundingRect(disp).height())
                            # place si code tient horizontal OU vertical
                            fits_h = (code_w + 1.0 <= band_w
                                      and code_h + 1.0 <= span_est)
                            fits_v = (code_h + 1.0 <= band_w
                                      and code_w + 1.0 <= span_est)
                            if not (fits_h or fits_v):
                                can_per_band = False
                                break
                    if len(label_parts) >= 2 and not can_per_band:
                        # Combo UNIQUEMENT pour rappel (trop serré)
                        displays = [p[2] for p in label_parts]
                        codes_raw = [p[1] for p in label_parts]
                        label_key = ("combo",) + tuple(displays)
                        label_text = " + ".join(displays)
                        first = label_parts[0]
                        last = label_parts[-1]
                        poly_a, poly_b = first[3], last[3]
                        o0, o1 = first[4], last[5]
                        top_mid = QPointF(
                            (poly_a[0].x() + poly_b[1].x()) / 2,
                            (poly_a[0].y() + poly_b[1].y()) / 2)
                        bottom_mid = QPointF(
                            (poly_a[3].x() + poly_b[2].x()) / 2,
                            (poly_a[3].y() + poly_b[2].y()) / 2)
                        tip = self._domain_tooltip(
                            ph, iv, codes_raw, domain, singular,
                            extra_attribute, extra_label)
                        active_keys = {label_key}
                        _open_or_extend_run(label_key, {
                            "code": label_text,
                            "top": top_mid, "bottom": bottom_mid,
                            "inner_top": (poly_a[0].x(), poly_a[0].y()),
                            "outer_top": (poly_b[1].x(), poly_b[1].y()),
                            "inner_bottom": (poly_a[3].x(), poly_a[3].y()),
                            "outer_bottom": (poly_b[2].x(), poly_b[2].y()),
                            "off_inner": o0,
                            "off_outer": o1,
                            "tooltip": tip,
                            "force_leader": True,  # combo = rappel
                        }, iv.from_depth, iv.to_depth)
                    else:
                        # Un run mono PAR bande (place OK ou 1 seul style)
                        for index, code, display_code, poly, o0, o1 in label_parts:
                            label_key = ("mono", index, code)
                            tip = self._domain_tooltip(
                                ph, iv, [code], domain, singular,
                                extra_attribute, extra_label)
                            top_mid = QPointF(
                                (poly[0].x() + poly[1].x()) / 2,
                                (poly[0].y() + poly[1].y()) / 2)
                            bottom_mid = QPointF(
                                (poly[3].x() + poly[2].x()) / 2,
                                (poly[3].y() + poly[2].y()) / 2)
                            active_keys.add(label_key)
                            _open_or_extend_run(label_key, {
                                "code": display_code,
                                "top": top_mid, "bottom": bottom_mid,
                                "inner_top": (poly[0].x(), poly[0].y()),
                                "outer_top": (poly[1].x(), poly[1].y()),
                                "inner_bottom": (poly[3].x(), poly[3].y()),
                                "outer_bottom": (poly[2].x(), poly[2].y()),
                                "off_inner": o0,
                                "off_outer": o1,
                                "tooltip": tip,
                                "force_leader": False,
                            }, iv.from_depth, iv.to_depth)

                # Fermer les runs qui ne continuent pas sur cet intervalle
                for stale in list(open_runs.keys()):
                    if stale not in active_keys:
                        runs.append(open_runs.pop(stale))

                # v2.8.1 — les traits fins GRAS apparaissent SEULEMENT
                # ici : intervalle à 2+ styles → frontières entre les
                # voies qui coexistent, sur la longueur de l'intervalle
                # seulement (jamais de grille sur toute la coupe).
                if len(visible_styles) > 1 and len(slots) > 1:
                    k = min(len(visible_styles), len(slots))
                    self._draw_interval_lane_lines(
                        items, ph, iv, base_offset, sign,
                        [slots[i][1] for i in range(1, k)])
            for _key, run in open_runs.items():
                runs.append(run)

            # Poser UN code par run, COMPLET. Priorités :
            # 1) horizontal — si la bande est assez large ;
            # 2) VERTICAL, le long de l'axe du trou (convention log) ;
            # 3) « À CÔTÉ », PERPENDICULAIRE à la trajectoire (déport
            #    avec fin trait de rappel) — micro-intervalles ;
            # 4) horizontal abrégé « … » en tout dernier recours.
            # Anti-chevauchement : TOUTES les poses respectent les
            # rectangles occupés (enveloppe exacte du texte pivoté, marge
            # 2 px — v2.7.10.18). v2.7.10.30 (retour écran) :
            # - PHASES : toutes les poses EN PLACE d'abord, les déportés
            #   ENSUITE — sinon un micro-intervalle garait son code « à
            #   côté » pile sur la place d'un long run et lui infligeait
            #   un rappel alors que son intervalle l'accueillait ;
            # - les traits de rappel sont des OBSTACLES enregistrés : un
            #   déport suivant ne peut plus en chevaucher un ;
            # - la mesure du glyphe se fait sur la boîte SERRÉE du code
            #   (tightBoundingRect), pas la hauteur de ligne avec son
            #   interlignage — un code qui tenait ne part plus inutilement.

            def _measure(code_text):
                def height_of(size):
                    return float(_fonts[size][1].tightBoundingRect(
                        code_text).height())

                def width_of(text, size):
                    return float(_fonts[size][1].tightBoundingRect(
                        text).width())
                return height_of, width_of

            def _draw_code(run, chosen, display, rotation, pos_x, pos_y,
                           with_leader):
                font, metrics = _fonts[chosen]
                text_item = self.scene.addText(display, font)
                text_item.setDefaultTextColor(ink)
                rect = text_item.boundingRect()
                if rotation:
                    # Pivoter autour du CENTRE du texte : le libellé reste
                    # centré sur son emplacement après rotation.
                    text_item.setTransformOriginPoint(rect.center())
                    text_item.setRotation(rotation)
                text_item.setPos(pos_x - rect.width() / 2,
                                 pos_y - rect.height() / 2)
                # v2.7.13.3 — retour écran (« certains codes se placent
                # sous les traits et on ne les voit pas ») : le code est
                # AU-DESSUS de tous les traits qu'il peut croiser — trace
                # fine (5), marqueurs (6), graduations (8), trait épais
                # (15), disque col (14).  À 4,2 il passait SOUS ces
                # traits et disparaissait.  Reste sous la tête (16) et
                # la flèche du nord (16–17).  Pas d'halo : texte plain
                # en encre, sans liseré ni fond.
                text_item.setZValue(15.5)
                if run.get("tooltip"):
                    text_item.setToolTip(run["tooltip"])
                items.append(text_item)
                fw, fh = rotated_aabb(rect.width(), rect.height(), rotation)
                occupied.append((pos_x - fw / 2, pos_y - fh / 2,
                                 pos_x + fw / 2, pos_y + fh / 2))
                if with_leader:
                    # v2.9.32 — DÉBUT DU RAPPEL = point visible sur le
                    # BORD EXTERNE de la bande (milieu From–To).
                    # Combo « DI + FL » : outer = bord de la dernière voie.
                    # Sans ça le trait « sortait du vide » (retour écran).
                    gy = float(run["gy"])
                    ox = oy = None
                    try:
                        from ..core.track_layout import band_edge_x
                        ot = run.get("outer_top")
                        ob = run.get("outer_bottom")
                        if ot is not None and ob is not None:
                            ox = float(band_edge_x(ot, ob, gy))
                            # y le long du bord outer (pas seulement gy
                            # du centre) : interpolation mid outer.
                            oy = (float(ot[1]) + float(ob[1])) / 2.0
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("section_dock : _draw_code", _exc)
                        # outer illisible — calcul ci-dessous
                        ox = oy = None
                    if ox is None or oy is None:
                        try:
                            half_band = abs(
                                float(run.get("off_outer", 0.0)
                                      - run.get("off_inner", 0.0))) / 2.0
                        except Exception as _exc:
                            from ..core.diagnostics import log_swallowed
                            log_swallowed("section_dock : _draw_code", _exc)
                            half_band = 2.0
                        side_out = 1.0 if pos_x >= float(run["gx"]) else -1.0
                        ox = float(run["gx"]) + side_out * max(half_band, 1.5)
                        oy = float(run["gy"])
                    # Direction ancre → label
                    ldx = float(pos_x) - ox
                    ldy = float(pos_y) - oy
                    ll = math.hypot(ldx, ldy) or 1.0
                    ux, uy = ldx / ll, ldy / ll
                    start_x, start_y = ox, oy
                    # Arrivée : bord du texte (pas le centre du glyphe)
                    end_x = float(pos_x) - ux * max(fw / 2.0 - 0.5, 0.0)
                    end_y = float(pos_y) - uy * max(fh / 2.0 - 0.5, 0.0)
                    leader_pen = QPen(ink, 1.0)
                    leader_pen.setStyle(Qt.SolidLine)
                    leader_pen.setCapStyle(Qt.RoundCap)
                    leader_item = self.scene.addLine(
                        start_x, start_y, end_x, end_y, leader_pen)
                    leader_item.setZValue(15.4)
                    # Ancre DÉBUT : pastille pleine sur le bord de bande
                    # → on voit clairement OÙ le trait commence.
                    anchor_r = 1.3
                    anchor = self.scene.addEllipse(
                        start_x - anchor_r, start_y - anchor_r,
                        anchor_r * 2.0, anchor_r * 2.0,
                        QPen(Qt.NoPen), QBrush(ink))
                    anchor.setZValue(15.45)
                    tip_base = run.get("tooltip") or ""
                    tip_lead = (
                        self.tr("Rappel « {} »\ndépart · bord externe de la bande")
                        .format(run.get('code', '')))
                    if tip_base:
                        tip_lead = tip_base + "\n——\n" + tip_lead
                    leader_item.setToolTip(tip_lead)
                    anchor.setToolTip(tip_lead)
                    items.append(leader_item)
                    items.append(anchor)
                    occupied.append((
                        min(start_x, pos_x) - 1.5,
                        min(start_y, pos_y) - 1.5,
                        max(start_x, pos_x) + 1.5,
                        max(start_y, pos_y) + 1.5))

            def _ink_center(gx, gy, code_text, size, rot):
                # v2.8.2 — CENTRE D'ENCRE du texte, pas centre de la
                # boîte de ligne : l'item est ancré au centre de la
                # boîte de LIGNE (boundingRect), mais la boîte SERRÉE
                # (tightBoundingRect) n'en est pas centrée — pour des
                # majuscules l'encre part sous le haut de la ligne.  Un
                # OBB ancré au mauvais centre « donne » 0,5 px de marge
                # fictive : deux encre touchaient malgré le test.
                # Décalage mesuré sur les métriques de la police
                # (repère police : origine à la baseline, y vers le haut
                # — le haut de B est B.y + B.h, celui de T est T.y + T.h,
                # la marge de l'item s'annule — indépendant de Qt).
                metrics = _fonts[size][1]
                b = metrics.boundingRect(code_text)
                t = metrics.tightBoundingRect(code_text)
                ox = t.x() + t.width() / 2.0 - b.width() / 2.0
                oy = (b.y() + b.height() - t.y() - t.height()) \
                    + t.height() / 2.0 - b.height() / 2.0
                rad = math.radians(rot)
                co, si = math.cos(rad), math.sin(rad)
                return (gx + ox * co - oy * si, gy + ox * si + oy * co)

            def _in_place_free(h_of, w_of, run, size, rot):
                # v2.8.2 — test EXACT : la boîte SERRÉE PIVOTÉE du
                # candidat (MÊME centre d'encre et même rotation que le
                # rendu) ne doit toucher AUCUN autre code en place
                # (séparation 1 px).  L'ancien AABB + 2 px rejetait le
                # code d'une voie à cause du code de la voie VOISINE
                # (voies collées de 10 px, AABB d'un code pivoté à 55–65°
                # élargi d'environ 4 px de chaque côté) : rappel
                # injustifié sur une bande qui recevait le code (retour
                # écran 22/08).
                cx, cy = _ink_center(run["gx"], run["gy"],
                                     run["code"], size, rot)
                cand = (cx, cy, w_of(run["code"], size), h_of(size), rot)
                return not any(
                    obb_intersects(cand, box, pad=0.2)
                    for box in in_place_rects)

            pending = []
            # v2.9.82 — fit sur le VRAI code (plus de « sizing sur le plus
            # large » qui forçait MA en rappel parce que BR est plus large).
            # Uniformité visuelle : après pose, on pourra rester à la taille
            # choisie par run ; l'important est EN BANDE d'abord.

            def _sizing_code(code_text):
                return str(code_text or "")

            # Phase 1 : toutes les poses EN PLACE (jamais de rappel pour
            # un code qui tient dans son intervalle).
            # v2.9.25 — force_leader (combo multi trop serré) → phase 2.
            for run in runs:
                top = run["top"]
                bottom = run["bottom"]
                tdx = bottom.x() - top.x()
                tdy = bottom.y() - top.y()
                run["tdx"], run["tdy"] = tdx, tdy
                span = max(math.hypot(tdx, tdy), 1.0)
                gy = (top.y() + bottom.y()) / 2.0
                x_inner = band_edge_x(
                    run["inner_top"], run["inner_bottom"], gy)
                x_outer = band_edge_x(
                    run["outer_top"], run["outer_bottom"], gy)
                run["gx"] = (x_inner + x_outer) / 2.0
                run["gy"] = gy
                run["span"] = span
                avail_w = abs(x_outer - x_inner) - 2.0
                run["avail_w"] = avail_w
                height_of, width_of = _measure(run["code"])
                if run.get("force_leader"):
                    pending.append(run)
                    continue
                # v2.9.10 — largeur illisible : ne PAS forcer le code
                # dans la bande (il se coince et disparaît).  Seuil =
                # largeur du code à la plus petite taille + 1 px ; en
                # dessous → déport + rappel (phase 2).
                # v2.9.25 — seuil un peu plus strict : si le code min
                # ne tient ni en largeur NI en hauteur de bande, rappel.
                _min_size = min(float(s) for s in _font_sizes)
                _sz_code = _sizing_code(run["code"])
                _min_code_w = width_of(_sz_code, _min_size) + 0.5
                _min_code_h = height_of(_min_size) + 0.5
                # v2.9.82 — seuil TRÈS souple : on tente toujours fit/micro
                # avant rappel. Rappel seulement si même 3.5 pt ne tient
                # ni en H ni en V (plus bas, margin 0).
                # (Ancien seuil envoyait en rappel des bandes qui tenaient.)
                chosen = fit_code_to_band(
                    _font_sizes, _sz_code, span, avail_w,
                    height_of, width_of, margin_px=0.5)
                if (chosen is not None
                        and _in_place_free(height_of, width_of,
                                           run, chosen, 0.0)):
                    cx, cy = _ink_center(run["gx"], run["gy"],
                                         run["code"], chosen, 0.0)
                    in_place_rects.append((
                        cx, cy,
                        width_of(run["code"], chosen),
                        height_of(chosen), 0.0))
                    _draw_code(run, chosen, run["code"], 0.0,
                               run["gx"], run["gy"], False)
                    continue
                chosen = fit_code_to_band(
                    _font_sizes, _sz_code, avail_w, span,
                    height_of, width_of, margin_px=0.5)
                if chosen is not None:
                    rotation_d = label_rotation_degrees(tdx, tdy)
                    if _in_place_free(height_of, width_of, run, chosen,
                                      rotation_d):
                        cx, cy = _ink_center(run["gx"], run["gy"],
                                             run["code"], chosen,
                                             rotation_d)
                        in_place_rects.append((
                            cx, cy,
                            width_of(run["code"], chosen),
                            height_of(chosen), rotation_d))
                        _draw_code(run, chosen, run["code"], rotation_d,
                                   run["gx"], run["gy"], False)
                        continue
                # v2.8.2 — micro-run : le code est posé dans la bande
                # tant qu'il y TIENT PHYSIQUEMENT (plus grande taille
                # SANS marge, 3,5 pt en dernière chance) — le rappel
                # n'est réservé qu'aux runs qui ne reçoivent VRAIMENT
                # pas le code (bande plus courte/étroite que la plus
                # petite taille de l'échelle).  Sans ça, deux runs
                # géométriquement identiques rendaient l'un en place
                # (dernier recours, déport impossible) et l'autre avec
                # rappel (déport possible) — incohérence visible.
                micro = fit_code_to_band(
                    _font_sizes, _sizing_code(run["code"]), span, avail_w,
                    height_of, width_of, margin_px=0.0)
                if (micro is not None
                        and _in_place_free(height_of, width_of,
                                           run, micro, 0.0)):
                    cx, cy = _ink_center(run["gx"], run["gy"],
                                         run["code"], micro, 0.0)
                    in_place_rects.append((
                        cx, cy,
                        width_of(run["code"], micro),
                        height_of(micro), 0.0))
                    _draw_code(run, micro, run["code"], 0.0,
                               run["gx"], run["gy"], False)
                    continue
                micro = fit_code_to_band(
                    _font_sizes, _sizing_code(run["code"]), avail_w, span,
                    height_of, width_of, margin_px=0.0)
                if micro is not None:
                    rotation_d = label_rotation_degrees(tdx, tdy)
                    if _in_place_free(height_of, width_of, run, micro,
                                      rotation_d):
                        cx, cy = _ink_center(run["gx"], run["gy"],
                                             run["code"], micro,
                                             rotation_d)
                        in_place_rects.append((
                            cx, cy,
                            width_of(run["code"], micro),
                            height_of(micro), rotation_d))
                        _draw_code(run, micro, run["code"], rotation_d,
                                   run["gx"], run["gy"], False)
                        continue
                pending.append(run)

            # Phase 2 — v2.9.14 : DÉPORT ANGULAIRE pour micro-intervalles
            # RÉELS (ex. TPDD006 52–60 : DF 1 m, MA 1 m, DF 1 m, MA 5 m).
            # Ce n'est PAS un seul run — chaque intervalle du CSV garde
            # son code.  Placement dans le plan (normale × tangente) :
            #   θ = 0  → rappel perpendiculaire court ;
            #   θ ≠ 0  → le code monte/descend à SA profondeur tout en
            #            restant hors bande (éventail ±15…±75°).
            # Anti-collision OBB globale (en place + déjà déportés).
            # Se recalcule à chaque _render (largeur de voie incluse).
            # v2.9.15 — du collet vers le fond : chaque micro-run
            # « voit » les déports déjà posés plus haut et s'écarte
            # en angle plutôt qu'en pure normale lointaine.
            pending.sort(key=lambda r: (
                r["gy"], r.get("span", 0.0), -r.get("avail_w", 0.0)))
            for run_i, run in enumerate(pending):
                avail_w = run["avail_w"]
                tdx, tdy = run["tdx"], run["tdy"]
                height_of, width_of = _measure(run["code"])
                depoted = fit_code_to_band(
                    _font_sizes, _sizing_code(run["code"]), 1.0e9, 1.0e9,
                    height_of, width_of)
                if depoted is None:
                    depoted = min(float(s) for s in _font_sizes)
                # Texte horizontal hors bande (lisible) ; le RAPPEL porte
                # l'angle (direction centre→label), pas le glyphe.
                rotation_d = 0.0
                tw = width_of(run["code"], depoted)
                th = height_of(depoted)
                aabb_w, aabb_h = rotated_aabb(tw, th, rotation_d)
                npx, npy = rightward_normal(tdx, tdy)
                sn = 1.0 if side == "right" else -1.0
                tl = math.hypot(tdx, tdy) or 1.0
                utx, uty = tdx / tl, tdy / tl
                # base = sortir de la bande + demi-texte
                base = max(avail_w, 0.0) / 2.0 + 2.5 + aabb_w / 2.0
                # Bias d'angle : micro-runs successifs alternent le
                # sens le long du trou (haut / bas) pour casser la
                # rangée horizontale MA/DF/MA/DF.
                prefer_sign = 1.0 if (run_i % 2 == 0) else -1.0
                candidates = []
                for side_sign in (sn, -sn):
                    for score, cx_c, cy_c, _r, ang in angled_depot_candidates(
                            run["gx"], run["gy"], npx, npy, utx, uty,
                            side_sign, base):
                        # side opposé pénalisé
                        pen = 0.0 if side_sign == sn else 40.0
                        # favoriser l'alternance haut/bas
                        if ang * prefer_sign < 0:
                            pen += 1.5
                        candidates.append((score + pen, cx_c, cy_c))
                candidates.sort(key=lambda c: c[0])
                placed = False
                pos_x = pos_y = 0.0
                for _sc, cx_c, cy_c in candidates:
                    if first_free_position(
                            [(cx_c, cy_c)], aabb_w, aabb_h,
                            occupied, padding=2.0) is None:
                        continue
                    label_poly = _rotated_label_poly(
                        cx_c, cy_c, aabb_w + 2.0, aabb_h + 2.0,
                        rotation_d)
                    if any(not band.intersected(label_poly).isEmpty()
                           for band in band_polys):
                        continue
                    cx_i, cy_i = _ink_center(
                        cx_c, cy_c, run["code"], depoted, rotation_d)
                    cand = (cx_i, cy_i, tw, th, rotation_d)
                    if any(obb_intersects(cand, box, pad=2.5)
                           for box in in_place_rects):
                        continue
                    pos_x, pos_y = cx_c, cy_c
                    placed = True
                    break
                if not placed:
                    # Pure normale lointaine — jamais de chevauchement
                    # volontaire sur un voisin.
                    pos_x = run["gx"] + sn * npx * (base + 90.0)
                    pos_y = run["gy"] + sn * npy * (base + 90.0)
                _draw_code(run, depoted, run["code"], rotation_d,
                           pos_x, pos_y, True)
                cx_i, cy_i = _ink_center(
                    pos_x, pos_y, run["code"], depoted, rotation_d)
                in_place_rects.append((cx_i, cy_i, tw, th, rotation_d))


    def _component_intensity(self, iv, code):
        """Intensité PROPRE du code (colonne Int_k), ou "" si absente.

        v2.9.15 — ne PAS retomber sur l'intensité d'intervalle (souvent
        Int_1) : une bande OXYDATION Int_2=MODEREE affichait FAIBLE parce
        que la bulle lisait attributes['intensity'] = Int_1 (retour écran).
        """
        target = str(code or "").strip()
        if not target:
            return ""
        target_cf = target.casefold()
        for c in (getattr(iv, "components", None) or []):
            raw = str(getattr(c, "raw_code", "") or "").strip()
            if raw == target or raw.casefold() == target_cf:
                return str(getattr(c, "intensity", "") or "").strip()
        # pas de repli silencieux sur Int_1 d'intervalle : la bulle
        # d'une voie 2 ne doit jamais afficher l'intensité de la voie 1
        return ""

    def _domain_tooltip(self, ph, iv, codes, domain, singular,
                        extra_attribute="", extra_label=""):
        # v2.9.16 — BLOC compact (pas une seule ligne-pavé) :
        #   trou · From–To
        #   CODE · INTENSITÉ
        # Seulement l'essentiel : code brut + Int_k propre.
        # Pas de libellé référentiel, pas Alt1/Alt2, pas CSV, pas minéraux
        # longs (sauf extra court si vraiment fourni et utile).
        lines = [self._tip_header(ph, iv)]
        for code in (codes or []):
            code = str(code).strip()
            if not code:
                continue
            own = self._component_intensity(iv, code)
            if own:
                lines.append(f"{code} · {own}")
            else:
                lines.append(code)
        if extra_attribute:
            extra = str(iv.attributes.get(extra_attribute, "") or "").strip()
            if extra:
                # un seul token utile (ex. minéraux), tronqué
                if len(extra) > 28:
                    extra = extra[:25] + "…"
                lines.append(extra)
        return "\n".join(lines)

    def _build_track_plan(self, sr):
        """v2.7.7 — plan de pistes unique (core.track_layout.plan_tracks).

        L'auto-collapse découle des « active » : une piste cachée OU sans
        donnée ne laisse aucun trou, la suivante se recolle au forage.

        v2.7.7.3 — la gouttière de profondeur est mesurée sur le pire
        libellé réellement affiché (font metrics), plus d'estimation large :
        la piste des teneurs se rapproche du forage.
        """
        from ..core.track_layout import (
            depth_lane_width, estimated_depth_label_width, plan_tracks)
        from .section_structure import track_spec as structure_track_spec
        from .section_imagery import imagery_track_spec
        from .section_geotech import geotech_track_spec
        _ae = multi_assay_mod.normalize_elements(
            self._assay_elements or ([self._element] if self._element else []))
        assay_active = bool(_ae and self._assay_scales)
        # Pire étiquette de profondeur réellement possible : autant de
        # chiffres que la profondeur totale, mesurée dans la vraie police.
        font = QFont("Segoe UI", int(self._depth_font_size))
        metrics = QFontMetrics(font)
        max_depth = max(
            (ph.total_depth for ph in sr.holes if ph.points), default=0.0)
        if max_depth > 0:
            digits = max(len(str(int(max_depth))), 3)
            label_width = metrics.horizontalAdvance("8" * digits) + 2.0
        else:
            label_width = estimated_depth_label_width(
                self._depth_font_size, digits=3)
        # v2.8.0 — VOIES PARALLÈLES FIXES (décision écran 22/08) : une
        # voie par code observé, largeur constante LANE_WIDTH_PX, voies
        # collées — la largeur de la piste = nb de voies observées ×
        # LANE_WIDTH_PX (le 13 px fixe de la v2.7.13.0 est retiré).
        # Sans donnée, la piste reste inactive → l'auto-collapse du plan
        # la fait disparaître.
        # Les clés sont les MÊMES attributs que les chemins de rendu
        # (« alteration » / « mineralization_style ») : les voies sont
        # comptées exactement comme les codes sont lus (en
        # minéralisation, seuls les styles du mode large comptent —
        # jamais un minéral).
        self._lane_count = {
            "alteration": self._compute_lane_count(
                sr, "holes", "alterations", "alteration", "alteration"),
            "mineralization_style": self._compute_lane_count(
                sr, "holes", "mineralizations", "mineralization_style",
                "mineralization_style"),
        }
        self._lane_slots = {
            "alteration": lane_slots(
                self._lane_count["alteration"], self._alter_width),
            "mineralization_style": lane_slots(
                self._lane_count["mineralization_style"],
                self._mineral_width),
        }
        # v2.8.0 — largeur de piste = nb voies × largeur de voie (le
        # spinner « Largeur de voie » garde la main : on ne l'écrase
        # jamais).  v2.8.1 : le nb de voies = le plus grand nombre de
        # codes d'un même intervalle (pas le nb de codes distincts).
        alter_track_width = self._alter_width * max(
            len(self._lane_slots["alteration"]), 1)
        mineral_track_width = self._mineral_width * max(
            len(self._lane_slots["mineralization_style"]), 1)
        _thr_raw = getattr(self, "_threshold_rules", None)
        if not _thr_raw:
            _one = getattr(self, "_threshold_rule", None)
            _thr_raw = [_one] if _one else []
        _n_int = len(threshold_rule_mod.active_rules(_thr_raw))
        tracks = {
            "assays": {
                "side": self._assay_side,
                # v2.9.92 — largeur piste = N sous-voies (module multi_assay)
                "width": multi_assay_mod.total_track_width(
                    len(_ae), self._assay_max_width),
                "active": bool(self._show_assays) and assay_active,
            },
            # v2.9.132 — intercepts : case utilisateur + au moins 1 règle ON.
            "intercepts": {
                "side": self._assay_side,
                "width": threshold_rule_mod.intercept_track_width(_n_int),
                "active": bool(getattr(self, "_show_intercepts", True))
                          and _n_int > 0,
            },
            "alterations": {
                "side": self._alter_side,
                "width": alter_track_width,
                "active": (bool(self._show_alterations)
                           and self._domain_has_data(
                               sr, "alterations", "alteration")),
            },
            "mineralizations": {
                "side": self._mineral_side,
                "width": mineral_track_width,
                "active": (bool(self._show_mineralizations)
                           and self._domain_has_data(
                               sr, "mineralizations",
                               "mineralization_style",
                               use_components=True)),
            },
            # v2.9.260 (étape 2) — piste des mesures de structure (point-
            # wise : une voie unique, largeur fixe, pas de sous-voies).
            "structures": structure_track_spec(self, sr),
            # v2.9.262 (Chantier 2 E2) — piste « Imagerie ».
            "imagery": imagery_track_spec(self, sr),
            # v2.9.264 (Chantier 3) — pistes géotechniques.
            "rqd": geotech_track_spec(self, sr, "rqd"),
            "recovery": geotech_track_spec(self, sr, "recovery"),
            "density": geotech_track_spec(self, sr, "density"),
        }
        # v2.7.11.1 — CM-03 : le rail des barrettes secondaires (D-01)
        # marche À GAUCHE de la piste litho ; son espace est désormais
        # réservé dans le plan (fin de l'empiètement sur la voie voisine).
        max_secondary = 0
        if self._show_litho:
            for ph in sr.holes:
                for iv in ph.litho:
                    bands = (component_band_layout(iv.components)
                             if iv.components else [])
                    rail_n = sum(1 for spec in bands if spec.kind == "reduced")
                    max_secondary = max(max_secondary, rail_n)
        left_reserve = reduced_rail_fraction(max_secondary) * self._litho_width
        return plan_tracks(
            litho_visible=self._show_litho,
            litho_width=self._litho_width,
            depth_visible=self._show_depth,
            depth_side=self._depth_side,
            depth_lane_w=depth_lane_width(
                float(self._depth_tick_length), label_width),
            tracks=tracks,
            left_reserve=left_reserve)

    def _draw_assays(self, sr):
        """Assay lane(s) — side/width from track plan ; multi via multi_assay.

        Modes : proportional / fixed / bars.  v2.9.92 multi-éléments.
        v2.9.287 — trait de rappel trace→marqueur (trous croisés).
        """
        from ..core.track_layout import rightward_normal
        elems = multi_assay_mod.normalize_elements(
            self._assay_elements or ([self._element] if self._element else []))
        scales = self._assay_scales or {}
        if not elems or not scales or not self._track_plan:
            return
        lane = self._track_plan.by_key.get("assays")
        if lane is None:
            return
        # Sous-voies : élément 0 = plus proche de la trace
        subs = multi_assay_mod.sublane_layout(
            len(elems), float(lane.inner_edge), float(lane.width),
            side=lane.side)
        if not subs:
            return
        bars_mode = self._assay_width_mode == "bars"
        alpha = round(255 * self._assay_opacity / 100.0)
        pals = dict(self._assay_element_palettes or {})

        for ph in sr.holes:
            items = self._hole_items.setdefault(ph.hole_id, [])
            for iv in ph.assays:
                for sub, elem in zip(subs, elems):
                    scale = scales.get(elem)
                    if not scale:
                        continue
                    v = iv.attributes.get(elem)
                    if v is None or not isinstance(v, (int, float)):
                        continue
                    vmax = scale.get("vmax", 1.0) or 1.0
                    sub_w = float(sub["width"])
                    if self._assay_width_mode == "fixed":
                        length = sub_w
                    else:
                        length = max(min((v / vmax) * sub_w, sub_w), 1.0)
                    # inner edge of this sub-lane ; grow outward by length
                    sign = 1.0 if lane.side == "right" else -1.0
                    off_inner = float(sub["inner"])
                    off_outer = off_inner + sign * float(length)
                    if bars_mode:
                        # v2.9.324 — retour écran : bâtonnets « cheveux »
                        # (3,5 px fixes).  La barre couvre l'intervalle
                        # RÉEL From–To (min 2 px) ; proportionnalité sur
                        # la longueur.
                        thickness = self._interval_thickness(
                            ph, float(iv.from_depth), float(iv.to_depth))
                        poly = self._stick_poly(
                            ph, (iv.from_depth + iv.to_depth) / 2.0,
                            off_inner, off_outer, thickness=thickness)
                    else:
                        poly = self._band_poly(
                            ph, iv.from_depth, iv.to_depth,
                            off_inner, off_outer)
                    if poly is None:
                        continue
                    _cls, ratio = classify_assay(v, scale)
                    pal = pals.get(elem) or (
                        self._assay_palette if elem == elems[0]
                        else multi_assay_mod.palette_for(
                            {"element_palettes": pals,
                             "palette": self._assay_palette,
                             "elements": elems}, elem))
                    col = QColor(assay_ramp_rgb(ratio, pal))
                    col.setAlpha(alpha)
                    item = self.scene.addPolygon(
                        poly, QPen(Qt.NoPen), QBrush(col))
                    # 345 — teneurs = données dures : toujours
                    # au-dessus des bandes litho/alté/miné (qui sont
                    # de l'interprétation), même aux chevauchements.
                    item.setZValue(70)
                    tip = (
                        f"{ph.hole_id} · {iv.from_depth:g}–{iv.to_depth:g} m\n"
                        f"{elem} · {v:g} / {vmax:g}")
                    item.setToolTip(tip)
                    items.append(item)
                    if not getattr(self, "_comfort_mode", True):
                        # 355 — le rappel trace→marqueur est du décor :
                        # masqué en confort (les marqueurs suffisent).
                        fr = self._depth_tick_anchor(ph, (iv.from_depth + iv.to_depth) / 2.0)
                        if fr is not None:
                            sp2, t2x, t2y = fr
                            n2x, n2y = rightward_normal(t2x, t2y)
                            self.scene.addLine(sp2.x(), sp2.y(), sp2.x() + n2x * off_inner, sp2.y() + n2y * off_inner, QPen(QColor(127, 140, 141, 80), 0.35)).setZValue(2)
        # v2.9.123 — libellé d'élément au-dessus de chaque colonne
        # 388 — les noms sont dessinés plus tard (après les cotes et « eoh »,
        # pour les éviter) : voir _flush_assay_labels().
        self._assay_labels_pending = (sr, elems, subs, lane)

    def _assay_column_caption(self, element: str) -> str:
        """Court libellé piste teneur (« Fe % ») — dock = export."""
        elem = str(element or "").strip()
        units = getattr(self, "_assay_element_units", None) or {}
        # 327 — retour écran : « · max X » surcharge la colonne ; le
        # titre reste COURT, l'échelle vit dans l'infobulle (326).
        return multi_assay_mod.column_caption(elem, units.get(elem) or "")

    def _flush_assay_labels(self) -> None:
        pend = getattr(self, "_assay_labels_pending", None)
        self._assay_labels_pending = None
        if pend:
            self._draw_assay_column_labels(*pend)

    def _assay_label_font(self):
        pt = min(6, int(getattr(self, "_collar_info_font_size", 7) or 7))
        return QFont("Segoe UI", max(5, pt))

    def _assay_label_context(self):
        """(elems, subs, lane) si les noms de teneurs doivent s'afficher."""
        if not getattr(self, "_show_assays", False):
            return None
        elems = multi_assay_mod.normalize_elements(
            self._assay_elements or ([self._element] if self._element else []))
        if not elems or not (self._assay_scales or {}) or not self._track_plan:
            return None
        lane = self._track_plan.by_key.get("assays")
        if lane is None:
            return None
        subs = multi_assay_mod.sublane_layout(
            len(elems), float(lane.inner_edge), float(lane.width),
            side=lane.side)
        return (elems, subs, lane) if subs else None

    def _reserve_assay_label_room(self, sr) -> None:
        """388 — retour écran : les noms (Li ppm, Rb ppm…) tombaient sur l'axe
        des distances sous le trou le plus profond. On abaisse min_elev
        JUSTE assez pour que la pile de noms tienne au-dessus de l'axe
        (en mètres d'élévation, via l'échelle verticale réelle) ; jamais
        relevé, et restitué avant chaque rendu (idempotent)."""
        applied = float(getattr(sr, "_assay_pad_m", 0.0) or 0.0)
        if applied:
            sr.min_elev += applied
        sr._assay_pad_m = 0.0
        ctx = self._assay_label_context()
        if ctx is None or self._sy <= 0:
            return
        elems, subs, _lane = ctx
        from ..core.assay_label_layout import stack_extent
        from ..core.track_layout import rightward_normal
        th = QFontMetricsF(self._assay_label_font()).height()
        max_mid = max(abs(0.5 * (float(x["inner"]) + float(x["outer"])))
                      for x in subs)
        floor = None
        for ph in sr.holes:
            pts = getattr(ph, "points", None) or []
            if len(pts) < 2 or not multi_assay_mod.hole_has_values(
                    ph.assays, elems):
                continue
            p0, p1 = pts[-2], pts[-1]
            dx = (p1.along - p0.along) * self._sx
            dy = -(p1.elevation - p0.elevation) * self._sy
            ln = math.hypot(dx, dy)
            if ln < 1e-9:
                continue
            uy = dy / ln
            if uy <= 0.0:
                continue                      # trou montant : noms au-dessus
            _nx, ny = rightward_normal(dx, dy)
            nl = math.hypot(_nx, ny) or 1.0
            # + la hauteur d'un bloc « chiffre / eoh » : un nom peut devoir
            # descendre sous le « eoh » d'un trou voisin.
            ext = (stack_extent(len(subs), th, uy)
                   + abs(ny / nl) * max_mid + 6.0
                   + (26.0 if getattr(self, "_show_depth", True) else 0.0))
            e = p1.elevation - ext / self._sy
            floor = e if floor is None else min(floor, e)
        if floor is not None and floor < sr.min_elev:
            sr._assay_pad_m = sr.min_elev - floor
            sr.min_elev = floor

    def _draw_assay_column_labels(self, sr, elems, subs, lane) -> None:
        """388 — noms de pistes de teneurs, placement garanti (core/assay_label_layout).

        * couchés (horizontaux) ; trait fin et léger dans le PROLONGEMENT
          du trou, jamais sur les pistes ;
        * texte du côté opposé à la fuite du trait : aucun trait ne
          traverse un nom (testé sous 20 000 orientations) ;
        * évitent les cotes de profondeur, « eoh » et les noms des autres
          trous, et ne descendent jamais sous l'axe des distances.
        """
        if not elems or not subs or lane is None:
            return
        from ..core.assay_label_layout import plan_end_labels
        from ..core.track_layout import rightward_normal
        font = self._assay_label_font()
        brush = QBrush(QColor(COLORS.get("text_medium") or "#7F8C8D"))
        leader_pen = QPen(QColor(COLORS['text_light']), 0.6)
        occupied: list = []
        if getattr(self, "_show_depth", True):
            occupied = [tuple(r) for r in (getattr(self, "_depth_placed", None) or [])]
        y_limit = float(self._to_scene(sr.min_along, sr.min_elev).y()) - 3.0
        for ph in sr.holes:
            pts = getattr(ph, "points", None) or []
            if not pts:
                continue
            if not multi_assay_mod.hole_has_values(ph.assays, elems):
                continue
            try:
                d0 = float(pts[-1].depth)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Piste teneurs : _draw_assay_column_labels", _exc)
                continue
            frame = self._depth_tick_anchor(ph, d0)
            if frame is None:
                continue
            sp, tdx, tdy = frame
            nx, ny = rightward_normal(tdx, tdy)
            nl = math.hypot(nx, ny) or 1.0
            nx, ny = nx / nl, ny / nl
            tlen = math.hypot(float(tdx), float(tdy)) or 1.0
            ux, uy = float(tdx) / tlen, float(tdy) / tlen
            items = self._hole_items.setdefault(ph.hole_id, [])
            entries = []        # (item, (ax, ay, t), (w, h))
            for sub, elem in zip(subs, elems):
                caption = self._assay_column_caption(elem)
                if not caption:
                    continue
                t = 0.5 * (float(sub["inner"]) + float(sub["outer"]))
                item = self.scene.addSimpleText(caption, font)
                item.setBrush(brush)
                try:
                    item.setAcceptedMouseButtons(Qt.NoButton)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Piste teneurs : étiquette 388", _exc)
                br = item.boundingRect()
                entries.append((item, (float(sp.x()) + nx * t,
                                       float(sp.y()) + ny * t, t),
                                (br.width(), br.height())))
            if not entries:
                continue
            plans = plan_end_labels(
                [e[1] for e in entries], (ux, uy), (nx, ny),
                [e[2] for e in entries], occupied, y_limit=y_limit)
            for (item, _anchor, _size), plan in zip(entries, plans):
                if plan is None:
                    self.scene.removeItem(item)
                    continue
                rect = plan["rect"]
                occupied.append(rect)
                item.setPos(rect[0], rect[1])
                item.setZValue(8.5)
                items.append(item)
                x0, y0, x1, y1 = plan["leader"]
                leader = self.scene.addLine(x0, y0, x1, y1, leader_pen)
                leader._is_leader = True
                leader._hole_id = ph.hole_id
                leader.setZValue(8)
                items.append(leader)

    def _collar_clusters(self, sr):
        """Group only truly shared XYZ collars, never projected coincidences."""
        projected = {ph.hole_id: ph for ph in sr.holes if ph.points}
        visible_drillholes = [
            dh for dh in self._drillholes if dh.hole_id in projected]
        clusters = []
        for group in group_shared_collars(
                visible_drillholes, self._shared_collar_tolerance):
            cluster = [(projected[dh.hole_id], dh) for dh in group]
            cluster.sort(key=lambda value: value[0].points[0].along)
            if cluster:
                clusters.append(cluster)
        return clusters

    def _draw_traces(self, sr):
        pen = QPen(QColor(self._trajectory_color), float(self._trajectory_width))
        for ph in sr.holes:
            items = self._hole_items.setdefault(ph.hole_id, [])
            if not self._show_trajectory or len(ph.points) < 2:
                continue
            # v2.9.90 — path trajectoire pour surbrillance légende symbole
            tpath = QPainterPath()
            first = True
            for i in range(1, len(ph.points)):
                p0, p1 = ph.points[i-1], ph.points[i]
                s0 = self._to_scene(p0.along, p0.elevation)
                s1 = self._to_scene(p1.along, p1.elevation)
                item = self.scene.addLine(s0.x(), s0.y(), s1.x(), s1.y(), pen)
                item._is_trace = True
                item._hole_id = ph.hole_id
                item.setZValue(5)
                items.append(item)
                if first:
                    tpath.moveTo(s0)
                    first = False
                tpath.lineTo(s1)
            if not tpath.isEmpty():
                self._legend_register_geom(
                    "symbol", "trajectory", "path", tpath)
        for cluster in self._collar_clusters(sr):
            ph = cluster[0][0]
            cp = ph.points[0]
            cs = self._to_scene(cp.along, cp.elevation)
            radius = self._collar_marker_size / 2.0
            marker = QGraphicsEllipseItem(
                float(cs.x())-radius, float(cs.y())-radius,
                self._collar_marker_size, self._collar_marker_size)
            marker.setBrush(QBrush(QColor("#C0392B")))
            marker.setPen(QPen(QColor("#000000"), 0.5))
            marker.setZValue(6)
            self.scene.addItem(marker)
            self._hole_items.setdefault(ph.hole_id, []).append(marker)
            # v2.9.90 — symbole légende collet
            self._legend_register_geom(
                "symbol", "collar", "ellipse",
                (float(cs.x()), float(cs.y()), float(radius)))
            if len(cluster) > 1:
                badge_font = QFont("Segoe UI", 7)
                badge_font.setBold(True)
                badge = self.scene.addText(f"×{len(cluster)}", badge_font)
                badge.setDefaultTextColor(QColor(COLORS['danger']))
                badge.setPos(cs.x() + radius + 2,
                             cs.y() - badge.boundingRect().height() / 2)
                badge.setZValue(9)

    
    def _hole_eoh_depth(self, ph) -> float:
        """Profondeur de fin de trou RÉELLE (m), pas un multiple du pas."""
        try:
            td = float(getattr(ph, "total_depth", 0.0) or 0.0)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _hole_eoh_depth", _exc)
            td = 0.0
        if td > 0:
            return td
        pts = getattr(ph, "points", None) or []
        if not pts:
            return 0.0
        try:
            return float(getattr(pts[-1], "depth", 0.0) or 0.0)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _hole_eoh_depth", _exc)
            return 0.0

    def _format_eoh_depth(self, td: float) -> str:
        """Valeur réelle : 150.4 si besoin, sinon 150."""
        if td <= 0:
            return "0"
        # 1 décimale si non entière (tolérance 1 cm)
        if abs(td - round(td)) >= 0.05:
            return f"{td:.1f}"
        return f"{td:.0f}"

    def _draw_eoh_labels(self, sr):
        """v2.9.64 — EOH = dernière graduation, même rendu que les cotes.

        - chiffre : MÊME QFont que ``_draw_depth_markers`` (pas de HTML
          dont le pt Qt diverge) + gras ;
        - « eoh » italique, même corps, collé sous le chiffre
          (2 items, margin 0, gap 0 px via metrics) ;
        - placement : juste sous le fond du forage, à droite du bout
          du barreau, bien serré (pas centré sur la normale / pas dérive).
        """
        if not sr or not getattr(sr, "holes", None):
            return
        if not getattr(self, "_show_depth", True):
            return
        from ..core.track_layout import depth_label_base, depth_tick_segment

        lane = self._track_plan.depth if self._track_plan else None
        if lane is None:
            return

        # v2.9.70 — MÊME graisse que les ticks (bold grossit le glyphe Qt)
        base_sz = int(getattr(self, "_depth_font_size", 6) or 6)
        f_num = QFont("Segoe UI", base_sz)
        f_num.setBold(False)   # identique à _draw_depth_markers
        f_eoh = QFont("Segoe UI", base_sz)
        f_eoh.setItalic(True)
        f_eoh.setBold(False)  # v316 : plus de halo EOH

        alpha = max(0, min(255, round(
            255 * float(getattr(self, "_depth_opacity", 70) or 70) / 100.0)))
        col = QColor("#566573")
        col.setAlpha(alpha)

        pen_tick = QPen(col, float(getattr(self, "_depth_tick_width", 1.0) or 1.0))
        overhang = float(getattr(self, "_depth_tick_length", 2.0) or 2.0)
        half = (self._litho_width / 2.0 + overhang
                if getattr(self, "_show_litho", True) else overhang)

        for ph in sr.holes:
            if not getattr(ph, "points", None):
                continue
            td = self._hole_eoh_depth(ph)
            if td <= 0:
                continue
            anchor = None
            try:
                anchor = self._depth_tick_anchor(ph, td)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : _draw_eoh_labels", _exc)
                # ancre optionnelle : repli sur dernier point
                anchor = None
            if anchor is None:
                last = ph.points[-1]
                sp = self._to_scene(last.along, last.elevation)
                if len(ph.points) >= 2:
                    a = self._to_scene(ph.points[-2].along,
                                       ph.points[-2].elevation)
                    tdx = float(sp.x() - a.x())
                    tdy = float(sp.y() - a.y())
                else:
                    tdx, tdy = 0.0, 1.0
            else:
                sp, tdx, tdy = anchor

            seg = depth_tick_segment(
                float(sp.x()), float(sp.y()), tdx, tdy,
                half, lane.side)
            tick = self.scene.addLine(
                seg["x1"], seg["y1"], seg["x2"], seg["y2"], pen_tick)
            tick.setZValue(8)
            self._hole_items.setdefault(ph.hole_id, []).append(tick)

            num_txt = self._format_eoh_depth(td)

            lbl_n = self.scene.addText(num_txt, f_num)
            lbl_n.setDefaultTextColor(col)
            try:
                lbl_n.document().setDocumentMargin(0)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : _draw_eoh_labels", _exc)
                # margin Qt optionnelle
                pass
            rn = lbl_n.boundingRect()

            lbl_e = self.scene.addText("eoh", f_eoh)
            lbl_e.setDefaultTextColor(col)
            try:
                lbl_e.document().setDocumentMargin(0)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : _draw_eoh_labels", _exc)
                # margin Qt optionnelle
                pass
            re_ = lbl_e.boundingRect()

            # Ancre au bout du barreau (côté lane), puis bloc bas-droite
            # serré : le chiffre touche le tiret ; eoh pile sous le chiffre.
            base_x, base_y = depth_label_base(
                seg["x2"], seg["y2"], seg["nx"], seg["ny"], gap=0.5)

            block_w = max(rn.width(), re_.width())
            # « à droite » du fond de trou = côté extérieur du barreau
            # (nx<0 → labels à gauche du trait, comme 130 ; sinon à droite)
            if seg["nx"] < 0:
                lx_block = base_x - block_w
            else:
                lx_block = base_x
            # bas du forage : le bloc part du bout du tiret vers le BAS
            # (Y scène ↓), chiffre d'abord, eoh collé (gap 0)
            ly_num = base_y - rn.height() * 0.15  # légèrement sous le tiret
            lx_num = lx_block + (block_w - rn.width())  # aligné au bord exter.
            # pour un look « bas-droite serré » : chiffre calé au bord
            # extérieur (droite du bloc si labels à droite, gauche sinon)
            if seg["nx"] >= 0:
                lx_num = lx_block  # bord gauche du bloc = près du tiret
                lx_eoh = lx_block  # eoh aussi calé à gauche (sous chiffre)
            else:
                lx_num = base_x - rn.width()
                lx_eoh = base_x - re_.width()

            lbl_n.setPos(lx_num, ly_num)
            # collé : top(eoh) = bottom(chiffre) + 0 px (metrics déjà serrées)
            ly_eoh = ly_num + rn.height() - 1.0
            lbl_e.setPos(lx_eoh, ly_eoh)
            lbl_n.setZValue(8.5)
            lbl_e.setZValue(8.5)
            self._depth_placed.append((lx_block, ly_num, block_w, rn.height() + re_.height()))
            self._hole_items.setdefault(ph.hole_id, []).append(lbl_n)
            self._hole_items.setdefault(ph.hole_id, []).append(lbl_e)

    def _draw_depth_markers(self, sr):
        """v2.7.8.1 — backbone de profondeur, convention classique de log.

        - graduations en **barreaux d'échelle** : segment de longueur fixe
          CENTRÉ sur le point du forage, perpendiculaire au segment
          réellement DESSINÉ (normale calculée en coordonnées scène entre
          les deux points projetés encadrant la profondeur) — exact quel
          que soit le pendage, l'exagération ou le sens de l'axe Y ;
        - le barreau déborde de 6 px de la bande litho : le trait est
          visible, l'étiquette est posée juste au-delà de son bout, jamais
          sur la piste voisine ;
        - étiquettes toutes les N graduations (défaut 2 : 10 m / 20 m),
          texte simple ;
        - pas automatique 1/2/5×10ⁿ si « Pas » = Auto.
        """
        from ..core.section import depth_tick_steps
        from ..core.track_layout import (
            depth_label_base, depth_tick_segment, label_rect_free)
        lane = self._track_plan.depth if self._track_plan else None; self._depth_placed = []; _wp = getattr(getattr(self, "_parent_section", None), "_project", None); self._depth_label_bg = bool(((_wp() if _wp else None) and ((getattr(_wp(), "config", None) or {}).get("display_profiles") or {}) or {}).get("label_bg")); self._zone_inset = bool(((_wp() if _wp else None) and ((getattr(_wp(), "config", None) or {}).get("display_profiles") or {}) or {}).get("zone_inset", False))  # v308 fond au choix / v310 encart zone / v315 défaut OFF (retour écran)
        if lane is None:
            return
        f = QFont("Segoe UI", int(self._depth_font_size)); f.setBold(False)  # v316 : plus de halo
        # v2.7.8.2 — opacité commune traits + chiffres (réglage
        # « Opacité des graduations », défaut 70 %).
        alpha = max(0, min(255, round(255 * self._depth_opacity / 100.0)))
        tick_colour = QColor("#566573")
        tick_colour.setAlpha(alpha)
        pen_tick = QPen(tick_colour, float(self._depth_tick_width))
        min_gap = max(12.0, float(self._depth_font_size) + 4.0)
        # Demi-longueur : le barreau traverse la trace et déborde de
        # « Débord des graduations » px au-delà de la bande lithologique
        # — un vrai barreau visible, sur lequel l'étiquette s'ancre.
        overhang = float(self._depth_tick_length)
        half = (self._litho_width / 2.0 + overhang
                if self._show_litho else overhang)
        total_depth = max(
            (ph.total_depth for ph in sr.holes if ph.points), default=0.0)
        major_step, label_step = depth_tick_steps(
            total_depth, self._depth_step, self._depth_label_every)
        if major_step <= 0:
            return
        if getattr(self, "_comfort_mode", True):
            label_step = max(2, int(label_step) * 2)  # 355 : respire

        for ph in sr.holes:
            if not ph.points:
                continue
            last_label_y = None
            d = major_step
            tick_index = 1
            eoh_d = self._hole_eoh_depth(ph)
            while d <= ph.total_depth:
                anchor = self._depth_tick_anchor(ph, d)
                if anchor is None:
                    d += major_step
                    tick_index += 1
                    continue
                sp, tdx, tdy = anchor
                seg = depth_tick_segment(
                    float(sp.x()), float(sp.y()), tdx, tdy,
                    half, lane.side)
                tick = self.scene.addLine(
                    seg["x1"], seg["y1"], seg["x2"], seg["y2"], pen_tick)
                tick.setZValue(8)

                # v2.9.60 — près de l'EOH : laisser la marque EOH (valeur réelle)
                near_eoh = (eoh_d > 0 and abs(d - eoh_d) < max(major_step * 0.45, 2.0))
                if (not near_eoh
                        and (tick_index - 1) % max(1, int(self._depth_label_every)) == 0
                        and (last_label_y is None
                             or abs(float(sp.y()) - last_label_y) >= min_gap)):
                    lbl = self.scene.addText(f"{d:.0f}", f)
                    label_colour = QColor("#566573"); label_colour.setAlpha(alpha)
                    lbl.setDefaultTextColor(label_colour)
                    rect = lbl.boundingRect()
                    base_x, base_y = depth_label_base(
                        seg["x2"], seg["y2"], seg["nx"], seg["ny"], gap=0.5)
                    lx = base_x - rect.width() if seg["nx"] < 0 else base_x
                    ly = base_y - rect.height() / 2.0
                    if label_rect_free(self._depth_placed, lx, ly, rect.width(), rect.height()):
                        if getattr(self, "_depth_label_bg", False):
                            self.scene.addRect(lx - 0.4, ly - 0.2, rect.width() + 0.8, rect.height() + 0.4,
                                               QPen(Qt.NoPen), QBrush(QColor(255, 255, 255, 215))).setZValue(7)
                        lbl.setPos(lx, ly)
                    else:
                        self.scene.removeItem(lbl)
                    lbl.setZValue(8)
                    last_label_y = float(sp.y())
                d += major_step
                tick_index += 1

    def _depth_tick_anchor(self, ph, target_depth):
        """Scene position AND scene-space tangent at a depth (v2.7.8.1).

        The perpendicular is computed on the DRAWN polyline : the two
        projected points bracketing the depth give the exact scene
        direction of the trace — no data-space mixing, no y-flip or
        exaggeration assumption. Returns ``(QPointF, dx, dy)`` or None.
        """
        for i in range(1, len(ph.points)):
            p0, p1 = ph.points[i-1], ph.points[i]
            if p0.depth <= target_depth <= p1.depth:
                denom = p1.depth - p0.depth
                t = 0.0 if denom < 1e-9 else (
                    (target_depth - p0.depth) / denom)
                along = p0.along + t * (p1.along - p0.along)
                elev = p0.elevation + t * (p1.elevation - p0.elevation)
                sp0 = self._to_scene(p0.along, p0.elevation)
                sp1 = self._to_scene(p1.along, p1.elevation)
                return (self._to_scene(along, elev),
                        float(sp1.x()) - float(sp0.x()),
                        float(sp1.y()) - float(sp0.y()))
        return None

    def _band_poly(self, ph, from_depth, to_depth, off_inner, off_outer):
        """v2.7.10.12 — trapèze from→to PERPENDICULAIRE à la trace dessinée.

        Ancres : les mêmes points et la même interpolation que les
        barreaux de profondeur (:meth:`_depth_tick_anchor`) ; les bords
        from/to suivent la normale scène locale au lieu d'être forcés
        horizontaux.  Résultat : la frontière d'un intervalle reste
        parallèle à la graduation située à la même profondeur, quel que
        soit le pendage du forage ou l'exagération verticale — fin du
        décorrélation visible entre polygones et graduations.  Pour un
        trou vertical la normale est horizontale : rendu strictement
        identique à l'ancien rectangle.  ``off_inner``/``off_outer``
        restent des décalages en pixels relatifs à la trace, positifs à
        droite de l'écran (convention historique des lanes).
        """
        from ..core.track_layout import band_trapezoid
        top = self._depth_tick_anchor(ph, from_depth)
        bottom = self._depth_tick_anchor(ph, to_depth)
        if top is None or bottom is None:
            return None
        sp_t, tdx_t, tdy_t = top
        sp_b, tdx_b, tdy_b = bottom
        corners = band_trapezoid(
            (float(sp_t.x()), float(sp_t.y())), (tdx_t, tdy_t),
            (float(sp_b.x()), float(sp_b.y())), (tdx_b, tdy_b),
            float(off_inner), float(off_outer))
        return QPolygonF([QPointF(cx, cy) for cx, cy in corners])

    def _interval_thickness(self, ph, from_depth, to_depth, minimum=2.0):
        """v2.9.324 — longueur tangentielle de l'intervalle (scène)."""
        fa = self._depth_tick_anchor(ph, float(from_depth))
        ta = self._depth_tick_anchor(ph, float(to_depth))
        if fa is None or ta is None:
            return float(minimum)
        return max(float(minimum), math.hypot(
            float(ta[0].x() - fa[0].x()), float(ta[0].y() - fa[0].y())))

    def _stick_poly(self, ph, mid_depth, off_inner, off_outer,
                    thickness=3.5):
        """v2.7.10.12 — bâtonnet d'histogramme soudé à la trace dessinée
        (longueur selon la normale, épaisseur selon la tangente)."""
        from ..core.track_layout import stick_polygon
        frame = self._depth_tick_anchor(ph, mid_depth)
        if frame is None:
            return None
        sp, tdx, tdy = frame
        corners = stick_polygon(
            (float(sp.x()), float(sp.y())), (tdx, tdy),
            float(off_inner), float(off_outer), float(thickness))
        return QPolygonF([QPointF(cx, cy) for cx, cy in corners])

    @staticmethod
    def _interp_at_depth(ph, target_depth):
        for i in range(1, len(ph.points)):
            p0, p1 = ph.points[i-1], ph.points[i]
            if p0.depth <= target_depth <= p1.depth:
                denom = p1.depth - p0.depth
                if denom < 1e-9:
                    return (p0.along, p0.elevation, 0.0, 1.0)
                t = (target_depth - p0.depth) / denom
                along = p0.along + t * (p1.along - p0.along)
                elev = p0.elevation + t * (p1.elevation - p0.elevation)
                # Vecteur tangent unitaire dans l'espace (along, elev).
                ux = p1.along - p0.along
                uy = p1.elevation - p0.elevation
                norm = math.hypot(ux, uy) or 1.0
                return (along, elev, ux / norm, uy / norm)
        return None

    @staticmethod
    def _label_anchor(rect, collar_point, anchor, gap, offset_x, offset_y):
        """Calculate a label's top-left point for one collar anchor."""
        x, y = float(collar_point.x()), float(collar_point.y())
        width, height = rect.width(), rect.height()
        if anchor == "left":
            px, py = x - gap - width, y - height / 2.0
        elif anchor == "right":
            px, py = x + gap, y - height / 2.0
        elif anchor == "bottom":
            px, py = x - width / 2.0, y + gap
        else:  # top
            px, py = x - width / 2.0, y - gap - height
        return QPointF(px + offset_x, py + offset_y)

    def _place_collar_label(self, item, collar_point, requested,
                            offset_x, offset_y, candidates, occupied):
        rect = item.boundingRect()
        gap = self._collar_marker_size / 2.0 + 3.0
        anchors = candidates if requested == "auto" else [requested]
        chosen_point = None
        chosen_rect = None
        for anchor in anchors:
            point = self._label_anchor(
                rect, collar_point, anchor, gap, offset_x, offset_y)
            candidate = QRectF(point.x(), point.y(), rect.width(), rect.height())
            padded = candidate.adjusted(-2, -2, 2, 2)
            if not any(padded.intersects(other) for other in occupied):
                chosen_point, chosen_rect = point, padded
                break
        if chosen_point is None:
            base = self._label_anchor(
                rect, collar_point, anchors[0], gap, offset_x, offset_y)
            # Fixed labels sharing the same anchor are stacked vertically.
            # User offsets default to zero; block layout supplies the spacing.
            for shift in range(0, 41, 2):
                point = QPointF(base.x(), base.y() + shift)
                padded = QRectF(
                    point.x() - 2, point.y() - 2,
                    rect.width() + 4, rect.height() + 4)
                if not any(padded.intersects(other) for other in occupied):
                    chosen_point, chosen_rect = point, padded
                    break
            if chosen_point is None:
                chosen_point = base
                chosen_rect = QRectF(
                    base.x() - 2, base.y() - 2,
                    rect.width() + 4, rect.height() + 4)
        item.setPos(chosen_point)
        occupied.append(chosen_rect)

    def _create_annotation_block(self, ph, drillhole, id_font, info_font,
                                 labels=None):
        from ..core.geometry import collar_info_text
        items = self._hole_items.setdefault(ph.hole_id, [])
        text = (labels or {}).get(ph.hole_id) or ph.hole_id  # v2.9.285 court
        id_item = self.scene.addText(text, id_font)
        id_item.setDefaultTextColor(QColor(COLORS['primary']))
        id_item._is_label = True
        id_item._hole_id = ph.hole_id
        id_item.setZValue(9)
        items.append(id_item)
        info_item = None
        if self._show_collar_info and drillhole and drillhole.collar:
            _txt = collar_info_text(drillhole.collar, drillhole.survey)
            if _txt:
                info_item = self.scene.addText(_txt, info_font)
            info_item.setDefaultTextColor(QColor(COLORS['text_medium']))
            info_item._is_info_label = True
            info_item._hole_id = ph.hole_id
            info_item.setZValue(9)
            items.append(info_item)

        id_rect = id_item.boundingRect()
        info_rect = info_item.boundingRect() if info_item else QRectF()
        content_width = max(id_rect.width(), info_rect.width())
        id_x = (content_width - id_rect.width()) / 2 + self._collar_id_offset_x
        id_y = self._collar_id_offset_y
        info_x = ((content_width - info_rect.width()) / 2
                  + self._collar_info_offset_x)
        info_y = id_rect.height() + 2 + self._collar_info_offset_y
        min_x = min(id_x, info_x if info_item else id_x)
        min_y = min(id_y, info_y if info_item else id_y)
        max_x = max(id_x + id_rect.width(),
                    info_x + info_rect.width() if info_item else id_x + id_rect.width())
        max_y = max(id_y + id_rect.height(),
                    info_y + info_rect.height() if info_item else id_y + id_rect.height())
        return {
            "hole": ph, "id": id_item, "info": info_item,
            "id_local": QPointF(id_x - min_x, id_y - min_y),
            "info_local": QPointF(info_x - min_x, info_y - min_y),
            "width": max_x - min_x, "height": max_y - min_y,
            "items": items,
        }

    @staticmethod
    def _block_anchor(block, collar_point, anchor, gap):
        x, y = float(collar_point.x()), float(collar_point.y())
        width, height = block["width"], block["height"]
        if anchor == "left":
            return QPointF(x - gap - width, y - height / 2)
        if anchor == "right":
            return QPointF(x + gap, y - height / 2)
        if anchor == "bottom":
            return QPointF(x - width / 2, y + gap)
        return QPointF(x - width / 2, y - gap - height)

    def _set_block_position(self, block, point):
        block["id"].setPos(point + block["id_local"])
        if block["info"]:
            block["info"].setPos(point + block["info_local"])
        block["rect"] = QRectF(
            point.x(), point.y(), block["width"], block["height"])

    def _add_block_leader(self, block, target):
        rect = block["rect"]
        start = rect.center()
        # Start from the closest horizontal edge for a shorter, clearer leader.
        start.setX(rect.left() if target.x() < rect.center().x() else rect.right())
        leader = self.scene.addLine(
            start.x(), start.y(), target.x(), target.y(),
            QPen(QColor(COLORS['text_light']), 0.7))
        leader._is_leader = True
        leader._hole_id = block["hole"].hole_id
        leader.setZValue(8)
        self._hole_items.setdefault(block["hole"].hole_id, []).append(leader)

    def _place_single_block(self, block, collar_point, requested, occupied):
        choices = (["top", "left", "right", "bottom"]
                   if requested == "auto" else [requested])
        gap = self._collar_marker_size / 2 + 4
        chosen = None
        moved = False
        for anchor in choices:
            base = self._block_anchor(block, collar_point, anchor, gap)
            for shift in range(0, 61, 4):
                point = QPointF(base.x() + (shift if anchor == "right" else
                                            -shift if anchor == "left" else 0),
                                base.y() - (shift if anchor in ("top", "bottom") else 0))
                rect = QRectF(point.x(), point.y(), block["width"], block["height"])
                padded = rect.adjusted(-3, -3, 3, 3)
                if not any(padded.intersects(other) for other in occupied):
                    chosen = point
                    moved = shift > 0 or anchor != choices[0]
                    occupied.append(padded)
                    break
            if chosen is not None:
                break
        if chosen is None:
            chosen = self._block_anchor(block, collar_point, choices[0], gap)
            occupied.append(QRectF(
                chosen.x() - 3, chosen.y() - 3,
                block["width"] + 6, block["height"] + 6))
        self._set_block_position(block, chosen)
        if moved:
            self._add_block_leader(block, collar_point)

    def _trajectory_leader_target(self, ph):
        depth = min(5.0, max(ph.total_depth, 0.0))
        point = self._interp_at_depth(ph, depth)
        if point is None:
            first = ph.points[min(1, len(ph.points) - 1)]
            point = (first.along, first.elevation)
        return self._to_scene(point[0], point[1])

    def _place_shared_cluster(self, cluster, blocks, occupied):
        ph0 = cluster[0][0]
        collar = self._to_scene(ph0.points[0].along, ph0.points[0].elevation)
        entries = []
        for (ph, _dh), block in zip(cluster, blocks):
            if len(ph.points) > 1:
                dx = ph.points[1].along - ph.points[0].along
                dz = ph.points[1].elevation - ph.points[0].elevation
            else:
                dx, dz = 0.0, -1.0
            entries.append((math.atan2(dz, dx), dx, block))
        entries.sort(key=lambda entry: entry[0])
        centre_entry = None
        if len(entries) == 3:
            left, centre_entry, right = [entries[0]], entries[1], [entries[2]]
        else:
            left = [entry for entry in entries if entry[1] < -1e-6]
            right = [entry for entry in entries if entry[1] >= -1e-6]
            if not left or not right:
                split = (len(entries) + 1) // 2
                left, right = entries[:split], entries[split:]

        def place_column(column, side):
            if not column:
                return
            total_height = sum(entry[2]["height"] + 5 for entry in column) - 5
            y = collar.y() - self._collar_marker_size / 2 - 12 - total_height
            for _angle, _dx, block in column:
                x = (collar.x() - 28 - block["width"]
                     if side == "left" else collar.x() + 28)
                point = QPointF(x, y)
                rect = QRectF(x, y, block["width"], block["height"])
                while any(rect.adjusted(-3, -3, 3, 3).intersects(other)
                          for other in occupied):
                    point.setY(point.y() - 8)
                    rect.moveTop(point.y())
                self._set_block_position(block, point)
                occupied.append(rect.adjusted(-3, -3, 3, 3))
                self._add_block_leader(
                    block, self._trajectory_leader_target(block["hole"]))
                y += block["height"] + 5

        if centre_entry:
            block = centre_entry[2]
            point = QPointF(
                collar.x() - block["width"] / 2,
                collar.y() - self._collar_marker_size / 2 - 30 - block["height"])
            rect = QRectF(point.x(), point.y(), block["width"], block["height"])
            while any(rect.adjusted(-3, -3, 3, 3).intersects(other)
                      for other in occupied):
                point.setY(point.y() - 8)
                rect.moveTop(point.y())
            self._set_block_position(block, point)
            occupied.append(rect.adjusted(-3, -3, 3, 3))
            self._add_block_leader(
                block, self._trajectory_leader_target(block["hole"]))
        place_column(left, "left")
        place_column(right, "right")

    def _draw_labels(self, sr):
        """Draw collision-safe blocks and fan layouts for shared collars."""
        id_font = QFont("Segoe UI", int(self._collar_id_font_size))
        id_font.setBold(True)
        info_font = QFont("Segoe UI", int(self._collar_info_font_size))
        occupied = []
        from ..core.short_ids import compact_labels
        labels = compact_labels([d.hole_id for d in (self._drillholes or [])]
                                or [ph.hole_id for ph in sr.holes])
        for cluster in self._collar_clusters(sr):
            blocks = [
                self._create_annotation_block(
                    ph, dh, id_font, info_font, labels)
                for ph, dh in cluster
            ]
            if len(cluster) > 1:
                self._place_shared_cluster(cluster, blocks, occupied)
                continue
            ph = cluster[0][0]
            collar_point = self._to_scene(
                ph.points[0].along, ph.points[0].elevation)
            self._place_single_block(
                blocks[0], collar_point, self._collar_id_position, occupied)

    @staticmethod
    def _footer_side(requested, automatic_side):
        if requested == "auto":
            return automatic_side
        return "left" if requested.endswith("left") else "right"

    # --- v2.7.6.2 : badges « de page » (nord, azimut, échelle) -----------
    # v2.7.6.9 : badges uniquement à l'écran — l'export a été retiré
    # définitivement (AUDIT_V2.7.6.9.md), la machinerie de masquage des
    # badges pendant le rendu export n'existe plus.
    def _draw_north_badge(self):
        """v2.7.6.3 (ORI-03) — rose de localisation en vue de plan.

        Le nord reste en haut et la trace de la coupe est fléchée à son
        azimut réel, de P1 vers P2. Faire tourner une aiguille dans le plan
        d'une coupe verticale était trompeur : ce plan n'a pas de nord.
        """
        if not self._line:
            return
        from ..core.geometry import (
            azimuth_label, section_azimuth_degrees, section_rose_model)
        az = section_azimuth_degrees(
            self._line.x1, self._line.y1, self._line.x2, self._line.y2)
        radius = 11.0
        cx, cy = 30.0, 32.0
        model = section_rose_model(az, cx, cy, radius)
        items = []

        disc = self.scene.addEllipse(
            cx - radius * 1.35, cy - radius * 1.35,
            radius * 2.7, radius * 2.7,
            QPen(QColor(COLORS['border']), 0.7),
            QBrush(QColor(255, 255, 255, 232)))
        disc.setZValue(14)
        items.append(disc)

        trace_pen = QPen(QColor("#B03A2E"), 1.4)
        trace = self.scene.addLine(
            model["p1"][0], model["p1"][1], model["p2"][0], model["p2"][1],
            trace_pen)
        trace.setZValue(15)
        head = self.scene.addPolygon(
            QPolygonF([QPointF(*point) for point in model["arrow"]]),
            QPen(QColor("#B03A2E"), 0.5), QBrush(QColor("#B03A2E")))
        head.setZValue(16)
        items.extend([trace, head])

        needle = model["needle"]
        south = self.scene.addPolygon(
            QPolygonF([QPointF(*point) for point in needle["south"]]),
            QPen(QColor(COLORS['primary']), 0.6), QBrush(QColor(255, 255, 255)))
        south.setZValue(16)
        north = self.scene.addPolygon(
            QPolygonF([QPointF(*point) for point in needle["north"]]),
            QPen(QColor(COLORS['primary']), 0.6),
            QBrush(QColor(COLORS['primary'])))
        north.setZValue(17)
        items.extend([south, north])

        label = self.scene.addText("N", QFont("Segoe UI", 7, QFont.Bold))
        label.setDefaultTextColor(QColor(COLORS['primary']))
        label_x, label_y = needle["label"]
        label.setPos(label_x - label.boundingRect().width() / 2,
                     label_y - label.boundingRect().height() / 2)
        label.setZValue(17)
        items.append(label)

        for key, text in (("p1_label", "P1"), ("p2_label", "P2")):
            mark = self.scene.addText(text, QFont("Segoe UI", 6))
            mark.setDefaultTextColor(QColor("#B03A2E"))
            mx, my = model[key]
            mark.setPos(mx - mark.boundingRect().width() / 2,
                        my - mark.boundingRect().height() / 2)
            mark.setZValue(17)
            items.append(mark)

        # 361 — la direction EN TOUTES LETTRES sous l'azimut : plus
        # personne ne confond l'axe de la ligne et le sens de lecture
        # (retour « WNW / ESE ? » + chef « pourquoi 290° »).
        from ..core.section import compass16
        sens = f"{compass16(az + 180)} → {compass16(az)}"
        caption = self.scene.addText(
            self.tr("coupe {} · {}").format(azimuth_label(az), sens),
            QFont("Segoe UI", 6))
        # 361 — infobulle pédagogique : azimut coupe = P1→P2 ; un
        # forage à ±180° suit le MÊME axe, lu en sens inverse.
        disc.setToolTip(self.tr(
            "Nord en haut · flèche rouge = ligne de coupe, sens P1→P2 "
            "({}).  Un forage dont l'azimut diffère d'environ 180° est "
            "foré LE LONG de la coupe, en sens inverse : même axe, lu "
            "P2→P1 — ce n'est pas une erreur.").format(sens))
        caption.setDefaultTextColor(QColor(COLORS['text_medium']))
        caption.setPos(cx - caption.boundingRect().width() / 2,
                       cy + radius * 1.35 + 2)
        caption.setZValue(17)
        items.append(caption)

        # 332 — « et ça c'est quoi ? » : la boussole s'explique
        # elle-même au survol.
        tip = self.tr(
            "Boussole de la coupe — flèche noire : Nord ; ligne rouge : "
            "ta ligne de coupe P1→P2 vue de dessus ; « coupe N…° » : "
            "azimut de P1 vers P2.")
        for it in items:
            it.setToolTip(tip)

    def _draw_orientation(self, sr):
        side = self._footer_side(self._orientation_position, "left")
        font = QFont("Segoe UI", int(self._orientation_font_size))
        font.setBold(True)
        # 333 — rose 16 : « ESE ---> WNW » au lieu de « E ---> W »
        az_l = float(self._line.azimuth)
        left = compass16(az_l + 180.0)
        right = compass16(az_l)
        # v2.9.321 — le commentaire libre (panneau) s'imprime SOUS la
        # ligne direction/azimut ; le cartouche grandit d'autant.
        note = str(getattr(self, "_orientation_note", "") or "").strip()
        body = self.tr("{}  ---->  {}  |  Azimut {} deg").format(
            left, right, round(self._line.azimuth))
        if note:
            body += "\n" + note
        text = self.scene.addText(body, font)
        text.setDefaultTextColor(QColor(COLORS['primary']))
        rect = text.boundingRect()
        x = 12 if side == "left" else self.scene.width() - rect.width() - 12
        y = self.scene.height() - rect.height() - 8
        # When both controls share a side, the scale moves above this badge.
        background = self.scene.addRect(
            x - 5, y - 4, rect.width() + 10, rect.height() + 8,
            QPen(QColor(COLORS['border']), 0.6),
            QBrush(QColor(255, 255, 255, 230)))
        background.setZValue(14)
        text.setPos(x, y)
        text.setZValue(15)

    def _draw_scale_bar(self, sr):
        side = self._footer_side(self._scale_position, "right")
        orientation_side = self._footer_side(
            self._orientation_position, "left")
        target_pixels = {"small": 80, "medium": 120, "large": 170}.get(
            self._scale_size, 120)
        real_length = self._nice(target_pixels / max(self._sx, 1e-9))
        pixel_length = real_length * self._sx
        max_width = max(self.scene.width() * 0.35, 30)
        while pixel_length > max_width and real_length > 1e-9:
            real_length /= 2.0
            pixel_length = real_length * self._sx
        x = 14 if side == "left" else self.scene.width() - pixel_length - 14
        x = min(max(x, 12), self.scene.width() - pixel_length - 12)
        y = self.scene.height() - 12
        if self._show_orientation and side == orientation_side:
            # v2.9.321 — cartouche à 2 lignes (commentaire) : l'échelle
            # remonte d'autant pour ne pas le chevaucher.
            y -= 58 if str(
                getattr(self, "_orientation_note", "") or "").strip() else 42
        pen = QPen(QColor(COLORS['primary']), 1.5)
        line = self.scene.addLine(x, y, x + pixel_length, y, pen)
        tick1 = self.scene.addLine(x, y - 5, x, y + 5, pen)
        tick2 = self.scene.addLine(
            x + pixel_length, y - 5, x + pixel_length, y + 5, pen)
        for item in (line, tick1, tick2):
            item.setZValue(15)
        font_size = {"small": 7, "medium": 8, "large": 10}.get(
            self._scale_size, 8)
        label = self.scene.addText(
            f"H: {real_length:g} {self._distance_unit}  |  Exag. V: {self._v_exag:.1f}x"
            + (f"  |  {self._scale_ratio_text}"
               if getattr(self, "_scale_ratio_text", "") else ""),
            QFont("Segoe UI", font_size))
        label.setDefaultTextColor(QColor(COLORS['primary']))
        label_x = x + (pixel_length - label.boundingRect().width()) / 2
        label_x = min(max(label_x, 4),
                      self.scene.width() - label.boundingRect().width() - 4)
        label.setPos(label_x, y - label.boundingRect().height() - 4)
        label.setZValue(15)

    def _common_ratio(self) -> int:
        """N de l'échelle de projet. Réglage « section_scale.ratio » :
        absent ou -1 → AUTO (la plus longue coupe du projet tient dans la
        largeur de référence) ; 0 → ancien mode « ajustée à la fenêtre » ;
        N > 0 → échelle fixe 1:N. Retourne 0 = ancien mode."""
        try:
            md = getattr(getattr(self, "_parent_section", None), "main_dock", None)
            cfg = (getattr(getattr(md, "project", None), "config", None) or {})
            raw = (cfg.get("section_scale") or {}).get("ratio", -1)
            n = int(raw if raw is not None else -1)
            if n > 0:
                return n
            if n == 0:
                return 0
            from ..core.section_scale import auto_project_ratio, unit_factor
            lengths = []
            for sec in (cfg.get("sections") or []):
                try:
                    lengths.append(float(sec.get("length") or math.hypot(
                        float(sec["x2"]) - float(sec["x1"]),
                        float(sec["y2"]) - float(sec["y1"]))))
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("section_scale : longueur de coupe", _exc)
            line = getattr(self, "_line", None)
            if line is not None:
                lengths.append(float(line.length))
            longest = max(lengths, default=0.0)
            if longest <= 0:
                return 0
            return auto_project_ratio(longest, unit_factor(self._distance_unit))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_scale : _common_ratio", _exc)
            return 0

    def _elev_window_mode(self) -> bool:
        """392 — « Fenêtre d'élévation commune au projet » activée ?"""
        try:
            md = getattr(getattr(self, "_parent_section", None), "main_dock", None)
            cfg = (getattr(getattr(md, "project", None), "config", None) or {})
            return ((cfg.get("section_scale") or {}).get("elev_window")
                    or "project") == "project"
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_scale : _elev_window_mode", _exc)
            return False

    def _project_elev_extrema(self):
        """(zmin, zmax) d'AFFICHAGE de tout le projet (collets + extrémités de
        trajectoire, profils Auger/Puits pris en compte), mis en cache."""
        dhs = self._drillholes or []
        md = getattr(getattr(self, "_parent_section", None), "main_dock", None)
        cfgd = ((getattr(getattr(md, "project", None), "config", None) or {})
                .get("display_profiles"))
        sig = (id(dhs), len(dhs), repr(cfgd))
        cache = getattr(self, "_elev_extrema_cache", None)
        if cache and cache[0] == sig:
            return cache[1]
        from ..core.display_profiles import make_display_transform
        zmin, zmax = float("inf"), float("-inf")
        for dh in dhs:
            tr = getattr(dh, "trajectory", None) or []
            if not tr:
                continue
            T = make_display_transform(dh, cfgd)
            zs = [float(dh.collar.z), float(tr[0].z), float(tr[-1].z)]
            if T:
                zs = [zs[0], float(T(tr[0].z)), float(T(tr[-1].z))]
            zmin, zmax = min(zmin, *zs), max(zmax, *zs)
        res = (zmin, zmax) if zmin <= zmax else None
        self._elev_extrema_cache = (sig, res)
        return res

    def _apply_common_elev_window(self, sr) -> None:
        """392 — fenêtre d'élévation COMMUNE à toutes les coupes (comme la 3D,
        où toutes les altitudes sont dans le même repère) : un même horizon
        tombe à la même hauteur d'une coupe à l'autre, mêmes graduations.
        Jamais plus étroite que les données de la coupe (aucun écrêtage) ;
        idempotent : la fenêtre propre de la coupe est mémorisée puis
        restituée avant chaque rendu (retour à « Auto » possible)."""
        applied = float(getattr(sr, "_assay_pad_m", 0.0) or 0.0)
        if applied:                               # marge noms de teneurs (re-calculée après)
            sr.min_elev += applied
        sr._assay_pad_m = 0.0
        if getattr(sr, "_elev_base", None) is None:
            sr._elev_base = (sr.min_elev, sr.max_elev,
                             sr.data_min_elev, sr.data_max_elev)
        (sr.min_elev, sr.max_elev,
         sr.data_min_elev, sr.data_max_elev) = sr._elev_base
        if not self._elev_window_mode():
            return
        ext = self._project_elev_extrema()
        if not ext:
            return
        from ..core.section_scale import (
            common_elev_window, grid_step_for_ratio, unit_factor)
        step = self._elevation_grid_step if self._elevation_grid_step > 0 else 20.0
        n_eff = self._effective_ratio()
        if n_eff:
            step = max(step, grid_step_for_ratio(
                n_eff, unit_factor(self._distance_unit), self._v_exag))
        lo, hi = common_elev_window(ext[0], ext[1], step)
        # Place des noms de teneurs sous le trou le plus profond du PROJET
        # (pire cas : trou vertical) : intégrée à la fenêtre COMMUNE, pour que
        # la marge ne creuse pas la fenêtre d'une seule coupe.
        ctx_fn = getattr(self, "_assay_label_context", None)
        ctx = ctx_fn() if ctx_fn else None
        if ctx is not None and self._sy > 0:
            from ..core.assay_label_layout import stack_extent
            _el, subs, _ln = ctx
            th = QFontMetricsF(self._assay_label_font()).height()
            max_mid = max(abs(0.5 * (float(x["inner"]) + float(x["outer"])))
                          for x in subs)
            need_px = (stack_extent(len(subs), th, 1.0) + max_mid + 6.0
                       + (26.0 if getattr(self, "_show_depth", True) else 0.0))
            lo = min(lo, math.floor((ext[0] - need_px / self._sy) / step) * step)
        sr.min_elev = min(lo, sr.min_elev)
        sr.max_elev = max(hi, sr.max_elev)
        sr.data_min_elev = sr.min_elev            # graduations sur toute la fenêtre
        sr.data_max_elev = sr.max_elev

    def _effective_ratio(self) -> float:
        """N effectif du rendu courant : export imposé, sinon échelle de projet,
        sinon 0 (échelle automatique : graduations historiques)."""
        from ..core.section_scale import ratio_from_sx, unit_factor
        fx = getattr(self, "_fixed_sx", None)
        if fx:
            return ratio_from_sx(fx, unit_factor(self._distance_unit))
        return float(self._common_ratio())

    @staticmethod
    def _nice(raw):
        if raw <= 0:
            return 1
        exp = math.floor(math.log10(raw))
        base = 10 ** exp
        f = raw / base
        if f < 1.5:
            return base
        if f < 3:
            return 2 * base
        if f < 7:
            return 5 * base
        return 10 * base

    def drawForeground(self, painter, rect):
        """v2.9.310/312 : encart « zone » fixe (plan + fenêtre)."""
        super().drawForeground(painter, rect)
        if not getattr(self, "_zone_inset", True):
            return
        line = getattr(self, "_line", None)
        holes = getattr(self, "_drillholes", None)
        if line is None or not holes:
            return
        from ..core.track_layout import (zone_inset_frame, zone_inset_project, mini_section_points)
        vp = self.viewport()
        frame = zone_inset_frame(vp.width(), vp.height())
        pts = [mini_section_points(line, h) for h in holes if h.trajectory]
        if frame is None or not pts:
            return
        view_along = None
        sr = getattr(self, "_result", None)
        sx = getattr(self, "_sx", 0)
        if sr is not None and sx:
            vis = self.mapToScene(vp.rect()).boundingRect()
            cl = getattr(self, "_content_left", 0)
            view_along = (sr.min_along + (vis.left() - cl) / sx, sr.min_along + (vis.right() - cl) / sx)
        polys, win = zone_inset_project(pts, frame, view_along)
        painter.save()
        try:
            painter.resetTransform()
            painter.setRenderHint(QPainter.Antialiasing, True)
            x0, y0, fw, fh = frame
            painter.setPen(QPen(QColor("#999999"), 1))
            painter.setBrush(QColor(255, 255, 255, 235))
            painter.drawRoundedRect(QRectF(x0, y0, fw, fh), 4, 4)
            painter.setClipRect(QRectF(x0 + 3, y0 + 3, fw - 6, fh - 6))
            for poly, sel in polys:
                painter.setPen(QPen(QColor("#0f76ff") if sel else QColor("#555555"), 1.6 if sel else 1.0))
                painter.drawPolyline(QPolygonF([QPointF(px, py) for px, py in poly]))
            if win:
                painter.setPen(QPen(QColor("#0f76ff"), 1.4))
                painter.setBrush(QColor(15, 118, 255, 45))
                painter.drawRect(QRectF(*win))
        finally:
            painter.restore()

    def contextMenuEvent(self, event):
        # v2.9.179 — clic droit sur un forage → « Exclure de la coupe »
        # (proposition validée ; logique dans ui/section_holes.py).
        from .section_holes import canvas_context_menu
        canvas_context_menu(self, event)

    def mousePressEvent(self, event):
        # v2.9.13 — clic gauche OU molette : on mémorise ; le pan ne
        # démarre qu'après 4 px de glisser (évident, sans modificateur).
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            self._pan_press = event.pos()
            self._pan_last = event.pos()
            self._pan_button = event.button()
            self._panning = False
            # Ne pas avaler le press : laisse le survol/tooltip et la
            # sélection de forage fonctionner sur un simple clic.
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_press is not None and self._pan_button is not None:
            if not self._panning:
                delta0 = event.pos() - self._pan_press
                if abs(delta0.x()) + abs(delta0.y()) >= 4:
                    # Glisser détecté → pan (main fermée). Tout le monde
                    # sait « cliquer-glisser pour déplacer ».
                    self._panning = True
                    self.viewport().setCursor(Qt.ClosedHandCursor)
            if self._panning:
                delta = event.pos() - self._pan_last
                self._pan_last = event.pos()
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - delta.x())
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - delta.y())
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_panning = self._panning
        if event.button() == self._pan_button:
            self._panning = False
            self._pan_press = None
            self._pan_last = None
            self._pan_button = None
            self.viewport().setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
        if was_panning:
            # Le glisser a déplacé la vue : ne pas traiter comme un clic.
            event.accept()
        elif event.button() == Qt.LeftButton:
            self._handle_interval_click(event.pos())

    def mouseDoubleClickEvent(self, event):
        """351 — double-clic sur un trou = le faire passer DEVANT
        (re-double-clic = rend la place).  C'est LE geste attendu
        depuis le début : « 9 cache 5 au croisement » → double-clic 5.
        """
        if event.button() == Qt.LeftButton:
            try:
                from .section_holes import hole_id_at
                hid = hole_id_at(self, event.pos())
                if hid:
                    dock = getattr(self, "_parent_section", None)
                    ws = getattr(
                        getattr(dock, "main_dock", None),
                        "workspace_state", None)
                    cur = getattr(self, "_selected", None)
                    target = None if cur == hid else hid
                    if ws is not None:
                        ws.set("selected_hole_id", target)
                    else:
                        self.highlight_hole(target)
                    # 359 — le geste doit avoir un effet VISIBLE : le
                    # trou passe premier dans l'ordre explicite.
                    if target is None:
                        self.send_hole_to_back(hid)
                    else:
                        self.bring_hole_to_front(hid)
                    event.accept()
                    return
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Coupe : double-clic trou devant", _exc)
        super().mouseDoubleClickEvent(event)

    def _handle_interval_click(self, pos):
        ws = None
        if getattr(self, "_parent_section", None) and getattr(self._parent_section, "main_dock", None):
            ws = getattr(self._parent_section.main_dock, "workspace_state", None)

        scene_pos = self.mapToScene(pos)
        items_at_pos = self.items(pos)
        import re
        found_target = None

        # v2.9.260 — MESURES `structure` (ponctuelles) : clic 2D →
        # sélection partagée, identifiée par `data(0)` posé sur chaque
        # item (voir section_structure.draw_structures).  Avant, la Vue
        # 3D ne voyait RIEN (l'infobulle n'a pas de plage from–to).
        from .section_structure import (
            apply_structure_click, structure_click_target)
        _target = structure_click_target(items_at_pos)
        if _target is not None:
            apply_structure_click(ws, _target)
            return

        for item in items_at_pos:
            # Ne pas utiliser les hit-pads élargis (AcceptedMouseButtons == NoButton)
            if hasattr(item, "acceptedMouseButtons") and item.acceptedMouseButtons() == Qt.NoButton:
                continue
            tip = item.toolTip() or ""
            if not tip:
                continue
            m = re.search(r"([A-Za-z0-9_\-\.]+)\s*[·\:]\s*([0-9\.\,]+)\s*[–\-]\s*([0-9\.\,]+)\s*m", tip)
            if m:
                is_inside = True
                if hasattr(item, "polygon"):
                    is_inside = item.polygon().containsPoint(scene_pos, Qt.OddEvenFill)
                elif hasattr(item, "path"):
                    is_inside = item.path().contains(scene_pos)
                if is_inside:
                    try:
                        hid = m.group(1)
                        fm = float(m.group(2).replace(",", "."))
                        tm = float(m.group(3).replace(",", "."))
                        found_target = (hid, fm, tm, tip)
                        break
                    except ValueError:
                        continue

        if not found_target:
            # Clic dans le vide ou hors intervalle : désélectionne proprement
            if ws and (ws.get_selected_interval() or ws.get("selected_hole_id")):
                ws.clear_selection()
            return

        hole_id, from_m, to_m, tip = found_target
        if ws:
            curr_sel = ws.get_selected_interval()
            # v2.9.141 — get_selected_interval() renvoie un objet
            # IntervalSelection (dataclass), pas un dict : accès par
            # attribut (plus .get()) — corrige l'AttributeError
            # « 'IntervalSelection' object has no attribute 'get' ».
            curr_hole = getattr(curr_sel, "hole_id", None) if curr_sel else None
            curr_from = getattr(curr_sel, "from_m", 0.0) if curr_sel else 0.0
            curr_to = getattr(curr_sel, "to_m", 0.0) if curr_sel else 0.0
            if (curr_sel and curr_hole == hole_id
                    and abs(curr_from - from_m) < 1e-3
                    and abs(curr_to - to_m) < 1e-3):
                # Toggle off si on clique sur l'intervalle déjà sélectionné
                ws.clear_selection()
                return

            ws.select_interval(
                hole_id=hole_id,
                from_m=from_m,
                to_m=to_m,
                domain="section_2d",
                source="section_2d",
                attributes={"tooltip": tip.strip()},
            )

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if not self._panning:
            self.viewport().setCursor(Qt.ArrowCursor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._result:
            QTimer.singleShot(50, self._render)


class SectionWidget(QWidget):

    """Cross-section canvas with one compact, live property panel."""

    _SWATCH_CACHE = {}

    section_generated = pyqtSignal(str)  # emits section name / DELETE:name

    def __init__(self, main_dock=None, parent=None):
        self.main_dock = main_dock
        self._drillholes = []
        self._line = None
        self._litho_styles = {}
        self._sections: dict[int, SectionLine] = {}
        self._current_section_id: Optional[int] = None
        self._buffer_unit = "m"
        # v2.9.179 — exclusions de forages (proposition validée) :
        # état courant + par coupe (historique).  Logique : section_holes.
        self._excluded_holes: set = set()
        self._excluded_by_section: dict = {}
        # v2.9.26 — pile Annuler / Rétablir (mauvaise manip)
        self._undo_stack = []       # snapshots style+assay+geo
        self._redo_stack = []
        self._undo_max = 40
        self._undo_coalesce_timer = None
        self._undo_pending_before = None
        self._undo_baseline = None
        self._undo_restoring = False
        self._loading_settings = False
        self._updating_history = False
        # v2.9.0 — cache du CSV topographie (chemin, mtime, points).
        self._topo_csv_cache = None
        super().__init__(parent)
        self._geometry_timer = QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.setInterval(180)
        self._geometry_timer.timeout.connect(self._apply_geometry_change)
        # v2.9.135 — coalescer clics / sliders / écriture JSON.
        self._style_timer = QTimer(self)
        self._style_timer.setSingleShot(True)
        self._style_timer.setInterval(70)
        self._style_timer.timeout.connect(self._flush_style_change)
        self._exag_timer = QTimer(self)
        self._exag_timer.setSingleShot(True)
        self._exag_timer.setInterval(50)
        self._exag_timer.timeout.connect(self._flush_exag_change)
        self._persist_timer = QTimer(self)
        self._persist_timer.setSingleShot(True)
        self._persist_timer.setInterval(400)
        self._persist_timer.timeout.connect(self._flush_persist)
        self._legends_timer = QTimer(self)
        self._legends_timer.setSingleShot(True)
        self._legends_timer.setInterval(40)
        self._legends_timer.timeout.connect(self._update_legends)
        self._persist_section = False
        self._persist_assay = False
        self._dhs_fp = None
        self._domain_data_memo = None
        self._legend_litho_sig = None
        self.legend_group_collapsible = None
        self._build()
        if self.main_dock and getattr(self.main_dock, "workspace_state", None):
            self.main_dock.workspace_state.subscribe("highlight_code", self.on_workspace_highlight_code)

    # ------------------------------------------------------------------
    # Layout: canvas + one right-hand accordion panel
    # ------------------------------------------------------------------
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # v2.9.136 (Option A) — bandeau unifié en en-tête global du Dock Visualisation :
        # suppression de la barre bleu nuit redondante, gain de 30 px de hauteur utile.
        self.info_label = QLabel()

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(True)
        self.canvas = SectionCanvas()
        self.canvas._parent_section = self
        self.canvas.setMinimumWidth(120)
        # v2.9.180 — le clic droit est ANNONCÉ sur le canvas lui-même
        # (retour écran : « il faut cliquer droit où ? »).
        self.canvas.setToolTip(self.tr(
            "Glisser · déplacer\nSurvol · infos\nMolette · déplacer\nClic droit sur un forage · exclure de la coupe"))
        # v2.9.0 — le canvas demande le profil de sol au widget à chaque
        # régénération (jamais d'état en cache du côté du canvas).
        self.canvas.surface_provider = self._surface_provider
        # v2.9.262 — imagerie : le canvas demande projet/CSV au dock.
        from .section_imagery import imagery_source_dir
        self.canvas.imagery_project_provider = self._project
        self.canvas.imagery_source_dir_provider = lambda: imagery_source_dir(self)
        # v2.9.1 — après CHAQUE rendu, la légende reflète exactement ce
        # que le canvas dessine (l'entrée ligne de sol apparaît/disparaît
        # avec sa source, pas avec l'ordre des appels).
        self.canvas.rendered.connect(self._schedule_legends)
        self.splitter.addWidget(self.canvas)

        panel_scroll = QScrollArea()
        panel_scroll.setWidgetResizable(True)
        panel_scroll.setFrameShape(QFrame.NoFrame)
        panel_scroll.setMinimumWidth(0)
        panel_scroll.setMaximumWidth(300)
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(3, 0, 3, 0)
        panel_layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel(self.tr("PROPRIÉTÉS DE LA COUPE"))
        title.setStyleSheet(
            f"color:{COLORS['primary']}; font-size:9pt; font-weight:bold; padding:5px;")
        title_row.addWidget(title, 1)
        panel_layout.addLayout(title_row)
        # v2.9.29 — Annuler/Rétablir : barre globale du dock Visualisation
        # (coin droit des onglets), plus ici dans Propriétés seules.
        self.undo_btn = None
        self.redo_btn = None

        # v2.9.58 — au chargement : seul « Coupe active » est déplié.
        # v2.9.59 — _loading_settings pendant build (signaux Pistes avant axes).
        self._loading_settings = True
        try:
            panel_layout.addWidget(CollapsibleGroup(
            self.tr("Coupe active"), self._build_active_section_group(), expanded=True))
            # v2.9.181 — HOME SÉMANTIQUE (retour écran : « Inclusion
            # des forages, c'est plus logique ») : buffer = la règle,
            # exclusion = l'exception.  Visibilité : le groupe s'ouvre
            # tout seul dès qu'il y a des exclusions (set_excluded).
            self.inclusion_group = CollapsibleGroup(
            self.tr("Inclusion des forages"), self._build_geometry_group(), expanded=False)
            panel_layout.addWidget(self.inclusion_group)
            panel_layout.addWidget(CollapsibleGroup(
            self.tr("Pistes"), self._build_tracks_group(), expanded=False))
            panel_layout.addWidget(CollapsibleGroup(self.tr(
            "Affichage de la coupe"), self._build_display_group(),
            expanded=False))
            # Topographie = couche de données (MNT/CSV/collets + QC) — accessible
            # en 1ᵉ niveau mais repliée par défaut (v2.9.58).
            panel_layout.addWidget(CollapsibleGroup(self.tr(
            "Topographie (ligne de sol)"),
            self._build_topography_group(), expanded=False))
            self.legend_group_collapsible = CollapsibleGroup(
            self.tr("Légendes"), self._build_legend_group(), expanded=False)
            panel_layout.addWidget(self.legend_group_collapsible)
        finally:
            self._loading_settings = False
        panel_layout.addStretch()
        panel_scroll.setWidget(panel)
        self.splitter.addWidget(panel_scroll)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, True)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([500, 240])
        layout.addWidget(self.splitter, 1)

        # MainDock reparents this single history widget into Assistant step 4.
        # Keeping one instance avoids duplicated rename/delete controls.
        self.history_group = CollapsibleGroup(self.tr(
            "Historique des coupes"), self._build_sections_group(),
            expanded=True)
        self.history_group.setVisible(False)

    @staticmethod
    def _group_frame():
        # v2.7.13.1 — REVUE ÉCRAN (blanc sur blanc) : ce cadre est stylé
        # en propre → c'est le contexte de style de ses enfants SANS
        # feuille (cases « Afficher… », libellés de légende, pastilles,
        # aperçu de rampe). Sans la règle QToolTip, leurs infobulles
        # retombaient sur le thème QGIS (le cadre coupe le cascade).
        frame = QFrame()
        # v2.9.126 — QLabel transparent : un stylesheet partiel sur un
        # QLabel shrink-wrap laisse le fond OS/QGIS (halo blanc autour
        # du texte). Même règle partout (Affichage, Teneurs, Seuils).
        frame.setStyleSheet(
            TOOLTIP_STYLE
            + f"QFrame {{ background:{COLORS['bg_card']}; }}"
            + "QLabel { background: transparent; }")
        return frame

    @staticmethod
    def _panel_subtitle(text):
        label = QLabel(text)
        label.setStyleSheet(
            f"color:{COLORS['primary']}; font-size:8pt; font-weight:bold; "
            f"background:transparent; "
            f"border-bottom:1px solid {COLORS['border']}; padding:5px 0 2px 0;")
        return label

    def _build_tracks_group(self):
        frame = self._group_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 8)
        layout.setSpacing(5)
        layout.addWidget(make_collapsible_help(
            self.tr("Sélectionnez une piste dans la liste pour afficher ses propriétés.")))

        # v2.9.28 — plus d'option « alignés sur l'axe » (motifs toujours
        # fixes écran = légende).  Évite de mélanger l'utilisateur.

        self.track_list = QListWidget()
        self.track_list.setMaximumHeight(130)
        # v2.7.12.8 — les infobulles des pistes : la liste est stylée en
        # propre (contexte de style) → elle porte la règle TOOLTIP_STYLE.
        # v2.9.133 — sélection = bleu accent (comme combos/tables) + texte blanc.
        # v2.9.120 avait copié l'ardoise du bandeau nodata : la ligne
        # active paraissait noire, alors que partout ailleurs c'est bleu.
        self.track_list.setStyleSheet(
            TOOLTIP_STYLE
            + f"QListWidget {{ background:{COLORS['bg_card']}; "
            f"color:{COLORS['text_dark']}; "
            f"border:1px solid {COLORS['border']}; "
            f"selection-background-color:{COLORS['accent']}; "
            f"selection-color:{COLORS['text_white']}; }}"
            + f"QListWidget::item {{ color:{COLORS['text_dark']}; }}"
            + f"QListWidget::item:selected, "
            f"QListWidget::item:selected:active, "
            f"QListWidget::item:selected:!active {{ "
            f"background:{COLORS['accent']}; "
            f"color:{COLORS['text_white']}; }}")
        layout.addWidget(self.track_list)
        self.track_pages = QStackedWidget()
        from .section_imagery import build_imagery_group as _imagery_page
        from .section_geotech import geotech_track_pages, geotech_track_tips
        # v2.9.132 — Intercepts cochable (comme Teneurs). Clic ouvre les
        # règles (teneurs ET + litho OU). Teneurs = grades seulement.
        # v2.9.118 — pages data-dépendantes : corps verrouillé + bandeau
        # si fichier non importé (plus d'édition « fantôme »).
        # v2.9.270 — ordre d'affichage par catégorie (tri stable plus bas).
        pages = [
            (self.tr("Profondeurs"), self._build_depth_group(), "depth",
             False),
            (self.tr("Lithologie"), self._build_litho_group(), "litho", True),
            (self.tr("Trajectoire"), self._build_trajectory_group(),
             "trajectory", False),
            (self.tr("Teneurs"), self._build_assay_group(), "assays", True),
            (self.tr("Intercepts"), self._build_threshold_group(),
             "intercepts", True),
            (self.tr("Altérations"), self._build_alteration_group(),
             "alterations", True),
            (self.tr("Minéralisations"), self._build_mineralization_group(),
             "mineralizations", True),
            (self.tr("Structures"), self._build_structure_group(),
             "structures", True),
            (self.tr("Imagerie"), _imagery_page(self), "imagery", True),
        ]
        pages.extend(geotech_track_pages(self))
        self._track_keys = []  # index → domain key
        self._track_page_bodies = {}   # key → widget props (enable/disable)
        self._track_page_banners = {}  # key → QLabel nodata
        # v2.9.178 — aide des pistes (question réelle : « pourquoi ma
        # piste est grisée ? » → parce que le fichier n'est pas importé).
        # v2.9.178 — bulles courtes (TT-17) ; l'info clé : « grisée =
        # fichier absent » (question réelle des utilisateurs)
        track_tips = {
            "depth": self.tr("Graduations de profondeur"),
            "litho": self.tr(
                "Codes + motifs du Référentiel · grisée sans fichier"),
            "trajectory": self.tr("Trace des forages"),
            "assays": self.tr(
                "1–3 éléments, rampe/élément · grisée sans analyses"),
            "intercepts": self.tr("Règles de seuil · grisée sans analyses"),
            "alterations": self.tr(
                "Intensité → largeur · grisée sans fichier"),
            "mineralizations": self.tr(
                "Styles + symboles · grisée sans fichier"),
            "structures": self.tr(
                "Points par mesure, couleur du Référentiel · grisée sans fichier"),
            "imagery": self.tr(
                "Bandes photo/scan + cache ≈ 512 px · grisée sans fichier"),
        }
        track_tips.update(geotech_track_tips(self))
        # v2.9.270 — liste Pistes par catégorie (Coupe → Géologie →
        # Géochimie → Géotechnique → Média) ; tri stable, titres non
        # interactifs (UserRole None, ignorés partout).
        _GROUP_OF = {"depth": 0, "trajectory": 0, "litho": 1,
                     "alterations": 1, "mineralizations": 1, "structures": 1,
                     "assays": 2, "intercepts": 2, "rqd": 3, "recovery": 3,
                     "density": 3, "imagery": 4}
        _GROUP_TITLES = {0: self.tr("Coupe"), 1: self.tr("Géologie"),
                         2: self.tr("Géochimie"), 3: self.tr("Géotechnique"),
                         4: self.tr("Média")}
        pages.sort(key=lambda e: _GROUP_OF.get(e[2], 5))
        current_group = None
        for index, (name, page, key, data_dep) in enumerate(pages):
            grp = _GROUP_OF.get(key, 5)
            if grp != current_group:
                current_group = grp
                head = QListWidgetItem(
                    _GROUP_TITLES.get(grp, self.tr("Autres")))
                head.setFlags(Qt.NoItemFlags)
                head.setForeground(QColor(COLORS["text_medium"]))
                self.track_list.addItem(head)
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, index)
            item.setData(Qt.UserRole + 1, key)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setToolTip(track_tips.get(key, name))
            self.track_list.addItem(item)
            if data_dep:
                page = self._wrap_data_track_page(key, name, page)
            self.track_pages.addWidget(page)
            self._track_keys.append(key)
        # cases par CLÉ de domaine (pas par ligne) : requis avec des titres.
        self._track_checkboxes = {
            "depth": self.chk_depth, "litho": self.chk_litho,
            "trajectory": self.chk_trajectory, "assays": self.chk_assays,
            "intercepts": self.chk_intercepts,
            "alterations": self.chk_alterations,
            "mineralizations": self.chk_mineralizations,
            "structures": self.chk_structures, "imagery": self.chk_imagery,
            "rqd": self.chk_rqd, "recovery": self.chk_recovery,
            "density": self.chk_density}
        self._track_data_keys = {
            key: True for (_n, _p, key, dep) in pages if dep}
        self._syncing_tracks = False
        self.track_list.itemClicked.connect(
            lambda item: self.track_pages.setCurrentIndex(
                int(item.data(Qt.UserRole)))
            if item.data(Qt.UserRole) is not None else None)
        self.track_list.itemChanged.connect(self._on_track_item_changed)
        for checkbox in self._track_checkboxes.values():
            if checkbox is None:
                continue
            checkbox.stateChanged.connect(self._sync_track_checks)
        for _r in range(self.track_list.count()):  # 1re piste, pas un titre
            if self.track_list.item(_r).data(Qt.UserRole) is not None:
                self.track_list.setCurrentRow(_r)
                break
        layout.addWidget(self.track_pages)
        return frame

    def _on_track_item_changed(self, item):
        if self._syncing_tracks:
            return
        # piste sans données : ignorer la recoché manuelle
        if not (item.flags() & Qt.ItemIsUserCheckable):
            return
        if not (item.flags() & Qt.ItemIsEnabled):
            return
        if item.data(Qt.UserRole) is None:  # ligne de titre
            return
        checkbox = self._track_checkboxes.get(
            str(item.data(Qt.UserRole + 1) or ""))
        if checkbox and checkbox.isEnabled():
            checkbox.setChecked(item.checkState() == Qt.Checked)

    def _sync_track_checks(self, *_args):
        if not hasattr(self, "track_list"):
            return
        self._syncing_tracks = True
        for index in range(self.track_list.count()):
            item = self.track_list.item(index)
            if item is None or item.data(Qt.UserRole) is None:
                continue  # ligne de titre
            checkbox = self._track_checkboxes.get(
                str(item.data(Qt.UserRole + 1) or ""))
            if checkbox is None:
                continue
            if not checkbox.isEnabled():
                # pas de données → forcer décoché + non interactif
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(
                    Qt.Checked if checkbox.isChecked() else Qt.Unchecked)
        self._syncing_tracks = False

    def _domain_file_imported(self, key: str) -> bool:
        """True si un fichier source est enregistré pour ce domaine.

        v2.9.120 — critère « fichier chargé » (pas seulement des
        intervalles déjà attachés aux forages). Un CSV importé à
        l'étape 2 active la piste même avant la géométrie 3D.
        """
        ft = {
            "litho": "litho",
            "assays": "assays",
            "intercepts": "assays",  # même CSV que Teneurs
            "alterations": "alterations",
            "mineralizations": "mineralizations",
            "structures": "structure",  # v2.9.260 (étape 2)
            "imagery": "imagery",       # v2.9.262 (Chantier 2 E2)
            "rqd": "rqd",               # v2.9.264 (Chantier 3)
            "recovery": "recovery",
            "density": "density",
        }.get(str(key))
        if not ft:
            return False
        project = None
        try:
            project = self._project() if hasattr(self, "_project") else None
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Import CSV : _domain_file_imported", _exc)
            project = None
        if project is None and getattr(self, "main_dock", None):
            project = getattr(self.main_dock, "project", None)
        if project is None:
            return False
        try:
            if project.get_imported_file_path(ft):
                return True
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Import CSV : _domain_file_imported", _exc)
            # chemin optionnel
            pass
        try:
            name = (project.config.get("imported_files") or {}).get(ft)
            return bool(str(name or "").strip())
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Import CSV : _domain_file_imported", _exc)
            return False

    def _default_track_checked(self, key: str) -> bool:
        """Piste cochée par défaut quand le domaine a des données.

        v2.9.120 — ON sauf si le projet a enregistré show_*=False.
        """
        style_key = {
            "depth": "show_depth",
            "litho": "show_litho",
            "trajectory": "show_trajectory",
            "assays": "show_assays",
            "intercepts": "show_intercepts",
            "alterations": "show_alterations",
            "mineralizations": "show_mineralizations",
            "structures": "show_structures",
            "imagery": "show_imagery",
            "rqd": "show_rqd",
            "recovery": "show_recovery",
            "density": "show_density",
        }.get(str(key))
        if not style_key:
            return True
        project = None
        try:
            project = self._project() if hasattr(self, "_project") else None
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Pistes : _default_track_checked", _exc)
            project = None
        if project is None:
            return True
        try:
            style = project.get_section_style() or {}
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Pistes : _default_track_checked", _exc)
            return True
        if style_key not in style:
            return True
        return bool(style.get(style_key, True))

    def _project_has_domain_data(self, key: str) -> bool:
        """True si le projet a un fichier / des données pour ce domaine.

        v2.9.117 — une piste cochée sans fichier importé est un bug
        d'architecture (légende « Aucune X disponible » fantôme).
        v2.9.120 — fichier importé OU intervalles attachés : les pistes
        des fichiers déjà chargés restent disponibles et cochées.
        """
        memo = getattr(self, "_domain_data_memo", None)
        k = str(key)
        if isinstance(memo, dict) and k in memo:
            return memo[k]
        found = self._project_has_domain_data_scan(k)
        if isinstance(memo, dict):
            memo[k] = found
        return found

    def _project_has_domain_data_scan(self, key: str) -> bool:
        dhs = getattr(self, "_drillholes", None) or []
        if not dhs and self.main_dock:
            dhs = getattr(self.main_dock, "drillholes", None) or []
        if not dhs and getattr(self, "canvas", None) is not None:
            dhs = getattr(self.canvas, "_drillholes", None) or []
        if key in ("depth", "trajectory"):
            # toujours disponibles dès qu'il y a des forages
            return bool(dhs)
        # v2.9.120 — fichier importé = domaine chargé (même sans dhs)
        if self._domain_file_imported(key):
            return True
        if key == "litho":
            for dh in dhs or []:
                if getattr(dh, "litho", None):
                    return True
            try:
                return bool(get_all_litho_codes(dhs) if dhs else [])
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Projet (sauvegarde/chargement) : _project_has_domain_data_scan", _exc)
                return False
        if key in ("assays", "intercepts"):
            # Intercepts : mêmes données que Teneurs (litho = filtre optionnel)
            for dh in dhs or []:
                if getattr(dh, "assays", None):
                    return True
            try:
                if getattr(self, "canvas", None) is not None:
                    return bool(self.canvas.get_available_elements())
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Projet (sauvegarde/chargement) : _project_has_domain_data_scan", _exc)
                # canvas pas prêt — scan manuel ci-dessous
                pass
            for dh in dhs or []:
                for iv in getattr(dh, "assays", None) or []:
                    attrs = getattr(iv, "attributes", None) or {}
                    for k, v in attrs.items():
                        if k in ("hole_id", "from", "to", "lithology",
                                 "alteration"):
                            continue
                        if isinstance(v, (int, float)):
                            return True
                        # valeurs numériques stockées en texte
                        try:
                            if str(v).strip() and float(
                                    str(v).replace(",", ".")):
                                return True
                        except (TypeError, ValueError):
                            continue
            return False
        if key == "alterations":
            for dh in dhs or []:
                if getattr(dh, "alterations", None):
                    return True
            return False
        if key == "mineralizations":
            for dh in dhs or []:
                if getattr(dh, "mineralizations", None):
                    return True
            return False
        if key == "structures":
            from .section_structure import has_data
            return has_data(dhs)
        if key == "imagery":
            from .section_imagery import has_data as imagery_has_data
            return imagery_has_data(dhs)
        if key in ("rqd", "recovery", "density"):
            from .section_geotech import has_data as geotech_has_data
            return geotech_has_data(dhs, key)
        return True

    def _wrap_data_track_page(self, key: str, title: str, body: "QWidget"):
        """v2.9.118 — enveloppe page piste data-dépendante.

        Corps (réglages) + bandeau nodata. Sans fichier importé : corps
        désactivé, bandeau visible → impossible de « changer des infos »
        d'un domaine absent.
        """
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        file_lab = {
            "assays": self.tr("Teneurs"),
            "intercepts": self.tr("Teneurs (requis pour les intercepts)"),
            "alterations": self.tr("Altérations"),
            "mineralizations": self.tr("Minéralisations"),
            "structures": self.tr("Structures"),
            "imagery": self.tr("Imagerie"),
            "litho": self.tr("Lithologie"),
            "rqd": self.tr("RQD"),
            "recovery": self.tr("Récupération"),
            "density": self.tr("Densité"),
        }.get(str(key), title)
        banner = QLabel(
            self.tr("<b>Aucun fichier {} importé.</b><br>Importez le fichier correspondant (Assistant → Import) pour afficher et régler cette piste. Les propriétés ci-dessous restent verrouillées tant que les données sont absentes.").format(file_lab))
        # v2.9.120 — pas label_hint (gris) : texte BLANC sur ardoise.
        banner.setObjectName("label_nodata_banner")
        banner.setWordWrap(True)
        banner.setTextFormat(Qt.RichText)
        banner.setStyleSheet(
            f"background:{COLORS.get('bg_header', '#2C3E50')}; "
            f"color:{COLORS.get('text_white', '#FFFFFF')}; "
            f"border:1px solid {COLORS.get('border_dark', '#AEB6BF')}; "
            f"border-radius:4px; padding:8px;")
        banner.setVisible(False)
        lay.addWidget(banner)
        lay.addWidget(body, 1)
        if not hasattr(self, "_track_page_bodies") or self._track_page_bodies is None:
            self._track_page_bodies = {}
        if not hasattr(self, "_track_page_banners") or self._track_page_banners is None:
            self._track_page_banners = {}
        self._track_page_bodies[str(key)] = body
        self._track_page_banners[str(key)] = banner
        return wrap

    def _set_track_page_editable(self, key: str, has_data: bool) -> None:
        """Active/désactive le corps de page + bandeau nodata (v2.9.118)."""
        k = str(key)
        body = (getattr(self, "_track_page_bodies", None) or {}).get(k)
        banner = (getattr(self, "_track_page_banners", None) or {}).get(k)
        if body is not None:
            try:
                body.setEnabled(bool(has_data))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Pistes : _set_track_page_editable", _exc)
                # widget mort
                pass
        if banner is not None:
            try:
                banner.setVisible(not bool(has_data))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Pistes : _set_track_page_editable", _exc)
                # banner optionnel
                pass
        # intercepts : formulaire de règles (teneurs + filtre litho)
        if k == "intercepts":
            try:
                if hasattr(self, "threshold_subtab"):
                    self.threshold_subtab.setEnabled(bool(has_data))
                if hasattr(self, "threshold_group"):
                    self.threshold_group.setEnabled(bool(has_data))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Pistes : _set_track_page_editable", _exc)
                # formulaire optionnel
                pass

    def _refresh_track_availability(self, *, apply_defaults: bool = False):
        """Grise / décoche les pistes sans données importées.

        v2.9.118 — verrouille aussi la page de propriétés (corps disabled
        + bandeau « Importez le fichier… »). Plus d'édition fantôme.
        """
        if not hasattr(self, "track_list") or not hasattr(
                self, "_track_checkboxes"):
            return
        self._domain_data_memo = {}
        # mapping key → checkbox
        key_to_chk = {
            "depth": getattr(self, "chk_depth", None),
            "litho": getattr(self, "chk_litho", None),
            "trajectory": getattr(self, "chk_trajectory", None),
            "assays": getattr(self, "chk_assays", None),
            "intercepts": getattr(self, "chk_intercepts", None),
            "alterations": getattr(self, "chk_alterations", None),
            "mineralizations": getattr(self, "chk_mineralizations", None),
            "structures": getattr(self, "chk_structures", None),
            "imagery": getattr(self, "chk_imagery", None),
            "rqd": getattr(self, "chk_rqd", None),
            "recovery": getattr(self, "chk_recovery", None),
            "density": getattr(self, "chk_density", None),
        }
        self._syncing_tracks = True
        try:
            for index in range(self.track_list.count()):
                item = self.track_list.item(index)
                # v2.9.270 — ligne de titre (UserRole None) : ignorée.
                if item is None or item.data(Qt.UserRole) is None:
                    continue
                key = str(item.data(Qt.UserRole + 1) or "")
                if not key:
                    continue
                has = self._project_has_domain_data(key)
                chk = key_to_chk.get(key)
                # always-on structural tracks stay enabled if holes exist
                if key in ("depth", "trajectory"):
                    has = bool(getattr(self, "_drillholes", None)
                               or (self.main_dock and getattr(
                                   self.main_dock, "drillholes", None))
                               or has)
                # item flags
                flags = item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled
                flags |= Qt.ItemIsUserCheckable
                if not has:
                    # sélectionnable (pour lire le bandeau) mais non coché
                    if chk is not None:
                        chk.blockSignals(True)
                        chk.setChecked(False)
                        chk.setEnabled(False)
                        chk.blockSignals(False)
                    item.setCheckState(Qt.Unchecked)
                    try:
                        item.setForeground(QColor(
                            COLORS.get("text_light", "#95A5A6")))
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("Pistes : _refresh_track_availability", _exc)
                        # couleur optionnelle
                        pass
                    tip = {
                        "assays": self.tr("Aucun fichier Teneurs importé."),
                        "intercepts": self.tr(
                            "Aucun fichier Teneurs importé (les intercepts lisent les teneurs ; la litho est un filtre optionnel)."),
                        "alterations": self.tr(
                            "Aucun fichier Altérations importé."),
                        "mineralizations": self.tr(
                            "Aucun fichier Minéralisations importé."),
                        "structures": self.tr(
                            "Aucun fichier Structures importé."),
                        "imagery": self.tr(
                            "Aucun fichier Imagerie importé."),
                        "litho": self.tr(
                            "Aucune lithologie dans le projet."),
                    }.get(key, self.tr("Pas de données pour cette piste."))
                    item.setToolTip(tip + self.tr(" Importez le fichier pour activer."))
                else:
                    if chk is not None:
                        chk.setEnabled(True)
                    # v2.9.133 — ne pas forcer text_dark (écraserait le
                    # blanc de la sélection bleue).
                    try:
                        item.setData(Qt.ForegroundRole, None)
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("Pistes : _refresh_track_availability", _exc)
                        # ForegroundRole optionnel (item déjà détruit)
                        pass
                    item.setToolTip(self.tr(""))
                    if apply_defaults and chk is not None:
                        # data présente : restaurer le style projet (ON)
                        want = self._default_track_checked(key)
                        chk.blockSignals(True)
                        chk.setChecked(bool(want))
                        chk.blockSignals(False)
                        item.setCheckState(
                            Qt.Checked if want else Qt.Unchecked)
                item.setFlags(flags)
                # v2.9.118 — page props : editable IFF has data
                if key in (getattr(self, "_track_page_bodies", None) or {}):
                    self._set_track_page_editable(key, has)
                elif key == "intercepts":
                    # fallback si wrap pas encore posé
                    try:
                        if hasattr(self, "threshold_subtab"):
                            self.threshold_subtab.setEnabled(bool(has))
                        if hasattr(self, "threshold_group"):
                            self.threshold_group.setEnabled(bool(has))
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("Pistes : _refresh_track_availability", _exc)
                        # widgets optionnels
                        pass
        finally:
            self._syncing_tracks = False

    def _build_display_group(self):
        frame = self._group_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 6)
        layout.setSpacing(4)

        layout.addWidget(CollapsibleGroup(self.tr(
            "Cadre, axes et échelle"), self._build_frame_axes_group(),
            expanded=True, level=1))
        layout.addWidget(CollapsibleGroup(self.tr(
            "Annotations des forages"), self._build_collars_group(),
            expanded=False, level=1))
        return frame

    def _build_active_section_group(self):
        frame = self._group_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 8)
        self.section_combo = QComboBox()
        self.section_combo.setStyleSheet(INPUT_STYLE)
        self.section_combo.setToolTip(self.tr("Coupe affichée · gestion = Assistant étape 4"))
        self.section_combo.currentIndexChanged.connect(
            self._on_section_combo_changed)
        layout.addWidget(self.section_combo)
        note = QLabel(self.tr("Renommer et supprimer dans Contrôle → Coupes"))
        note.setObjectName("label_hint")
        note.setWordWrap(True)
        layout.addWidget(note)
        return frame

    def _build_sections_group(self):
        frame = self._group_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(3)
        layout.addWidget(make_collapsible_help(
            self.tr("Sélectionnez une ligne pour ouvrir la coupe. Double-cliquez sur son nom pour le modifier.")))

        self.section_table = QTableWidget(0, 4)
        self.section_table.setHorizontalHeaderLabels([
            self.tr("Nom"), self.tr("Direction"),
            self.tr("Longueur"), self.tr("Buffer"),
        ])
        self.section_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch)
        for column in (1, 2, 3):
            self.section_table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeToContents)
        self.section_table.verticalHeader().setVisible(False)
        self.section_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.section_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.section_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.section_table.setContextMenuPolicy(Qt.CustomContextMenu)
        # v2.7.12.13 — REVUE ÉCRAN (étape 4) : le plafond de 130 px était
        # un reliquat de l'ancienne place de l'historique (bas du panneau
        # coupes). Depuis v2.7.10.34 l'historique vit en permanence dans
        # l'étape 4 : la table OCCUPE l'espace restant de l'étape, et
        # avec beaucoup de coupes elle défile à l'intérieur.
        self.section_table.setMinimumHeight(84)
        self.section_table.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.section_table.setStyleSheet(TABLE_STYLE)
        # itemClicked fires even when the row was already selected, so a
        # single click always reopens the optional visualization dock.
        self.section_table.itemClicked.connect(
            lambda _item: self._on_history_selection())
        self.section_table.itemChanged.connect(self._on_history_item_changed)
        self.section_table.customContextMenuRequested.connect(
            self._show_history_menu)
        layout.addWidget(self.section_table)
        return frame

    def _build_geometry_group(self):
        frame = self._group_frame()
        form = QFormLayout(frame)
        form.setContentsMargins(6, 6, 6, 8)
        form.setSpacing(6)

        self.buffer_spin = QDoubleSpinBox()
        self.buffer_spin.setRange(1, 5000)
        self.buffer_spin.setValue(50.0)
        self.buffer_spin.setSuffix(" m")
        self.buffer_spin.setKeyboardTracking(True)
        self.buffer_spin.setAccelerated(True)
        self.buffer_spin.setStyleSheet(INPUT_STYLE)
        # v2.9.178 — explicite mais COURT (question : « buffer de quoi ? »)
        self.buffer_spin.setToolTip(self.tr("Corridor du trait de coupe · forages < N m · maj auto"))
        self.buffer_spin.valueChanged.connect(self._on_geometry_change)
        self.buffer_spin.lineEdit().textEdited.connect(
            self._on_buffer_text_edited)
        self.buffer_spin.editingFinished.connect(self._apply_geometry_change)
        form.addRow(self.tr("Buffer"), self.buffer_spin)
        self.buffer_status = QLabel(self.tr("Buffer appliqué : ±50 m (collets)"))
        self.buffer_status.setObjectName("label_hint")
        self.buffer_status.setWordWrap(True)
        form.addRow("", self.buffer_status)

        # v2.9.179/181 — forages de la coupe : à côté du buffer (règle
        # + exceptions).  Logique : ui/section_holes.py.
        from .section_holes import build_hole_filter_row
        form.addRow("", build_hole_filter_row(self))


        self.buffer_mode_combo = QComboBox()
        self.buffer_mode_combo.addItem(
            self.tr("Distance du collet (recommandé)"), "collar")
        self.buffer_mode_combo.addItem(
            self.tr("Intersection de la trajectoire"), "trajectory")
        self.buffer_mode_combo.setStyleSheet(INPUT_STYLE)
        self.buffer_mode_combo.setToolTip(self.tr("Collet · distance au collet\nTrajectoire · corridor du trou"))
        self.buffer_mode_combo.currentIndexChanged.connect(
            self._on_geometry_change)
        form.addRow(self.tr("Mode de sélection"), self.buffer_mode_combo)
        self.chk_buffer_map = QCheckBox(self.tr("Afficher le corridor sur la carte"))
        # v2.7.8 — OFF par défaut : le tracé d'une coupe ne doit rien
        # afficher de surprenant sur la carte QGIS.
        self.chk_buffer_map.setChecked(False)
        self.chk_buffer_map.stateChanged.connect(self._on_geometry_change)
        form.addRow(self.chk_buffer_map)
        self.buffer_diagnostics = QLabel(self.tr("Aucune coupe active."))
        self.buffer_diagnostics.setWordWrap(True)
        self.buffer_diagnostics.setTextFormat(Qt.RichText)
        self.buffer_diagnostics.setStyleSheet(
            f"font-size:8pt; color:{COLORS['text_medium']};")
        form.addRow(self.tr("Distances"), self.buffer_diagnostics)

        return frame

    def _build_collars_group(self):
        frame = self._group_frame()
        form = QFormLayout(frame)
        form.setContentsMargins(6, 6, 6, 8)
        form.setSpacing(6)

        self.chk_labels = QCheckBox(self.tr("Afficher les étiquettes"))
        self.chk_labels.setChecked(True)
        self.chk_labels.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_labels)

        self.chk_collar_info = QCheckBox(self.tr("Afficher azimut / dip"))
        self.chk_collar_info.setChecked(True)
        self.chk_collar_info.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_collar_info)

        self.collar_id_size = QSpinBox()
        self.collar_id_size.setRange(6, 24)
        self.collar_id_size.setValue(8)
        self.collar_id_size.setStyleSheet(INPUT_STYLE)
        self.collar_id_size.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Taille identifiant"), self.collar_id_size)

        self.collar_info_size = QSpinBox()
        self.collar_info_size.setRange(6, 20)
        self.collar_info_size.setValue(7)
        self.collar_info_size.setStyleSheet(INPUT_STYLE)
        self.collar_info_size.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Taille az/dip"), self.collar_info_size)

        positions = [
            (self.tr("Automatique anti-collision"), "auto"),
            (self.tr("Gauche"), "left"), (self.tr("Droite"), "right"),
            (self.tr("Haut"), "top"), (self.tr("Bas"), "bottom"),
        ]
        self.collar_block_position = QComboBox()
        for label, value in positions:
            self.collar_block_position.addItem(label, value)
        self.collar_block_position.setStyleSheet(INPUT_STYLE)
        self.collar_block_position.currentIndexChanged.connect(
            self._on_section_style_change)
        form.addRow(self.tr("Position bloc ID + Az/Dip"),
                    self.collar_block_position)

        def offset_pair():
            widget = QWidget()
            row = QHBoxLayout(widget)
            row.setContentsMargins(0, 0, 0, 0)
            x_spin, y_spin = QDoubleSpinBox(), QDoubleSpinBox()
            for prefix, spin in (("X ", x_spin), ("Y ", y_spin)):
                spin.setRange(-100, 100)
                spin.setPrefix(prefix)
                spin.setSuffix(" px")
                spin.setStyleSheet(INPUT_STYLE)
                spin.valueChanged.connect(self._on_section_style_change)
                row.addWidget(spin)
            return widget, x_spin, y_spin

        id_offsets, self.collar_id_offset_x, self.collar_id_offset_y = offset_pair()
        info_offsets, self.collar_info_offset_x, self.collar_info_offset_y = offset_pair()
        form.addRow(self.tr("Décalage identifiant"), id_offsets)
        form.addRow(self.tr("Décalage Az/Dip"), info_offsets)

        self.collar_marker_size = QDoubleSpinBox()
        self.collar_marker_size.setRange(2, 24)
        self.collar_marker_size.setValue(6)
        self.collar_marker_size.setSuffix(" px")
        self.collar_marker_size.setStyleSheet(INPUT_STYLE)
        self.collar_marker_size.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Taille du symbole"), self.collar_marker_size)
        self.shared_collar_tolerance = QDoubleSpinBox()
        self.shared_collar_tolerance.setRange(0.0, 100.0)
        self.shared_collar_tolerance.setDecimals(2)
        self.shared_collar_tolerance.setValue(0.10)
        self.shared_collar_tolerance.setStyleSheet(INPUT_STYLE)
        self.shared_collar_tolerance.setToolTip(self.tr("Tolérance XYZ · collets partagés"))
        self.shared_collar_tolerance.valueChanged.connect(
            self._on_section_style_change)
        form.addRow(self.tr("Tolérance collet partagé"),
                    self.shared_collar_tolerance)
        return frame

    def _build_trajectory_group(self):
        frame = self._group_frame()
        form = QFormLayout(frame)
        form.setContentsMargins(6, 6, 6, 8)
        form.setSpacing(6)
        self.chk_trajectory = QCheckBox(self.tr("Afficher la trajectoire"))
        self.chk_trajectory.setToolTip(self.tr("Trace des forages"))
        self.chk_trajectory.setChecked(True)
        self.chk_trajectory.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_trajectory)
        self.trajectory_width = QDoubleSpinBox()
        self.trajectory_width.setRange(0.2, 8.0)
        self.trajectory_width.setSingleStep(0.1)
        self.trajectory_width.setValue(0.5)
        self.trajectory_width.setSuffix(" px")
        self.trajectory_width.setStyleSheet(INPUT_STYLE)
        self.trajectory_width.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Épaisseur"), self.trajectory_width)
        self.trajectory_color_btn = self._create_color_button("#34495E")
        form.addRow(self.tr("Couleur"), self.trajectory_color_btn)
        form.addRow(make_collapsible_help(
            self.tr("Piste centrale de référence. Les symboles de collet restent visibles lorsqu'elle est masquée.")))
        return frame





    def _build_depth_group(self):
        frame = self._group_frame()
        form = QFormLayout(frame)
        form.setContentsMargins(6, 6, 6, 8)
        form.setSpacing(6)

        self.chk_depth = QCheckBox(self.tr("Afficher profondeurs"))
        self.chk_depth.setChecked(True)
        self.chk_depth.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_depth)

        self.depth_spin = QDoubleSpinBox()
        # v2.7.7 — 0 = pas automatique (1/2/5×10ⁿ, ~10-12 graduations).
        self.depth_spin.setRange(0, 500)
        self.depth_spin.setValue(10)
        self.depth_spin.setSpecialValueText("Auto")
        self.depth_spin.setSuffix(" m")
        self.depth_spin.setToolTip(self.tr("Pas graduations · Auto = 1/2/5×10ⁿ"))
        self.depth_spin.setStyleSheet(INPUT_STYLE)
        self.depth_spin.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Graduations tous les"), self.depth_spin)

        self.depth_label_every = QSpinBox()
        self.depth_label_every.setRange(1, 5)
        self.depth_label_every.setValue(2)
        self.depth_label_every.setSuffix(" graduations")
        self.depth_label_every.setToolTip(self.tr("Étiquette toutes les N graduations"))
        self.depth_label_every.setStyleSheet(INPUT_STYLE)
        self.depth_label_every.valueChanged.connect(
            self._on_section_style_change)
        form.addRow(self.tr("Étiquettes toutes les"), self.depth_label_every)

        self.depth_font_size = QSpinBox()
        self.depth_font_size.setRange(6, 20)
        self.depth_font_size.setValue(6)
        self.depth_font_size.setStyleSheet(INPUT_STYLE)
        self.depth_font_size.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Taille du texte"), self.depth_font_size)

        self.depth_tick_length = QDoubleSpinBox()
        # v2.7.8.2 — le barreau est centré sur la trace (convention) ;
        # ce réglage pilote le DÉBORD au-delà de la litho.
        self.depth_tick_length.setRange(2, 14)
        self.depth_tick_length.setValue(2)
        self.depth_tick_length.setSuffix(" px")
        self.depth_tick_length.setToolTip(self.tr("Débord graduations (px)"))
        self.depth_tick_length.setStyleSheet(INPUT_STYLE)
        self.depth_tick_length.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Débord des graduations"), self.depth_tick_length)

        self.depth_opacity = QSpinBox()
        self.depth_opacity.setRange(0, 100)
        self.depth_opacity.setValue(80)
        self.depth_opacity.setSuffix(" %")
        self.depth_opacity.setToolTip(self.tr("Opacité profondeur"))
        self.depth_opacity.setStyleSheet(INPUT_STYLE)
        self.depth_opacity.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Opacité des graduations"), self.depth_opacity)

        self.depth_tick_width = QDoubleSpinBox()
        self.depth_tick_width.setRange(0.1, 5)
        self.depth_tick_width.setSingleStep(0.1)
        self.depth_tick_width.setValue(1.0)
        self.depth_tick_width.setStyleSheet(INPUT_STYLE)
        self.depth_tick_width.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Épaisseur graduation"), self.depth_tick_width)

        self.depth_side = QComboBox()
        self.depth_side.addItem(self.tr("Gauche"), "left")
        self.depth_side.addItem(self.tr("Droite"), "right")
        self.depth_side.setStyleSheet(INPUT_STYLE)
        self.depth_side.currentIndexChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Côté"), self.depth_side)
        return frame

    def _build_litho_group(self):
        frame = self._group_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 8)
        layout.setSpacing(6)

        self.chk_litho = QCheckBox(self.tr("Afficher la lithologie"))
        self.chk_litho.setToolTip(self.tr(
            "Couleur + motif + veine/accessoire/barrette · grisée sans fichier"))
        self.chk_litho.setChecked(True)
        self.chk_litho.stateChanged.connect(self._on_section_style_change)
        layout.addWidget(self.chk_litho)

        form = QFormLayout()
        self.litho_width = QDoubleSpinBox()
        self.litho_width.setRange(2, 60)
        self.litho_width.setValue(17)
        self.litho_width.setSuffix(" px")
        self.litho_width.setStyleSheet(INPUT_STYLE)
        self.litho_width.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Largeur"), self.litho_width)

        self.litho_opacity = QSpinBox()
        self.litho_opacity.setRange(0, 100)
        self.litho_opacity.setValue(100)
        self.litho_opacity.setSuffix(" %")
        self.litho_opacity.setStyleSheet(INPUT_STYLE)
        self.litho_opacity.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Opacité"), self.litho_opacity)
        layout.addLayout(form)

        layout.addWidget(make_collapsible_help(
            self.tr("Styles partagés avec QGIS et les autres vues.")))
        self.edit_litho_symbols = QPushButton(self.tr("Libellés et symboles…"))
        self.edit_litho_symbols.setStyleSheet(BUTTON_SECONDARY)
        self.edit_litho_symbols.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edit_litho_symbols.setToolTip(self.tr("Référentiel · lithologie"))
        self.edit_litho_symbols.clicked.connect(self._open_lithology_reference)
        layout.addWidget(self.edit_litho_symbols)
        # Les autres pages (notamment Teneurs) sont plus hautes. Le ressort
        # absorbe leur hauteur commune sous les contrôles, jamais entre eux.
        layout.addStretch(1)
        return frame

    def _build_domain_track_group(self, show_text, reference_domain,
                                  default_width=8.0):
        """Shared properties page for coded tracks (AM-01 : grouped piste,
        width/opacity only ; symbols live in the Référentiel)."""
        frame = self._group_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 8)
        layout.setSpacing(6)

        show = QCheckBox(show_text)
        show.setToolTip(self.tr("Référentiel + largeur/opacité · grisée sans fichier"))
        show.setChecked(True)
        show.stateChanged.connect(self._on_section_style_change)
        layout.addWidget(show)

        form = QFormLayout()
        side = QComboBox()
        side.addItem(self.tr("Gauche"), "left")
        side.addItem(self.tr("Droite"), "right")
        side.setCurrentIndex(1)  # défaut : droite (AUDIT_V2.7.7.md)
        side.setStyleSheet(INPUT_STYLE)
        side.setToolTip(self.tr("Côté de la piste"))
        side.currentIndexChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Côté"), side)
        width = QDoubleSpinBox()
        width.setRange(2, 40)
        width.setValue(default_width)
        width.setSuffix(" px")
        width.setStyleSheet(INPUT_STYLE)
        width.valueChanged.connect(self._on_section_style_change)
        # v2.8.0 — pour les pistes codées, le réglage porte sur la
        # largeur de VOIE (la piste = nb voies observées × cette valeur).
        form.addRow(self.tr("Largeur de voie"), width)
        opacity = QSpinBox()
        opacity.setRange(0, 100)
        opacity.setValue(80)
        opacity.setSuffix(" %")
        opacity.setStyleSheet(INPUT_STYLE)
        opacity.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Opacité"), opacity)
        layout.addLayout(form)

        layout.addWidget(make_collapsible_help(
            self.tr("Une seule bande de largeur fixe : les codes d'un même intervalle se partagent sa largeur ; l'intensité règle la largeur totale. Libellés, couleurs et motifs : bouton ci-dessous.")))

        edit_symbols = QPushButton(self.tr("Libellés et symboles…"))
        edit_symbols.setStyleSheet(BUTTON_SECONDARY)
        edit_symbols.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        edit_symbols.setToolTip(self.tr("Référentiel · ce domaine"))
        edit_symbols.clicked.connect(
            lambda _checked=False, d=reference_domain:
                self._open_domain_reference(d))
        layout.addWidget(edit_symbols)
        layout.addStretch(1)

        return frame, show, side, width, opacity

    def _build_alteration_group(self):
        (frame, self.chk_alterations, self.alter_side,
         self.alter_width, self.alter_opacity) = (
             self._build_domain_track_group(
                 self.tr("Afficher les altérations"), "alteration",
                 default_width=LANE_WIDTH_PX))  # v2.8.0 — voie minimale lisible
        return frame

    def _build_mineralization_group(self):
        (frame, self.chk_mineralizations, self.mineral_side,
         self.mineral_width, self.mineral_opacity) = (
             self._build_domain_track_group(
                 self.tr("Afficher les minéralisations"),
                 "mineralization_style",
                 default_width=LANE_WIDTH_PX))  # v2.8.0 — voie minimale lisible
        return frame

    def _build_structure_group(self):
        """v2.9.260 — page « Structures » (etape 2) : piste point-wise."""
        from .section_structure import build_structure_group
        return build_structure_group(self)

    def _build_assay_group(self):
        """v2.9.130 — Teneurs = affichage des pistes de grades.

        Les règles (teneurs ET + filtre litho OU) sont sur Intercepts.
        """
        frame = self._group_frame()
        root = QVBoxLayout(frame)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        self.chk_assays = QCheckBox(self.tr("Afficher les teneurs"))
        self.chk_assays.setToolTip(self.tr(
            "1–3 éléments, bornes Jenks/manuelles · grisée sans analyses"))
        self.chk_assays.setChecked(True)
        self.chk_assays.stateChanged.connect(self._on_section_style_change)
        root.addWidget(self.chk_assays)

        # v2.9.126 — même architecture que « Affichage de la coupe » :
        # sous-groupes CollapsibleGroup (plus de QTabWidget différent).
        # --- page Affichage (contenu teneurs historique) ---
        display_page = QWidget()
        outer = QVBoxLayout(display_page)
        outer.setContentsMargins(6, 6, 6, 8)
        outer.setSpacing(8)

        def _sec(title: str) -> QFormLayout:
            # même sous-titre que Affichage (plein largeur, pas de halo blanc)
            outer.addWidget(self._panel_subtitle(title))
            form = QFormLayout()
            form.setContentsMargins(0, 0, 0, 0)
            form.setSpacing(5)
            form.setHorizontalSpacing(8)
            wrap = QWidget()
            wrap.setLayout(form)
            outer.addWidget(wrap)
            return form

        # --- 1. Quels éléments ---
        f1 = _sec(self.tr("Éléments (max 3 · même côté)"))
        self.element_combo = QComboBox()
        self.element_combo.setStyleSheet(INPUT_STYLE)
        self.element_combo.setToolTip(self.tr("1er élément (le plus près de la trace)"))
        self.element_combo.currentIndexChanged.connect(self._on_assay_change)
        f1.addRow(self.tr("Élément 1"), self.element_combo)

        self.element2_combo = QComboBox()
        self.element2_combo.setStyleSheet(INPUT_STYLE)
        self.element2_combo.setToolTip(self.tr("2e élément (optionnel) — même côté"))
        self.element2_combo.currentIndexChanged.connect(self._on_assay_change)
        f1.addRow(self.tr("Élément 2"), self.element2_combo)

        self.element3_combo = QComboBox()
        self.element3_combo.setStyleSheet(INPUT_STYLE)
        self.element3_combo.setToolTip(self.tr("3e élément (optionnel, max)"))
        self.element3_combo.currentIndexChanged.connect(self._on_assay_change)
        f1.addRow(self.tr("Élément 3"), self.element3_combo)

        self.edit_assay_elements = QPushButton(
            self.tr("Unités, décimales, limite de détection…"))
        self.edit_assay_elements.setStyleSheet(BUTTON_SECONDARY)
        self.edit_assay_elements.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edit_assay_elements.setToolTip(self.tr(
            "Référentiel · Éléments mesurés\nCorriger libellés, unités (ppm / %), décimales et LD."))
        self.edit_assay_elements.clicked.connect(
            lambda *_a: self._open_domain_reference("assay_elements"))
        outer.addWidget(self.edit_assay_elements)

        # --- 2. Échelle / classes ---
        f2 = _sec(self.tr("Échelle des valeurs"))
        self.classif_combo = QComboBox()
        for key, label in CLASSIFICATION_METHODS.items():
            self.classif_combo.addItem(self.tr(label), key)
        self.classif_combo.setStyleSheet(INPUT_STYLE)
        self.classif_combo.setToolTip(self.tr("Linéaire · Quantiles · Log · Jenks · Seuils manuels"))
        self.classif_combo.currentIndexChanged.connect(self._on_assay_change)
        f2.addRow(self.tr("Méthode"), self.classif_combo)

        self._classification_help = make_collapsible_help("")
        self.classification_hint = self._classification_help._help_body
        f2.addRow(self._classification_help)

        self.n_classes_spin = QSpinBox()
        self.n_classes_spin.setRange(2, 12)
        self.n_classes_spin.setValue(7)
        self.n_classes_spin.setStyleSheet(INPUT_STYLE)
        self.n_classes_spin.valueChanged.connect(self._on_assay_change)
        f2.addRow(self.tr("Nb de classes"), self.n_classes_spin)

        self.round_breaks_chk = QCheckBox(
            self.tr("Arrondir les bornes de classes (Jenks)"))
        self.round_breaks_chk.setChecked(True)
        self.round_breaks_chk.setToolTip(self.tr("Bornes lisibles (ex. 5, 10, 20) au lieu de 4,87 / 11,3…"))
        self.round_breaks_chk.stateChanged.connect(self._on_assay_change)
        f2.addRow(self.round_breaks_chk)

        # 371 — TROIS champs, un par élément : plus de syntaxe à
        # apprendre, chaque élément a le sien (retour écran).
        self._mb_edits = []
        self._mb_labels = []
        for _i in range(3):
            edit = QLineEdit()
            edit.setPlaceholderText(self.tr("2000; 8000; 15000"))
            edit.setStyleSheet(INPUT_STYLE)
            edit.setToolTip(self.tr(
                "Seuils manuels de cet élément (si méthode = seuils) : "
                "valeurs séparées par « ; ». Vide = Jenks (grille "
                "ronde)."))
            edit.editingFinished.connect(self._on_assay_change)
            lbl = QLabel(self.tr("Seuils · Élément %d") % (_i + 1))
            f2.addRow(lbl, edit)
            self._mb_labels.append(lbl)
            self._mb_edits.append(edit)
        # nom historique = champ de l'élément 1
        self.manual_breaks_edit = self._mb_edits[0]
        self.manual_breaks2_edit = self._mb_edits[1]
        self.manual_breaks3_edit = self._mb_edits[2]

        self.scale_scope_combo = QComboBox()
        self.scale_scope_combo.addItem(
            self.tr("Projet entier (carte + coupes)"), "project")
        self.scale_scope_combo.addItem(
            self.tr("Coupe courante seulement"), "section")
        self.scale_scope_combo.setStyleSheet(INPUT_STYLE)
        self.scale_scope_combo.setToolTip(self.tr("Sur quelles données calculer min / max / classes"))
        self.scale_scope_combo.currentIndexChanged.connect(
            self._on_assay_change)
        f2.addRow(self.tr("Étendue"), self.scale_scope_combo)

        # --- 3. Couleurs ---
        f3 = _sec(self.tr("Couleurs (une palette par élément)"))
        self.ramp_combo = QComboBox()
        for key, label in ASSAY_RAMPS.items():
            self.ramp_combo.addItem(self.tr(label), key)
        self.ramp_combo.setStyleSheet(INPUT_STYLE)
        self.ramp_combo.setToolTip(self.tr("Palette élément 1"))
        self.ramp_combo.currentIndexChanged.connect(self._on_assay_change)
        f3.addRow(self.tr("Palette 1"), self.ramp_combo)

        self.ramp2_combo = QComboBox()
        for key, label in ASSAY_RAMPS.items():
            self.ramp2_combo.addItem(self.tr(label), key)
        self.ramp2_combo.setStyleSheet(INPUT_STYLE)
        self.ramp2_combo.setToolTip(self.tr("Palette élément 2 (indépendante)"))
        self.ramp2_combo.currentIndexChanged.connect(self._on_assay_change)
        f3.addRow(self.tr("Palette 2"), self.ramp2_combo)

        self.ramp3_combo = QComboBox()
        for key, label in ASSAY_RAMPS.items():
            self.ramp3_combo.addItem(self.tr(label), key)
        self.ramp3_combo.setStyleSheet(INPUT_STYLE)
        self.ramp3_combo.setToolTip(self.tr("Palette élément 3 (indépendante)"))
        self.ramp3_combo.currentIndexChanged.connect(self._on_assay_change)
        f3.addRow(self.tr("Palette 3"), self.ramp3_combo)

        self.ramp_preview = QLabel()
        self.ramp_preview.setTextFormat(Qt.RichText)
        self.ramp_preview.setToolTip(self.tr("Aperçu palette 1 · faible → forte"))
        f3.addRow(self.tr("Aperçu"), self.ramp_preview)

        # --- 4. Piste sur la coupe ---
        f4 = _sec(self.tr("Piste sur la coupe"))
        self.assay_side = QComboBox()
        self.assay_side.addItem(self.tr("Gauche"), "left")
        self.assay_side.addItem(self.tr("Droite"), "right")
        self.assay_side.setStyleSheet(INPUT_STYLE)
        self.assay_side.setToolTip(self.tr("Côté de la piste teneurs"))
        self.assay_side.currentIndexChanged.connect(
            self._on_section_style_change)
        f4.addRow(self.tr("Côté"), self.assay_side)

        self.assay_width_mode = QComboBox()
        self.assay_width_mode.addItem(self.tr("Ruban proportionnel"), "proportional")
        self.assay_width_mode.addItem(self.tr("Ruban pleine largeur"), "fixed")
        self.assay_width_mode.addItem(self.tr("Bâtonnets"), "bars")
        self.assay_width_mode.setStyleSheet(INPUT_STYLE)
        self.assay_width_mode.setToolTip(self.tr(
            "Proportionnel = largeur selon la valeur ; bâtonnets = histogramme le long du trou"))
        self.assay_width_mode.currentIndexChanged.connect(
            self._on_section_style_change)
        f4.addRow(self.tr("Mode"), self.assay_width_mode)

        self.assay_max_width = QDoubleSpinBox()
        self.assay_max_width.setRange(2, 80)
        self.assay_max_width.setValue(15)
        self.assay_max_width.setSuffix(" px")
        self.assay_max_width.setStyleSheet(INPUT_STYLE)
        self.assay_max_width.valueChanged.connect(
            self._on_section_style_change)
        f4.addRow(self.tr("Largeur max"), self.assay_max_width)

        self.assay_opacity = QSpinBox()
        self.assay_opacity.setRange(0, 100)
        self.assay_opacity.setValue(100)
        self.assay_opacity.setSuffix(" %")
        self.assay_opacity.setStyleSheet(INPUT_STYLE)
        self.assay_opacity.valueChanged.connect(self._on_assay_change)
        f4.addRow(self.tr("Opacité"), self.assay_opacity)

        # 358 — « enlève-le des propriétés de la coupe » : l'épaisseur
        # carte QGIS n'est PAS une propriété de coupe.  Le widget reste
        # construit (persistance + carte lisent .value()) mais n'est
        # plus affiché ici ; défaut 1.8 conservé.
        self.assay_map_width = QDoubleSpinBox()
        self.assay_map_width.setRange(0.1, 10)
        self.assay_map_width.setSingleStep(0.1)
        self.assay_map_width.setValue(1.8)
        self.assay_map_width.setStyleSheet(INPUT_STYLE)
        self.assay_map_width.valueChanged.connect(self._on_assay_change)

        outer.addStretch(1)
        root.addWidget(display_page, 1)
        self.assay_display_group = display_page  # alias (plus d'accordéon)
        return frame

    def _build_threshold_group(self):
        """v2.9.132 — page Intercepts : case afficher + règles.

        Teneurs (critères ET) + litho (filtre OU optionnel) → blocs.
        Décocher masque la piste (règles conservées).
        """
        frame = self._group_frame()  # même cadre que Litho / Teneurs
        self.threshold_subtab = frame
        self.threshold_group = frame
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(6, 6, 6, 8)
        outer.setSpacing(6)

        self.chk_intercepts = QCheckBox(self.tr("Afficher les intercepts"))
        # v2.9.178 — infobulle existante juste après : doublon retiré
        self.chk_intercepts.setChecked(True)
        self.chk_intercepts.setToolTip(self.tr(
            "Masquer la piste sans perdre les règles. Comme « Afficher les teneurs »."))
        self.chk_intercepts.stateChanged.connect(self._on_section_style_change)
        outer.addWidget(self.chk_intercepts)

        help_btn = QToolButton()
        help_btn.setText(self.tr("ⓘ Aide"))
        help_btn.setCheckable(True)
        help_btn.setChecked(False)
        help_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.setToolTip(self.tr("Afficher l'aide des règles de seuil"))
        help_btn.setStyleSheet(
            f"QToolButton {{ color:{COLORS['text_medium']}; border:none; "
            f"padding:2px 0; font-size:8pt; text-align:left; }}"
            f"QToolButton:checked {{ font-weight:bold; }}")
        self.threshold_help_btn = help_btn
        outer.addWidget(help_btn, 0, Qt.AlignLeft)

        help_body = QLabel(
            self.tr(
                "Cette piste dessine les intervalles qui matchent une règle.\nChaque règle combine : teneurs (critères ET, obligatoires) et lithologie (filtre OU, optionnel).\nJusqu'à 3 règles indépendantes (cyan, magenta, ambre).\nLa valeur de chaque critère est bornée au minimum et au maximum réellement présents pour l'élément.\nDécochez « Afficher les intercepts » pour masquer la piste (les règles restent).\nIdentique en coupe et à l'export PNG."))
        help_body.setObjectName("label_hint")
        help_body.setWordWrap(True)
        help_body.setVisible(False)
        self.threshold_help_body = help_body
        help_btn.toggled.connect(help_body.setVisible)
        # CHK-35 — rallumeur : même setter, argument non-const
        help_body.setVisible(help_btn.isChecked())
        outer.addWidget(help_body)

        self.threshold_rule_widgets = []
        # rétrocompat single-rule aliases (remplis après boucle)
        self.threshold_clause_widgets = []
        self.threshold_enabled = None
        self.threshold_litho = None
        self.threshold_element = None
        self.threshold_operator = None
        self.threshold_value = None

        for ri in range(threshold_rule_mod.MAX_RULES):
            slot = threshold_rule_mod.rule_color_for_index(ri)
            box = QFrame()
            box.setStyleSheet(
                f"QFrame {{ border:1px solid {slot['hex']}; "
                f"border-radius:4px; }}")
            box_l = QVBoxLayout(box)
            box_l.setContentsMargins(6, 4, 6, 6)
            box_l.setSpacing(4)

            # En-tête : flèche + nom · pastille · Activer
            # (replié/déplié INDEPENDANT de la case Activer)
            header = QWidget()
            hdr = QHBoxLayout(header)
            hdr.setContentsMargins(0, 0, 0, 0)
            hdr.setSpacing(6)
            toggle = QToolButton()
            toggle.setCheckable(True)
            toggle.setChecked(False)
            toggle.setArrowType(Qt.RightArrow)
            toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            toggle.setText(
                self.tr("Règle {} · {}").format(ri + 1, slot['name']))
            toggle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setToolTip(self.tr(
                "Cliquer pour afficher ou masquer les critères. Indépendant de la case Activer."))
            toggle.setStyleSheet(
                f"QToolButton {{ color:{slot['hex']}; font-weight:bold; "
                f"border:none; padding:2px 0; text-align:left; }}")
            en = QCheckBox(self.tr("Activer"))
            en.setToolTip(self.tr(
                "Piste Intercepts {} ({}) sur les intervalles matchés — aucune modification des sources").format(
                slot['name'], slot['hex']))
            en.stateChanged.connect(self._on_threshold_change)
            swatch = QLabel("  ")
            swatch.setFixedSize(16, 16)
            swatch.setStyleSheet(
                f"background:{slot['hex']}; "
                f"border:1px solid {COLORS.get('border_dark', '#888')}; "
                f"border-radius:8px;")
            swatch.setToolTip(self.tr(
                "Couleur fixe slot {} — non modifiable").format(ri + 1))
            hdr.addWidget(toggle, 1)
            hdr.addWidget(en, 0)
            hdr.addWidget(swatch, 0)
            box_l.addWidget(header)

            body = QWidget()
            form = QFormLayout(body)
            form.setContentsMargins(2, 2, 2, 2)
            form.setSpacing(4)
            body.setVisible(False)

            def _on_rule_toggle(checked, t=toggle, b=body):
                t.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
                b.setVisible(bool(checked))

            toggle.toggled.connect(_on_rule_toggle)
            # CHK-35 — rallumeur : même setter, argument non-const
            body.setVisible(toggle.isChecked())

            clause_widgets = []
            # range(3) == MAX_CLAUSES (tests AND-109) ; par règle
            for ci in range(3):
                row = QWidget()
                hl = QHBoxLayout(row)
                hl.setContentsMargins(0, 0, 0, 0)
                hl.setSpacing(4)
                elem_cb = QComboBox()
                elem_cb.setStyleSheet(INPUT_STYLE)
                elem_cb.setToolTip(
                    self.tr("Élément du critère {0} (vide = inactif)")
                    .format(ci + 1))
                elem_cb.currentIndexChanged.connect(self._on_threshold_change)
                op_cb = QComboBox()
                op_cb.setStyleSheet(INPUT_STYLE)
                for op, lab in (
                    (">", ">"), (">=", "≥"), ("<", "<"), ("<=", "≤"),
                ):
                    op_cb.addItem(lab, op)
                op_cb.currentIndexChanged.connect(self._on_threshold_change)
                val_sp = QDoubleSpinBox()
                val_sp.setDecimals(4)
                val_sp.setRange(0.0, 1.0)
                val_sp.setValue(0.5)
                val_sp.setKeyboardTracking(False)
                val_sp.setStyleSheet(INPUT_STYLE)
                val_sp.setMaximumWidth(110)
                val_sp.setToolTip(self.tr("Borne aux valeurs réellement présentes pour l'élément."))
                val_sp.valueChanged.connect(self._on_threshold_change)
                hl.addWidget(elem_cb, 2)
                hl.addWidget(op_cb, 0)
                hl.addWidget(val_sp, 1)
                label = (self.tr("Critère 1") if ci == 0
                         else self.tr("ET critère {0}").format(ci + 1))
                form.addRow(label, row)
                clause_widgets.append({
                    "element": elem_cb, "operator": op_cb, "value": val_sp,
                })

            litho_scroll = QScrollArea()
            litho_scroll.setWidgetResizable(True)
            litho_scroll.setMaximumHeight(88)
            litho_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            litho_scroll.setStyleSheet(
                TOOLTIP_STYLE
                + f"QScrollArea {{ background:transparent; "
                f"border:1px solid {COLORS['border']}; }}"
                + "QWidget { background:transparent; }"
                + "QCheckBox { background:transparent; }")
            litho_scroll.setToolTip(self.tr(
                "Optionnel : codes litho (OU). Aucune case cochée = toutes les lithologies."))
            litho = QWidget()
            litho_l = QVBoxLayout(litho)
            litho_l.setContentsMargins(4, 2, 4, 2)
            litho_l.setSpacing(1)
            litho._dm_litho_checks = []
            litho_scroll.setWidget(litho)
            form.addRow(self.tr("Litho (OU)"), litho_scroll)

            box_l.addWidget(body)
            outer.addWidget(box)
            self.threshold_rule_widgets.append({
                "enabled": en,
                "clauses": clause_widgets,
                "litho": litho,
                "litho_scroll": litho_scroll,
                "color": slot["hex"],
                "color_name": slot["name"],
                "box": box,
                "toggle": toggle,
                "body": body,
            })

        # alias rétrocompat → règle 1 (tests THR-102 / AND-109)
        r0 = self.threshold_rule_widgets[0]
        self.threshold_enabled = r0["enabled"]
        self.threshold_clause_widgets = r0["clauses"]
        self.threshold_litho = r0["litho"]
        self.threshold_element = r0["clauses"][0]["element"]
        self.threshold_operator = r0["clauses"][0]["operator"]
        self.threshold_value = r0["clauses"][0]["value"]

        self.threshold_hint = QLabel(
            self.tr("Aucune règle active. Activez une règle ci-dessus (ex. Fe > 10 → cyan, Cu > 1 → magenta)."))
        self.threshold_hint.setObjectName("label_hint")
        self.threshold_hint.setWordWrap(True)
        outer.addWidget(self.threshold_hint)

        outer.addStretch(1)
        return frame


    def _create_color_button(self, colour):
        button = QPushButton(colour.upper())
        button._colour = colour.upper()
        button.setStyleSheet(
            f"QPushButton {{ background:{colour}; border:1px solid {COLORS['border_dark']}; padding:4px; }}")
        button.clicked.connect(lambda: self._choose_style_colour(button))
        return button

    def _set_color_button(self, button, colour):
        button._colour = colour.upper()
        button.setText(colour.upper())
        text_colour = "#FFFFFF" if QColor(colour).lightness() < 128 else "#000000"
        button.setStyleSheet(
            f"QPushButton {{ background:{colour}; color:{text_colour}; "
            f"border:1px solid {COLORS['border_dark']}; padding:4px; }}")

    def _choose_style_colour(self, button):
        colour = QColorDialog.getColor(QColor(button._colour), self)
        if colour.isValid():
            self._set_color_button(button, colour.name().upper())
            self._on_section_style_change()

    def _automatic_step_spin(self):
        spin = QDoubleSpinBox()
        spin.setRange(0, 1000000)
        spin.setDecimals(1)
        spin.setSpecialValueText(self.tr("Automatique"))
        spin.setSuffix(f" {self._buffer_unit}")
        spin.setStyleSheet(INPUT_STYLE)
        spin.valueChanged.connect(self._on_section_style_change)
        return spin

    def _build_grid_advanced_group(self):
        frame = self._group_frame()
        form = QFormLayout(frame)
        form.setContentsMargins(6, 6, 6, 8)
        form.setSpacing(6)

        self.grid_color_btn = self._create_color_button("#D5DBDB")
        form.addRow(self.tr("Couleur grille"), self.grid_color_btn)
        self.grid_width_spin = QDoubleSpinBox()
        self.grid_width_spin.setRange(0.2, 3.0)
        self.grid_width_spin.setSingleStep(0.1)
        self.grid_width_spin.setValue(0.7)
        self.grid_width_spin.setSuffix(" px")
        self.grid_width_spin.setStyleSheet(INPUT_STYLE)
        self.grid_width_spin.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Épaisseur grille"), self.grid_width_spin)
        self.grid_style_combo = QComboBox()
        self.grid_style_combo.addItem(self.tr("Continu"), "solid")
        self.grid_style_combo.addItem(self.tr("Tirets"), "dash")
        self.grid_style_combo.addItem(self.tr("Pointillé"), "dot")
        self.grid_style_combo.setStyleSheet(INPUT_STYLE)
        self.grid_style_combo.currentIndexChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Style grille"), self.grid_style_combo)
        self.grid_opacity_spin = QSpinBox()
        self.grid_opacity_spin.setRange(10, 100)
        self.grid_opacity_spin.setValue(70)
        self.grid_opacity_spin.setSuffix(" %")
        self.grid_opacity_spin.setStyleSheet(INPUT_STYLE)
        self.grid_opacity_spin.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Opacité grille"), self.grid_opacity_spin)

        self.elevation_step_spin = self._automatic_step_spin()
        self.elevation_step_spin.setValue(20.0)  # v2.9.70 défaut 20 m
        self.distance_step_spin = self._automatic_step_spin()
        form.addRow(self.tr("Pas d’élévation"), self.elevation_step_spin)
        form.addRow(self.tr("Pas de distance"), self.distance_step_spin)

        self.axis_value_size_spin = QSpinBox()
        self.axis_value_size_spin.setRange(6, 16)
        self.axis_value_size_spin.setValue(7)
        self.axis_value_size_spin.setSuffix(" pt")
        self.axis_value_size_spin.setStyleSheet(INPUT_STYLE)
        self.axis_value_size_spin.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Taille valeurs"), self.axis_value_size_spin)
        self.axis_value_color_btn = self._create_color_button("#7F8C8D")
        form.addRow(self.tr("Couleur valeurs"), self.axis_value_color_btn)
        self.axis_value_bold_chk = QCheckBox(self.tr("Valeurs en gras"))
        self.axis_value_bold_chk.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.axis_value_bold_chk)
        self.axis_decimals_spin = QSpinBox()
        self.axis_decimals_spin.setRange(0, 3)
        self.axis_decimals_spin.setValue(0)
        self.axis_decimals_spin.setStyleSheet(INPUT_STYLE)
        self.axis_decimals_spin.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Décimales"), self.axis_decimals_spin)

        self.axis_title_size_spin = QSpinBox()
        self.axis_title_size_spin.setRange(7, 18)
        self.axis_title_size_spin.setValue(8)
        self.axis_title_size_spin.setSuffix(" pt")
        self.axis_title_size_spin.setStyleSheet(INPUT_STYLE)
        self.axis_title_size_spin.valueChanged.connect(self._on_section_style_change)
        form.addRow(self.tr("Taille titres"), self.axis_title_size_spin)
        self.axis_title_color_btn = self._create_color_button("#566573")
        form.addRow(self.tr("Couleur titres"), self.axis_title_color_btn)
        self.axis_title_bold_chk = QCheckBox(self.tr("Titres en gras"))
        self.axis_title_bold_chk.setChecked(True)
        self.axis_title_bold_chk.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.axis_title_bold_chk)
        return frame

    def _build_frame_axes_group(self):
        frame = self._group_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 8)
        layout.setSpacing(6)
        form = QFormLayout()
        form.setSpacing(6)
        form.addRow(self._panel_subtitle(self.tr("Proportions")))

        exag_row = QWidget()
        exag_layout = QHBoxLayout(exag_row)
        exag_layout.setContentsMargins(0, 0, 0, 0)
        self.exag_slider = QSlider(Qt.Horizontal)
        # v2.9.275 — retour écran : trous de 5 m ici, 120 m ailleurs.  Le
        # curseur montait à 10x : trop peu pour des forages peu profonds sur
        # une longue coupe.  On monte à 100x et on ajoute un mode « Auto ».
        self.exag_slider.setRange(5, 1000)
        self.exag_slider.setValue(10)
        # v2.9.178 — question réelle (« ça déforme mes données ? ») :
        # non, l'exagération est visuelle.
        # v2.9.178 — question réelle (« ça déforme mes données ? »)
        self.exag_slider.setToolTip(self.tr("Exag. verticale ×N · visuelle, coordonnées intactes"))
        self.exag_label = QLabel(self.tr("1.0x"))
        self.exag_label.setMinimumWidth(32)
        self.exag_slider.valueChanged.connect(self._on_geometry_change)
        exag_layout.addWidget(self.exag_slider, 1)
        exag_layout.addWidget(self.exag_label)
        # v2.9.275 — « Auto » : exagération calculée sur la profondeur réelle
        # des trous et la longueur de la coupe (5 m comme 120 m).
        self.exag_auto_btn = QPushButton(self.tr("Auto"))
        self.exag_auto_btn.setToolTip(self.tr(
            "Adapter l'exagération verticale à la profondeur des forages"))
        self.exag_auto_btn.clicked.connect(self._auto_vertical_exag)
        exag_layout.addWidget(self.exag_auto_btn)
        form.addRow(self.tr("Exagération"), exag_row); from .display_profiles_dialog import attach_hole_type_row, attach_surface_anchor_row; attach_hole_type_row(self, form); attach_surface_anchor_row(self, form); from .display_profiles_dialog import attach_common_scale_row; attach_common_scale_row(self, form)  # v2.9.296 type / v314 ancrage topo / v391 échelle de projet
        # 349 — l'exergue est une PROPRIÉTÉ DE COUPE : ses réglages
        # vivent ici, pas dans le dialogue d'export (déchargé).
        form.addRow(self._panel_subtitle(self.tr("Exergue légende")))
        self.chk_legend_fade = QCheckBox(self.tr("Estomper les autres bandes"))
        self.chk_legend_fade.setChecked(False)  # 350 : opt-in
        self.chk_legend_fade.setToolTip(self.tr(
            "Quand des codes sont en exergue : estompe les autres à 35 %"))
        self.chk_legend_fade.stateChanged.connect(
            self._on_legend_fade_change)
        form.addRow(self.chk_legend_fade)
        self.btn_legend_clear = QPushButton(self.tr("Effacer l'exergue"))
        self.btn_legend_clear.setToolTip(self.tr(
            "Clic légende = 1 code · Ctrl+clic = plusieurs codes · "
            "ce bouton efface tout"))
        self.btn_legend_clear.clicked.connect(
            self._on_legend_clear_clicked)
        form.addRow(self.btn_legend_clear)
        # 355 — confort visuel : débrayable, annoncé.
        self.chk_comfort = QCheckBox(
            self.tr("Réduire la densité visuelle (confort)"))
        self.chk_comfort.setChecked(True)
        self.chk_comfort.setToolTip(self.tr(
            "Masque traits de rappel et liserés, espace les chiffres "
            "de profondeur : reposant aux croisements"))
        self.chk_comfort.stateChanged.connect(self._on_comfort_change)
        form.addRow(self.chk_comfort)
        form.addRow(self._panel_subtitle(self.tr("Grille et axes")))

        self.chk_grid = QCheckBox(self.tr("Afficher la grille"))
        self.chk_grid.setChecked(True)
        self.chk_grid.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_grid)
        self.chk_elevation_values = QCheckBox(self.tr("Afficher les valeurs d’élévation"))
        self.chk_elevation_values.setChecked(True)
        self.chk_elevation_values.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_elevation_values)
        self.chk_distance_values = QCheckBox(self.tr("Afficher les valeurs de distance"))
        self.chk_distance_values.setChecked(True)
        self.chk_distance_values.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_distance_values)
        self.chk_axis_titles = QCheckBox(self.tr("Afficher les titres des axes"))
        self.chk_axis_titles.setChecked(True)
        self.chk_axis_titles.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_axis_titles)
        layout.addLayout(form)
        layout.addWidget(CollapsibleGroup(
            self.tr("Style avancé de la grille et des axes"),
            self._build_grid_advanced_group(), expanded=False, level=1))

        orientation_form = QFormLayout()
        orientation_form.setSpacing(6)
        orientation_form.addRow(self._panel_subtitle(self.tr("Orientation")))
        self.chk_orientation = QCheckBox(self.tr("Afficher la direction de la coupe"))
        self.chk_orientation.setChecked(True)
        self.chk_orientation.stateChanged.connect(self._on_section_style_change)
        orientation_form.addRow(self.chk_orientation)
        self.orientation_position = QComboBox()
        self.orientation_position.addItem(self.tr("Automatique (bas gauche)"), "auto")
        self.orientation_position.addItem(self.tr("Bas gauche"), "bottom_left")
        self.orientation_position.addItem(self.tr("Bas droite"), "bottom_right")
        self.orientation_position.setStyleSheet(INPUT_STYLE)
        self.orientation_position.currentIndexChanged.connect(self._on_section_style_change)
        orientation_form.addRow(self.tr("Position direction"),
                                self.orientation_position)
        self.orientation_font_size = QSpinBox()
        self.orientation_font_size.setRange(7, 16)
        self.orientation_font_size.setValue(9)
        self.orientation_font_size.setSuffix(" pt")
        self.orientation_font_size.setStyleSheet(INPUT_STYLE)
        self.orientation_font_size.valueChanged.connect(self._on_section_style_change)
        orientation_form.addRow(self.tr("Taille direction"),
                                self.orientation_font_size)
        # v2.9.321 — commentaire libre dans le cartouche bas de carte
        self.orientation_note = QLineEdit()
        self.orientation_note.setMaxLength(140)
        self.orientation_note.setPlaceholderText(self.tr(
            "Ex. : ZRA-KAB — campagne Q1 2026"))
        self.orientation_note.setStyleSheet(INPUT_STYLE)
        self.orientation_note.editingFinished.connect(
            self._on_section_style_change)
        orientation_form.addRow(self.tr("Commentaire (cartouche)"),
                                self.orientation_note)
        # 329 — auteur imprimé dans le cartouche d'infos de l'export.
        self.orientation_author = QLineEdit()
        self.orientation_author.setMaxLength(80)
        self.orientation_author.setPlaceholderText(self.tr(
            "Ex. : Y. Bonful"))
        self.orientation_author.setStyleSheet(INPUT_STYLE)
        self.orientation_author.editingFinished.connect(
            self._on_section_style_change)
        orientation_form.addRow(self.tr("Auteur (cartouche)"),
                                self.orientation_author)
        orientation_form.addRow(self._panel_subtitle(self.tr("Échelle")))

        self.chk_scale_bar = QCheckBox(self.tr("Afficher l'échelle horizontale"))
        self.chk_scale_bar.setChecked(True)
        self.chk_scale_bar.stateChanged.connect(self._on_section_style_change)
        orientation_form.addRow(self.chk_scale_bar)
        self.scale_position = QComboBox()
        self.scale_position.addItem(self.tr("Automatique (bas droite)"), "auto")
        self.scale_position.addItem(self.tr("Bas gauche"), "bottom_left")
        self.scale_position.addItem(self.tr("Bas droite"), "bottom_right")
        self.scale_position.setStyleSheet(INPUT_STYLE)
        self.scale_position.currentIndexChanged.connect(self._on_section_style_change)
        orientation_form.addRow(self.tr("Position échelle"),
                                self.scale_position)
        self.scale_size = QComboBox()
        self.scale_size.addItem(self.tr("Petite"), "small")
        self.scale_size.addItem(self.tr("Moyenne"), "medium")
        self.scale_size.addItem(self.tr("Grande"), "large")
        self.scale_size.setStyleSheet(INPUT_STYLE)
        self.scale_size.currentIndexChanged.connect(self._on_section_style_change)
        orientation_form.addRow(self.tr("Taille échelle"), self.scale_size)
        layout.addLayout(orientation_form)
        return frame

    def _build_topography_group(self):
        """v2.9.0 — réglages de la ligne de sol (cascade de sources).

        La CASCADE est automatique (décision écran) : MNT raster du projet
        QGIS → CSV x;y;z du dossier du projet → collets seulement. Le
        combo « Source » ne sert qu'à forcer un MNT précis ou à passer au
        CSV/collets quand le raster n'est pas le bon.
        """
        frame = self._group_frame()
        form = QFormLayout(frame)
        form.setContentsMargins(6, 6, 6, 8)
        form.setSpacing(6)

        self.chk_surface = QCheckBox(self.tr("Afficher la ligne de sol"))
        self.chk_surface.setChecked(True)
        self.chk_surface.stateChanged.connect(self._on_section_style_change)
        form.addRow(self.chk_surface)

        self.surface_combo = QComboBox()
        self.surface_combo.addItem(self.tr("Automatique (MNT du projet)"), "auto")
        self.surface_combo.addItem(self.tr("Aucun raster (CSV / collets)"), "none")
        self.surface_combo.setStyleSheet(INPUT_STYLE)
        # TT-17 : bulle courte — la cascade reste « Auto · … »
        self.surface_combo.setToolTip(self.tr("Auto · MNT → CSV → collets"))
        self.surface_combo.currentIndexChanged.connect(
            self._on_surface_source_change)
        form.addRow(self.tr("Source MNT"), self.surface_combo)

        self.surface_qc_threshold = QDoubleSpinBox()
        self.surface_qc_threshold.setRange(0.5, 20.0)
        self.surface_qc_threshold.setSingleStep(0.5)
        self.surface_qc_threshold.setValue(2.0)
        self.surface_qc_threshold.setSuffix(" m")
        self.surface_qc_threshold.setStyleSheet(INPUT_STYLE)
        self.surface_qc_threshold.setToolTip(self.tr("Seuil QC MNT ↔ collets (m)"))
        self.surface_qc_threshold.valueChanged.connect(
            self._on_surface_qc_change)
        form.addRow(self.tr("Seuil écart MNT ↔ collets"),
                    self.surface_qc_threshold)

        self.surface_color_btn = self._create_color_button("#8B6F52")
        form.addRow(self.tr("Couleur"), self.surface_color_btn)

        self.surface_status = QLabel()
        self.surface_status.setObjectName("label_hint")
        self.surface_status.setWordWrap(True)
        form.addRow("", self.surface_status)
        return frame

    def _build_legend_group(self):
        frame = self._group_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 8)
        # v2.9.1 — CLÉ DE LECTURE (retour écran 23/08 : « c'est
        # important les symboles dans la coupe pour que l'utilisateur
        # comprenne ») : chaque symbole graphique du canvas a son entrée
        # avec le style EXACT qui est dessiné (trait plein mesuré /
        # pointillé interpolé, pastille collet, trait forage) — plus de
        # ligne ni de point « non marqués dans la légende ».
        symbols_title = QLabel(self.tr("Symboles de la coupe"))
        symbols_title.setStyleSheet(
            f"font-weight:bold; color:{COLORS['primary']};")
        self.symbols_legend_title = symbols_title
        layout.addWidget(symbols_title)
        self.symbols_legend_widget = QWidget()
        self.symbols_legend_layout = QGridLayout(self.symbols_legend_widget)
        self.symbols_legend_layout.setContentsMargins(0, 2, 0, 0)
        self.symbols_legend_layout.setHorizontalSpacing(8)
        self.symbols_legend_layout.setVerticalSpacing(5)
        layout.addWidget(self.symbols_legend_widget)

        assay_title = QLabel(self.tr("Teneurs — échelle quantitative"))
        assay_title.setStyleSheet(
            f"font-weight:bold; color:{COLORS['primary']};")
        self.assay_legend_title = assay_title
        layout.addWidget(assay_title)
        self.assay_legend = QLabel(self.tr("Aucune échelle de teneur disponible."))
        self.assay_legend.setWordWrap(True)
        self.assay_legend.setTextFormat(Qt.RichText)
        layout.addWidget(self.assay_legend)

        # v2.9.134 — Intercepts = bloc légende frère (même poids que Teneurs)
        self.threshold_legend_title = QLabel(self.tr("Intercepts"))
        self.threshold_legend_title.setStyleSheet(
            f"font-weight:bold; color:{COLORS['primary']}; margin-top:6px;")
        self.threshold_legend_title.setVisible(False)
        layout.addWidget(self.threshold_legend_title)
        self.threshold_legend_label = QLabel(self.tr(""))
        self.threshold_legend_label.setObjectName("label_hint")
        self.threshold_legend_label.setWordWrap(True)
        self.threshold_legend_label.setVisible(False)
        layout.addWidget(self.threshold_legend_label)

        litho_title = QLabel(self.tr("Lithologie — catégories"))
        litho_title.setStyleSheet(
            f"font-weight:bold; color:{COLORS['primary']}; margin-top:6px;")
        self.litho_legend_title = litho_title
        layout.addWidget(litho_title)
        self.litho_legend_widget = QWidget()
        self.litho_legend_layout = QGridLayout(self.litho_legend_widget)
        self.litho_legend_layout.setContentsMargins(0, 2, 0, 0)
        self.litho_legend_layout.setHorizontalSpacing(8)
        self.litho_legend_layout.setVerticalSpacing(5)
        layout.addWidget(self.litho_legend_widget)

        alter_title = QLabel(self.tr("Altérations — catégories"))
        alter_title.setStyleSheet(
            f"font-weight:bold; color:{COLORS['primary']}; margin-top:6px;")
        self.alter_legend_title = alter_title
        layout.addWidget(alter_title)
        self.alter_legend_widget = QWidget()
        self.alter_legend_layout = QGridLayout(self.alter_legend_widget)
        self.alter_legend_layout.setContentsMargins(0, 2, 0, 0)
        self.alter_legend_layout.setHorizontalSpacing(8)
        self.alter_legend_layout.setVerticalSpacing(5)
        layout.addWidget(self.alter_legend_widget)
        self._alter_legend_help = make_collapsible_help(
            self.tr("La largeur des bandes reflète l'intensité (faible < modérée < forte) ; la couleur identifie le type."))
        self.alter_legend_hint = self._alter_legend_help
        layout.addWidget(self._alter_legend_help)

        mineral_title = QLabel(self.tr("Minéralisations — styles"))
        mineral_title.setStyleSheet(
            f"font-weight:bold; color:{COLORS['primary']}; margin-top:6px;")
        self.mineral_legend_title = mineral_title
        layout.addWidget(mineral_title)
        self.mineral_legend_widget = QWidget()
        self.mineral_legend_layout = QGridLayout(self.mineral_legend_widget)
        self.mineral_legend_layout.setContentsMargins(0, 2, 0, 0)
        self.mineral_legend_layout.setHorizontalSpacing(8)
        self.mineral_legend_layout.setVerticalSpacing(5)
        layout.addWidget(self.mineral_legend_widget)

        # v2.9.260 (étape 2) — légende des structures (pastilles par type).
        from .section_structure import create_legend_widgets
        create_legend_widgets(self, layout)
        from .section_imagery import create_legend_widgets \
            as create_imagery_legend_widgets
        create_imagery_legend_widgets(self, layout)
        from .section_geotech import add_geotech_legends
        add_geotech_legends(self, layout)

        self._legend_help = make_collapsible_help(
            self.tr("Pistes cochées + données importées seulement (sans fichier → piste grisée, hors légende). Clic légende · surligne en anthracite (absent du PNG). Intercepts = règles (teneurs ET + filtre litho OU) ; la case masque la piste sans perdre les règles."))
        self.legend_hint_global = self._legend_help._help_body
        layout.addWidget(self._legend_help)
        # v2.9.36 — référence pour grab export PNG (+ légendes)
        self._legend_group_frame = frame
        return frame

    # ------------------------------------------------------------------
    # Persistence and live updates
    # ------------------------------------------------------------------
    def _project(self):
        return self.main_dock.project if self.main_dock else None

    @staticmethod
    def _set_combo_data(combo, value):
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def load_project_settings(self):
        """Load saved panel settings; safe for old projects without V2.4 keys."""
        project = self._project()
        if not project:
            return
        self._loading_settings = True
        self._buffer_unit = (
            self.main_dock.get_map_unit_label() if self.main_dock else "m")
        self.buffer_spin.setSuffix(f" {self._buffer_unit}")
        self.canvas._distance_unit = self._buffer_unit
        section_cfg = project.get_section_config()
        style = project.get_section_style()
        assay = project.get_assay_style(); from .section_holes import sync_hole_type_combo; sync_hole_type_combo(self)  # v2.9.306 combo suit le projet

        self._apply_project_values(
            style, assay,
            buffer=section_cfg.get("buffer", 50.0),
            exaggeration=section_cfg.get(
                "vertical_exaggeration", 1.0))

        # v2.9.0 — le combo MNT liste les rasters du projet QGIS actif.
        self._populate_surface_combo()
        self._set_combo_data(self.classif_combo, assay["method"])
        self.n_classes_spin.setValue(assay["n_classes"])
        self.round_breaks_chk.setChecked(assay.get("round_breaks", True))
        mb = assay["manual_breaks"]  # 371 : remplis après les combos
        self._set_combo_data(self.scale_scope_combo, assay["scale_scope"])
        self._set_combo_data(self.ramp_combo, assay["palette"])
        # v2.9.92 — multi-teneurs (après populate_elements si déjà fait)
        elems = list(assay.get("elements") or [])
        pals = dict(assay.get("element_palettes") or {})
        if hasattr(self, "element2_combo") and len(elems) >= 2:
            self._set_combo_data(self.element2_combo, elems[1])
        if hasattr(self, "element3_combo") and len(elems) >= 3:
            self._set_combo_data(self.element3_combo, elems[2])
        self._fill_manual_breaks_fields(mb)  # 371 : après les codes
        if hasattr(self, "ramp2_combo") and len(elems) >= 2:
            self._set_combo_data(
                self.ramp2_combo, pals.get(elems[1], "viridis"))
        if hasattr(self, "ramp3_combo") and len(elems) >= 3:
            self._set_combo_data(
                self.ramp3_combo, pals.get(elems[2], "blue_red"))
        self.assay_opacity.setValue(assay["opacity"])
        self.assay_map_width.setValue(assay["map_line_width"])
        # v2.9.102/116 — règles de seuil (multi)
        thr_payload = (assay.get("threshold_rules")
                       if assay.get("threshold_rules") is not None
                       else assay.get("threshold_rule"))
        try:
            self._populate_threshold_combos()
            self._apply_threshold_widgets(thr_payload)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Projet (sauvegarde/chargement) : load_project_settings", _exc)
            # widgets seuil absents (init partiel)
            pass
        self._litho_styles = project.get_litho_styles()
        self.canvas._litho_styles = self._litho_styles
        self._loading_settings = False
        # v2.9.117 — pistes sans data : décocher AVANT push canvas
        try:
            self._refresh_track_availability(apply_defaults=False)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Projet (sauvegarde/chargement) : load_project_settings", _exc)
            # liste pistes absente
            pass
        self._sync_track_checks()
        # re-lire style après refresh (show_* corrigés)
        try:
            style = self._section_style_values()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Projet (sauvegarde/chargement) : load_project_settings", _exc)
            # style déjà en main
            pass

        self.canvas.set_display_style(**style, assay_opacity=assay["opacity"])
        self.canvas.update_params(
            element=assay.get("element") or None,
            elements=assay.get("elements") or [],
            element_palettes=assay.get("element_palettes") or {},
            classification=assay["method"],
            n_classes=assay["n_classes"],
            manual_breaks=assay["manual_breaks"],
            round_breaks=assay.get("round_breaks", True),
            scale_scope=assay["scale_scope"],
            palette=assay["palette"],
            threshold_rules=assay.get("threshold_rules") or [],
            threshold_rule=assay.get("threshold_rule"),
        )
        self._update_assay_controls()
        try:
            self._update_threshold_hint(
                assay.get("threshold_rules") or assay.get("threshold_rule"))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Projet (sauvegarde/chargement) : load_project_settings", _exc)
            # hint optionnel
            pass
        self._populate_litho_table()
        self._update_legends()
        # v2.9.26 — nouveau projet / reload : pile vide
        self._undo_stack = []
        self._redo_stack = []
        self._undo_pending_before = None
        self._undo_baseline = None
        self._refresh_undo_buttons()
        # baseline = état chargé
        self._undo_baseline = self._capture_undo_state()

    def _apply_project_values(self, style: dict, assay: dict, *,
                              buffer: float = 50.0,
                              exaggeration: float = 1.0):
        """Applique un couple (style de coupe, style de teneurs) aux
        widgets du panneau.

        v2.7.6.9 (RESET-01) — extrait de ``load_project_settings`` pour
        qu'un projet fermé/réinitialisé ramène le panneau aux valeurs
        d'usine au lieu de garder celles du projet précédent.
        """
        self.buffer_spin.setValue(buffer)
        self.exag_slider.setValue(round(exaggeration * 10))
        self.exag_label.setText(f"{self.exag_slider.value()/10:.1f}x")
        self.chk_grid.setChecked(style["show_grid"])
        self.chk_elevation_values.setChecked(style["show_elevation_values"])
        self.chk_distance_values.setChecked(style["show_distance_values"])
        self.chk_axis_titles.setChecked(style["show_axis_titles"])
        self._set_color_button(self.grid_color_btn, style["grid_color"])
        self.grid_width_spin.setValue(style["grid_width"])
        self._set_combo_data(self.grid_style_combo, style["grid_style"])
        self.grid_opacity_spin.setValue(style["grid_opacity"])
        if getattr(self, "elevation_step_spin", None) is not None:
            self.elevation_step_spin.setSuffix(f" {self._buffer_unit}")
            _es = float(style.get("elevation_grid_step", 20.0) or 0.0)
            # v2.9.70 : 0 (ancien Auto) → 20 m (Auto donnait 10 m trop serré)
            if _es <= 0:
                _es = 20.0
            self.elevation_step_spin.setValue(_es)
        if getattr(self, "distance_step_spin", None) is not None:
            self.distance_step_spin.setSuffix(f" {self._buffer_unit}")
            self.distance_step_spin.setValue(
                style.get("distance_grid_step", 0.0))
        self.axis_value_size_spin.setValue(style["axis_value_font_size"])
        self._set_color_button(self.axis_value_color_btn, style["axis_value_color"])
        self.axis_value_bold_chk.setChecked(style["axis_value_bold"])
        self.axis_decimals_spin.setValue(style["axis_value_decimals"])
        self.axis_title_size_spin.setValue(style["axis_title_font_size"])
        self._set_color_button(self.axis_title_color_btn, style["axis_title_color"])
        self.axis_title_bold_chk.setChecked(style["axis_title_bold"])
        self._set_combo_data(self.buffer_mode_combo, style["buffer_mode"])
        mode_text = (self.tr("collets") if style["buffer_mode"] == "collar"
                     else self.tr("trajectoires"))
        self.buffer_status.setText(self.tr(
            "Buffer appliqué : ±{} {} ({})").format(
                f"{self.buffer_spin.value():g}", self._buffer_unit, mode_text))
        self.chk_buffer_map.setChecked(style["show_buffer_on_map"])
        self.chk_labels.setChecked(style["show_collar_labels"])
        self.chk_collar_info.setChecked(style["show_collar_info"])
        self.collar_id_size.setValue(style["collar_id_font_size"])
        self.collar_info_size.setValue(style["collar_info_font_size"])
        block_position = style["collar_id_position"]
        style["collar_info_position"] = block_position
        self._set_combo_data(self.collar_block_position, block_position)
        self.collar_id_offset_x.setValue(style["collar_id_offset_x"])
        self.collar_id_offset_y.setValue(style["collar_id_offset_y"])
        self.collar_info_offset_x.setValue(style["collar_info_offset_x"])
        self.collar_info_offset_y.setValue(style["collar_info_offset_y"])
        self.collar_marker_size.setValue(style["collar_marker_size"])
        self.shared_collar_tolerance.setSuffix(f" {self._buffer_unit}")
        self.shared_collar_tolerance.setValue(style["shared_collar_tolerance"])
        self.chk_trajectory.setChecked(style["show_trajectory"])
        self.trajectory_width.setValue(style["trajectory_width"])
        self._set_color_button(
            self.trajectory_color_btn, style["trajectory_color"])
        self.chk_depth.setChecked(style["show_depth"])
        self.depth_spin.setValue(style["depth_step"])
        self.depth_label_every.setValue(style.get("depth_label_every", 2))
        self.depth_font_size.setValue(style["depth_font_size"])
        self.depth_tick_length.setValue(style["depth_tick_length"])
        self.depth_tick_width.setValue(style["depth_tick_width"])
        self.depth_opacity.setValue(style.get("depth_opacity", 70))
        self._set_combo_data(self.depth_side, style["depth_side"])
        self.chk_litho.setChecked(style["show_litho"])
        self.litho_width.setValue(style["litho_width"])
        self.litho_opacity.setValue(style["litho_opacity"])
        # v2.9.28 — patterns_follow_hole_axis ignoré (toujours False)
        self.chk_alterations.setChecked(style.get("show_alterations", True))
        self.alter_width.setValue(style.get("alter_width", LANE_WIDTH_PX))
        self.alter_opacity.setValue(style.get("alter_opacity", 80))
        self._set_combo_data(
            self.alter_side, style.get("alter_side", "right"))
        self.chk_mineralizations.setChecked(
            style.get("show_mineralizations", True))
        self.mineral_width.setValue(style.get("mineral_width", LANE_WIDTH_PX))
        self.mineral_opacity.setValue(style.get("mineral_opacity", 80))
        self._set_combo_data(
            self.mineral_side, style.get("mineral_side", "right"))
        # v2.9.260 (étape 2) — piste des structures.
        if hasattr(self, "chk_structures"):
            from .section_structure import apply_structure_style_to_widget
            apply_structure_style_to_widget(self, style)
        from .section_imagery import apply_imagery_style_to_widget
        apply_imagery_style_to_widget(self, style)
        from .section_geotech import apply_geotech_style_to_widget
        for kind in ("rqd", "recovery", "density"):
            apply_geotech_style_to_widget(self, style, kind)
        self.chk_assays.setChecked(style["show_assays"])
        if hasattr(self, "chk_intercepts"):
            self.chk_intercepts.setChecked(
                style.get("show_intercepts", True))
        self.assay_max_width.setValue(style["assay_max_width"])
        self._set_combo_data(self.assay_width_mode, style["assay_width_mode"])
        self._set_combo_data(
            self.assay_side, style.get("assay_side", "left"))
        self.chk_orientation.setChecked(style["show_orientation"])
        self._set_combo_data(
            self.orientation_position, style["orientation_position"])
        self.orientation_font_size.setValue(style["orientation_font_size"])
        self.chk_scale_bar.setChecked(style["show_scale_bar"])
        self._set_combo_data(self.scale_position, style["scale_position"])
        self._set_combo_data(self.scale_size, style["scale_size"])
        # v2.9.0 — topographie (.get : projets antérieurs à la v2.9.0).
        self.chk_surface.setChecked(
            style.get("show_surface", True))
        self._set_color_button(
            self.surface_color_btn,
            style.get("surface_color", "#8B6F52"))
        self.surface_qc_threshold.setValue(
            style.get("surface_qc_threshold", 2.0))


    def reset_after_project_close(self):
        """v2.7.6.9 (RESET-01) — le panneau repart des valeurs d'usine après
        la fermeture ou la réinitialisation d'un projet. Aucune valeur du
        projet précédent ne peut « fuiter » dans le suivant.

        v2.7.7.1 — vide aussi l'historique des coupes (onglet Coupe) et la
        coupe active ; le corridor de buffer QGIS est effacé et ne peut
        plus être redessiné par le timer de géométrie (garde de chargement
        + ligne active mise à None).
        """
        from ..core.project import default_assay_style, default_section_style
        style = default_section_style()
        assay = default_assay_style()
        self._loading_settings = True
        try:
            # Coupe active et historique : repartir comme au premier
            # lancement (aucune section résiduelle dans l'onglet Coupe).
            self._line = None
            self._current_section_id = None
            self._updating_history = True
            self.section_table.setRowCount(0)
            self.section_combo.blockSignals(True)
            self.section_combo.clear()
            self.section_combo.blockSignals(False)
            self._sections.clear()
            self._updating_history = False
            # v2.7.10.34 — l'historique ne quitte JAMAIS l'Assistant
            # étape 4 (plus de setVisible(False) hérité de l'onglet Coupe
            # autonome : c'est lui qui rendait l'historique introuvable
            # après chaque ouverture de projet — constaté à l'écran).
            self.history_group.setVisible(True)
            self.info_label.setText(self.tr("Aucune coupe sélectionnée."))
            self.buffer_diagnostics.setText(self.tr("Aucune coupe active."))
            if self.main_dock:
                self.main_dock.update_section_buffer_preview(None, 0, False)
                self.main_dock.clear_map_overlays()

            self._litho_styles = {}
            self.canvas._litho_styles = {}
            self.canvas._style_resolver = None
            self.canvas._style_cache.clear()
            self.canvas._assay_scale = None
            self.canvas._result = None
            self.canvas._track_plan = None
            self.canvas.scene.clear()
            # v2.9.0 — topographie : aucune surface du projet précédent
            # ne peut « fuiter » dans le suivant.
            self.canvas._surface = None
            self.canvas._surface_source = ""
            self.canvas._surface_tooltip = ""
            self._topo_csv_cache = None
            self.surface_combo.blockSignals(True)
            self._populate_surface_combo()
            self.surface_combo.blockSignals(False)
            self._apply_project_values(style, assay)
            self.canvas.set_display_style(
                **style, assay_opacity=assay["opacity"])
            self.canvas.update_params(
                element=assay.get("element") or None,
                elements=assay.get("elements") or [],
                element_palettes=assay.get("element_palettes") or {},
                classification=assay["method"],
                n_classes=assay["n_classes"],
                manual_breaks=assay["manual_breaks"],
                round_breaks=assay.get("round_breaks", True),
                scale_scope=assay["scale_scope"],
                palette=assay["palette"],
                threshold_rules=assay.get("threshold_rules") or [],
                threshold_rule=assay.get("threshold_rule"),
            )
            self._populate_elements()
            try:
                thr_payload = (assay.get("threshold_rules")
                               if assay.get("threshold_rules") is not None
                               else assay.get("threshold_rule"))
                self._populate_threshold_combos()
                self._apply_threshold_widgets(thr_payload)
                self._update_threshold_hint(thr_payload)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Projet (sauvegarde/chargement) : reset_after_project_close", _exc)
                # widgets seuil absents au reset
                pass
            try:
                self._refresh_track_availability(apply_defaults=False)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Projet (sauvegarde/chargement) : reset_after_project_close", _exc)
                # pistes absentes
                pass
            self._populate_litho_table()
            self._update_legends()
        finally:
            self._loading_settings = False

    def _safe_spin_value(self, name, default=0):
        """v2.9.59 — lit un spin/combo même s'il n'existe pas encore (init)."""
        w = getattr(self, name, None)
        if w is None:
            return default
        try:
            if hasattr(w, "value"):
                return w.value()
            if hasattr(w, "isChecked"):
                return w.isChecked()
            if hasattr(w, "currentData"):
                return w.currentData()
            if hasattr(w, "_colour"):
                return w._colour
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _safe_spin_value", _exc)
            return default
        return default

    def _section_style_values(self):
        # getattr défensif : certains widgets axes sont créés après Pistes
        from .section_structure import read_structure_style
        values = {
            "show_grid": bool(self._safe_spin_value("chk_grid", True)),
            "show_elevation_values": bool(
                self._safe_spin_value("chk_elevation_values", True)),
            "show_distance_values": bool(
                self._safe_spin_value("chk_distance_values", True)),
            "show_axis_titles": bool(
                self._safe_spin_value("chk_axis_titles", True)),
            "grid_color": self._safe_spin_value(
                "grid_color_btn", "#D5DBDB") or "#D5DBDB",
            "grid_width": float(self._safe_spin_value("grid_width_spin", 0.7)),
            "grid_style": (
                self._safe_spin_value("grid_style_combo", "dash") or "dash"),
            "grid_opacity": int(self._safe_spin_value("grid_opacity_spin", 70)),
            "elevation_grid_step": float(
                self._safe_spin_value("elevation_step_spin", 20.0)),
            "distance_grid_step": float(
                self._safe_spin_value("distance_step_spin", 0.0)),
            "axis_value_font_size": int(
                self._safe_spin_value("axis_value_size_spin", 7)),
            "axis_value_color": self._safe_spin_value(
                "axis_value_color_btn", "#7F8C8D") or "#7F8C8D",
            "axis_value_bold": bool(
                self._safe_spin_value("axis_value_bold_chk", False)),
            "axis_value_decimals": int(
                self._safe_spin_value("axis_decimals_spin", 0)),
            "axis_title_font_size": int(
                self._safe_spin_value("axis_title_size_spin", 8)),
            "axis_title_color": self._safe_spin_value(
                "axis_title_color_btn", "#566573") or "#566573",
            "axis_title_bold": bool(
                self._safe_spin_value("axis_title_bold_chk", True)),
            "buffer_mode": self.buffer_mode_combo.currentData() or "collar",
            "show_buffer_on_map": self.chk_buffer_map.isChecked(),
            "show_collar_labels": self.chk_labels.isChecked(),
            "show_collar_info": self.chk_collar_info.isChecked(),
            "collar_id_font_size": self.collar_id_size.value(),
            "collar_info_font_size": self.collar_info_size.value(),
            "collar_id_position": self.collar_block_position.currentData() or "auto",
            "collar_info_position": self.collar_block_position.currentData() or "auto",
            "collar_id_offset_x": self.collar_id_offset_x.value(),
            "collar_id_offset_y": self.collar_id_offset_y.value(),
            "collar_info_offset_x": self.collar_info_offset_x.value(),
            "collar_info_offset_y": self.collar_info_offset_y.value(),
            "collar_marker_size": self.collar_marker_size.value(),
            "shared_collar_tolerance": self.shared_collar_tolerance.value(),
            "show_trajectory": self.chk_trajectory.isChecked(),
            "trajectory_color": self.trajectory_color_btn._colour,
            "trajectory_width": self.trajectory_width.value(),
            "show_depth": self.chk_depth.isChecked(),
            "depth_step": self.depth_spin.value(),
            "depth_label_every": self.depth_label_every.value(),
            "depth_font_size": self.depth_font_size.value(),
            "depth_tick_length": self.depth_tick_length.value(),
            "depth_tick_width": self.depth_tick_width.value(),
            "depth_opacity": self.depth_opacity.value(),
            "depth_side": self.depth_side.currentData() or "left",
            "show_litho": self.chk_litho.isChecked(),
            "litho_width": self.litho_width.value(),
            "litho_opacity": self.litho_opacity.value(),
            "patterns_follow_hole_axis": False,  # v2.9.28 : toujours fixe
            "show_alterations": self.chk_alterations.isChecked(),
            "alter_width": self.alter_width.value(),
            "alter_opacity": self.alter_opacity.value(),
            "alter_side": self.alter_side.currentData() or "right",
            "show_mineralizations": self.chk_mineralizations.isChecked(),
            "mineral_width": self.mineral_width.value(),
            "mineral_opacity": self.mineral_opacity.value(),
            "mineral_side": self.mineral_side.currentData() or "right",
            "show_assays": self.chk_assays.isChecked(),
            "show_intercepts": (
                self.chk_intercepts.isChecked()
                if hasattr(self, "chk_intercepts") else True),
            "assay_max_width": self.assay_max_width.value(),
            "assay_width_mode": self.assay_width_mode.currentData() or "proportional",
            "assay_side": self.assay_side.currentData() or "left",
            "show_orientation": self.chk_orientation.isChecked(),
            "orientation_position": self.orientation_position.currentData() or "auto",
            "orientation_font_size": self.orientation_font_size.value(),
            "orientation_note": (self.orientation_note.text() or "").strip(),
            "show_scale_bar": self.chk_scale_bar.isChecked(),
            "scale_position": self.scale_position.currentData() or "auto",
            "scale_size": self.scale_size.currentData() or "medium",
            # v2.9.0 — topographie (ligne de sol).
            "show_surface": self.chk_surface.isChecked(),
            "surface_color": self.surface_color_btn._colour,
            "surface_qc_threshold": self.surface_qc_threshold.value(),
        }
        if hasattr(self, "chk_structures"):
            values.update(read_structure_style(self))
        from .section_imagery import read_imagery_style
        values.update(read_imagery_style(self))
        from .section_geotech import read_geotech_style
        for kind in ("rqd", "recovery", "density"):
            values.update(read_geotech_style(self, kind))
        return values

    def _refresh_info_header(self, count=None):
        if not self._line:
            self.info_label.setText(self.tr("Aucune coupe sélectionnée."))
            if self.main_dock and getattr(self.main_dock, "visualization_dock", None):
                self.main_dock.visualization_dock.sync_context()
            return
        if count is None:
            count = len(self.canvas._result.holes) if self.canvas._result else 0
        _sel = self.canvas._selected
        active = (self.tr("  |  Forage actif : {}").format(', '.join(_sel) if isinstance(_sel, list) else _sel) if _sel else "")
        # v2.9.181 — signal PERMANENT au-dessus du canvas : « 12/14 ·
        # 2 exclu(s) » — l'inclusion est visible sans ouvrir le groupe.
        n_excl = len(set(getattr(self, "_excluded_holes", None) or set()))
        excl_txt = (self.tr("/{} · {} exclu(s)").format(count + n_excl, n_excl)
                    if n_excl else "")
        self.info_label.setText(
            f"{self._line.name or self.tr('Coupe')}  |  {self._line.summary}"
            + self.tr("  |  Buffer : ±{} {}").format(f"{self.buffer_spin.value():.0f}", self._buffer_unit)
            + self.tr("  |  Forages: {}{}").format(count, excl_txt) + active
            + self.tr("  |  Glisser pour déplacer · survol = infos"))
        if self.main_dock and getattr(self.main_dock, "visualization_dock", None):
            self.main_dock.visualization_dock.sync_context()

    def _update_buffer_diagnostics(self, buffer_value, buffer_mode):
        if not self._line or not self._drillholes:
            self.buffer_diagnostics.setText(self.tr("Aucune coupe active."))
            if self.main_dock:
                self.main_dock.update_section_buffer_preview(None, 0, False)
            return []
        statuses = compute_buffer_diagnostics(
            self._drillholes, self._line, buffer_value, buffer_mode)
        rows = []
        for status in statuses[:8]:
            included = status["included"]
            colour = COLORS['success'] if included else COLORS['danger']
            mark = "&#10003;" if included else "&#10007;"
            distance = status["distance"]
            distance_text = (f"{distance:.2f} {self._buffer_unit}"
                             if math.isfinite(distance)
                             else self.tr("hors segment"))
            rows.append(
                f'<span style="color:{colour};">{mark}</span> '
                f'{status["hole_id"]}: {distance_text}')
        if len(statuses) > 8:
            rows.append(self.tr("... {} autre(s) forage(s)")
                        .format(len(statuses) - 8))
        included_count = sum(status["included"] for status in statuses)
        rows.insert(0, self.tr("<b>{}/{} inclus</b>")
                    .format(included_count, len(statuses)))
        self.buffer_diagnostics.setText("<br>".join(rows))
        if self.main_dock:
            self.main_dock.update_section_buffer_preview(
                self._line, buffer_value, self.chk_buffer_map.isChecked())
        return statuses

    def _on_buffer_text_edited(self, text):
        if self._loading_settings:
            return
        self.buffer_status.setText(
            self.tr("Buffer demande : {} — recalcul en attente...")
            .format(text))
        self.buffer_status.setStyleSheet(
            f"color:{COLORS['warning']}; font-size:8pt;")
        self._geometry_timer.start()

    def _on_geometry_change(self, *_args):
        """Queue expensive buffer projection while keeping the slider live."""
        self.exag_label.setText(f"{self.exag_slider.value()/10:.1f}x")
        if self._loading_settings or getattr(self, "_undo_restoring", False):
            return
        # v2.9.26 — figer le « avant » (baseline) pour Annuler
        self._ensure_undo_baseline()
        if self._undo_pending_before is None:
            import copy
            self._undo_pending_before = copy.deepcopy(self._undo_baseline)
        if self.sender() is self.exag_slider:
            self._exag_timer.start()
            self._persist_section = True
            self._persist_timer.start()
            return
        self.buffer_status.setText(self.tr("Buffer demandé : ±{} {} — recalcul...")
                                    .format(f"{self.buffer_spin.value():g}", self._buffer_unit))
        self.buffer_status.setStyleSheet(
            f"color:{COLORS['warning']}; font-size:8pt;")
        self._geometry_timer.start()

    def _apply_geometry_change(self):
        if self._loading_settings or self._undo_restoring:
            return
        self.buffer_spin.interpretText()
        self._geometry_timer.stop()
        buffer_value = self.buffer_spin.value()
        buffer_mode = self.buffer_mode_combo.currentData() or "collar"
        buffer_changed = (
            buffer_value != self.canvas._buffer
            or buffer_mode != self.canvas._buffer_mode)
        if buffer_changed and self.canvas._drillholes and self.canvas._line:
            # Force a full inclusion/projection rebuild, not only a title refresh.
            self.canvas._buffer = buffer_value
            self.canvas._buffer_mode = buffer_mode
            self.canvas._v_exag = self.exag_slider.value() / 10.0
            self.canvas._regenerate()
        else:
            self.canvas.update_params(
                v_exag=self.exag_slider.value() / 10.0)
        statuses = self._update_buffer_diagnostics(buffer_value, buffer_mode)
        project = self._project()
        if project:
            project.save_section_style(
                buffer_mode=buffer_mode,
                show_buffer_on_map=self.chk_buffer_map.isChecked())
            project.save_section_config(
                self.buffer_spin.value(), self.exag_slider.value() / 10.0)
        if self._line:
            self._line.buffer = self.buffer_spin.value()
            if project and self._current_section_id is not None:
                project.update_section(
                    self._current_section_id, buffer=self._line.buffer)
            row = self._history_row_for_id(self._current_section_id)
            if row >= 0:
                self._updating_history = True
                self.section_table.item(row, 3).setText(
                    f"{self._line.buffer:.0f} {self._buffer_unit}")
                self._updating_history = False
            count = sum(status["included"] for status in statuses)
            mode_text = (self.tr("collets") if buffer_mode == "collar"
                         else self.tr("trajectoires"))
            n_excl = len(set(self._excluded_holes or set())
                         & {s["hole_id"] for s in statuses if s["included"]})
            excl_txt = (self.tr(" · {} exclu(s)").format(n_excl) if n_excl else "")
            self.buffer_status.setText(self.tr(
                "Buffer appliqué : ±{} {} ({}) — {}/{} forage(s){}").format(
                    f"{self.buffer_spin.value():g}", self._buffer_unit, mode_text,
                    count - n_excl, count, excl_txt))
            from .section_holes import refresh_hole_filter_ui
            refresh_hole_filter_ui(self)
            self.buffer_status.setStyleSheet(
                f"color:{COLORS['success']}; font-size:8pt;")
            self._refresh_info_header(count)


    # ------------------------------------------------------------------
    # v2.9.26 — Annuler / Rétablir (mauvaise manip)
    # ------------------------------------------------------------------
        # v2.9.26 — enregistrer l'état précédent pour Annuler
        self._commit_undo_checkpoint()


    def build_global_undo_bar(self, parent=None):
        """v2.9.29 — barre Annuler/Rétablir pour le dock Visualisation.

        Placée à l'extrême droite des onglets (Coupe 2D / 3D)
        pour être générale, pas enfouie dans Propriétés de la coupe.
        """
        host = QWidget(parent)
        row = QHBoxLayout(host)
        row.setContentsMargins(4, 0, 6, 0)
        row.setSpacing(4)
        btn_css = (
            f"QPushButton {{ font-size:9pt; font-weight:bold; padding:4px 10px; "
            f"background:{COLORS['bg_input']}; color:{COLORS['primary']}; "
            f"border:1px solid {COLORS['border_dark']}; border-radius:3px; }}"
            f"QPushButton:enabled:hover {{ background:{COLORS['border']}; }}"
            # v2.9.204 — désactivé à PLAT (on voit la différence)
            f"QPushButton:disabled {{ color:{COLORS['text_light']}; "
            f"border-color:{COLORS['border']}; "
            f"background:transparent; }}"
        )
        self.undo_btn = QPushButton(self.tr("↶ Annuler"), host)
        self.undo_btn.setToolTip(self.tr("Annuler la dernière manip (Ctrl+Z)"))
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self._undo)
        self.undo_btn.setStyleSheet(btn_css)
        row.addWidget(self.undo_btn)
        self.redo_btn = QPushButton(self.tr("↷ Rétablir"), host)
        self.redo_btn.setToolTip(self.tr("Rétablir (Ctrl+Y)"))
        self.redo_btn.setEnabled(False)
        self.redo_btn.clicked.connect(self._redo)
        self.redo_btn.setStyleSheet(btn_css)
        row.addWidget(self.redo_btn)
        # v2.9.34 — export PNG de la vue actuelle (pas de composition maison)
        self.export_btn = QPushButton(self.tr("Exporter…"), host)
        self.export_btn.setToolTip(self.tr(
            "Exporter la coupe 2D en PNG\nLégendes et mini-carte optionnelles\nLégendes + mini-carte optionnelles\nCtrl+E"))
        self.export_btn.clicked.connect(self._export_view_png)
        self.export_btn.setStyleSheet(btn_css)
        row.addWidget(self.export_btn)
        # 386 — export À L'ÉCHELLE (A4/A3/A2/A1, 1:N, PDF + PNG calibrés).
        self.export_scaled_btn = QPushButton(self.tr("Export en page…"), host)
        self.export_scaled_btn.setToolTip(self.tr(
            "Exporter la coupe sur une page A4/A3 mise en page "
            "automatiquement (paysage ou portrait), ajustée à la page ou à "
            "l'échelle 1:N.\nPDF + PNG à la taille exacte de la page "
            "(reportable sur papier millimétré)."))
        self.export_scaled_btn.clicked.connect(self._export_scaled)
        self.export_scaled_btn.setStyleSheet(btn_css)
        row.addWidget(self.export_scaled_btn)
        # Raccourcis sur le SectionWidget (toujours actifs en Coupe 2D)
        if not hasattr(self, "_undo_shortcut") or self._undo_shortcut is None:
            self._undo_shortcut = QShortcut(QKeySequence.Undo, self)
            self._undo_shortcut.activated.connect(self._undo)
            self._redo_shortcut = QShortcut(QKeySequence.Redo, self)
            self._redo_shortcut.activated.connect(self._redo)
            self._redo_shortcut_y = QShortcut(QKeySequence("Ctrl+Y"), self)
            self._redo_shortcut_y.activated.connect(self._redo)
            self._export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
            self._export_shortcut.activated.connect(self._export_view_png)
        self._refresh_undo_buttons()
        return host

    def _export_view_png(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import export_view_png
        return export_view_png(self, *args, **kwargs)
    def _export_scaled(self, *args, **kwargs):
        """386 — export à l'échelle (module ui/section_export_scaled)."""
        from .section_export_scaled import export_scaled_dialog
        return export_scaled_dialog(self)
    def _run_deferred_export(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import run_deferred_export
        return run_deferred_export(self, *args, **kwargs)
    def _export_png_dialog(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import export_png_dialog
        return export_png_dialog(self, *args, **kwargs)
    def _export_scene_rect(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import export_scene_rect
        return export_scene_rect(self, *args, **kwargs)
    @staticmethod
    def _crop_white_margins(img, bg_rgb=(255, 255, 255), tol=14, pad=4):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import crop_white_margins
        return crop_white_margins(img, bg_rgb=(255, 255, 255), tol=14, pad=4)
    def _grab_legends_image(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import grab_legends_image
        return grab_legends_image(self, *args, **kwargs)
    def _paint_legends_image(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import paint_legends_image
        return paint_legends_image(self, *args, **kwargs)
    def _paint_legends_image_impl(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import paint_legends_image_impl
        return paint_legends_image_impl(self, *args, **kwargs)
    def _export_domain_codes(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import export_domain_codes
        return export_domain_codes(self, *args, **kwargs)
    def _export_meta_dict(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import export_meta_dict
        return export_meta_dict(self, *args, **kwargs)
    def _paint_export_title(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import paint_export_title
        return paint_export_title(self, *args, **kwargs)
    def _paint_export_footer(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import paint_export_footer
        return paint_export_footer(self, *args, **kwargs)
    def _paint_export_cartouche(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import paint_export_cartouche
        return paint_export_cartouche(self, *args, **kwargs)
    def _paint_locator_map(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import paint_locator_map
        return paint_locator_map(self, *args, **kwargs)

    def _compose_export_page(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import compose_export_page
        return compose_export_page(self, *args, **kwargs)


    def _stamp_locator_on_section(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import stamp_locator_on_section
        return stamp_locator_on_section(self, *args, **kwargs)
    def _render_canvas_to_png(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import render_canvas_to_png
        return render_canvas_to_png(self, *args, **kwargs)
    def _get_svg_generator_class(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import get_svg_generator_class
        return get_svg_generator_class(self, *args, **kwargs)
    def _render_canvas_to_svg(self, *args, **kwargs):
        """Délégué à ui/section_export (v2.9.160)."""
        from .section_export import render_canvas_to_svg
        return render_canvas_to_svg(self, *args, **kwargs)

    def _capture_undo_state(self):
        """Snapshot complet réglages panneau + géométrie coupe."""
        try:
            style = self._section_style_values()
            assay = self._assay_style_values()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Annuler/Rétablir : _capture_undo_state", _exc)
            # widgets pas encore prêts au tout premier paint
            return None
        return {
            "style": dict(style),
            "assay": dict(assay),
            "buffer": float(self.buffer_spin.value()),
            "exaggeration": float(self.exag_slider.value()) / 10.0,
            "section_id": self._current_section_id,
        }

    def _states_equal(self, a, b):
        if a is None or b is None:
            return a is b
        import json
        try:
            return json.dumps(a, sort_keys=True, default=str) == \
                json.dumps(b, sort_keys=True, default=str)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("État/sélection : _states_equal", _exc)
            # comparaison JSON impossible → considérer différent
            return False

    def _ensure_undo_baseline(self):
        """État de référence = dernier état « stable » (avant toute manip)."""
        if getattr(self, "_undo_baseline", None) is None:
            self._undo_baseline = self._capture_undo_state()

    def _schedule_undo_checkpoint(self):
        """Coalescence : un spin continu = 1 entrée d'historique.

        Important : au moment du signal valueChanged, le widget a DÉJÀ
        la nouvelle valeur.  On pousse donc le *baseline* (état d'avant
        la manip), pas un snapshot « current » trop tardif.
        """
        if self._undo_restoring or self._loading_settings:
            return
        self._ensure_undo_baseline()
        if self._undo_pending_before is None:
            # copie du baseline = vrai « avant »
            import copy
            self._undo_pending_before = copy.deepcopy(self._undo_baseline)
        if self._undo_coalesce_timer is None:
            self._undo_coalesce_timer = QTimer(self)
            self._undo_coalesce_timer.setSingleShot(True)
            self._undo_coalesce_timer.timeout.connect(
                self._commit_undo_checkpoint)
        self._undo_coalesce_timer.start(450)

    def _push_undo_now(self):
        """Commit immédiat (actions discrètes)."""
        if self._undo_restoring or self._loading_settings:
            return
        if self._undo_coalesce_timer is not None \
                and self._undo_coalesce_timer.isActive():
            self._undo_coalesce_timer.stop()
            self._commit_undo_checkpoint()
        self._ensure_undo_baseline()
        import copy
        self._undo_pending_before = copy.deepcopy(self._undo_baseline)
        QTimer.singleShot(0, self._commit_undo_checkpoint)

    def _commit_undo_checkpoint(self):
        before = self._undo_pending_before
        self._undo_pending_before = None
        after = self._capture_undo_state()
        if before is None or after is None:
            return
        if self._states_equal(before, after):
            # même état : baseline reste, rien à empiler
            self._undo_baseline = after
            return
        self._undo_stack.append(before)
        if len(self._undo_stack) > self._undo_max:
            self._undo_stack = self._undo_stack[-self._undo_max:]
        self._redo_stack.clear()
        # nouvel état stable
        self._undo_baseline = after
        self._refresh_undo_buttons()

    def _refresh_undo_buttons(self):
        if hasattr(self, "undo_btn"):
            n = len(self._undo_stack)
            self.undo_btn.setEnabled(n > 0)
            # v2.9.205 — périmètre DIT (retour écran : « pour un seul onglet ? »)
            self.undo_btn.setToolTip(
                self.tr("Annuler réglage coupe 2D ({}) — Ctrl+Z")
                .format(n) if n else self.tr("Rien à annuler"))
        if hasattr(self, "redo_btn"):
            n = len(self._redo_stack)
            self.redo_btn.setEnabled(n > 0)
            self.redo_btn.setToolTip(
                self.tr("Rétablir réglage coupe 2D ({}) — Ctrl+Y")
                .format(n) if n else self.tr("Rien à rétablir"))

    def _restore_undo_state(self, state):
        if not state:
            return
        self._undo_restoring = True
        self._loading_settings = True
        try:
            self._apply_project_values(
                state["style"], state["assay"],
                buffer=state.get("buffer", 50.0),
                exaggeration=state.get("exaggeration", 1.0))
            style = state["style"]
            assay = state["assay"]
            self.canvas.set_display_style(
                **style, assay_opacity=assay.get("opacity", 100))
            self.canvas.update_params(
                element=assay.get("element") or None,
                elements=assay.get("elements") or [],
                element_palettes=assay.get("element_palettes") or {},
                classification=assay.get("method", "linear"),
                n_classes=assay.get("n_classes", 7),
                manual_breaks=assay.get("manual_breaks") or [],
                round_breaks=assay.get("round_breaks", True),
                scale_scope=assay.get("scale_scope", "project"),
                palette=assay.get("palette", "grade"),
                threshold_rules=assay.get("threshold_rules") or [],
                threshold_rule=assay.get("threshold_rule"),
            )
            # géométrie buffer/exag
            self.canvas.update_params(
                v_exag=float(state.get("exaggeration", 1.0)))
            if (self.canvas._drillholes and self.canvas._line
                    and (float(state.get("buffer", 50.0))
                         != float(self.canvas._buffer))):
                self.canvas._buffer = float(state.get("buffer", 50.0))
                self.canvas._regenerate()
            project = self._project()
            if project:
                project.save_section_style(**style)
                project.save_assay_style(**assay)
                project.save_section_config(
                    float(state.get("buffer", 50.0)),
                    float(state.get("exaggeration", 1.0)))
            self._sync_track_checks()
            self._update_assay_controls()
            self._update_legends()
            if self._line:
                self._refresh_info_header()
        finally:
            self._loading_settings = False
            self._undo_restoring = False
            self._undo_baseline = self._capture_undo_state()
            self._refresh_undo_buttons()

    def _undo(self, *_args):
        # flush coalescence en cours
        if self._undo_coalesce_timer is not None \
                and self._undo_coalesce_timer.isActive():
            self._undo_coalesce_timer.stop()
            self._commit_undo_checkpoint()
        if not self._undo_stack:
            return
        current = self._capture_undo_state()
        before = self._undo_stack.pop()
        if current is not None:
            self._redo_stack.append(current)
        self._restore_undo_state(before)

    def _redo(self, *_args):
        if not self._redo_stack:
            return
        current = self._capture_undo_state()
        after = self._redo_stack.pop()
        if current is not None:
            self._undo_stack.append(current)
        self._restore_undo_state(after)

    def _on_section_style_change(self, *_args):
        if self._loading_settings or self._undo_restoring:
            return
        self._schedule_undo_checkpoint()
        self._sync_track_checks()
        self._style_timer.start()
        self._persist_section = True
        self._persist_timer.start()

    def _schedule_legends(self, *_args):
        self._legends_timer.start()

    def _flush_style_change(self):
        if self._loading_settings or self._undo_restoring:
            return
        style = self._section_style_values()
        self.canvas.set_display_style(**style)

    def _auto_vertical_exag(self):
        """v2.9.275 — exagération verticale adaptée aux données.

        On vise une hauteur visuelle d'environ un quart de la longueur de la
        coupe pour le forage le plus profond, bornée à [1, 100].  Marche pour
        des trous de 5 m comme de 120 m.
        """
        canvas = getattr(self, "canvas", None)
        line = getattr(canvas, "_line", None) if canvas else None
        holes = getattr(canvas, "_drillholes", None) if canvas else None
        if not line or not holes:
            return
        # v2.9.279 — retour écran : l'ancien calcul (longueur / profondeur
        # max) sortait x100 sur une grille plate de trous de 5 m et dispersait
        # les collets en haut/bas.  On base désormais l'exagération sur
        # l'ÉTENDUE VERTICALE RÉELLE (écart d'altitude des collets + profondeur
        # max) et on PLAFONNE à 5x : un relief lisible sans désastre.
        # v2.9.281 — retour écran : à 3-5x un trou de 2-5 m reste un trait
        # illisible ; il faut ~x10-20 pour lire la colonne.  L'Auto vise
        # désormais une hauteur lisible (15 % de la longueur de coupe pour le
        # trou le plus profond), plafonnée à 20x : lisible sans le désastre
        # du x100.  Un trou profond (120 m) retombe à ~1x (échelle vraie).
        depth_max = max((h.total_depth for h in holes), default=0.0)
        length = line.length
        if depth_max <= 0 or length <= 0:
            return
        exag = max(1.0, min(20.0, (length * 0.15) / depth_max))
        self.exag_slider.setValue(int(round(exag * 10)))
        self._on_geometry_change()

    def _flush_exag_change(self):
        if self._loading_settings or self._undo_restoring:
            return
        self.canvas.update_params(
            v_exag=self.exag_slider.value() / 10.0)

    def _flush_persist(self):
        project = self._project()
        if project is None:
            return
        try:
            if self._persist_section:
                project.save_section_style(**self._section_style_values())
                self._persist_section = False
            if self._persist_assay:
                project.save_assay_style(**self._assay_style_values())
                self._persist_assay = False
                if self.main_dock and getattr(self.main_dock, "visualization_dock", None):
                    viz = self.main_dock.visualization_dock
                    if hasattr(viz, "view_3d_widget"):
                        viz.view_3d_widget.sync_with_project(project)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _flush_persist", _exc)
            # disque occupé / projet fermé — réessayer au prochain geste
            pass

    def _mb_combo_code(self, i: int) -> str:
        """371 — code sélectionné dans le combo d'élément n° i+1."""
        combos = (getattr(self, "element_combo", None),
                  getattr(self, "element2_combo", None),
                  getattr(self, "element3_combo", None))
        cb = combos[i] if i < len(combos) else None
        if cb is None:
            return ""
        code = ((cb.currentData() or "").strip()
                or (cb.currentText() or "").strip())
        return "" if code in ("—", "-") else code

    def _sync_manual_break_labels(self):
        """371 — libellé de chaque champ = code de l'élément choisi."""
        for i, lbl in enumerate(getattr(self, "_mb_labels", [])):
            code = self._mb_combo_code(i)
            if code:
                lbl.setText(self.tr("Seuils · %s") % code)
            else:
                lbl.setText(self.tr("Seuils · Élément %d") % (i + 1))

    def _fill_manual_breaks_fields(self, mb):
        """371 — répartit les seuils enregistrés dans les 3 champs."""
        edits = list(getattr(self, "_mb_edits", None) or [])
        if not edits:
            return
        for ed in edits:
            ed.setText("")
        if isinstance(mb, dict) and mb:
            by = {k: list(v) for k, v in mb.items() if v}
        elif isinstance(mb, (list, tuple)) and mb:
            by = {"": list(mb)}
        else:
            by = {}
        for i, ed in enumerate(edits):
            code = self._mb_combo_code(i)
            vs = by.pop(code, None) if code else None
            if vs is None and i == 0:
                vs = by.pop("", None)
            if vs:
                ed.setText(" ; ".join(
                    f"{v:g}".replace(".", ",") for v in vs))

    def _parse_manual_breaks(self):
        """371 — UN CHAMP PAR ÉLÉMENT → {code: [seuils]}.  Champ 1
        sans élément sélectionné enregistré sous "" (= premier)."""
        out: dict = {}
        edits = list(getattr(self, "_mb_edits", None)
                     or [getattr(self, "manual_breaks_edit", None)])
        for i, ed in enumerate(edits):
            if ed is None:
                continue
            values = []
            for token in (ed.text() or "").split(";"):
                token = token.strip().replace(",", ".")
                if not token:
                    continue
                try:
                    values.append(float(token))
                except ValueError:
                    continue
            if not values:
                continue
            code = self._mb_combo_code(i)
            if not code and i > 0:
                continue  # élément non choisi : seuils sans objet
            out[code] = sorted(set(values))
        return out

    def _read_one_threshold_rule(self, rw: dict, slot_index: int = 0) -> dict:
        """Lit un bloc UI règle → dict normalisé (couleur de slot)."""
        clauses = []
        for wset in (rw.get("clauses") or []):
            elem_cb = wset.get("element")
            op_cb = wset.get("operator")
            val_sp = wset.get("value")
            elem = ""
            if elem_cb is not None:
                elem = elem_cb.currentData() or ""
                if not elem:
                    t = (elem_cb.currentText() or "").strip()
                    if t and t not in ("—", "-"):
                        elem = t
            if not elem:
                continue
            op = ">"
            if op_cb is not None:
                op = op_cb.currentData() or ">"
            val = 0.5
            if val_sp is not None:
                try:
                    val = float(val_sp.value())
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Intercepts/seuils : _read_one_threshold_rule", _exc)
                    val = 0.5
            clauses.append({
                "element": elem, "operator": op, "value": val,
            })
        litho_codes = []
        litho_w = rw.get("litho")
        if litho_w is not None:
            try:
                # v2.9.126 — cases à cocher (v2.9.123) ; plus selectedItems
                litho_codes = list(self._litho_checked_codes(litho_w))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Intercepts/seuils : _read_one_threshold_rule", _exc)
                # cases litho optionnelles
                litho_codes = []
        en_w = rw.get("enabled")
        enabled = bool(en_w.isChecked()) if en_w is not None else False
        payload = {
            "enabled": enabled,
            "clauses": clauses,
            "litho_filter": litho_codes,
            "color": rw.get("color") or threshold_rule_mod.rule_color_for_index(
                slot_index)["hex"],
            "color_name": rw.get("color_name") or threshold_rule_mod.rule_color_for_index(
                slot_index)["name"],
        }
        if clauses:
            payload["element"] = clauses[0]["element"]
            payload["operator"] = clauses[0]["operator"]
            payload["value"] = clauses[0]["value"]
        return threshold_rule_mod.normalize_rule(payload, slot_index=slot_index)

    def _threshold_rules_values(self) -> list:
        """Lit les 0..3 règles du formulaire multi (onglet Seuils)."""
        rws = getattr(self, "threshold_rule_widgets", None) or []
        if not rws:
            # rétrocompat single-rule UI
            if hasattr(self, "threshold_enabled"):
                return [self._threshold_rule_values()]
            return []
        out = []
        for i, rw in enumerate(rws):
            if i >= threshold_rule_mod.MAX_RULES:
                break
            out.append(self._read_one_threshold_rule(rw, slot_index=i))
        return out

    def _threshold_rule_values(self) -> dict:
        """Miroir legacy : 1ʳᵉ règle active (ou slot 0)."""
        rules = self._threshold_rules_values()
        mig = threshold_rule_mod.migrate_threshold_payload({
            "threshold_rules": rules})
        return mig.get("threshold_rule") or threshold_rule_mod.empty_rule(0)

    def _apply_one_threshold_widgets(self, rw: dict, rule: dict,
                                     slot_index: int = 0) -> None:
        """Applique un dict règle sur un bloc UI."""
        rule = threshold_rule_mod.normalize_rule(rule, slot_index=slot_index)
        widgets = [rw.get("enabled"), rw.get("litho")]
        for wset in (rw.get("clauses") or []):
            widgets.extend([
                wset.get("element"), wset.get("operator"), wset.get("value"),
            ])
        widgets = [w for w in widgets if w is not None]
        for w in widgets:
            try:
                w.blockSignals(True)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Intercepts/seuils : _apply_one_threshold_widgets", _exc)
                # widget Qt sans blockSignals
                pass
        try:
            en = rw.get("enabled")
            if en is not None:
                en.setChecked(bool(rule.get("enabled")))
            clauses = list(rule.get("clauses") or [])
            for i, wset in enumerate(rw.get("clauses") or []):
                elem_cb = wset.get("element")
                op_cb = wset.get("operator")
                val_sp = wset.get("value")
                cl = clauses[i] if i < len(clauses) else None
                elem = (cl or {}).get("element") or ""
                if elem_cb is not None:
                    if elem and elem_cb.findData(elem) < 0:
                        elem_cb.addItem(elem, elem)
                    self._set_combo_data(elem_cb, elem if elem else "")
                if op_cb is not None:
                    self._set_combo_data(
                        op_cb, (cl or {}).get("operator") or ">")
                if val_sp is not None:
                    try:
                        self._apply_threshold_value_range(val_sp, elem)
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("Intercepts/seuils : _apply_one_threshold_widgets", _exc)
                        # plage optionnelle
                        pass
                    if cl and cl.get("value") is not None:
                        try:
                            val_sp.setValue(float(cl["value"]))
                        except Exception as _exc:
                            from ..core.diagnostics import log_swallowed
                            log_swallowed("Intercepts/seuils : _apply_one_threshold_widgets", _exc)
                            # valeur hors plage spin — clamp Qt
                            pass
            litho_w = rw.get("litho")
            if litho_w is None:
                return
            want = {
                str(c).strip().casefold()
                for c in (rule.get("litho_filter") or [])
                if str(c).strip()
            }
            existing = []
            seen = set()
            for cb in getattr(litho_w, "_dm_litho_checks", None) or []:
                try:
                    code = str(cb.property("dm_litho_code") or cb.text() or "")
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Intercepts/seuils : _apply_one_threshold_widgets", _exc)
                    # checkbox Qt déjà détruit
                    continue
                cf = code.casefold()
                if code and cf not in seen:
                    existing.append(code)
                    seen.add(cf)
            for c in (rule.get("litho_filter") or []):
                cs = str(c).strip()
                if cs and cs.casefold() not in seen:
                    existing.append(cs)
                    seen.add(cs.casefold())
            self._rebuild_litho_checks(litho_w, existing, want)
        finally:
            for w in widgets:
                try:
                    w.blockSignals(False)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Intercepts/seuils : _apply_one_threshold_widgets", _exc)
                    # widget Qt sans blockSignals
                    pass

    def _apply_threshold_widgets(self, rule_or_rules) -> None:
        """Applique threshold_rule (legacy) OU threshold_rules (liste)."""
        rws = getattr(self, "threshold_rule_widgets", None) or []
        if not rws:
            return
        if isinstance(rule_or_rules, (list, tuple)):
            rules = threshold_rule_mod.normalize_rules(rule_or_rules)
        elif isinstance(rule_or_rules, dict) and (
                "threshold_rules" in rule_or_rules
                or "threshold_rule" in rule_or_rules):
            mig = threshold_rule_mod.migrate_threshold_payload(rule_or_rules)
            rules = mig.get("threshold_rules") or []
        else:
            # single rule → slot 0 ; autres slots vides
            rules = threshold_rule_mod.normalize_rules(
                [rule_or_rules] if rule_or_rules else [])
        # pad to MAX_RULES empty slots so UI clears unused rules
        while len(rules) < len(rws):
            rules.append(threshold_rule_mod.empty_rule(len(rules)))
        for i, rw in enumerate(rws):
            r = rules[i] if i < len(rules) else threshold_rule_mod.empty_rule(i)
            self._apply_one_threshold_widgets(rw, r, slot_index=i)

    def _populate_threshold_combos(self) -> None:
        """Remplit éléments + litho pour TOUTES les règles (onglet Seuils)."""
        rws = getattr(self, "threshold_rule_widgets", None) or []
        if not rws and not getattr(self, "threshold_clause_widgets", None):
            return
        codes_opts = []
        seen = set()
        for combo_name in ("element_combo", "element2_combo", "element3_combo"):
            cb = getattr(self, combo_name, None)
            if cb is None:
                continue
            for i in range(cb.count()):
                data = cb.itemData(i)
                text = cb.itemText(i)
                code = data if data else text
                if not code or code in seen or code in ("—", "-"):
                    continue
                seen.add(code)
                codes_opts.append((str(text or code), code))

        # collect all clause element combos across rules
        clause_cbs = []
        litho_ws = []
        if rws:
            for rw in rws:
                for wset in (rw.get("clauses") or []):
                    if wset.get("element") is not None:
                        clause_cbs.append(wset.get("element"))
                if rw.get("litho") is not None:
                    litho_ws.append(rw.get("litho"))
        else:
            for wset in getattr(self, "threshold_clause_widgets", None) or []:
                if wset.get("element") is not None:
                    clause_cbs.append(wset.get("element"))
            if getattr(self, "threshold_litho", None) is not None:
                litho_ws.append(self.threshold_litho)

        for elem_cb in clause_cbs:
            cur = elem_cb.currentData() or ""
            elem_cb.blockSignals(True)
            elem_cb.clear()
            elem_cb.addItem(self.tr("—"), "")
            for lab, code in codes_opts:
                elem_cb.addItem(lab, code)
            if cur:
                self._set_combo_data(elem_cb, cur)
            elem_cb.blockSignals(False)

        # litho codes partagés (même liste pour chaque règle)
        codes = []
        try:
            dhs = getattr(self, "_drillholes", None) or []
            if not dhs and self.main_dock:
                dhs = getattr(self.main_dock, "drillholes", None) or []
            if not dhs:
                dhs = getattr(self.canvas, "_drillholes", None) or []
            codes = get_all_litho_codes(dhs) if dhs else []
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Intercepts/seuils : _populate_threshold_combos", _exc)
            codes = []
        codes_sorted = sorted(codes, key=lambda c: str(c).casefold())
        for litho_w in litho_ws:
            cur_sel = {
                str(c).casefold()
                for c in self._litho_checked_codes(litho_w)
            }
            self._rebuild_litho_checks(litho_w, codes_sorted, cur_sel)

    def _litho_checked_codes(self, litho_w) -> list:
        """Codes litho cochés (cases) — présentation only, même modèle."""
        codes = []
        if litho_w is None:
            return codes
        for cb in getattr(litho_w, "_dm_litho_checks", None) or []:
            try:
                if not cb.isChecked():
                    continue
                data = cb.property("dm_litho_code") or cb.text()
                if data:
                    codes.append(str(data))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Piste lithologie : _litho_checked_codes", _exc)
                # checkbox Qt déjà détruit
                continue
        return codes

    def _rebuild_litho_checks(self, litho_w, codes, selected_fold) -> None:
        """Recrée les cases litho (connect APRÈS setChecked → pas de signal)."""
        if litho_w is None:
            return
        layout = litho_w.layout()
        if layout is None:
            layout = QVBoxLayout(litho_w)
            layout.setContentsMargins(4, 2, 4, 2)
            layout.setSpacing(1)
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget() if item is not None else None
            if w is not None:
                w.deleteLater()
        selected_fold = {
            str(c).strip().casefold() for c in (selected_fold or [])
            if str(c).strip()
        }
        checks = []
        codes_list = [str(c).strip() for c in (codes or []) if str(c).strip()]
        if not codes_list:
            hint = QLabel(self.tr("Aucune lithologie importée."))
            hint.setObjectName("label_hint")
            hint.setWordWrap(True)
            layout.addWidget(hint)
            litho_w._dm_litho_checks = []
            return
        for code in codes_list:
            cb = QCheckBox(str(code))
            cb.setProperty("dm_litho_code", str(code))
            cb.setChecked(str(code).casefold() in selected_fold)
            cb.stateChanged.connect(self._on_threshold_change)
            layout.addWidget(cb)
            checks.append(cb)
        litho_w._dm_litho_checks = checks

    def _threshold_intervals_source(self):
        """Forages du projet / canvas pour lire les teneurs réelles."""
        dhs = getattr(self, "_drillholes", None) or []
        if not dhs and getattr(self, "main_dock", None):
            dhs = getattr(self.main_dock, "drillholes", None) or []
        if not dhs and getattr(self, "canvas", None) is not None:
            dhs = getattr(self.canvas, "_drillholes", None) or []
        return dhs

    def _element_numeric_range(self, element: str):
        """(vmin, vmax) réels de l'élément, ou None."""
        return threshold_rule_mod.element_value_range(
            element, self._threshold_intervals_source())

    def _apply_threshold_value_range(self, val_sp, element: str) -> bool:
        """Borne le spin aux valeurs présentes. True si la valeur a bougé."""
        if val_sp is None:
            return False
        prev = None
        try:
            prev = float(val_sp.value())
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Intercepts/seuils : _apply_threshold_value_range", _exc)
            prev = None
        elem = str(element or "").strip()
        val_sp.blockSignals(True)
        try:
            if not elem:
                val_sp.setEnabled(False)
                val_sp.setToolTip(self.tr("Choisissez d'abord un élément."))
                return False
            val_sp.setEnabled(True)
            rng = self._element_numeric_range(elem)
            if rng is None:
                val_sp.setRange(0.0, 1.0)
                val_sp.setDecimals(3)
                val_sp.setSingleStep(0.1)
                val_sp.setToolTip(
                    self.tr("{} : aucune valeur numérique dans le projet.").format(elem))
                return False
            lo, hi = float(rng[0]), float(rng[1])
            if hi < lo:
                lo, hi = hi, lo
            val_sp.setRange(lo, hi)
            span = hi - lo
            if span <= 0:
                val_sp.setDecimals(4)
                val_sp.setSingleStep(0.01)
            elif span <= 1:
                val_sp.setDecimals(4)
                val_sp.setSingleStep(0.01)
            elif span <= 50:
                val_sp.setDecimals(3)
                val_sp.setSingleStep(0.1)
            elif span <= 500:
                val_sp.setDecimals(2)
                val_sp.setSingleStep(1.0)
            else:
                val_sp.setDecimals(1)
                val_sp.setSingleStep(10.0)
            lo_s = f"{lo:g}"
            hi_s = f"{hi:g}"
            val_sp.setToolTip(
                self.tr("{} : {} – {} (valeurs présentes dans le projet)").format(elem, lo_s, hi_s))
        finally:
            val_sp.blockSignals(False)
        try:
            now = float(val_sp.value())
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Intercepts/seuils : _apply_threshold_value_range", _exc)
            return False
        if prev is None:
            return False
        return abs(now - prev) > 1e-12

    def _refresh_threshold_value_ranges(self) -> bool:
        """Recale tous les spins seuil sur le min/max de leur élément."""
        changed = False
        rws = getattr(self, "threshold_rule_widgets", None) or []
        clause_sets = []
        if rws:
            for rw in rws:
                clause_sets.extend(rw.get("clauses") or [])
        else:
            clause_sets = list(
                getattr(self, "threshold_clause_widgets", None) or [])
        for wset in clause_sets:
            elem_cb = wset.get("element")
            val_sp = wset.get("value")
            if val_sp is None:
                continue
            elem = ""
            if elem_cb is not None:
                elem = elem_cb.currentData() or ""
                if not elem:
                    t = (elem_cb.currentText() or "").strip()
                    if t and t not in ("—", "-"):
                        elem = t
            if self._apply_threshold_value_range(val_sp, elem):
                changed = True
        return changed

    def _on_threshold_change(self, *_args):
        if self._loading_settings or self._undo_restoring:
            return
        try:
            self._refresh_threshold_value_ranges()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Intercepts/seuils : _on_threshold_change", _exc)
            # plage min/max optionnelle
            pass
        self._schedule_undo_checkpoint()
        style = self._assay_style_values()
        rules = style.get("threshold_rules") or []
        if hasattr(self.canvas, "set_threshold_rules"):
            self.canvas.set_threshold_rules(rules)
        else:
            self.canvas.set_threshold_rule(style.get("threshold_rule") or {})
        try:
            self.canvas._render()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Intercepts/seuils : _on_threshold_change", _exc)
            # scène non prête — outlines appliqués au prochain render
            pass
        project = self._project()
        if project:
            project.save_assay_style(**style)
        self._update_threshold_hint(rules)

    def _sync_assay_element_units(self) -> None:
        """Unités par élément pour les libellés de piste (« Fe % »)."""
        units = {}
        try:
            elems = []
            try:
                style = self._assay_style_values()
                elems = multi_assay_mod.normalize_elements(
                    list(style.get("elements") or [])
                    or ([style.get("element")] if style.get("element") else []))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Piste teneurs : _sync_assay_element_units", _exc)
                # combos pas encore prêts
                elems = []
            if not elems and getattr(self, "canvas", None) is not None:
                elems = multi_assay_mod.normalize_elements(
                    getattr(self.canvas, "_assay_elements", None) or [])
            for el in elems:
                u = self._threshold_unit_for_element(el)
                if u:
                    units[str(el)] = u
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste teneurs : _sync_assay_element_units", _exc)
            # référentiel optionnel — libellé = code seul
            units = {}
        if getattr(self, "canvas", None) is not None:
            self.canvas._assay_element_units = units

    def _threshold_unit_for_element(self, element: str) -> str:
        """Unité d'un élément (Référentiel) — jamais partagée entre clauses."""
        elem = str(element or "").strip()
        if not elem:
            return ""
        try:
            project = self._project() if hasattr(self, "_project") else None
            if project is None:
                return ""
            repo = project.get_reference_repository()
            entry = None
            try:
                entry = repo.get_entry("assay_elements", elem)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Piste teneurs : _threshold_unit_for_element", _exc)
                entry = None
            if entry is None:
                domain = (repo.domains.get("assay_elements")
                          or repo.domains.get("assay")
                          or None)
                if domain is not None:
                    entries = getattr(domain, "entries", None) or {}
                    entry = entries.get(elem)
            if entry is None:
                return ""
            u = (getattr(entry, "display_unit", None)
                 or getattr(entry, "source_unit", None)
                 or "")
            return str(u).strip() if u else ""
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste teneurs : _threshold_unit_for_element", _exc)
            # référentiel optionnel
            return ""

    def _threshold_units_map(self, rule=None) -> dict:
        """Dict élément → unité pour TOUTES les clauses (une ou multi-règles).

        v2.9.111 — unités par clause.
        v2.9.116 — accepte une règle OU une liste de règles.
        """
        rules = []
        if rule is None:
            rules = list(getattr(self.canvas, "_threshold_rules", None) or [])
            if not rules:
                r = getattr(self.canvas, "_threshold_rule", None)
                if r:
                    rules = [r]
        elif isinstance(rule, (list, tuple)):
            rules = list(rule)
        else:
            rules = [rule]
        out = {}
        for r0 in rules:
            r = threshold_rule_mod.normalize_rule(r0)
            for cl in (r.get("clauses") or []):
                el = str(cl.get("element") or "").strip()
                if not el or el in out:
                    continue
                u = self._threshold_unit_for_element(el)
                if u:
                    out[el] = u
            if r.get("element") and str(r.get("element")) not in out:
                u = self._threshold_unit_for_element(r.get("element"))
                if u:
                    out[str(r.get("element"))] = u
        return out

    def _threshold_unit_for_rule(self, rule=None) -> str:
        """Rétrocompat : unité de la 1ʳᵉ clause seulement (ne plus utiliser
        seule pour multi-ET — préférer _threshold_units_map)."""
        rule = threshold_rule_mod.normalize_rule(
            rule if rule is not None else getattr(
                self.canvas, "_threshold_rule", None))
        elem = rule.get("element") or ""
        if not elem and (rule.get("clauses") or []):
            elem = (rule["clauses"][0] or {}).get("element") or ""
        return self._threshold_unit_for_element(elem)

    def _refresh_threshold_legend_panel(self, text: str = "") -> None:
        """Affiche / masque la ligne légende seuil dans le panneau Légendes."""
        if not hasattr(self, "threshold_legend_label"):
            return
        t = (text or "").strip()
        if not t:
            try:
                t = self.threshold_legend_text()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Légende : _refresh_threshold_legend_panel", _exc)
                t = ""
        if t:
            self.threshold_legend_label.setText(t)
            self.threshold_legend_label.setVisible(True)
            if hasattr(self, "threshold_legend_title"):
                self.threshold_legend_title.setVisible(True)
        else:
            self.threshold_legend_label.setText(self.tr(""))
            self.threshold_legend_label.setVisible(False)
            if hasattr(self, "threshold_legend_title"):
                self.threshold_legend_title.setVisible(False)

    def threshold_legend_text(self, rule=None) -> str:
        """Source unique dock + export : légende multi-règles.

        v2.9.111 — unités **par clause**.
        v2.9.116 — une ligne par règle active (cyan / magenta / ambre).
        ``rule`` peut être une règle, une liste, ou None (= canvas).
        """
        rules = None
        if rule is None:
            rules = list(getattr(self.canvas, "_threshold_rules", None) or [])
            if not rules:
                r = getattr(self.canvas, "_threshold_rule", None)
                if threshold_rule_mod.is_active(r):
                    rules = [r]
                else:
                    try:
                        rules = self._threshold_rules_values()
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("Légende : threshold_legend_text", _exc)
                        # widgets absents
                        rules = []
        elif isinstance(rule, (list, tuple)):
            rules = list(rule)
        else:
            rules = [rule]
        units = self._threshold_units_map(rules)
        entries = threshold_rule_mod.legend_labels_multi(rules, units=units)
        if not entries:
            return ""
        return "\n".join(e["text"] for e in entries)

    def _update_threshold_hint(self, rule=None):
        if not hasattr(self, "threshold_hint"):
            return
        text = self.threshold_legend_text(rule)
        if not text:
            self.threshold_hint.setText(self.tr(
                "Aucune règle active. Activez une règle ci-dessus (ex. Fe > 10 → cyan, Cu > 1 → magenta). Visible en coupe et à l'export PNG."))
            try:
                self._refresh_threshold_legend_panel("")
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Intercepts/seuils : _update_threshold_hint", _exc)
                # panneau légende optionnel
                pass
            return
        # règles actives — légende auto (multi-lignes)
        self.threshold_hint.setText(text)
        if hasattr(self, "threshold_legend_label"):
            try:
                self.threshold_legend_label.setText(text)
                self.threshold_legend_label.setVisible(True)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Intercepts/seuils : _update_threshold_hint", _exc)
                # label optionnel
                pass
        try:
            self._refresh_threshold_legend_panel(text)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Intercepts/seuils : _update_threshold_hint", _exc)
            # panneau légende optionnel
            pass

    def _assay_style_values(self):
        e1 = self.element_combo.currentData() or ""
        e2 = getattr(self, "element2_combo", None)
        e3 = getattr(self, "element3_combo", None)
        e2v = (e2.currentData() if e2 is not None else None) or ""
        e3v = (e3.currentData() if e3 is not None else None) or ""
        elements = multi_assay_mod.normalize_elements([e1, e2v, e3v])
        p1 = self.ramp_combo.currentData() or "grade"
        p2 = (getattr(self, "ramp2_combo", None).currentData()
              if getattr(self, "ramp2_combo", None) is not None else p1) or p1
        p3 = (getattr(self, "ramp3_combo", None).currentData()
              if getattr(self, "ramp3_combo", None) is not None else p1) or p1
        palettes = {}
        if len(elements) >= 1:
            palettes[elements[0]] = p1
        if len(elements) >= 2:
            palettes[elements[1]] = p2
        if len(elements) >= 3:
            palettes[elements[2]] = p3
        rules = self._threshold_rules_values()
        mig = threshold_rule_mod.migrate_threshold_payload({
            "threshold_rules": rules})
        style = {
            "element": elements[0] if elements else "",
            "elements": elements,
            "element_palettes": palettes,
            "method": self.classif_combo.currentData() or "linear",
            "n_classes": self.n_classes_spin.value(),
            "manual_breaks": self._parse_manual_breaks(),
            "round_breaks": self.round_breaks_chk.isChecked(),
            "scale_scope": self.scale_scope_combo.currentData() or "project",
            "palette": p1,
            "opacity": self.assay_opacity.value(),
            "map_line_width": self.assay_map_width.value(),
            "threshold_rule": mig.get("threshold_rule"),
            "threshold_rules": mig.get("threshold_rules") or rules,
        }
        return multi_assay_mod.migrate_assay_style(style)

    def _update_assay_controls(self):
        method = self.classif_combo.currentData() or "linear"
        manual = method == "manual"
        classified = method in ("equal", "quantile", "jenks")
        for _ed in getattr(self, "_mb_edits", None) or \
                [self.manual_breaks_edit]:
            _ed.setEnabled(manual)
        self._sync_manual_break_labels()  # 371 : « Seuils · Li »…
        self.n_classes_spin.setEnabled(classified)
        self.round_breaks_chk.setEnabled(method == "jenks")
        hints = {
            "linear": self.tr(
                "Rampe continue : chaque teneur reçoit une couleur selon le min/max du projet."),
            "log": self.tr(
                "Rampe continue logarithmique : adaptée aux teneurs couvrant plusieurs ordres de grandeur."),
            "equal": self.tr(
                "Classes discrètes de largeur égale. Changer le nombre de classes modifie les bornes et les couleurs."),
            "quantile": self.tr(
                "Classes discrètes avec un effectif proche par classe. Changer le nombre modifie les bornes et les couleurs."),
            "jenks": self.tr(
                "Classes par ruptures naturelles (groupes homogènes). 7 classes et bornes arrondies recommandées."),
            "manual": self.tr(
                "Classes discrètes définies par les limites saisies dans le champ Seuils."),
        }
        self.classification_hint.setText(hints.get(method, ""))

    def _on_assay_change(self, *_args):
        self._update_assay_controls()
        if self._loading_settings or self._undo_restoring:
            return
        self._schedule_undo_checkpoint()
        style = self._assay_style_values()
        if self.main_dock:
            self.main_dock.workspace_state.set(
                "active_element", style["element"] or None)
        try:
            self._sync_assay_element_units()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste teneurs : _on_assay_change", _exc)
            # unités optionnelles — libellé = code seul
            pass
        self.canvas.set_display_style(assay_opacity=style["opacity"])
        self.canvas.update_params(
            element=style["element"] or None,
            elements=style.get("elements") or [],
            element_palettes=style.get("element_palettes") or {},
            classification=style["method"],
            n_classes=style["n_classes"],
            manual_breaks=style["manual_breaks"],
            round_breaks=style["round_breaks"],
            scale_scope=style["scale_scope"],
            palette=style["palette"],
        )
        self._persist_assay = True
        self._persist_timer.start()
        if self.main_dock:
            self.main_dock.update_assay_layer_style(style)

    # ------------------------------------------------------------------
    # Lithology reference and legends
    # ------------------------------------------------------------------
    def _open_lithology_reference(self, *_args):
        self._open_domain_reference("lithology")

    def _open_domain_reference(self, domain_key, *_args):
        """Open the project referential straight on the right domain —
        same shortcut for every coded track (litho, altérations,
        minéralisations)."""
        if self.main_dock:
            self.main_dock._open_reference_dialog(domain_key)


    @staticmethod
    def _lithology_symbol_pixmap(style):
        """Pastille légende = MÊME rendu que la bande (v2.9.27 / v2.9.80).

        v2.9.81 — jamais lever jusqu'à set_drillholes : repli aplat si
        motif/engine indisponible (protection plugin).
        """
        key = (
            (style or {}).get("color"),
            (style or {}).get("pattern"),
            (style or {}).get("hatch"),
        )
        cache = SectionWidget._SWATCH_CACHE
        hit = cache.get(key)
        if hit is not None:
            return hit
        try:
            pm = SectionWidget._lithology_symbol_pixmap_impl(style)
            cache[key] = pm
            return pm
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste lithologie : _lithology_symbol_pixmap", _exc)
            # defensive: pastille neutre plutôt que bloquer l'étape 3→4
            try:
                w, h = 32, 18
                pixmap = QPixmap(w, h)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                base = QColor((style or {}).get("color") or "#CCCCCC")
                painter.fillRect(0, 0, w - 1, h - 1, QBrush(base, Qt.SolidPattern))
                painter.setPen(QPen(QColor("#888888"), 1))
                painter.setBrush(QBrush(Qt.NoBrush))
                painter.drawRect(0, 0, w - 1, h - 1)
                painter.end()
                return pixmap
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Piste lithologie : _lithology_symbol_pixmap", _exc)
                return QPixmap(32, 18)

    @staticmethod
    def _lithology_symbol_pixmap_impl(style):
        """Pastille légende = rendu motifs 2.9.33 (coupe=légende)."""
        data = style or {}
        brush_style = _LITHO_BRUSH_PATTERNS.get(
            normalise_pattern(data.get("pattern", "")), Qt.SolidPattern)
        w, h = 32, 18
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, False)
        gradient = data.get("gradient")
        base = QColor(data.get("color") or "#CCCCCC")
        if gradient and len(gradient) >= 2:
            from qgis.PyQt.QtGui import QLinearGradient
            grad = QLinearGradient(0, h / 2.0, w - 1, h / 2.0)
            n = len(gradient)
            for i, hexs in enumerate(gradient):
                grad.setColorAt(i / max(n - 1, 1), QColor(hexs))
            painter.fillRect(0, 0, w - 1, h - 1, QBrush(grad))
        elif brush_style != Qt.SolidPattern:
            underlay = QColor(base)
            underlay.setAlpha(round(255 * PATTERN_UNDERLAY_ALPHA_RATIO))
            painter.fillRect(0, 0, w - 1, h - 1,
                             QBrush(underlay, Qt.SolidPattern))
        else:
            painter.fillRect(0, 0, w - 1, h - 1, QBrush(base, Qt.SolidPattern))
        legend_ink = _pattern_ink_colour(base, brush_style)
        if brush_style in _LINE_BRUSH_STYLES:
            legend_ink.setAlpha(min(max(legend_ink.alpha(), 180), 230))
        elif brush_style != Qt.SolidPattern:
            legend_ink.setAlpha(max(legend_ink.alpha(), 200))
        if brush_style != Qt.SolidPattern:
            if brush_style in _LINE_BRUSH_STYLES:
                painter.setPen(QPen(Qt.NoPen))
                painter.setBrush(QBrush(Qt.NoBrush))
                pen = QPen(legend_ink, 1.0)
                painter.setPen(pen)
                if brush_style in (Qt.HorPattern, Qt.CrossPattern):
                    for frac in (0.33, 0.66):
                        y = h * frac
                        painter.drawLine(1, int(y), w - 2, int(y))
                if brush_style in (Qt.VerPattern, Qt.CrossPattern):
                    for frac in (0.33, 0.66):
                        x = w * frac
                        painter.drawLine(int(x), 1, int(x), h - 2)
                if brush_style in (Qt.FDiagPattern, Qt.DiagCrossPattern):
                    painter.drawLine(1, 1, w - 2, h - 2)
                    painter.drawLine(1, h // 3, w * 2 // 3, h - 2)
                    painter.drawLine(w // 3, 1, w - 2, h * 2 // 3)
                if brush_style in (Qt.BDiagPattern, Qt.DiagCrossPattern):
                    painter.drawLine(1, h - 2, w - 2, 1)
                    painter.drawLine(1, h * 2 // 3, w * 2 // 3, 1)
                    painter.drawLine(w // 3, h - 2, w - 2, h // 3)
            else:
                painter.setPen(QPen(Qt.NoPen))
                painter.setBrush(QBrush(legend_ink, brush_style))
                painter.drawRect(0, 0, w - 1, h - 1)
        painter.setPen(QPen(QColor(COLORS.get("border_dark", "#7F8C8D")), 1))
        painter.setBrush(QBrush(Qt.NoBrush))
        painter.drawRect(0, 0, w - 1, h - 1)
        painter.end()
        return pixmap

    def set_litho_styles(self, styles):
        self._litho_styles = styles or {}
        self.canvas._litho_styles = self._litho_styles
        self._populate_litho_table()
        if self.canvas._result:
            self.canvas._render()

    def set_style_resolver(self, resolver):
        """Inject the live project category resolver (Référentiel du projet).

        Used by domains without a legacy colour stack (alteration,
        mineralization style…).  The resolver reads the saved référentiel,
        so redraws always reflect the latest accepted changes.
        """
        self.canvas._style_resolver = resolver
        self.canvas._style_cache.clear()
        if self.canvas._result:
            self.canvas._render()

    def reload_reference_styles(self):
        """v2.7.10 — CHEMIN UNIQUE de synchronisation.

        Reconstruit TOUT depuis le dépôt du projet, sans cache : styles
        de lithologie, résolveur de symboles, échelle d'éléments, rendu
        de la coupe et légendes. Appelé après chaque édition du
        Référentiel — si quelque chose ne se reflète pas, c'est un bug
        signalé ici, pas une chaîne d'appels à deviner.
        """
        project = self._project()
        if project:
            self._litho_styles = project.get_litho_styles()
            self.canvas._litho_styles = self._litho_styles
            self.canvas._style_resolver = project.resolve_category_style
        self.canvas._style_cache.clear()
        self._populate_elements()
        self._populate_litho_table()
        if self.canvas._result:
            self.canvas._render()
        self._update_legends()

    def refresh_styles(self):
        """Alias de compatibilité du chemin unique (v2.7.10)."""
        self.reload_reference_styles()

    def _populate_litho_table(self):
        """Compatibility hook: symbols now live only in the Référentiel."""
        self._update_legends()

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _format_assay_value(self, value, element=None):
        project = self._project()
        if project and element:
            entry = project.get_reference_repository().get_entry(
                "assay_elements", element)
            if entry and entry.precision is not None:
                precision = max(0, min(int(entry.precision), 12))
                return f"{value:.{precision}f}"
        # 358 — JAMAIS de notation scientifique (« 1.01e+04 » rejeté
        # en retour écran) : formateur partagé, bornes lisibles.
        from ..core.multi_assay import format_grade_value
        return format_grade_value(float(value))

    def _update_legends(self):
        if hasattr(self, "legend_group_collapsible") and self.legend_group_collapsible:
            if not self.legend_group_collapsible.header.isChecked():
                self.legend_group_collapsible.header.setChecked(True)
        self._domain_data_memo = {}
        palette = self.ramp_combo.currentData() or "grade"
        swatches = "".join(
            f'<span style="background:{assay_ramp_rgb(ratio, palette)};">&nbsp;&nbsp;</span>'
            for ratio in (0.0, 0.25, 0.5, 0.75, 1.0)
        )
        self.ramp_preview.setText(self.tr("Faible&nbsp; {} &nbsp;Fort").format(swatches))

        scales = getattr(self.canvas, "_assay_scales", None) or {}
        elems = multi_assay_mod.normalize_elements(
            getattr(self.canvas, "_assay_elements", None)
            or ([self.canvas._element] if self.canvas._element else []))
        pals = dict(getattr(self.canvas, "_assay_element_palettes", None) or {})
        scope = (self.tr("projet")
                 if self.scale_scope_combo.currentData() == "project"
                 else self.tr("coupe"))
        if scales and elems:
            blocks = []
            for code in elems:
                scale = scales.get(code)
                if not scale:
                    continue
                method = scale.get("method", "linear")
                element = self._element_display_label(code)
                pal = pals.get(code) or palette
                if method in ("linear", "log"):
                    colours = "".join(
                        f'<span style="background:{assay_ramp_rgb(r, pal)};">'
                        f'&nbsp;&nbsp;&nbsp;</span>'
                        for r in (0.0, 0.25, 0.5, 0.75, 1.0))
                    method_label = (
                        self.tr("continue linéaire")
                        if method == "linear"
                        else self.tr("continue logarithmique"))
                    minimum = self._format_assay_value(scale["vmin"], code)
                    maximum = self._format_assay_value(scale["vmax"], code)
                    blocks.append(
                        f"<b>{element}</b><br>{minimum} &nbsp;{colours}&nbsp; "
                        f"{maximum}<br><i>{method_label}</i>")
                else:
                    rows = [f"<b>{element}</b>"]
                    for lower, upper, ratio in assay_scale_classes(scale):
                        colour = assay_ramp_rgb(ratio, pal)
                        lower_text = self._format_assay_value(lower, code)
                        upper_text = self._format_assay_value(upper, code)
                        rows.append(
                            f'<span style="background:{colour}; '
                            f'border:1px solid #777;">'
                            f'&nbsp;&nbsp;&nbsp;</span> '
                            f'{lower_text} – {upper_text}')
                    # v2.9.95 — pas de « Jenks arrondi… » sous chaque
                    # élément (casse la 2-col et jargon inutile : les
                    # bornes affichées SONT déjà les classes).
                    blocks.append("<br>".join(rows))
            if blocks:
                # note unique sous le bloc (pas une ligne par colonne)
                any_rounded = any(
                    (scales.get(c) or {}).get("method") == "jenks"
                    and (scales.get(c) or {}).get("rounding_step")
                    for c in elems)
                tail = self.tr("<br><i>échelle {}").format(scope)
                if len(elems) > 1:
                    tail += self.tr(" · {} éléments").format(len(elems))
                if any_rounded:
                    tail += self.tr(" · bornes de classes arrondies")
                tail += "</i>"
                if len(blocks) >= 2:
                    # v2.9.94 — 2 colonnes côte à côte (gain de place)
                    cells = []
                    for b in blocks:
                        cells.append(
                            f'<td style="vertical-align:top;padding:0 8px 6px 0;">'
                            f'{b}</td>')
                    rows_html = []
                    for i in range(0, len(cells), 2):
                        pair = cells[i:i + 2]
                        if len(pair) == 1:
                            pair.append('<td></td>')
                        rows_html.append("<tr>" + "".join(pair) + "</tr>")
                    html = (
                        '<table cellspacing="0" cellpadding="0" width="100%">'
                        + "".join(rows_html) + "</table>" + tail)
                    self.assay_legend.setText(html)
                else:
                    self.assay_legend.setText("<br><br>".join(blocks) + tail)
            else:
                self.assay_legend.setText(
                    self.tr("Aucune échelle de teneur disponible."))
        else:
            self.assay_legend.setText(self.tr("Aucune échelle de teneur disponible."))

        # v2.7.6.1 (LEG-02) — la légende suit les cases à cocher du groupe
        # « Pistes » : une piste décochée disparaît de la légende.
        # v2.9.117 — + masquée si AUCUNE donnée importée (plus de message
        # « Aucune X disponible » pour une piste fantôme cochée par défaut).
        has_assays = self._project_has_domain_data("assays")
        has_litho = self._project_has_domain_data("litho")
        has_alter = self._project_has_domain_data("alterations")
        has_mineral = self._project_has_domain_data("mineralizations")
        has_structure = self._project_has_domain_data("structures")
        show_assays = bool(
            getattr(self.canvas, "_show_assays", False) and has_assays and (
                getattr(self.canvas, "_element", None)
                or getattr(self.canvas, "_assay_elements", None)))
        for widget in (self.assay_legend_title, self.assay_legend):
            widget.setVisible(show_assays)
        # v2.9.104 — ligne seuil auto (masquée si règle inactive
        # ou piste teneurs décochée / absente)
        try:
            if not getattr(self.canvas, "_show_intercepts", True):
                if hasattr(self, "threshold_legend_label"):
                    self.threshold_legend_label.setVisible(False)
                if hasattr(self, "threshold_legend_title"):
                    self.threshold_legend_title.setVisible(False)
            else:
                self._refresh_threshold_legend_panel()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Légende : _update_legends", _exc)
            # légende intercepts optionnelle
            pass
        show_litho = bool(
            getattr(self.canvas, "_show_litho", False) and has_litho)
        for widget in (self.litho_legend_title, self.litho_legend_widget):
            widget.setVisible(show_litho)
        show_alterations = bool(
            getattr(self.canvas, "_show_alterations", False) and has_alter)
        for widget in (self.alter_legend_title, self.alter_legend_widget,
                       self.alter_legend_hint):
            widget.setVisible(show_alterations)
        show_mineralizations = bool(
            getattr(self.canvas, "_show_mineralizations", False) and has_mineral)
        for widget in (self.mineral_legend_title,
                       self.mineral_legend_widget):
            widget.setVisible(show_mineralizations)
        from .section_structure import update_legend_visibility
        show_structures = update_legend_visibility(self, has_structure)
        from .section_imagery import refresh_imagery_legend
        refresh_imagery_legend(self)
        from .section_geotech import refresh_all_geotech_legends
        refresh_all_geotech_legends(self)

        # v2.9.320 — légende litho = COUPE affichée (comme altérations/
        # minéralisations/structures depuis 303/313) : le projet entier
        # listait 10 codes pour une coupe à 3 (retour écran).
        from .section_holes import legend_source_holes
        codes = get_all_litho_codes(legend_source_holes(self))
        # v2.7.9.7 — les lithologies décochées quittent aussi la légende.
        codes = [
            code for code in codes
            if get_litho_style(code, self._litho_styles).get("visible",
                                                             True)]
        # v2.9.117 — pas de label « Aucune lithologie… » : bloc masqué
        # v2.7.6.1 — tri par libellé lisible (ordre « logique » demandé :
        # une légende se consulte alphabétiquement, pas en ordre
        # d'apparition dans le fichier).
        codes = sorted(
            codes,
            key=lambda code: (
                get_litho_style(code, self._litho_styles).get("label", code)
                or code).casefold())
        litho_sig = tuple(
            (c,
             get_litho_style(c, self._litho_styles).get("color"),
             get_litho_style(c, self._litho_styles).get("pattern"))
            for c in codes)
        rebuild_litho = litho_sig != getattr(self, "_legend_litho_sig", None)
        if rebuild_litho:
            self._legend_litho_sig = litho_sig
            self._clear_layout(self.litho_legend_layout)
        for index, code in enumerate(codes):
            if not rebuild_litho:
                break
            style = get_litho_style(code, self._litho_styles)
            entry = QWidget()
            row_layout = QHBoxLayout(entry)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            swatch = QLabel()
            swatch.setFixedSize(28, 16)
            swatch.setPixmap(self._lithology_symbol_pixmap(style))
            swatch.setToolTip(f"{code}" if not style.get("label")
                              or str(style.get("label")).casefold() == str(code).casefold()
                              else f"{code} · {style['label']}")
            # v2.9.22 — petites capitales (demande écran litho/légende)
            label = _legend_label(style.get("label") or code)
            label.setToolTip(str(code))
            row_layout.addWidget(swatch)
            row_layout.addWidget(label, 1)
            # v2.9.89 — clic → surbrillance coupe (pas d'édition symbole)
            self._wire_legend_highlight_entry(entry, "lithology", code)
            self.litho_legend_layout.addWidget(entry, index // 2, index % 2)

        # v2.7.3 — legends for the two coded tracks (never color alone).
        # v2.9.117 — empty_msg="" : pas de fantôme si domaine absent
        # (bloc déjà masqué via show_* && has_data ci-dessus).
        if show_alterations:
            self._fill_domain_legend(
                self.alter_legend_layout, "alteration", "alterations",
                "alteration", True, "")
        if show_mineralizations:
            # v2.7.11.8 — composants large (pas seulement attribut canonique)
            self._fill_domain_legend(
                self.mineral_legend_layout, "mineralization_style",
                "mineralizations", "mineralization_style", True,
                "",
                pattern_identity=True)
        if show_structures:
            self._fill_structure_legend(self.structure_legend_layout)

        # v2.9.1 — clé de lecture : la légende des symboles suit le
        # canvas (resynchronisée après chaque rendu, signal ``rendered``).
        self._fill_symbols_legend()
        # v2.9.89 — chrome sélection légende (après rebuild des rows)
        self._refresh_legend_highlight_chrome()

    def _fill_symbols_legend(self):
        """v2.9.1 — CLÉ DE LECTURE du dessin de la coupe.

        Chaque symbole graphique que le canvas DRESSE a son entrée,
        avec le style exact qui est dessiné (retour écran 23/08 : la
        ligne de sol en pointillé et les points collet étaient « non
        marqués dans la légende »).  La légende suit le canvas
        (signal ``rendered``) et non l'ordre des appels : l'entrée
        ligne de sol apparaît/disparaît avec sa source réellement
        dessinée, le trait forage suit sa piste « Trajectoire ».

        v2.9.90 — rows cliquables (surlignage coupe), même contrat que
        litho/altéro/miné.
        """
        grid = self.symbols_legend_layout
        self._clear_layout(grid)
        rows = []  # (widget, symbol_code|None)
        if getattr(self.canvas, "_show_trajectory", False):
            rows.append((self._symbol_line_row(
                self.tr("Forage (trajectoire)"),
                self.canvas._trajectory_color,
                max(1.2, float(self.canvas._trajectory_width)),
                Qt.SolidLine), "trajectory"))
        if self.canvas._result and self.canvas._result.holes:
            rows.append((self._symbol_collar_row(), "collar"))
        # v2.9.20 — clé de lecture litho composite (H)
        # v2.9.277 — retour écran : « même quand y a zéro donnée, ils sont là,
        # pourquoi ? ».  Les symboles « secondaire » / « veine » s'affichaient
        # dès que la piste litho était active, même sans AUCUNE barrette ou
        # veine dans les données.  On ne les montre que si le projet en
        # contient réellement.
        if getattr(self.canvas, "_show_litho", False):
            holes = (self.canvas._result.holes
                     if self.canvas._result else [])
            has_secondary = any(
                comp.role == "secondary"
                for h in holes for iv in h.litho for comp in iv.components)
            has_vein = any(
                comp.role in ("vein", "accessory")
                for h in holes for iv in h.litho for comp in iv.components)
            if has_secondary:
                rows.append((self._symbol_litho_secondary_row(),
                             "litho_secondary"))
            if has_vein:
                rows.append((self._symbol_litho_vein_row(), "litho_vein"))
        if (getattr(self.canvas, "_show_surface", False)
                and self.canvas._result
                and self.canvas._result.surface
                and self.canvas._surface_source):
            source = self.canvas._surface_source
            labels = {
                "dem": self.tr("Ligne de sol — MNT (mesurée)"),
                "csv": self.tr("Ligne de sol — points mesurés (CSV)"),
                "collars": self.tr("Ligne de sol — interpolée aux collets (pointillé)"),
            }
            rows.append((self._symbol_line_row(
                labels[source], self.canvas._surface_color, 1.4,
                Qt.DashLine if source == "collars" else Qt.SolidLine,
                tooltip=(self.tr("Pointillé · collets") if source == "collars"
                         else self.tr("Plein · mesuré (MNT/CSV)"))),
                "surface"))
        for index, (row, sym_code) in enumerate(rows):
            if sym_code:
                self._wire_legend_highlight_entry(row, "symbol", sym_code)
            grid.addWidget(row, index, 0, 1, 2)


    @staticmethod
    def _symbol_line_row(label, color, width, style, tooltip=""):
        """v2.9.1 — rangée de légende : trait 24×14 au style exact."""
        entry = QWidget()
        row_layout = QHBoxLayout(entry)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        swatch = QLabel()
        swatch.setFixedSize(24, 14)
        pixmap = QPixmap(24, 14)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(color), float(width), style))
        painter.drawLine(2, 7, 22, 7)
        painter.end()
        swatch.setPixmap(pixmap)
        text = _legend_label(label)
        if tooltip:
            swatch.setToolTip(tooltip)
            text.setToolTip(tooltip)
        row_layout.addWidget(swatch)
        row_layout.addWidget(text, 1)
        return entry

    @staticmethod
    def _symbol_collar_row():
        """v2.9.1 — pastille IDENTIQUE au marqueur du canvas (même
        rouge #C0392B, liseré noir 0,5 px, 6 px de diamètre)."""
        entry = QWidget()
        row_layout = QHBoxLayout(entry)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        swatch = QLabel()
        swatch.setFixedSize(24, 14)
        pixmap = QPixmap(24, 14)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#C0392B")))
        painter.setPen(QPen(QColor("#000000"), 0.5))
        painter.drawEllipse(QPointF(12, 7), 3.0, 3.0)
        painter.end()
        swatch.setPixmap(pixmap)
        text = _legend_label(QCoreApplication.translate(
            "SectionWidget", "Collet (point de forage)"))
        row_layout.addWidget(swatch)
        row_layout.addWidget(text, 1)
        return entry


    @staticmethod
    def _symbol_litho_secondary_row():
        """v2.9.20 — barrette secondaire INTERNE (D-01 sans %)."""
        entry = QWidget()
        row_layout = QHBoxLayout(entry)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        swatch = QLabel()
        swatch.setFixedSize(24, 14)
        pixmap = QPixmap(24, 14)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#566573"), 0.5))
        painter.setBrush(QBrush(QColor("#AED6F1")))
        painter.drawRect(2, 2, 20, 10)
        painter.setBrush(QBrush(QColor("#F5B041")))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRect(3, 3, 6, 8)
        painter.end()
        swatch.setPixmap(pixmap)
        text = _legend_label(QCoreApplication.translate(
            "SectionWidget", "Litho · secondaire (barrette)"))
        # v2.9.251 — FIX CRASH : @staticmethod → PAS de self.
        tip = QCoreApplication.translate("SectionWidget", "Secondaire sans % · fine bande dans l'hôte")
        swatch.setToolTip(tip)
        text.setToolTip(tip)
        row_layout.addWidget(swatch)
        row_layout.addWidget(text, 1)
        return entry

    @staticmethod
    def _symbol_litho_vein_row():
        """v2.9.20 — filet veine / accessoire diagonal."""
        entry = QWidget()
        row_layout = QHBoxLayout(entry)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        swatch = QLabel()
        swatch.setFixedSize(24, 14)
        pixmap = QPixmap(24, 14)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#566573"), 0.5))
        painter.setBrush(QBrush(QColor("#D5D8DC")))
        painter.drawRect(2, 2, 20, 10)
        painter.setPen(QPen(QColor("#5D6D7E"), 1.6))
        painter.drawLine(4, 3, 20, 11)
        painter.end()
        swatch.setPixmap(pixmap)
        text = _legend_label(QCoreApplication.translate(
            "SectionWidget", "Litho · veine / accessoire"))
        # v2.9.251 — FIX CRASH : @staticmethod → PAS de self.
        tip = QCoreApplication.translate("SectionWidget", "Filet diagonal sur l'hôte (veine / accessoire)")
        swatch.setToolTip(tip)
        text.setToolTip(tip)
        row_layout.addWidget(swatch)
        row_layout.addWidget(text, 1)
        return entry



    # ==================================================================
    # v2.9.89 — LÉGENDE → SURBRILLANCE (UI panneau, lot isolé)
    # ------------------------------------------------------------------
    # Branche les rows litho/altéro/miné.  Aucune édition de symbole.
    # ==================================================================

    def _wire_legend_highlight_entry(self, entry: QWidget, domain: str, code: str) -> None:
        """Rend une row de légende cliquable (surlignage coupe uniquement)."""
        entry.setCursor(Qt.PointingHandCursor)
        entry.setProperty("dm_legend_domain", str(domain or ""))
        entry.setProperty("dm_legend_code", str(code or ""))
        tip_extra = self.tr("Clic · surligne sur la coupe · re-clic efface")
        for child in entry.findChildren(QLabel):
            base = child.toolTip() or ""
            if tip_extra not in base:
                child.setToolTip((base + "\n" + tip_extra).strip())
        base_e = entry.toolTip() or ""
        if tip_extra not in base_e:
            entry.setToolTip((base_e + "\n" + tip_extra).strip() if base_e
                             else tip_extra)

        def _on_click(event, d=domain, c=code, w=entry):
            try:
                if event.button() == Qt.LeftButton:
                    self._on_legend_highlight_clicked(
                        d, c, bool(event.modifiers() & Qt.ControlModifier))
                    event.accept()
                    return
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : _on_click", _exc)
                # clic légende non bloquant
                pass
            QWidget.mousePressEvent(w, event)

        entry.mousePressEvent = _on_click  # type: ignore[method-assign]

    def _on_legend_highlight_clicked(self, domain: str, code: str,
                                     add: bool = False) -> None:
        """Clic = remplace ; Ctrl+clic (add) = ajoute/retire (348)."""
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        d = str(domain or "").strip()
        c = str(code or "").strip()
        if not d or not c:
            return
        norm = (d, SectionCanvas._legend_norm_code(c))
        active_code = None
        if add:
            canvas.toggle_legend_highlight(d, c)
            if norm in canvas.legend_highlight_keys():
                active_code = c
        elif canvas.legend_highlight_key() == norm and \
                len(canvas.legend_highlight_keys()) == 1:
            canvas.clear_legend_highlight()
        else:
            canvas.set_legend_highlight(d, c)
            active_code = c
        self._refresh_legend_highlight_chrome()
        if self.main_dock and getattr(self.main_dock, "workspace_state", None):
            self.main_dock.workspace_state.set("highlight_code", active_code)

    def _refresh_legend_highlight_chrome(self) -> None:
        """Marque visuellement la row sélectionnée dans le panneau."""
        canvas = getattr(self, "canvas", None)
        key = canvas.legend_highlight_key() if canvas else None
        sel_style = _selection_chrome_stylesheet()
        clear_style = ""
        for layout in (
                getattr(self, "litho_legend_layout", None),
                getattr(self, "alter_legend_layout", None),
                getattr(self, "mineral_legend_layout", None),
                getattr(self, "structure_legend_layout", None),
                getattr(self, "symbols_legend_layout", None)):
            if layout is None:
                continue
            for i in range(layout.count()):
                item = layout.itemAt(i)
                w = item.widget() if item else None
                if w is None:
                    continue
                dom = w.property("dm_legend_domain") or ""
                code = w.property("dm_legend_code") or ""
                if not dom:
                    continue
                keys = canvas.legend_highlight_keys() if canvas else set()
                match = (str(dom), SectionCanvas._legend_norm_code(
                    code)) in keys
                try:
                    w.setStyleSheet(sel_style if match else clear_style)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Légende : _refresh_legend_highlight_chrome", _exc)
                    # style optionnel
                    pass

    # ==================================================================
    # fin UI lot v2.9.89
    # ==================================================================

    def _fill_structure_legend(self, grid):
        """v2.9.260 (étape 2) — pastille de point + libellé par type."""
        from .section_structure import fill_structure_legend
        fill_structure_legend(self, grid)

    def _fill_domain_legend(self, grid, domain, hole_attribute, attribute,
                            use_components, empty_text,
                            pattern_identity=False):
        """One swatch + label per code, in project-data order.

        Reads the same drillholes as the lithology legend so the panel
        always decodes exactly what the canvas can draw."""
        self._clear_layout(grid)
        from .section_holes import legend_source_holes  # v2.9.303 légende = coupe affichée
        codes = {
            code for dh in legend_source_holes(self)
            for iv in getattr(dh, hole_attribute, [])
            for code in SectionCanvas._interval_codes(
                iv, attribute, use_components)
            # v2.7.9.7 — une entrée décochée n'apparaît plus en légende.
            if self.canvas._style_for(domain, code).get("visible", True)}
        # v2.7.6.1 — tri par libellé résolu (lisible), pas par code brut.
        codes = sorted(
            codes,
            key=lambda code: (
                (self.canvas._style_for(domain, code).get("label") or code)
                .casefold(),
                code.casefold()))
        if not codes:
            # v2.9.117 — empty_text="" → silence (bloc parent déjà masqué)
            if empty_text:
                empty = QLabel(empty_text)
                empty.setObjectName("label_hint")
                grid.addWidget(empty, 0, 0, 1, 2)
            return
        for index, code in enumerate(codes):
            style = self.canvas._style_for(domain, code)
            not_drawn = False
            style_key = ""
            if pattern_identity:
                # v2.7.10.4 — la pastille montre le CODE de style (texte),
                # exactement comme la coupe l'écrit dans la bande.
                from ..core.mineral_symbols import style_display_code
                style_key = style_display_code(
                    code, style.get("symbol_id"), style.get("pattern"))
                not_drawn = not style_key
            entry = QWidget()
            row_layout = QHBoxLayout(entry)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            swatch = QLabel()
            swatch.setFixedSize(24, 14)
            if pattern_identity:
                if not_drawn:
                    pixmap = QPixmap(24, 14)
                    pixmap.fill(Qt.transparent)
                    painter = QPainter(pixmap)
                    painter.setPen(QPen(
                        QColor(COLORS["text_light"]), 1, Qt.DashLine))
                    painter.drawRect(0, 0, 23, 13)
                    painter.end()
                    swatch.setPixmap(pixmap)
                    swatch.setToolTip(self.tr("{} · transparent").format(code))
                else:
                    swatch.setText(style_key)
                    swatch.setAlignment(Qt.AlignCenter)
                    # v2.7.13.1 — la pastille stylée en propre est son
                    # propre contexte d'infobulle : elle porte la règle.
                    swatch.setStyleSheet(
                        TOOLTIP_STYLE
                        + "QLabel { color: #5D6D7E; font-weight: bold; "
                        "font-size: 7pt; font-variant: small-caps; "
                        "background: transparent; "
                        "border: 1px solid #AAB7B8; }")
                    swatch.setToolTip(
                        code if not style.get("label")
                        or str(style.get("label")).casefold()
                        == str(code).casefold()
                        else f"{code} · {style['label']}")
            else:
                swatch.setPixmap(self._lithology_symbol_pixmap(style))
                swatch.setToolTip(
                    code if not style.get("label")
                    or str(style.get("label")).casefold()
                    == str(code).casefold()
                    else f"{code} · {style['label']}")
            # v2.7.10 — légendes NON cliquables (décision écran) :
            # lignes simples, la modification passe par le Référentiel.
            label = _legend_label(style.get("label") or code)
            if not_drawn:
                label.setStyleSheet(
                    TOOLTIP_STYLE
                    + "QLabel { font-variant: small-caps; "
                    f"color: {COLORS['text_light']}; }}")
            label.setToolTip(str(code))
            row_layout.addWidget(swatch)
            row_layout.addWidget(label, 1)
            # v2.9.89 — clic → surbrillance coupe (pas d'édition symbole)
            self._wire_legend_highlight_entry(entry, domain, code)
            grid.addWidget(entry, index // 2, index % 2)

    # ------------------------------------------------------------------
    # Section management
    # ------------------------------------------------------------------
    def _add_history_row(self, line, buffer_value, select=False):
        self._updating_history = True
        row = self.section_table.rowCount()
        self.section_table.insertRow(row)
        name_item = QTableWidgetItem(line.name or f"Section {line.section_id:03d}")
        name_item.setData(Qt.UserRole, line.section_id)
        direction_item = QTableWidgetItem(line.direction_label)
        length_item = QTableWidgetItem(f"{line.length:.0f} m")
        buffer_item = QTableWidgetItem(
            f"{buffer_value:.0f} {self._buffer_unit}")
        readonly = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        for item in (direction_item, length_item, buffer_item):
            item.setFlags(readonly)
        self.section_table.setItem(row, 0, name_item)
        self.section_table.setItem(row, 1, direction_item)
        self.section_table.setItem(row, 2, length_item)
        self.section_table.setItem(row, 3, buffer_item)
        self.section_combo.blockSignals(True)
        if self.section_combo.findData(line.section_id) < 0:
            self.section_combo.addItem(name_item.text(), line.section_id)
        if select:
            self.section_table.selectRow(row)
            self.section_combo.setCurrentIndex(
                self.section_combo.findData(line.section_id))
        self.section_combo.blockSignals(False)
        self._updating_history = False
        return row

    def _history_row_for_id(self, section_id):
        for row in range(self.section_table.rowCount()):
            item = self.section_table.item(row, 0)
            if item and item.data(Qt.UserRole) == section_id:
                return row
        return -1

    def add_section(self, dhs, line, section_id, section_name):
        line.name = section_name
        line.section_id = section_id
        line.buffer = self.buffer_spin.value()
        self._sections[section_id] = line
        self._drillholes = dhs
        self._line = line
        self._current_section_id = section_id
        if self._history_row_for_id(section_id) < 0:
            self._add_history_row(line, line.buffer, select=True)
        project = self._project()
        if project:
            project.set_current_section(section_id)
        self._generate_and_display()

    def restore_sections(self, records, dhs=None):
        """Restore section history, active section and canvas from config."""
        self._updating_history = True
        self.section_table.setRowCount(0)
        self.section_combo.blockSignals(True)
        self.section_combo.clear()
        self.section_combo.blockSignals(False)
        self._sections.clear()
        self._updating_history = False
        if dhs is not None:
            self._drillholes = dhs
        for record in records or []:
            try:
                line = SectionLine(
                    float(record["x1"]), float(record["y1"]),
                    float(record["x2"]), float(record["y2"]),
                    name=record.get("name", ""),
                    section_id=int(record.get("id", 0)),
                )
            except (KeyError, TypeError, ValueError):
                continue
            line.buffer = float(record.get("buffer", 50.0))
            self._sections[line.section_id] = line
            self._add_history_row(line, line.buffer)
            # v2.9.179 — exclusions de cette coupe (historique)
            from .section_holes import parse_record
            parse_record(self, record)

        project = self._project()
        current = project.get_current_section_id() if project else None
        if current not in self._sections and self._sections:
            current = sorted(self._sections)[-1]
        if current in self._sections:
            row = self._history_row_for_id(current)
            self._updating_history = True
            self.section_table.selectRow(row)
            self._updating_history = False
            self._activate_section(current)

    def _activate_section(self, section_id):
        if section_id not in self._sections:
            return
        self._current_section_id = section_id
        self._line = self._sections[section_id]
        if self.main_dock:
            self.main_dock.workspace_state.set(
                "current_section_id", section_id)
        combo_index = self.section_combo.findData(section_id)
        if combo_index >= 0 and combo_index != self.section_combo.currentIndex():
            self.section_combo.blockSignals(True)
            self.section_combo.setCurrentIndex(combo_index)
            self.section_combo.blockSignals(False)
        self._loading_settings = True
        self.buffer_spin.setValue(
            float(getattr(self._line, "buffer", self.buffer_spin.value())))
        self._loading_settings = False
        # v2.9.179 — exclusions PAR coupe : elles reviennent + le
        # groupe s'ouvre si besoin (v2.9.181)
        from .section_holes import restore_for_section
        restore_for_section(self, section_id)
        project = self._project()
        if project:
            project.set_current_section(section_id)
        if self._drillholes:
            self._generate_and_display()

    def _on_section_combo_changed(self, *_args):
        section_id = self.section_combo.currentData()
        if section_id in self._sections:
            row = self._history_row_for_id(section_id)
            if row >= 0:
                self._updating_history = True
                self.section_table.selectRow(row)
                self._updating_history = False
            self._activate_section(section_id)

    def _on_history_selection(self):
        if self._updating_history:
            return
        row = self.section_table.currentRow()
        item = self.section_table.item(row, 0) if row >= 0 else None
        if item:
            self._activate_section(item.data(Qt.UserRole))
            if self.main_dock:
                self.main_dock.show_section_tab()

    def _on_history_item_changed(self, item):
        if self._updating_history or item.column() != 0:
            return
        section_id = item.data(Qt.UserRole)
        line = self._sections.get(section_id)
        if not line:
            return
        new_name = item.text().strip()
        old_name = line.name
        duplicate = any(
            sid != section_id and other.name.casefold() == new_name.casefold()
            for sid, other in self._sections.items()) if new_name else False
        if not new_name or duplicate:
            self._updating_history = True
            item.setText(old_name)
            item.setToolTip(self.tr("Nom déjà utilisé") if duplicate
                            else self.tr("Nom requis"))
            self._updating_history = False
            return
        item.setToolTip(self.tr(""))
        line.name = new_name
        combo_index = self.section_combo.findData(section_id)
        if combo_index >= 0:
            self.section_combo.setItemText(combo_index, new_name)
        project = self._project()
        if project:
            project.rename_section(section_id, new_name)
        if self.main_dock:
            self.main_dock.rename_section_layer(old_name, new_name)
        if self._current_section_id == section_id:
            self._generate_and_display()

    def _on_legend_fade_change(self, *_a) -> None:
        """349 — case Estomper : état canvas + reapplique."""
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        try:
            canvas._legend_fade_enabled = bool(
                self.chk_legend_fade.isChecked())
            canvas._legend_fade_apply()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Panneau : estompage exergue", _exc)

    def _on_comfort_change(self, *_a) -> None:
        """355 — case confort : état canvas + re-rendu."""
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        try:
            canvas._comfort_mode = bool(self.chk_comfort.isChecked())
            if canvas._result:
                canvas._render()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Panneau : mode confort", _exc)

    def _on_legend_clear_clicked(self) -> None:
        """349 — bouton Effacer l'exergue (panneau propriétés)."""
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        try:
            canvas.clear_legend_highlight()
            self._refresh_legend_highlight_chrome()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Panneau : effacer exergue", _exc)

    def _show_history_menu(self, point):
        item = self.section_table.itemAt(point)
        if not item:
            return
        self.section_table.selectRow(item.row())
        menu = QMenu(self.section_table)
        open_action = menu.addAction(self.tr("Ouvrir la coupe"))
        rename_action = menu.addAction(self.tr("Renommer"))
        flip_action = menu.addAction(
            self.tr("Inverser P1/P2 (retourner la coupe)"))
        delete_action = menu.addAction(self.tr("Supprimer"))
        selected = menu.exec_(self.section_table.viewport().mapToGlobal(point))
        if selected == open_action:
            self._on_history_selection()
        elif selected == flip_action:
            self._flip_current_section()
        elif selected == rename_action:
            self.section_table.editItem(self.section_table.item(item.row(), 0))
        elif selected == delete_action:
            self._delete_current_section()

    def _flip_current_section(self):
        """338 — « P2 peut pas être à gauche ? » : OUI — retourne la
        coupe sans retracer : P1↔P2, azimut +180°, régénération,
        persistance, carte QGIS et mini-carte resynchronisées."""
        sid = self._current_section_id
        line = self._sections.get(sid) if sid is not None else None
        if line is None:
            return
        line.flip()
        name = line.name or f"Section {line.section_id:03d}"
        project = self._project()
        if project is not None and sid is not None:
            project.update_section(
                sid, x1=line.x1, y1=line.y1, x2=line.x2, y2=line.y2,
                azimuth=line.azimuth, direction=line.direction_label,
                length=line.length)
            # carte QGIS : couche ligne reconstruite (P1/P2 à jour)
            try:
                from qgis.core import QgsProject
                for _lid, lyr in list(
                        QgsProject.instance().mapLayers().items()):
                    if lyr.name() == name:
                        QgsProject.instance().removeMapLayer(lyr.id())
                        break
                if self.main_dock is not None:
                    self.main_dock.create_section_line_layer(
                        (line.x1, line.y1), (line.x2, line.y2), name=name)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : flip couche QGIS", _exc)
        row = self._history_row_for_id(sid)
        if row >= 0:
            self._updating_history = True
            self.section_table.item(row, 1).setText(line.direction_label)
            self._updating_history = False
        self._generate_and_display()
        from ..core.diagnostics import record_timing
        record_timing("section flip P1/P2", 0.0)

    def _delete_current_section(self):
        row = self.section_table.currentRow()
        item = self.section_table.item(row, 0) if row >= 0 else None
        if not item:
            return
        section_id = item.data(Qt.UserRole)
        section_name = item.text()
        self._updating_history = True
        self.section_table.removeRow(row)
        combo_index = self.section_combo.findData(section_id)
        if combo_index >= 0:
            self.section_combo.blockSignals(True)
            self.section_combo.removeItem(combo_index)
            self.section_combo.blockSignals(False)
        self._updating_history = False
        self._sections.pop(section_id, None)
        project = self._project()
        if project:
            project.delete_section(section_id)
        self.section_generated.emit(f"DELETE:{section_name}")
        if self._current_section_id == section_id:
            self._current_section_id = None
            if self.main_dock:
                self.main_dock.workspace_state.set("current_section_id", None)
            self._line = None
            self.canvas._result = None
            self.canvas.scene.clear()
            self.info_label.setText(self.tr("Aucune coupe sélectionnée."))
            if self.section_table.rowCount():
                next_row = min(row, self.section_table.rowCount() - 1)
                self._updating_history = True
                self.section_table.selectRow(next_row)
                self._updating_history = False
                next_item = self.section_table.item(next_row, 0)
                self._activate_section(next_item.data(Qt.UserRole))
            elif self.main_dock:
                self.main_dock.update_section_buffer_preview(None, 0, False)
                self.buffer_diagnostics.setText(self.tr("Aucune coupe active."))

    # ------------------------------------------------------------------
    # v2.9.0 — Topographie : ligne de sol (cascade MNT → CSV → collets)
    # ------------------------------------------------------------------
    def _surface_provider(self, *args, **kwargs):
        """Délégué à ui/section_surface (v2.9.150)."""
        from .section_surface import surface_provider
        return surface_provider(self, *args, **kwargs)
    @staticmethod
    def _qgis_raster_layers():
        """Rasters du projet QGIS — délégué (v2.9.149, ui/section_surface)."""
        from .section_surface import qgis_raster_layers
        return qgis_raster_layers()
    def _surface_raster_layer(self):
        """MNT à échantillonner selon le combo — délégué (v2.9.149)."""
        from .section_surface import surface_raster_layer
        return surface_raster_layer(self)
    @staticmethod
    def _extract_raster_sample(result, band=1):
        """Élévation d'un résultat identify — délégué (v2.9.149)."""
        from .section_surface import extract_raster_sample
        return extract_raster_sample(result, band=band)
    @staticmethod
    def _sample_raster_along_line(layer, line, a_min, a_max, n=256):
        """Échantillonnage du MNT le long de la coupe — délégué (v2.9.149)."""
        from .section_surface import sample_raster_along_line
        return sample_raster_along_line(layer, line, a_min, a_max, n=n)

    def _topography_csv_path(self):
        """CSV x;y;z du projet — délégué (v2.9.149)."""
        from .section_surface import topography_csv_path
        return topography_csv_path(self)
    def _topography_csv_points(self):
        """Points du CSV topographie — délégué (v2.9.149)."""
        from .section_surface import topography_csv_points
        return topography_csv_points(self)
    def _surface_tooltip_text(self, *args, **kwargs):
        """Délégué à ui/section_surface (v2.9.150)."""
        from .section_surface import surface_tooltip_text
        return surface_tooltip_text(self, *args, **kwargs)
    def _update_surface_status(self, *args, **kwargs):
        """Délégué à ui/section_surface (v2.9.150)."""
        from .section_surface import update_surface_status
        return update_surface_status(self, *args, **kwargs)
    def _update_surface_detection_status(self, *args, **kwargs):
        """Délégué à ui/section_surface (v2.9.150)."""
        from .section_surface import update_surface_detection_status
        return update_surface_detection_status(self, *args, **kwargs)
    def _on_surface_source_change(self, *args, **kwargs):
        """Délégué à ui/section_surface (v2.9.150)."""
        from .section_surface import on_surface_source_change
        return on_surface_source_change(self, *args, **kwargs)
    def _on_surface_qc_change(self, *args, **kwargs):
        """Délégué à ui/section_surface (v2.9.150)."""
        from .section_surface import on_surface_qc_change
        return on_surface_qc_change(self, *args, **kwargs)
    def _refresh_surface_combo(self, *args, **kwargs):
        """Délégué à ui/section_surface (v2.9.150)."""
        from .section_surface import refresh_surface_combo
        return refresh_surface_combo(self, *args, **kwargs)
    def _populate_surface_combo(self, *args, **kwargs):
        """Délégué à ui/section_surface (v2.9.150)."""
        from .section_surface import populate_surface_combo
        return populate_surface_combo(self, *args, **kwargs)
    def _generate_and_display(self):
        if not self._drillholes or not self._line:
            return
        self.canvas._litho_styles = self._litho_styles
        self.canvas._drillholes = self._drillholes
        self.canvas._line = self._line
        # v2.9.179 — exclusions de forages (le résultat les suit)
        self.canvas._excluded_hole_ids = set(self._excluded_holes)
        try:
            self.canvas._surface_choice = str(
                self.surface_combo.currentData() or "")
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _generate_and_display", _exc)
            # combo optionnel
            pass
        fp = (id(self._drillholes), len(self._drillholes or []))
        if fp != getattr(self, "_dhs_fp", None):
            self._dhs_fp = fp
            self._populate_elements()
            # légende : signal rendered (plus ici + timer 80 ms)

        assay = self._assay_style_values()
        self.canvas._classification = assay["method"]
        self.canvas._n_classes = assay["n_classes"]
        self.canvas._manual_breaks = assay["manual_breaks"]
        self.canvas._round_breaks = assay.get("round_breaks", True)
        self.canvas._scale_scope = assay["scale_scope"]
        self.canvas._assay_palette = assay["palette"]
        self.canvas._assay_opacity = assay["opacity"]
        # v2.9.92 — multi-teneurs avant set_data / scale
        self.canvas._assay_elements = list(assay.get("elements") or [])
        self.canvas._assay_element_palettes = dict(
            assay.get("element_palettes") or {})
        self.canvas.set_display_style(
            redraw=False, **self._section_style_values())
        try:
            self._sync_assay_element_units()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : _generate_and_display", _exc)
            # unités optionnelles — libellé = code seul
            pass
        buffer_mode = self.buffer_mode_combo.currentData() or "collar"
        self.canvas.set_data(
            self._drillholes, self._line,
            self.buffer_spin.value(), self.exag_slider.value() / 10.0,
            element=assay["element"] or None,
            buffer_mode=buffer_mode,
        )
        # v2.9.282 — retour écran : l'Auto forcé au chargement masquait les
        # teneurs et « faussait le réel ».  Par défaut = ÉCHELLE VRAIE (1x) ;
        # l'Auto reste un bouton MANUEL (plafonné 20x) déclenché par l'usage.
        statuses = self._update_buffer_diagnostics(
            self.buffer_spin.value(), buffer_mode)
        count = sum(status["included"] for status in statuses)
        # v2.9.179 — les exclusions comptent (statut cohérent)
        n_excl = len(set(self._excluded_holes or set())
                     & {s["hole_id"] for s in statuses if s["included"]})
        excl_txt = f" · {n_excl} exclu(s)" if n_excl else ""
        mode_text = (self.tr("collets") if buffer_mode == "collar"
                     else self.tr("trajectoires"))
        self.buffer_status.setText(self.tr(
            "Buffer appliqué : ±{} {} ({}) — {}/{} forage(s){}").format(
                f"{self.buffer_spin.value():g}", self._buffer_unit, mode_text,
                count - n_excl, count, excl_txt))
        self.buffer_status.setStyleSheet(
            f"color:{COLORS['success']}; font-size:8pt;")
        self._refresh_info_header(count - n_excl)
        from .section_holes import refresh_hole_filter_ui
        refresh_hole_filter_ui(self)

    def _element_display_label(self, element):
        project = self._project()
        if not project or not element:
            return element or self.tr("Élément")
        entry = project.get_reference_repository().get_entry(
            "assay_elements", element)
        if not entry:
            return element
        label = entry.label or element
        if entry.symbol and entry.symbol.casefold() not in label.casefold():
            label = f"{label} ({entry.symbol})"
        return f"{label} — {entry.source_unit}" if entry.source_unit else label

    def _populate_elements(self):
        self.canvas._drillholes = self._drillholes
        elements = self.canvas.get_available_elements()
        saved_style = {}
        project = self._project()
        if project:
            saved_style = multi_assay_mod.migrate_assay_style(
                project.get_assay_style())
        saved_elems = list(saved_style.get("elements") or [])
        saved = saved_style.get("element", "") or (
            saved_elems[0] if saved_elems else "")
        current = self.element_combo.currentData() or saved
        combos = [self.element_combo]
        if getattr(self, "element2_combo", None) is not None:
            combos.append(self.element2_combo)
        if getattr(self, "element3_combo", None) is not None:
            combos.append(self.element3_combo)
        for combo in combos:
            combo.blockSignals(True)
            combo.clear()
        if elements:
            for element in elements:
                lab = self._element_display_label(element)
                self.element_combo.addItem(lab, element)
            target = current if current in elements else elements[0]
            self._set_combo_data(self.element_combo, target)
            # extras : (aucun) + list without forcing duplicates
            for combo in combos[1:]:
                combo.addItem(self.tr("(aucun)"), None)
                for element in elements:
                    combo.addItem(
                        self._element_display_label(element), element)
            # restore saved multi
            if len(saved_elems) >= 2 and hasattr(self, "element2_combo"):
                e2 = saved_elems[1]
                if e2 in elements:
                    self._set_combo_data(self.element2_combo, e2)
            if len(saved_elems) >= 3 and hasattr(self, "element3_combo"):
                e3 = saved_elems[2]
                if e3 in elements:
                    self._set_combo_data(self.element3_combo, e3)
            # palettes
            pals = saved_style.get("element_palettes") or {}
            if saved_elems:
                self._set_combo_data(
                    self.ramp_combo,
                    pals.get(saved_elems[0], saved_style.get("palette", "grade")))
            if len(saved_elems) >= 2 and hasattr(self, "ramp2_combo"):
                self._set_combo_data(
                    self.ramp2_combo,
                    pals.get(saved_elems[1], "viridis"))
            if len(saved_elems) >= 3 and hasattr(self, "ramp3_combo"):
                self._set_combo_data(
                    self.ramp3_combo,
                    pals.get(saved_elems[2], "blue_red"))
        else:
            self.element_combo.addItem(self.tr("(aucun)"), None)
            for combo in combos[1:]:
                combo.addItem(self.tr("(aucun)"), None)
        for combo in combos:
            combo.blockSignals(False)
        if elements and project and saved not in elements:
            style = self._assay_style_values()
            project.save_assay_style(**style)
        try:
            self._populate_threshold_combos()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste teneurs : _populate_elements", _exc)
            # combos seuil absents
            pass
        try:
            self._sync_assay_element_units()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste teneurs : _populate_elements", _exc)
            # unités optionnelles — libellé = code seul
            pass

    def set_drillholes(self, dhs):
        """Make project styles/legends available before the first section.

        v2.9.117/120 — rafraîchit pistes (ON si fichier chargé).
        """
        self._drillholes = dhs or []
        if getattr(self, "canvas", None) is not None:
            try:
                self.canvas._drillholes = list(self._drillholes)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : set_drillholes", _exc)
                # canvas optionnel
                pass
        try:
            self._populate_elements()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : set_drillholes", _exc)
            # combos éléments optionnels au reset projet
            pass
        try:
            self._populate_litho_table()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : set_drillholes", _exc)
            # légendes optionnelles au boot / ouverture projet
            pass
        try:
            self._populate_threshold_combos()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : set_drillholes", _exc)
            # combos seuil absents
            pass
        try:
            self._refresh_track_availability(apply_defaults=True)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : set_drillholes", _exc)
            # liste pistes pas encore build
            pass
        try:
            self._sync_track_checks()
            if getattr(self, "canvas", None) is not None:
                style = self._section_style_values()
                self.canvas.set_display_style(**style)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : set_drillholes", _exc)
            # widgets / canvas pas prêts
            pass
        if getattr(self, "_line", None) is not None:
            try:
                self._update_legends()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : set_drillholes", _exc)
                # légendes optionnelles au boot
                pass

    def update_section(self, dhs, line):
        self._drillholes = dhs
        self._line = line
        # v2.9.179 — nouvelle coupe tracée : exclusions à zéro (elles
        # sont PAR coupe).
        if line is not None and line is not self._sections.get(
                getattr(self, "_current_section_id", None)):
            self._excluded_holes = set()
            self.canvas._excluded_hole_ids = set()
        self._generate_and_display()

    def apply_visibility(self, *_args):
        """Compatibility entry point used by the step-4 widget."""
        self._on_section_style_change()

    def highlight_hole(self, hid):
        self.canvas.highlight_hole(hid)
        self._refresh_info_header()

    def highlight_interval(self, hid, from_m, to_m, domain=None):
        if hasattr(self.canvas, "highlight_interval"):
            self.canvas.highlight_interval(hid, from_m, to_m,
                                           domain=domain)

    def on_workspace_interval(self, interval_data):
        if not interval_data:
            if hasattr(self.canvas, "clear_interval_highlight"):
                self.canvas.clear_interval_highlight()
            return
        hid = interval_data.get("hole_id")
        f_m = float(interval_data.get("from_m", interval_data.get("from", 0.0)))
        t_m = float(interval_data.get("to_m", interval_data.get("to", 0.0)))
        # v2.9.260 — propager le domaine : une sélection `structure` doit
        # dessiner le contour de sélection sur la MESURE ponctuelle, pas
        # sur la bande litho (vide pour from == to).
        domain = interval_data.get("domain")
        self.highlight_interval(hid, f_m, t_m, domain=domain)

    def on_workspace_highlight_code(self, code):
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        if not code:
            canvas.clear_legend_highlight()
            self._refresh_legend_highlight_chrome()
            return
        norm = SectionCanvas._legend_norm_code(code)
        # v2.9.260 — le canal `highlight_code` ne transporte pas le
        # domaine.  S'il ne correspond à aucune géométrie enregistrée
        # (piste Structures fermée au moment du clic, ou famille à code
        # composé), on NE retombe plus aveuglément sur `lithology` : on
        # cherche d'abord dans les mesures `structure` du résultat.
        found_domain = None
        for _e in getattr(canvas, "_legend_band_registry", []):
            d, c = _e[0], _e[1]
            if c == norm:
                found_domain = d
                break
        if found_domain is None:
            sr = getattr(canvas, "_result", None)
            for ph in (getattr(sr, "holes", None) or []):
                for rec in (getattr(ph, "structure", None) or []):
                    c = str(getattr(rec, "structure_type", "")
                            or getattr(rec, "type", "") or "").strip()
                    if canvas._legend_norm_code(c) == norm:
                        found_domain = "structure"
                        break
                if found_domain:
                    break
        if found_domain is None:
            found_domain = "lithology"
        canvas.set_legend_highlight(found_domain, code)
        self._refresh_legend_highlight_chrome()
