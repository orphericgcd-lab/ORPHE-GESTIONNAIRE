# ORPHE - GEST

Gestionnaire de fichiers avec assistant IA intégré, pensé pour un usage hors ligne et inspiré d’une interface Windows 11.

## Télécharger l’application Windows

- [Télécharger et lancer ORPHE-GEST (.exe)](https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/latest/download/ORPHE-GEST.exe) — téléchargez le fichier puis double-cliquez dessus.
- [Télécharger ORPHE-GEST en ZIP portable](https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/latest/download/ORPHE-GEST.zip) — extrayez l’archive puis lancez `ORPHE-GEST.exe`.

Ces liens téléchargent l’application compilée. L’archive « Source code (zip) » de GitHub contient le code source et ne permet pas de lancer le gestionnaire.

## Prérequis

- Python 3.10+
- Windows 10/11 recommandé

## Installation

1. Ouvrir un terminal dans le dossier du projet.
2. Créer un environnement virtuel (recommandé) :

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Lancer le projet

Pour le démarrer sans terminal, double-cliquer sur **Lancer ORPHE-GEST.vbs** dans le dossier du projet. La fenêtre se ferme
normalement avec son bouton **X**. Le lanceur utilise l’environnement `.venv` ou `venv` du projet s’il existe, sinon Python
disponible dans `PATH`.

Pour le développement, il est aussi possible de le lancer depuis un terminal :

```bash
python fif.py
```

## Fonctionnement optionnel

### IA locale hors ligne

Installer Ollama puis télécharger un modèle local :

```powershell
ollama pull qwen2.5:3b
```

Ensuite, dans l’interface, choisir le modèle dans les réglages de l’IA. L’assistant comprend les demandes libres,
consulte le dossier et la sélection courants, puis utilise les fonctions du gestionnaire avec aperçu et confirmation
pour les opérations sensibles. Il peut ranger récursivement un dossier ou un lecteur par extension; pour un lecteur,
indique sa racine (par exemple `D:\\`). Les fichiers cachés et les chemins système protégés sont laissés en place et
signalés. Sans modèle local, l’analyseur intégré gère les commandes courantes.

### Voix hors ligne

Installer les dépendances vocales facultatives :

```bash
pip install sounddevice SpeechRecognition vosk
```

### IA en ligne

Le projet supporte aussi l’API Anthropic si une clé est fournie dans l’interface ou dans la variable d’environnement :

```powershell
$env:ANTHROPIC_API_KEY="votre_cle"
```

### Aperçu des fichiers

Le volet **Aperçu** est activé depuis la barre supérieure. Il présente les informations des fichiers, le texte des formats courants,
le texte des PDF et des documents DOCX/ODT/PPTX. Les conversations de l’assistant restent en mémoire pendant la session courante
et ne sont pas restaurées à la prochaine ouverture.

Les lecteurs amovibles apparaissent avec leur nom de volume lorsqu’il est disponible. Les transferts vers et depuis ces lecteurs
utilisent les opérations standard du système et demandent confirmation à l’assistant lorsqu’elles touchent des emplacements externes.
Un clic sur l’ampoule fait défiler les thèmes système, blanc, noir, bleu et beige. Dans l’aperçu vidéo, les flèches pour changer
de vidéo apparaissent au milieu des côtés de l’image, y compris pendant la lecture; les images sont également navigables. Les
flèches précédente/suivante ne s’affichent que lorsqu’un média correspondant existe dans cette direction. Le nom reste centré
sous la vidéo et le bouton plein écran contrasté se trouve en bas à droite. Le curseur de lecture permet de rejoindre un passage précis par clic ou
glissement. Les vidéos et fichiers audio s’ouvrent en lecture dans l’aperçu au double-clic. La lecture continue pendant la
navigation dans les dossiers du gestionnaire. L’assistant reçoit le contenu du dossier courant avec le type détecté et l’extension
de chaque élément. Le bouton à icône seule dans l’aperçu permet de lire les vidéos (ou les musiques) du dossier dans l’ordre,
de répéter le média en cours ou de lire les médias du même type de manière aléatoire. Les dossiers peuvent être épinglés dans
la barre latérale avec le menu contextuel et restent épinglés après le redémarrage.

Le menu contextuel des fichiers propose leurs propriétés (type, emplacement, tailles et dates). L’onglet Sécurité crée une
archive 7z protégée par mot de passe avec chiffrement du contenu et des noms; le fichier original reste inchangé. La compression
ZIP est intégrée; l’option RAR apparaît uniquement si WinRAR (`rar.exe`) est installé et détecté. Les archives ZIP, TAR, TAR.GZ,
TGZ et 7z peuvent être décompressées depuis le menu contextuel; l’extraction RAR nécessite un extracteur compatible installé.
Les chemins contenus dans une archive sont contrôlés avant extraction.

## Build exécutable

Le build crée l’application Windows autonome dans `dist\ORPHE-GEST.exe`, avec le logo intégré comme icône du fichier :

```bash
python -m PyInstaller --clean ORPHE-GEST.spec
```

Pour utiliser ORPHE-GEST depuis Windows, exécutez `Installer ORPHE-GEST.ps1` depuis le dossier du projet après le build.
Le programme est copié dans `%LOCALAPPDATA%\Programs\ORPHE-GEST`, puis les menus contextuels des dossiers, du fond d’un
dossier et des lecteurs proposent **Ouvrir dans ORPHE-GEST**. L’installation est limitée au compte Windows courant et ne
remplace pas l’Explorateur ni les applications par défaut. Exécutez `Désinstaller ORPHE-GEST.ps1` pour retirer l’intégration.

### Mises à jour

La version installée recherche les nouvelles versions publiques au démarrage; le bouton de rechargement de la barre d’outils
permet aussi de lancer la recherche manuellement. Une nouvelle version est téléchargée après confirmation et son empreinte
SHA-256 est vérifiée avant de remplacer l’exécutable. La mise à jour automatique fonctionne avec les releases publiques du
dépôt indiqué dans `orphe_gest\version.py`.

Le workflow `.github\workflows\release.yml` construit et publie l’exécutable ainsi que son empreinte lorsqu’une étiquette
Git `vX.Y.Z` est publiée. Avant de créer une release, incrémentez `APP_VERSION` dans `orphe_gest\version.py` et utilisez la
même version dans l’étiquette. Le dépôt GitHub public doit exister pour que les vérifications et téléchargements fonctionnent.

### Télécharger et lancer l’application

Dans la page [des dernières versions](https://github.com/orphericgcd-lab/ORPHE-GESTIONNAIRE/releases/latest), téléchargez
l’asset **ORPHE-GEST.zip** sous « Assets », puis extrayez-le. Le fichier `ORPHE-GEST.exe` se trouve à la racine du dossier
extrait; double-cliquez dessus pour lancer le gestionnaire. L’archive « Source code (zip) » proposée par GitHub contient le
code du projet, pas l’application compilée.

## Notes

- Le projet est principalement structuré autour de [fif.py](fif.py).
- L’interface principale est en PySide6.
- L’IA en ligne utilise l’API Anthropic; le mode local utilise Ollama sans envoyer le contexte des fichiers sur Internet.
