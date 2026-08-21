# HT Dark — thème sombre pour Hattrick

Extension Chrome **CSS uniquement, sans une ligne de JavaScript**. Elle conserve la couleur de
chaque équipe comme accent au lieu de l'aplatir.

**Ne jamais ajouter de JavaScript ici.** L'absence de code exécutable est ce qui rend cette
extension techniquement incapable de lire ou d'envoyer quoi que ce soit, et c'est un argument
de confiance qu'on ne rend pas.

---

## Méthode — les règles qui comptent

Elles viennent toutes d'erreurs réellement commises sur ce projet. Les ignorer coûte des
allers-retours.

### 1. Mesurer avant de corriger, jamais à l'œil

Calculer les rapports de contraste WCAG dans la page (voir `sondes.md`). Sans ça on corrige le
mauvais élément : les liens verts du forum semblaient illisibles à 1.46 — le vert était parfait,
c'est le fond des conteneurs qui était resté clair. Les assombrir aurait aggravé la situation.

Corollaire : beaucoup de défauts sont **invisibles à l'écran** — onglets repliés, texte noir sur
fond noir, panneaux fermés. La mesure les trouve, pas la capture d'écran.

Corollaire inverse, appris trois fois : **si l'élément à mesurer n'est pas affiché, demander
qu'on l'ouvre plutôt que déduire.** Supposer un conteneur a produit deux régressions — dont un
rectangle noir derrière chaque joueur du terrain, parce que `ht-flip-front` désigne les jetons
et non la fiche. Et penser au filtre de taille : un panneau replié mesure 0×0 et échappe aux
relevés.

### 2. Remonter à la cause racine, pas au symptôme

Toujours chercher **la règle du site** qui produit le défaut, et la traiter à sa source.

Exemple vécu : l'olive `rgb(102,136,51)` a été rattrapé trois fois de suite — `.mainBox > h2`
sur la page club, `td > h2` sur les fans, `.boxBody > div > h2` sur les finances — avant qu'on
découvre `h2 { color: rgb(102,136,51) }`, un sélecteur de balise nu qui colore **tous** les h2
du site. Une règle a remplacé les trois et couvert toutes les pages non encore visitées.

Même chose pour les finances : 91 cellules sans règle propre, héritant toutes de
`.financeDetailsBox`. Une déclaration au lieu de quatre.

**Signal d'alerte : si on écrit une règle par page pour le même défaut visuel, on est au
mauvais niveau.**

### 3. Un fond clair qui résiste à `background-color` est une image

Vérifié deux fois : `#header` et `.pageOverlayHeader` avaient déjà la bonne couleur de fond, et
une `background-image` se peignait par-dessus. Relever systématiquement `backgroundImage` en
même temps que `backgroundColor`.

### 4. Vérifier la spécificité avant d'ajouter `!important`

Les feuilles de Hattrick sont chargées **après** le CSS du content script. À spécificité égale
et `!important` des deux côtés, **c'est Hattrick qui gagne**. Un `!important` de plus ne sert à
rien ; il faut monter en spécificité.

Ne pas deviner : énumérer les règles qui s'appliquent réellement via `el.matches(r.selectorText)`
(sonde n°2 de `sondes.md`). Échecs évitables sur ce projet : `.folderHeaderHighlight` (0,1,0
contre 0,1,0), `table.htMlTable th` (0,1,2 contre notre 0,1,1), `.cfDeleted`, `.htbox-light`.

**Toujours relever la priorité, pas seulement le sélecteur.** Le cas `.cfDeleted` a été raté
parce qu'une sonde improvisée n'affichait pas `getPropertyPriority()` : le `!important` de
Hattrick est passé inaperçu, seule la couleur de texte a pris, et le contraste a été *dégradé*
au lieu d'être amélioré. Utiliser les sondes du fichier, qui l'affichent, plutôt que d'en
réécrire une à la volée.

**Symptôme caractéristique** : sur un même élément, une propriété prend et l'autre non. C'est la
signature d'un conflit de spécificité, pas d'une erreur de sélecteur.

**Une règle qui échoue le fait silencieusement.** `.htbox-light` était perdante sans que rien ne
le signale — le fond restait clair, le texte noir du site restait lisible. Le bug n'est apparu
qu'en corrigeant autre chose par-dessus, ce qui a donné du clair sur clair. Vérifier la valeur
**calculée** après coup, pas seulement la règle adverse avant.

