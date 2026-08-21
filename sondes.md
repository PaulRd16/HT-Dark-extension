# Sondes d'inspection

Scripts à coller **dans la console DevTools (F12 → onglet Console)** sur une page Hattrick.
Tous en lecture seule : ils ne modifient rien, ils mesurent.

Ce sont les outils qui ont construit le thème. Les réutiliser sur une nouvelle page avant
d'écrire la moindre règle — cf. la règle 1 du `CLAUDE.md` : mesurer, jamais corriger à l'œil.

---

## 1. Bilan d'une page — contrastes et surfaces claires

La sonde principale. Donne les textes sous le seuil AA (4.5:1) et les fonds restés clairs,
triés par gravité et par volume.

```js
(() => {
  const parse = (c) => { const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/.exec(c); return m ? { r: +m[1], g: +m[2], b: +m[3], a: m[4] === undefined ? 1 : +m[4] } : null; };
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const L = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const ratio = (a, b) => { const l1 = L(a), l2 = L(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
  const effBg = (el) => { let n = el; while (n) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > 0.5) return c; n = n.parentElement; } return { r: 20, g: 24, b: 28, a: 1 }; };
  const path = (el) => { const p = []; let n = el; for (let i = 0; i < 3 && n && n.tagName; i++) { p.unshift(n.tagName.toLowerCase() + [...n.classList].slice(0, 4).map(c => '.' + c).join('')); n = n.parentElement; } return p.join(' > '); };
  const skip = (e) => e.closest('[class*="cky"], #claude-agent-glow-border-inner');
  const hasText = (e) => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);

  const light = new Map(), low = new Map();
  for (const el of document.querySelectorAll('*')) {
    if (skip(el)) continue;
    const cs = getComputedStyle(el);
    const bg = parse(cs.backgroundColor);
    if (bg && bg.a > 0.5 && L(bg) > 0.3) {
      const k = path(el);
      if (!light.has(k)) light.set(k, { bg: cs.backgroundColor, n: 0 });
      light.get(k).n++;
    }
    if (!hasText(el) || cs.visibility === 'hidden') continue;
    const fg = parse(cs.color); if (!fg) continue;
    const r = ratio(fg, effBg(el));
    if (r >= 4.5) continue;
    const k = path(el) + '|' + cs.color;
    if (!low.has(k)) low.set(k, { p: path(el), fg: cs.color, ratio: +r.toFixed(2), n: 0 });
    low.get(k).n++;
  }
  return {
    surfacesClaires: [...light].sort((a, b) => b[1].n - a[1].n).slice(0, 20).map(([k, v]) => `${v.n}x ${k} -> ${v.bg}`),
    contrastesFaibles: [...low.values()].sort((a, b) => a.ratio - b.ratio).slice(0, 25)
  };
})()
```

**Lecture.** Un rapport sous 1.5 signifie « invisible », pas « peu lisible ». Le nombre
d'occurrences indique où est le volume : 140 barres à 1.11 pèsent plus qu'un titre isolé à 3.9.

**Limite connue : `effBg` remonte les ANCÊTRES.** Quand un aplat est peint par un élément
*frère* posé en `position: absolute` sous le texte, la sonde ne le voit pas et mesure le fond
d'un ancêtre. Vu sur l'analyse d'équipe : les valeurs de secteur étaient annoncées à 3.72 alors
qu'elles reposaient en réalité sur le voile turquoise `rgb(148,207,185)`, soit environ 1.5. La
sonde **sous-estimait** le défaut.

Le signe qui doit alerter : un ratio médiocre mais pas catastrophique sur un élément dont tous
les ancêtres sont transparents. Comparer alors les rectangles des deux couches — si l'un est
contenu dans l'autre, c'est lui le vrai fond.

**Deuxième limite, la plus coûteuse : la sonde ne regarde QUE les fonds et les textes.**
Une **bordure** claire ne l'est jamais. Le réseau de recrutement portait trois séparateurs
blancs de 4 px — une croix blanche en travers d'un panneau sombre de 626×461 — qui ont traversé
toutes les passes de vérification sans jamais apparaître dans un relevé. Le module est bâti en
`div`, donc la règle globale `table, th, td { border-color }` ne le rattrapait pas non plus.

Sur un composant qui n'est pas un `<table>`, ajouter ce balayage :

```js
[...document.querySelectorAll('LE_CONTENEUR *')].flatMap(e => {
  const cs = getComputedStyle(e);
  return ['Top', 'Right', 'Bottom', 'Left']
    .filter(s => parseFloat(cs['border' + s + 'Width']) >= 1)
    .map(s => `${e.className} border-${s.toLowerCase()} ${cs['border' + s + 'Width']} ${cs['border' + s + 'Color']}`);
}).filter(l => /rgb\((2[0-4]\d|25[0-5]), /.test(l))
```

Corriger ensuite en `border-color` **seul** — jamais le raccourci `border`, qui repose aussi la
largeur et décale la page (point 8 du `CLAUDE.md`).

**Troisième limite : la sonde ne teste pas la visibilité.** Un élément en `visibility: hidden` a
bien une taille et une couleur de fond, donc il apparaît dans les surfaces claires alors qu'il
n'est jamais peint. Vu sur `a.close-overlay` (le voile des fenêtres superposées), signalé comme
508 000 px² de blanc alors qu'il est masqué au repos. Ajouter `getComputedStyle(e).visibility` au
filtre, ou vérifier l'élément avant de conclure.

---

## 2. Quelle règle gagne sur cet élément ?

À lancer **avant** d'ajouter un `!important` qui ne servira à rien. Énumère les règles qui
s'appliquent réellement et leur priorité.

