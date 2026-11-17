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

# Intégration d'une fenêtre d'un autre programme
import subprocess, sys, time, tkinter as tk
import hub

p = subprocess.Popen([sys.executable, "-c", "import tkinter as t; r=t.Tk(); r.title('cible-test'); r.mainloop()"])
try:
    root = tk.Tk()
    box = tk.Frame(root, width=300, height=200)
    box.pack()
    root.update()
    target = None
    for _ in range(50):
        target = next((h for h, pid in hub.top_windows() if pid == p.pid and hub.u32.IsWindowVisible(h)
                       and hub.style(h, hub.GWL_STYLE) & hub.WS_CAPTION == hub.WS_CAPTION), None)
        if target:
            break
        time.sleep(0.1)
    assert target, "fenêtre de test introuvable"
    styles = hub.embed(target, box.winfo_id())
    assert styles and hub.u32.GetParent(target) == box.winfo_id()
    hub.release(target, styles, show=True)
    assert not hub.u32.GetParent(target)
    root.destroy()
finally:
    p.kill()
print("OK")