**Le cas miroir est plus dangereux : une règle à nous qui GAGNE trop.** Sur la liste des ordres
de match, Hattrick distingue quatre états sur la même ligne — non retenu, sur le banc, dans le
onze, sélectionné — tous portés par le fond, et **aucun avec `!important`**. Notre
`.cdk-drag-handle.beach-players { background-color: … !important }`, à spécificité égale, les
écrasait tous les quatre : quatre informations réduites à un aplat uniforme, sans le moindre
signe d'erreur. Rien ne clignote quand on efface une distinction ; la page reste jolie.

Le réflexe qui l'attrape : avant de poser un aplat sur une classe, **énumérer les règles du site
qui visent cette classe accompagnée d'une autre** (`.beach-players.beach-players-on-field`,
`.beach-players.highlighted-player`…). Si elles existent, la règle large doit les exclure par
`:not()` ou leur rendre un niveau — c'est le motif déjà employé pour
`.htbox-light:not(.htbox-highlight)`.

**Et vérifier ce que le signal doit dominer.** Une fois les quatre états rendus, la sélection
restait terne : les lignes *sans* information portaient un liseré `rgb(204,204,204)` à 9.8:1
quand le vert de sélection plafonnait à 2.47. Un signal ne ressort pas dans l'absolu, mais
**par rapport au bruit autour** — calmer le neutre valait mieux que crier plus fort.

**Comment gagner sans dépendre d'un hachage** :

- doubler une classe stable (`table.htMlTable.htMlTable th`) monte la spécificité sans dépendre
  du contexte ;
- un `id` stable du conteneur (`#ngChat`, `#ngHelp`, `#ft-monitor-div`) pèse plus que n'importe
  quel nombre de classes, et évite d'empiler des doublements jusqu'à (0,5,0) ;
- parfois le plus simple est de **peindre un autre élément** : l'onglet actif du tableau de bord
  est défendu en (0,4,1), mais le `<a>` qu'il contient occupe la même surface et personne ne
  dispute son fond.

**Deux cas où la sonde ne verra rien**, et où il faut monter en spécificité à l'aveugle :

- Les extensions qui injectent leur CSS **par leur manifeste** n'apparaissent pas dans
  `document.styleSheets`. Les boutons `svbf` des ordres de match étaient en blanc sur blanc
  (ratio 1.00) sans qu'aucune règle ne soit lisible ; le module `#skillCalcOverlay` a demandé un
  identifiant doublé, seul endroit du thème où l'on surenchérit sans avoir lu l'adversaire.
- Les composants **Angular** encapsulent leurs styles par des attributs générés du type
  `[_nghost-ng-c573703697]`. Ces hachages changent à chaque build de Hattrick : **ne jamais s'en
  servir comme sélecteur**. Ils comptent chacun pour une classe dans le calcul de spécificité,
  d'où des règles adverses en (0,3,0) ou (0,4,1) qu'il faut compter avant d'écrire.

### 4 bis. Shadow DOM : lire la feuille adoptée avant de conclure

`hattrick-playoff-tree` (tableau de coupe) est le seul composant du site à utiliser un vrai
Shadow DOM avec du contenu propre. Aucun sélecteur n'y entre, et `querySelectorAll` ne le
traverse pas — la sonde ne voit donc même pas le défaut, ce qui est le vrai piège.

Mais les **propriétés personnalisées traversent la frontière**. Avant de conclure qu'un
composant est inatteignable, lire sa feuille adoptée
(`el.shadowRoot.adoptedStyleSheets[0].cssRules`) et chercher une API de variables. Celui-ci en
expose une complète sur son `:host` — il suffit de poser les valeurs sur l'hôte, les règles du
document primant sur celles de `:host`. `hattrick-field`, lui, n'expose que `--size` : rien à
faire, et c'est le terrain de football, donc sans conséquence.

Les carrousels `swiper-container` ont aussi un Shadow DOM, mais leur contenu est *slotté* depuis
le DOM clair : le CSS l'atteint normalement.

### 5. Ne jamais toucher aux sélecteurs d'identité d'équipe

`#menu`, `.boxHead`, `.header-icon`, `.header-right a`, `.switchClubTheme`, `.switchClubTab`.

Hattrick injecte par page un bloc `<style>` qui y pose les couleurs de l'équipe affichée, en
`!important`. C'est ce qui permet de reconnaître l'équipe affichée au premier coup d'œil —
la fonctionnalité centrale du thème, obtenue sans une ligne de code.

Conséquence acceptée : le blanc sur le vert par défaut plafonne à 2.78:1. C'est le contraste
d'origine de Hattrick, identique en mode clair — ce n'est pas une régression du thème.

