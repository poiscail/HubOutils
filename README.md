# HubOutils

Une seule fenêtre pour lancer tous mes outils Windows : un clic sur une carte lance l'outil.

## Utilisation

Double-cliquer sur `HubOutils.exe` (ou `Lancer.bat` depuis le code). Le hub doit rester dans `Outils\HubOutils` : il cherche les outils dans les dossiers voisins.

Un dossier devient un outil s'il contient `<NomDuDossier>.exe`, à la racine, dans `dist\` ou dans `publish\`. La description vient de la première phrase du `README.md` de l'outil. Un nouvel outil apparaît donc tout seul.

## Créer l'exe

```
python -m PyInstaller --onefile --noconsole --name HubOutils hub.py
```

Puis copier `dist\HubOutils.exe` à la racine du dossier.

## Test

```
python test_hub.py
```
