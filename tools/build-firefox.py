#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construit le paquet Firefox de HT Dark.

Usage :
    python tools/build-firefox.py

Produit dist/ht-dark-<version>.zip, pret a televerser sur addons.mozilla.org.

Le script ne MODIFIE aucun fichier source. Il refuse de produire le zip si un
controle echoue : mieux vaut pas de paquet qu'un mauvais paquet.

Quatre garde-fous :
  - la liste des fichiers empaquetes est DERIVEE DU MANIFESTE, jamais d'un
    parcours de repertoire. Un fichier nouveau pose a la racine ne peut donc pas
    fuiter dans le paquet, meme si personne ne met une liste d'exclusion a jour ;
  - un balayage refuse toute donnee personnelle residuelle dans TOUT fichier
    texte du paquet — pas seulement le CSS ;
  - un second balayage refuse tout vecteur de requete reseau dans le CSS
    (`url()`, `@import`, `@font-face`...). Sans canal reseau, un selecteur ne
    peut rien exfiltrer : c'est la forme forte de la promesse « aucune ressource
    externe » ;
  - les manifestes sont verifies par ce qu'ils N'ONT PAS. HT Dark ne demande
    aucune permission et ne vise que hattrick.org ; ces deux absences sont
    affirmees ici, pas seulement constatees a la relecture.

