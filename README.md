# HT Dark

*[English version](README.en.md)*

Thème sombre pour [Hattrick](https://www.hattrick.org), qui **conserve la couleur de chaque équipe
comme accent** au lieu de l'aplatir. CSS uniquement — pas une ligne de JavaScript.

## Ce qui le distingue

**Aucun JavaScript.** L'extension ne contient qu'un tableau de fichiers CSS dans son manifeste.
Sans code exécutable, elle n'a techniquement aucun moyen de lire quoi que ce soit sur les pages ni
d'envoyer quoi que ce soit. Aucune permission n'est demandée, aucune requête réseau n'est émise,
aucune donnée n'est stockée.

**La couleur de votre équipe est préservée.** Hattrick injecte lui-même, page par page, un bloc
`<style>` qui pose les couleurs du club affiché sur `#menu`, `.boxHead` et `.header-icon`. Le thème
laisse délibérément ces sélecteurs intacts : l'accent d'équipe continue de fonctionner tel quel,
pour la vôtre comme pour celle d'un adversaire, et il survit à un changement de thème dans les
réglages du jeu.

**Contrastes mesurés, pas estimés.** Chaque règle a été écrite après un relevé du rapport de
contraste WCAG dans la page. Le seuil visé est 4.5:1 sur le texte de corps. Les rares écarts
assumés sont documentés en commentaire, avec leur valeur.

### Sur l'avertissement de permission

Le navigateur affichera « Lire et modifier vos données sur hattrick.org ». C'est inévitable et ce
n'est pas une erreur : tout script de contenu, même purement CSS, déclenche cet avertissement,
parce que le manifeste ne distingue pas ce qui lit de ce qui décore. Le `manifest.json` ne contient
qu'un tableau `css` — c'est vérifiable en trois secondes.

## Installation

### Firefox

Installer depuis [addons.mozilla.org](https://addons.mozilla.org) *(fiche à venir)*.

Pour charger une version de développement : `about:debugging` → **Ce Firefox** → « Charger un
module complémentaire temporaire » → sélectionner `manifest.firefox.json`.

### Chrome

1. `chrome://extensions`
2. Activer le **mode développeur**
3. **Charger l'extension non empaquetée** → sélectionner ce dossier

Après une mise à jour des fichiers, cliquer l'icône de rechargement sur la carte de l'extension,
puis `Ctrl+F5` sur la page — le navigateur met les ressources d'extension en cache.

## Architecture

| Fichier | Rôle |
|---|---|
| `css/01-palette.css` | Les variables CSS — seule source de vérité des couleurs |
| `css/02-base.css` | Fond global, texte, liens, contrôles natifs |
| `css/03-components.css` | Composants présents sur l'ensemble du site |
| `css/04-pages.css` | Correctifs propres à une page |
| `css/05-foxtrick.css` | Règles ciblant l'extension FoxTrick |
| `css/06-dhth.css` | Règles ciblant l'extension dhth |
| `css/07-skillvalue.css` | Règles ciblant les modules CHPP SkillValue |

Les trois derniers fichiers sont **inertes** si l'extension correspondante n'est pas installée :
leurs sélecteurs ne correspondent alors à aucun élément de la page.

Les fichiers sont injectés dans l'ordre du manifeste, avant le rendu : pas de flash blanc au
chargement.

Le `matches` en `https://*.hattrick.org/*` couvre `www.hattrick.org` comme les serveurs numérotés.

### La ligne qui fait le plus de travail

```css
:root { color-scheme: dark; }
```

Elle bascule d'un coup les contrôles natifs, les barres de défilement et le fond par défaut. Elle
ne pilote que les contrôles **natifs** — un `select` remplacé par une extension y échappe.

## Principes

**`!important` uniquement sur la couleur.** Les feuilles de Hattrick sont chargées *après* le CSS
du script de contenu ; à spécificité égale, elles gagnent. `!important` est donc nécessaire sur les
propriétés de fond et de couleur — mais jamais sur la mise en page, et chaque usage porte un
commentaire indiquant quelle règle du site il neutralise.

**Pas de mise en page.** Le thème corrige des couleurs. Les bordures passent par `box-shadow: inset`
plutôt que `border` : sur un site aussi dense, un pixel de bordure décale toute la page.

**Les couleurs sémantiques sont préservées.** Le jaune d'un fil suivi, le rose d'un message
supprimé, le bleu domicile / extérieur sont des *informations*, pas de la décoration. Elles sont
assombries, jamais aplaties.

**Pas de filtre global sur les images.** Inverser toutes les images est ce qui rend la plupart des
thèmes sombres laids. Seuls les jeux d'icônes identifiés comme illisibles reçoivent un filtre
ciblé, au cas par cas.

## Vérification

- **Pas de flash blanc** : recharger avec `Ctrl+F5`, le fond doit être sombre dès la première image.
- **Contraste** ≥ 4.5:1 sur le texte de corps, mesuré et non estimé.
- **Le test qui décide de tout** : passer d'une équipe à une autre. Le fond doit rester identique,
  l'accent changer — assez pour savoir où on est sans lire le nom de l'équipe.
- **Non-régression** : désactiver l'extension, Hattrick doit revenir exactement à son apparence
  d'origine. Aucun résidu possible — ni stockage, ni script.

## Légitimité

Hattrick publie lui-même un tutoriel expliquant comment restyler le site : « Dark theme for
Hattrick website » (Hattrick Press, `ArticleID=22846`, par vlar3, 13/01/2023). Un restyling est
purement local, n'émet aucune requête et n'automatise rien.

Ce thème ne redistribue aucune image ni élément de charte graphique de Hattrick — il ne contient
que des règles CSS et ses propres icônes.

## Licence

[MPL-2.0](LICENSE).

---

*Hattrick est une marque d'Extra Living AB. Ce projet n'est ni affilié à Hattrick, ni approuvé par
Hattrick. FoxTrick et dhth sont des projets tiers indépendants.*
