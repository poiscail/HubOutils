# HubOutils

Tous mes outils Windows dans une seule fenêtre : un onglet par outil. Le hub lance l'outil et accroche sa fenêtre dans l'onglet (SetParent de Windows), donc ça marche quel que soit le langage (Python, C#, PowerShell…).

## Utilisation

Double-cliquer sur `HubOutils.exe` (ou `Lancer.bat` depuis le code). Le hub doit rester dans `Outils\HubOutils` : il cherche les outils dans les dossiers voisins.

- Le hub demande les droits administrateur : sans eux, Windows interdit d'intégrer les outils qui tournent en admin (Optimiseur, Moniteur). Conséquence : glisser-déposer un fichier depuis l'Explorateur dans un outil intégré ne marche pas.
- Les outils déjà lancés (démarrage de Windows, zone de notification) sont retrouvés et intégrés.
- Fermer le hub ne ferme pas les outils : leurs fenêtres redeviennent normales (le serveur Minecraft continue de tourner).

Un dossier devient un outil s'il contient `<NomDuDossier>.exe`, à la racine, dans `dist\` ou dans `publish\`. La description vient de la première phrase du `README.md` de l'outil. Un nouvel outil apparaît donc tout seul.

## Créer l'exe

```
python -m PyInstaller --onefile --noconsole --uac-admin --name HubOutils hub.py
```

Puis copier `dist\HubOutils.exe` à la racine du dossier.

## Test

```
python test_hub.py
```
