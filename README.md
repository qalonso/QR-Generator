# QR Generator

Petite application de bureau (Tkinter) pour générer des QR Codes à partir d'une **URL** ou d'un **réseau Wi-Fi**.

## Fonctionnalités

- **Mode URL** : transforme n'importe quelle adresse en QR Code (le `https://` est ajouté automatiquement si besoin).
- **Mode Wi-Fi** : génère un QR Code qui connecte directement les appareils au réseau une fois scanné.
  - Nom du réseau (SSID)
  - Mot de passe (avec option pour l'afficher)
  - Type de sécurité : WPA/WPA2/WPA3, WEP ou aucune
  - Réseau masqué (optionnel)
- Aperçu instantané dans la fenêtre.
- **Affichage paysage ou portrait** : le bouton `⇄ PORTRAIT` / `⇄ PAYSAGE` en haut à droite permet de basculer entre les deux dispositions (saisie à gauche et QR Code à droite, ou l'un au-dessus de l'autre).
- **Adaptation à l'écran** : la taille de la fenêtre, des polices et des marges s'ajuste automatiquement à la résolution de l'écran. La fenêtre est redimensionnable et l'aperçu du QR Code suit sa taille.
- Sauvegarde automatique dans le dossier `medias/`, plus un bouton pour enregistrer ailleurs.

## Installation

Prérequis : Python 3.8 ou plus récent, avec Tkinter (inclus par défaut sur Windows et macOS ; sous Linux : `sudo apt install python3-tk`).

```bash
pip install -r requirements.txt
```

Contenu de `requirements.txt` :

```
qrcode[pil]
Pillow
```

## Utilisation

```bash
python qr_generator.py
```

1. Choisissez l'onglet **URL** ou **WI-FI**.
2. Remplissez les champs.
3. Cliquez sur **GÉNÉRER** (ou appuyez sur Entrée).
4. Le QR Code s'affiche et est enregistré dans `medias/`. Utilisez **SAUVEGARDER** pour le copier à un autre endroit.

Les fichiers sont nommés ainsi :

| Mode  | Nom du fichier               |
|-------|------------------------------|
| URL   | `qrcode_<url>.png`           |
| Wi-Fi | `qrcode_wifi_<ssid>.png`     |

## Compiler en .exe (Windows)

Avec [PyInstaller](https://pyinstaller.org), vous pouvez créer un exécutable autonome qui fonctionne sans Python installé.

1. Installez PyInstaller :

   ```bash
   pip install pyinstaller
   ```

2. Lancez la compilation depuis le dossier du projet :

   ```bash
   pyinstaller --onefile --windowed --name QRGenerator qr_generator.py
   ```

   - `--onefile` : produit un seul fichier `.exe`.
   - `--windowed` : n'ouvre pas de console noire derrière la fenêtre.
   - `--name QRGenerator` : nom de l'exécutable.

3. Récupérez l'exécutable dans `dist/QRGenerator.exe`. Vous pouvez ensuite supprimer les dossiers `build/` et `dist/` ainsi que le fichier `QRGenerator.spec` si vous n'en avez plus besoin.

Optionnel : ajoutez `--icon icone.ico` pour donner une icône personnalisée à l'application.

### Bon à savoir

- **Compilez sur le système cible** : PyInstaller ne fait pas de compilation croisée. Pour un `.exe`, il faut compiler sous Windows (sous macOS ou Linux, la même commande produit un exécutable pour ce système).
- **Dossier `medias/`** : il est créé à côté de l'endroit d'où l'exécutable est lancé (le dossier courant). Si vous lancez l'app depuis un raccourci, vérifiez le dossier de travail du raccourci pour savoir où iront les images.
- **Premier lancement lent** : avec `--onefile`, l'exécutable se décompresse à chaque démarrage, ce qui prend quelques secondes. Utilisez `--onedir` à la place pour un démarrage plus rapide (vous obtiendrez alors un dossier à distribuer).
- **Antivirus** : Windows Defender ou d'autres antivirus signalent parfois à tort les exécutables créés avec PyInstaller. Si c'est le cas, essayez `--onedir` ou ajoutez une exception pour le fichier.

## Format Wi-Fi

Le QR Code Wi-Fi suit le format standard reconnu par les appareils photo d'iOS et d'Android :

```
WIFI:T:WPA;S:MonReseau;P:MonMotDePasse;;
```

Les caractères spéciaux (`\ ; , : "`) sont échappés automatiquement.

## Sécurité

Le mot de passe Wi-Fi est encodé **en clair** dans le QR Code et dans l'image PNG enregistrée. Gardez ces fichiers privés et supprimez-les du dossier `medias/` quand vous n'en avez plus besoin.

## Structure du projet

```
.
├── qr_generator.py
├── requirements.txt
├── README.md
├── medias/          # créé automatiquement
├── build/           # créé par PyInstaller (supprimable)
└── dist/            # contient QRGenerator.exe après compilation
```