Bibliotheque standard uniquement — rien a installer.
"""

import json
import re
import sys
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
MANIFESTE_FIREFOX = RACINE / "manifest.firefox.json"
MANIFESTE_CHROME = RACINE / "manifest.json"
INTERDITS_LOCAUX = RACINE / "tools" / "interdits.local.txt"
DIST = RACINE / "dist"

# Horodatage fixe : deux builds du meme source donnent le meme zip, octet pour octet.
HORODATAGE = (2001, 1, 1, 0, 0, 0)

# La seule cible autorisee. Toute autre valeur elargit la portee de l'extension.
MATCHES_ATTENDUS = ["https://*.hattrick.org/*"]

# Limite de longueur de la description, sur AMO comme sur le Chrome Web Store.
DESCRIPTION_MAX = 132

# Cles qui ne doivent JAMAIS apparaitre dans un manifeste de HT Dark. L'extension
# est du CSS et rien d'autre : elle ne demande aucune permission, n'expose aucune
# ressource et n'execute aucun code. Ces absences sont son argument de confiance ;
# on les verifie, on ne les suppose pas.
CLES_INTERDITES = (
    "permissions",
    "optional_permissions",
    "host_permissions",
    "optional_host_permissions",
    "background",
    "web_accessible_resources",
    "externally_connectable",
    "content_security_policy",
    "declarative_net_request",
    "devtools_page",
    "options_page",
    "options_ui",
    "action",
    "browser_action",
    "page_action",
    "sidebar_action",
    "commands",
    "user_scripts",
    "chrome_url_overrides",
)

# Motifs qui ne doivent jamais partir dans un paquet public.
#
# Ils decrivent la FORME du defaut, jamais la valeur reelle : une liste qui cite
# les identifiants qu'elle protege les publie a son tour, et ce fichier est suivi
# par git. Les valeurs exactes vivent dans tools/interdits.local.txt, gitignore.
#
# `\bPauls?\b` ne matche volontairement pas « PaulRd16 » : il n'y a pas de limite
# de mot entre « Paul » et « Rd16 ». C'est voulu — ce pseudonyme est public et
# figure dans le manifeste. Ne pas « corriger » en `Paul\w*`.
INTERDITS = [
    (r"\bPauls?\b", "le prenom de l'auteur"),
    (r"\b\d{6,}\b", "un identifiant numerique (equipe, joueur, match)"),
    (r"(?:team|player|match|user|youth)id\s*=", "un identifiant dans une URL"),
    (r"stage\.hattrick", "le serveur de test prive"),
    (r"Keep[- ]?Alive", "un renvoi au projet voisin"),
    (r"[\w.+-]+@[\w-]+\.[a-z]{2,}", "une adresse e-mail"),
]

# Vecteurs de requete reseau ou d'execution. Aucun n'a sa place dans ce theme.
VECTEURS = [
    (r"url\s*\(", "un url() — ressource externe possible"),
    (r"@import", "un @import"),
    (r"@font-face", "une police embarquee"),
    (r"image-set\s*\(", "un image-set()"),
    (r"-moz-binding", "un binding XBL"),
    (r"expression\s*\(", "une expression() executable"),
    (r"javascript\s*:", "une URL javascript:"),
    (r"behavior\s*:", "une propriete behavior"),
]

problemes = []
avertissements = []


def verifier(condition, message):
    if not condition:
        problemes.append(message)


def rapporter():
    print("ECHEC — aucun paquet produit.")
    for p in problemes:
        print("  - " + p)
    return 1


def charger_interdits_locaux():
    """Ajoute les motifs a valeur reelle, gardes hors du depot.

    Une expression reguliere par ligne ; « # » commente, les lignes vides sont
    ignorees. Le fichier absent n'est PAS une erreur : les motifs structurels
    ci-dessus restent actifs, et quelqu'un qui clone le depot doit pouvoir
    construire.
    """
    if not INTERDITS_LOCAUX.is_file():
        avertissements.append(
            "{} est absent — seuls les motifs structurels sont actifs. "
            "Y placer les noms et identifiants reels a surveiller.".format(
                INTERDITS_LOCAUX.relative_to(RACINE)
            )
        )
        return
    ajoutes = 0
    for ligne in INTERDITS_LOCAUX.read_text(encoding="utf-8").splitlines():
        motif = ligne.strip()
        if not motif or motif.startswith("#"):
            continue
        try:
            re.compile(motif)
        except re.error as erreur:
            problemes.append(
                "{} : motif invalide en tant qu'expression reguliere ({})".format(
                    INTERDITS_LOCAUX.relative_to(RACINE), erreur
                )
            )
            continue
        # Le libelle ne cite pas le motif : les messages d'echec de ce script
        # finissent regulierement colles dans un rapport ou une issue.
        INTERDITS.append((motif, "une donnee personnelle (liste locale)"))
        ajoutes += 1
    verifier(
        ajoutes,
        "{} ne contient aucun motif".format(INTERDITS_LOCAUX.relative_to(RACINE)),
    )


def scanner(chemin, jeu):
    """Cherche un jeu de motifs dans un fichier texte."""
    try:
        contenu = chemin.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        problemes.append(
            "{} n'est pas de l'UTF-8 valide — non verifiable".format(
                chemin.relative_to(RACINE)
            )
        )
        return
    for numero, ligne in enumerate(contenu.splitlines(), start=1):
        for motif, libelle in jeu:
            if re.search(motif, ligne, re.IGNORECASE):
                problemes.append(
                    "{}:{} contient {} -> {}".format(
                        chemin.relative_to(RACINE), numero, libelle,
                        ligne.strip()[:90],
                    )
                )


def ecrire(zf, arcname, donnees):
    info = zipfile.ZipInfo(arcname, date_time=HORODATAGE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, donnees)


def main():
    # --- 1. Lire les deux manifestes -------------------------------------
    verifier(MANIFESTE_FIREFOX.is_file(), "manifest.firefox.json est introuvable")
    verifier(MANIFESTE_CHROME.is_file(), "manifest.json est introuvable")
    if problemes:
        return rapporter()

    ff = json.loads(MANIFESTE_FIREFOX.read_text(encoding="utf-8"))
    ch = json.loads(MANIFESTE_CHROME.read_text(encoding="utf-8"))
    manifestes = ((ff, "manifest.firefox.json"), (ch, "manifest.json"))

    charger_interdits_locaux()

    # --- 2. Coherence entre les deux manifestes --------------------------
    verifier(ff.get("manifest_version") == 2, "manifest.firefox.json doit etre en MV2")
    verifier(ch.get("manifest_version") == 3, "manifest.json doit etre en MV3")
    for cle in ("name", "version", "description", "icons", "content_scripts",
                "default_locale"):
        verifier(cle in ff, "manifest.firefox.json : cle « {} » manquante".format(cle))
        verifier(cle in ch, "manifest.json : cle « {} » manquante".format(cle))
        if cle in ff and cle in ch and ff[cle] != ch[cle]:
            problemes.append("les deux manifestes divergent sur « {} »".format(cle))
    verifier(
        ff.get("browser_specific_settings", {}).get("gecko", {}).get("id"),
        "browser_specific_settings.gecko.id est obligatoire pour AMO",
    )
    if problemes:
        return rapporter()

    # --- 2 bis. Ce que les manifestes ne doivent PAS contenir ------------
    # Verifier les presences ne protege de rien : c'est une cle en trop qui
    # trahirait la promesse, pas une cle manquante.
    for manifeste, nom in manifestes:
        for cle in CLES_INTERDITES:
            verifier(
                cle not in manifeste,
                "{} declare « {} » — HT Dark ne demande rien et n'execute rien".format(
                    nom, cle
                ),
            )
        for bloc in manifeste.get("content_scripts", []):
            verifier(
                not bloc.get("js"),
                "{} : un content_script declare du JavaScript".format(nom),
            )
            verifier(
                bloc.get("matches") == MATCHES_ATTENDUS,
                "{} : matches vaut {} au lieu de {}".format(
                    nom, bloc.get("matches"), MATCHES_ATTENDUS
                ),
            )
    if problemes:
        return rapporter()

    # --- 3. Liste blanche EXACTE de ce qui entre dans le zip -------------
    a_empaqueter = []
    for bloc in ff["content_scripts"]:
        for rel in bloc.get("css", []):
            a_empaqueter.append((RACINE / rel, rel))
    for rel in ff["icons"].values():
        a_empaqueter.append((RACINE / rel, rel))
    a_empaqueter.append((RACINE / "LICENSE", "LICENSE"))

    # Les traductions ne sont pas referencees par le manifeste : elles sont
    # retrouvees a partir de `default_locale`, donc ajoutees explicitement.
    if ff.get("default_locale"):
        locales = sorted((RACINE / "_locales").glob("*/messages.json"))
        verifier(locales, "default_locale est declare mais _locales/ est vide")
        verifier(
            any(p.parent.name == ff["default_locale"] for p in locales),
            "aucune traduction pour la langue par defaut « {} »".format(ff["default_locale"]),
        )
        for p in locales:
            a_empaqueter.append((p, "_locales/{}/messages.json".format(p.parent.name)))
            # La longueur se mesure sur le TEXTE REEL, pas sur le marqueur
            # `__MSG_extensionDescription__` du manifeste, qui fait 28 caracteres
            # et passerait n'importe quelle limite.
            try:
                messages = json.loads(p.read_text(encoding="utf-8"))
            except ValueError as erreur:
                problemes.append(
                    "{} : JSON invalide ({})".format(p.relative_to(RACINE), erreur)
                )
                continue
            for cle in ("extensionName", "extensionDescription"):
                verifier(
                    cle in messages,
                    "{} : « {} » manquant".format(p.relative_to(RACINE), cle),
                )
            texte = messages.get("extensionDescription", {}).get("message", "")
            verifier(
                len(texte) <= DESCRIPTION_MAX,
                "{} : la description fait {} caracteres (limite {})".format(
                    p.relative_to(RACINE), len(texte), DESCRIPTION_MAX
                ),
            )

    for source, arcname in a_empaqueter:
        verifier(
            source.is_file(),
            "fichier declare dans le manifeste mais absent : {}".format(arcname),
        )
        verifier(
            source.suffix != ".js",
            "fichier JavaScript dans le paquet : {}".format(arcname),
        )
    if problemes:
        return rapporter()

    # --- 4. Balayage du contenu livre ------------------------------------
    # Tout fichier TEXTE du paquet, manifeste compris. Les fichiers de langue
    # portent le nom et la description affiches sur la fiche AMO : c'est le
    # texte le plus expose a une touche personnelle, et il etait jusqu'ici le
    # seul a partir sans avoir ete lu.
    scanner(MANIFESTE_FIREFOX, INTERDITS)
    for source, arcname in a_empaqueter:
        if source.suffix in (".css", ".json", ""):
            scanner(source, INTERDITS)
        if source.suffix == ".css":
            scanner(source, VECTEURS)
    if problemes:
        return rapporter()

    # --- 5. Ecrire le zip ------------------------------------------------
    DIST.mkdir(exist_ok=True)
    cible = DIST / "ht-dark-{}.zip".format(ff["version"])
    if cible.exists():
        cible.unlink()

    with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as zf:
        ecrire(zf, "manifest.json", MANIFESTE_FIREFOX.read_bytes())
        for source, arcname in a_empaqueter:
            ecrire(zf, arcname, source.read_bytes())

    # --- 6. Rendre compte ------------------------------------------------
    print("OK  {}  ({} octets)".format(cible.relative_to(RACINE), cible.stat().st_size))
    print("Contenu du paquet :")
    with zipfile.ZipFile(cible) as zf:
        for info in zf.infolist():
            print("    {:<28} {:>7} octets".format(info.filename, info.file_size))
    for a in avertissements:
        print()
        print("AVERTISSEMENT : " + a)
    print()
    print("Verification independante avant televersement :")
    print("    npx addons-linter {}".format(cible.relative_to(RACINE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