```js
((selecteur, propriete) => {
  const el = document.querySelector(selecteur);
  if (!el) return 'introuvable';
  const res = [];
  [...document.styleSheets].forEach((sh, i) => {
    let rules; try { rules = sh.cssRules; } catch { return; }
    for (const r of rules) {
      if (!r.selectorText) continue;
      let ok = false; try { ok = el.matches(r.selectorText); } catch { continue; }
      if (!ok) continue;
      const v = r.style.getPropertyValue(propriete);
      if (v) res.push(`[${i}] ${(sh.href || 'INLINE').split('/').pop().slice(0, 25)} | ${r.selectorText.slice(0, 60)} | ${v} ${r.style.getPropertyPriority(propriete)}`);
    }
  });
  return { calcule: getComputedStyle(el)[propriete], regles: res };
})('th.ft-dummy', 'background-color')
```

Changer les deux arguments de la dernière ligne.

**Piège classique.** Une liste vide alors que la propriété a bien une valeur calculée signifie
que l'élément **hérite** : la règle est sur un ancêtre. C'est le cas de `.financeDetailsBox`,
dont 91 cellules héritaient sans en avoir aucune. Utiliser alors la sonde 3.

---

## 3. Remonter la chaîne d'héritage

```js
((selecteur, propriete) => {
  let n = document.querySelector(selecteur);
  const chaine = [];
  for (let i = 0; i < 7 && n && n.tagName; i++) {
    const regles = [];
    [...document.styleSheets].forEach((sh, idx) => {
      let rules; try { rules = sh.cssRules; } catch { return; }
      for (const r of rules) {
        if (!r.selectorText) continue;
        let ok = false; try { ok = n.matches(r.selectorText); } catch { continue; }
        if (ok && r.style.getPropertyValue(propriete)) regles.push(`[${idx}] ${r.selectorText.slice(0, 50)} => ${r.style.getPropertyValue(propriete)} ${r.style.getPropertyPriority(propriete)}`);
      }
    });
    chaine.push({ el: n.tagName.toLowerCase() + (n.id ? '#' + n.id.slice(0, 20) : '') + [...n.classList].slice(0, 4).map(c => '.' + c).join(''), valeur: getComputedStyle(n)[propriete], regles: regles.slice(0, 3) });
    n = n.parentElement;
  }
  return chaine;
})('td.formatted-num', 'color')
```

Le premier ancêtre dont `regles` n'est pas vide est la cause racine. C'est **lui** qu'il faut
corriger, pas les descendants — règle 2 du `CLAUDE.md`.

---

## 4. Traquer les images de fond

Pour les fonds clairs qui résistent à `background-color` (règle 3 du `CLAUDE.md`). Deux cas
rencontrés : `#header` et `.pageOverlayHeader`, tous deux avec un dégradé servi depuis
`App_Themes/Standard/page/`.

```js
(() => {
  const path = (el) => { const p = []; let n = el; for (let i = 0; i < 4 && n && n.tagName; i++) { p.unshift(n.tagName.toLowerCase() + (n.id ? '#' + n.id.slice(0, 20) : '') + [...n.classList].slice(0, 4).map(c => '.' + c).join('')); n = n.parentElement; } return p.join(' > '); };
  const res = [];
  for (const el of document.querySelectorAll('*')) {
    if (el.closest('[class*="cky"]')) continue;
    const cs = getComputedStyle(el);
    if (cs.backgroundImage === 'none') continue;
    if (/chrome-extension|ClubTheme|Avatar|res\.hattrick|kits\//.test(cs.backgroundImage)) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 60 || r.height < 15) continue;
    res.push({ aire: Math.round(r.width * r.height), p: path(el), pos: `${Math.round(r.width)}x${Math.round(r.height)}`, img: cs.backgroundImage.slice(0, 75), bg: cs.backgroundColor });
  }
  return res.sort((a, b) => b.aire - a.aire).slice(0, 15);
})()
```

Le filtre écarte les images légitimes — avatars, maillots, thèmes de club, ressources
d'extensions. Ce qui reste est suspect.

---

## 5. Structure d'un composant

Quand il faut comprendre un bloc avant de le styler (message de forum, dossier, bulle de
match). Ne sort que balises, classes et styles calculés : **aucun texte de la page**, donc
rien de personnel.

```js
((selecteurRacine) => {
  const out = [];
  const walk = (el, d) => {
    if (d > 4 || !el) return;
    for (const c of el.children) {
      const cs = getComputedStyle(c), r = c.getBoundingClientRect();
      out.push(`${'| '.repeat(d)}${c.tagName.toLowerCase()}${[...c.classList].slice(0, 4).map(x => '.' + x).join('')} [${Math.round(r.width)}x${Math.round(r.height)}] bg:${cs.backgroundColor} col:${cs.color} padL:${cs.paddingLeft}`);
      walk(c, d + 1);
    }
  };
  const root = document.querySelector(selecteurRacine);
  if (root) walk(root, 0);
  return out.slice(0, 40);
})('.cfWrapper')
```

C'est cette sonde qui a montré que `div.folderHeader` et `tr.threadItem.even` avaient
exactement le même fond — d'où les trois bandes grises d'affilée dans la liste des forums.

---

## Note sur les identifiants ASP.NET

Hattrick génère des `id` du type `ctl00_ctl00_CPContent_…`. Ils sont longs, instables d'une
version à l'autre, et certains outils les tronquent ou les masquent. **Ne jamais s'en servir
comme sélecteur** : préférer les classes, qui sont stables depuis des années.
