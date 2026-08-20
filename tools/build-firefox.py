#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construit le paquet Firefox de HT Dark.

Usage :
    python tools/build-firefox.py

Produit dist/ht-dark-<version>.zip, pret a televerser sur addons.mozilla.org.

Le script ne MODIFIE aucun fichier source. Il refuse de produire le zip si un
controle echoue : mieux vaut pas de paquet qu'un mauvais paquet.

Deux garde-fous :
  - la liste des fichiers empaquetes est DERIVEE DU MANIFESTE, jamais d'un
    parcours de repertoire. Un fichier nouveau pose a la racine ne peut donc pas
    fuiter dans le paquet, meme si personne ne met une liste d'exclusion a jour ;
  - un balayage refuse toute donnee personnelle residuelle dans le CSS livre.

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
DIST = RACINE / "dist"

# Horodatage fixe : deux builds du meme source donnent le meme zip, octet pour octet.
HORODATAGE = (2001, 1, 1, 0, 0, 0)

# Motifs qui ne doivent jamais partir dans un paquet public.
# Ajouter ici tout nouvel identifiant personnel.
INTERDITS = [
    (r"\bPauls?\b", "le prenom de l'auteur"),
    (r"\b963655\b", "un identifiant d'equipe"),
    (r"TeamID\s*=", "un identifiant d'equipe dans une URL"),
    (r"stage\.hattrick", "le serveur de test prive"),
    (r"Pas de Transfert", "un nom d'equipe reel"),
    (r"Ch[aâ]teau\s+Charlotte", "un nom d'equipe reel"),
    (r"Keep[- ]?Alive", "un renvoi au projet voisin"),
    (r"[\w.+-]+@[\w-]+\.[a-z]{2,}", "une adresse e-mail"),
]

problemes = []


def verifier(condition, message):
    if not condition:
        problemes.append(message)


def rapporter():
    print("ECHEC — aucun paquet produit.")
    for p in problemes:
        print("  - " + p)
    return 1


def scanner(chemin):
    """Cherche les motifs interdits dans un fichier texte."""
    for numero, ligne in enumerate(
        chemin.read_text(encoding="utf-8").splitlines(), start=1
    ):
        for motif, libelle in INTERDITS:
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

    # --- 2. Coherence entre les deux manifestes --------------------------
    verifier(ff.get("manifest_version") == 2, "manifest.firefox.json doit etre en MV2")
    verifier(ch.get("manifest_version") == 3, "manifest.json doit etre en MV3")
    for cle in ("name", "version", "description", "icons", "content_scripts"):
        verifier(cle in ff, "manifest.firefox.json : cle « {} » manquante".format(cle))
        verifier(cle in ch, "manifest.json : cle « {} » manquante".format(cle))
        if cle in ff and cle in ch and ff[cle] != ch[cle]:
            problemes.append("les deux manifestes divergent sur « {} »".format(cle))
    verifier(
        len(ff.get("description", "")) <= 132,
        "la description depasse 132 caracteres (limite Chrome)",
    )
    verifier(
        ff.get("browser_specific_settings", {}).get("gecko", {}).get("id"),
        "browser_specific_settings.gecko.id est obligatoire pour AMO",
    )
    if problemes:
        return rapporter()

    # --- 3. Liste blanche EXACTE de ce qui entre dans le zip -------------
    a_empaqueter = []
    for bloc in ff["content_scripts"]:
        verifier(not bloc.get("js"), "un content_script declare du JavaScript")
        for rel in bloc.get("css", []):
            a_empaqueter.append((RACINE / rel, rel))
    for rel in ff["icons"].values():
        a_empaqueter.append((RACINE / rel, rel))
    a_empaqueter.append((RACINE / "LICENSE", "LICENSE"))

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

    # --- 4. Aucune donnee personnelle dans le CSS livre -----------------
    for source, arcname in a_empaqueter:
        if source.suffix == ".css":
            scanner(source)
    for motif, libelle in INTERDITS:
        if re.search(motif, ff["description"], re.IGNORECASE):
            problemes.append("la description du manifeste contient " + libelle)
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
    print()
    print("Verification independante avant televersement :")
    print("    npx addons-linter {}".format(cible.relative_to(RACINE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