**Une exception à une règle large doit annuler, pas surenchérir.** Pour protéger les en-têtes de
la règle sur `h2`, `#ffffff` forcé avait été écrit : sur le bandeau d'une équipe au thème jaune
cela donnait 1.49 là où le gris choisi par le site donnait 3.58. La bonne écriture est
`color: inherit`, qui neutralise sans décider à la place du site. Elle couvre aussi les `a` et
les `span` posés dans un en-tête.

### 6. Une règle large exige ses exceptions, écrites dans la foulée

`h2 { color: … }` a nécessité `.boxHead h2` puis `h2.category` (bandeaux gris de la liste des
joueurs, tombés à 1.37). La seconde n'a été trouvée que parce qu'elle a été signalée à l'usage. Même
histoire pour `h1`, d'abord borné à `#mainBody` et `.boxBody`, ce qui laissait passer tous les
autres.

Quand on pose une règle sur un sélecteur nu, énumérer immédiatement où ce sélecteur vit ailleurs.

**Vérifier sur quel fond vit un texte avant de lui appliquer la couleur « secondaire ».** Deux
fois `--ht-fg-dim` a été posé sur un texte qui reposait en fait sur un aplat coloré, le faisant
tomber à 1.12 et 1.40.

### 7. Préserver les couleurs sémantiques, les assombrir sans les aplatir

Le jaune d'un fil suivi, le rose d'un dossier à lire ou d'un spoiler, le vert d'un forum public,
le bleu domicile / extérieur, l'orange de la loyauté : ce sont des **informations**, pas de la
décoration.

- Aplat de fond porteur d'information → garder la teinte, assombrir.
- Couleur de donnée (barres de possession, de compétence) → **ne pas y toucher**, corriger
  seulement le texte posé dessus, en `#10222b`.
- Bouton plein → le fond marque l'action et reste ; seul le texte passe en blanc. Le vert des
  liens posé sur le vert d'un bouton donne 2.66, et le cas revient souvent.
- Mise en exergue → préférer un filet vertical de 3 px en `box-shadow` à un aplat plein, qui
  devient vite bruyant quand il se répète des dizaines de fois.
- Deux signaux identiques méritent la même couleur : messages supprimés et spoilers partagent
  `#3d2528`.

**Distinguer surface et état dans une même famille.** `.htbox-light` est une surface : on
l'assombrit. `.htbox-ok`, `.htbox-warning`, `.htbox-danger` sont des états : leur couleur est
l'information, on ne touche qu'au texte. C'est le nom qui départage.

**Cas particulier : un texte qui chevauche deux fonds.** Aucune couleur plate n'est lisible des
deux côtés d'une frontière clair/sombre. La bonne réponse est de **supprimer la frontière**
(rapprocher les deux fonds en luminance), pas de chercher un compromis ni d'empiler un
`text-shadow`. C'est pourquoi la piste des barres est en ton moyen `#8d99a3` et non sombre —
**ne pas l'assombrir sans revoir la couleur du libellé en même temps**.

Les composants récents écrivent le libellé **deux fois**, une copie dans `.ht-bar-max` et une
dans `.ht-bar-level`, chacune tronquée par `overflow: hidden`. La portion visible au-delà de la
barre est celle de `.ht-bar-max` et porte sa propre couleur.

### 8. Ne pas toucher à la mise en page

Le thème corrige des couleurs. Utiliser `box-shadow: inset` plutôt que `border` : sur un site
aussi dense, une bordure de 1 px décale toute la page.

Quatre exceptions assumées, toutes sans `!important` : la marge entre messages du forum, le
retrait des fils sous leur dossier, le filet des citations, et l'encadré ambre de la mention
d'équipe nationale sur la fiche joueur.

**Une cinquième s'était glissée sans être déclarée**, et elle montre par où la fuite arrive :
`.cfHeader` et `.cfFooter` avaient reçu `border-bottom: 1px solid` — la forme **raccourcie**,
qui pose aussi la largeur. Vérification faite dans `Standard_main_11.css`, ces deux éléments
n'ont aucune bordure : la règle en créait une, et poussait chaque message de 2 px sur une page
qui en compte vingt. Corrigé en `box-shadow: inset`.

**Pour ne colorer qu'une bordure, écrire `border-color`, jamais `border`.** Le raccourci a
l'air inoffensif parce qu'on ne pense qu'à la couleur en l'écrivant.

### 9. Suivre le découpage du site, pas le sien

