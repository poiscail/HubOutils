"""Test de la détection des outils : python test_hub.py"""
import os, tempfile
from hub import find_tools

with tempfile.TemporaryDirectory() as root:
    def make(*parts, text="x"):
        p = os.path.join(root, *parts)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(text)

    make("TriTelechargements", "TriTelechargements.exe")
    make("TriTelechargements", "README.md", text="# Tri\n\nRange le dossier Téléchargements.\n")
    make("Traducteur", "dist", "Traducteur.exe")
    make("Presse", "publish", "Presse.exe")
    make("SansExe", "app.py")
    make("HubOutils", "HubOutils.exe")
    make("Autre", "Pas-le-bon-nom.exe")

    tools = find_tools(root)
    names = [t["name"] for t in tools]
    assert names == ["Presse", "Traducteur", "Tri Telechargements"], names
    assert tools[2]["desc"] == "Range le dossier Téléchargements.", tools[2]["desc"]
    assert tools[1]["exe"].endswith(os.path.join("dist", "Traducteur.exe"))
print("OK")