Le zébrage se pilote par les classes `.even` / `.odd` de Hattrick, qui **ne suivent pas la
parité du DOM**. Une règle en `tr:nth-child(even) > td` peignait des bandes en décalage avec les
leurs, d'où des blocs gris orphelins.

Même logique pour les boîtes : Hattrick les imbrique (`.box.mainBox` dans `.boxBody` dans
`.box.main`). Encadrer chaque niveau donnait 64 anneaux sur une page. D'où `.box:not(.box *)`.

Et pour les états : dans la liste des ordres de match, le signal est porté par la **bordure
gauche**, pas par le fond. Des fonds dérivés d'un autre découpage créaient deux signaux
concurrents, donc aucun lisible.

### 10. La palette est la source unique

Toutes les couleurs vivent dans `css/01-palette.css`.

**Le critère est la répétition.** Une teinte employée à **deux endroits ou plus** devient une
variable nommée — sinon les deux copies dérivent, et deux signaux identiques finissent avec
deux couleurs différentes. Une teinte qui ne sert qu'une fois reste écrite dans sa règle, avec
en commentaire la couleur du site qu'elle remplace.

Nommées à ce titre : `--ht-on-accent` (le texte sombre sur aplat saturé, onze emplois),
`--ht-removed-bg` / `--ht-removed-fg` (message supprimé et spoiler), `--ht-marked-bg` (fil
suivi et mention d'équipe nationale), `--ht-green-fill`, `--ht-green-soft`, `--ht-select`.

**Un `var()` non résolu échoue en silence, et de la pire façon.** Si la variable n'existe
pas, la déclaration est invalide *au calcul* : la propriété retombe sur la valeur **héritée**,
pas sur une valeur par défaut. Mesuré : une pastille censée passer à 4.61 est redescendue à
2.81 en héritant du texte clair — le thème avait l'air de fonctionner, il avait juste empiré
l'endroit qu'il prétendait corriger.

En pratique cela arrive quand la page tourne encore avec l'**ancienne feuille** : `01-palette.css`
est mis à jour mais l'extension n'a pas été rechargée. Avant de conclure sur une mesure, vérifier
que les variables employées sont bien définies :
`getComputedStyle(document.documentElement).getPropertyValue('--ht-on-accent')`.

### 11. Un garde-fou se juge sur ce qu'il refuse, pas sur ce qu'il vérifie

`tools/build-firefox.py` est le seul contrôle automatique du projet : c'est lui qui garantit
qu'aucun JavaScript, aucune permission et aucune donnée personnelle ne part dans le paquet.
L'audit du 21/08/2026 y a trouvé trois défauts, tous de la même famille.

**Vérifier des présences ne protège de rien.** Le script s'assurait que les clés attendues
*existent* et que les deux manifestes concordent. Rien n'interdisait à une clé **indésirable**
d'apparaître : un futur `permissions`, un `background`, un `web_accessible_resources` ou un
`matches` élargi aurait été empaqueté sans un mot. Pour une extension dont l'argument tient
entièrement à ce qu'elle **n'a pas**, ce sont les absences qu'il faut affirmer — c'est
l'assertion la moins chère à écrire, et la seule qui protège l'invariant contre soi-même dans
six mois.

**Une liste d'interdits qui cite ses valeurs les publie à son tour.** Le balayage
anti-données-personnelles nommait en clair l'identifiant d'équipe et deux noms d'équipe réels.
Il faisait parfaitement son travail sur le paquet — qui n'a jamais rien contenu — pendant que
sa propre définition, suivie par git, les exposait sur le dépôt public. Les motifs du fichier
suivi décrivent désormais la **forme** du défaut (`\b\d{6,}\b` : un nombre de six chiffres n'a
rien à faire dans une feuille de style) ; les valeurs exactes vivent dans
`tools/interdits.local.txt`, gitignoré. Corollaire : **corriger le fichier n'efface pas
l'historique**, où les valeurs restent lisibles.

**Et la portée du balayage est un piège en soi.** Il ne lisait que le CSS, alors que le paquet
embarque aussi `_locales/*/messages.json` — qui porte le nom et la description affichés sur la
fiche AMO, donc le texte le plus exposé à une touche personnelle. Un contrôle qui ne couvre
qu'une partie de ce qu'il livre donne la même assurance qu'un contrôle absent, en moins
visible.

**Un garde-fou qu'on n'a jamais vu échouer n'est pas un garde-fou.** Les seize défauts de
l'audit ont été injectés un par un, sources restaurées à chaque fois, pour vérifier que le
build refuse bien. Le détail qui compte : en ne mutant **qu'un** manifeste, c'est le contrôle
de divergence qui tirait le premier — le refus était obtenu, mais par le mauvais contrôle, et
le garde-fou visé restait non prouvé. Il faut muter les **deux** de façon cohérente, ce qui est
de toute façon l'erreur réaliste puisqu'on modifie les manifestes ensemble. **Un test qui passe
pour la mauvaise raison ne prouve rien** — et c'est indétectable sans lire le motif du refus.

---

## Repères

**Structure** : `01-palette.css` (variables) → `02-base.css` (fond, texte, liens,
`color-scheme: dark`) → `03-components.css` (site-wide) → `04-pages.css` (par page). Un défaut
vu sur deux pages appartient à `03`, pas à `04`.

**Hiérarchie des surfaces**, à respecter pour que les niveaux restent lisibles :

```
--ht-bg        #14181c   fond de page
--ht-surface   #1f252b   boîtes, lignes impaires
--ht-surface-2 #272f36   en-têtes de boîte, lignes paires
--ht-surface-3 #313b43   titres de dossier, survol, élément actif
```

Un titre de dossier avait d'abord été mis en `surface-2`, identique aux lignes paires : trois
bandes de la même valeur d'affilée. Les niveaux doivent rester distincts.

**`color-scheme: dark` sur `:root`** est la ligne la plus rentable du thème : contrôles natifs,
barres de défilement et fond par défaut basculent seuls. Elle ne pilote que les contrôles
**natifs** — un `select` remplacé par une extension (FoxTrick) y échappe.

**Le site empile plusieurs générations de composants.** Traiter l'un ne traite pas les autres :

| Fonction | Composants coexistants |
|---|---|
| Onglets | `ul.tabbedList`, `.nav-tab`, `.ht-tabs`, `.dashboard-navigation` |
| Barres de valeur | `.bar-max` / `.bar-level`, `.ht-bar-max` / `.ht-bar-level` |
| Familles de cartes | `htbox-*` (ordres de match), `casual-*` (Arena), `c-*` (calendrier) |

**Une même fonction se traite en un seul endroit, quelles que soient ses générations.** Les
quatre systèmes d'onglets vivaient dans trois sections de page différentes de `04`, avec les
mêmes valeurs recopiées ; ils sont désormais regroupés dans `03`, sous un seul couple de
déclarations. Même chose pour les boutons pleins, dont le défaut « vert sur vert » était
corrigé trois fois. Quand Hattrick livrera un cinquième système d'onglets, il y aura **une
ligne** à ajouter à une liste, pas un bloc à réécrire.

Attention en regroupant : le regroupement doit être **neutre en rendu**. Réunir des sélecteurs
qui n'avaient pas exactement les mêmes déclarations en ajoute silencieusement aux uns ou aux
autres — c'est pourquoi la bordure des onglets fait l'objet d'une règle séparée, limitée aux
deux familles qui en dessinent une.

**Images** : ne pas y toucher par défaut. Un SVG chargé en `<img>` est opaque au CSS — ni
`color` ni `fill` ne l'atteignent, seul un filtre agit, et il faut le cibler étroitement
(`.box-action img`) sous peine de détruire avatars, drapeaux et maillots. Les graphiques
`.RadChart` sont des PNG rendus par le serveur : `invert(0.92)` est calculé, pas choisi — il
fait tomber le blanc sur `rgb(20,…)`, soit exactement `--ht-bg`.

**Code tiers** (FoxTrick, dhth, modules CHPP comme `#skillCalcOverlay`) : isolé dans ses propres
sections. C'est la partie fragile — leur balisage peut changer à une mise à jour, contrairement
aux classes de Hattrick, stables depuis des années. Quand un nom de classe est générique
(`.label`, `.result`, `.ft-dummy`), le scoper par son conteneur.

## Vérification

**Celle qui prime sur toutes les autres** : passer d'une équipe à une autre. Le fond doit rester
identique, l'accent changer. Si les couleurs d'équipe disparaissent, une règle a débordé sur la
zone interdite du point 5 — c'est le seul défaut qui casse la raison d'être du thème.

- Pas de flash blanc au chargement (`Ctrl+F5`).
- Contraste ≥ 4.5 sur le texte de corps, mesuré et non estimé.
- Survol : le lien doit rester lisible. Hattrick pose `a:hover { color: rgb(141,141,28) }`, un
  olive prévu pour un fond clair qui tombe à 3.99 chez nous.
- Désactiver l'extension : Hattrick doit revenir exactement à son apparence d'origine. Aucun
  résidu possible, ni stockage ni script.
