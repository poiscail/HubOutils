"""Hub : une seule fenêtre pour lancer tous les outils du dossier Outils."""
import os, re, sys, tkinter as tk

BG, CARD, HOVER, TEXT, MUTED, ACCENT = "#0f1115", "#181b22", "#232836", "#e8eaf0", "#8a93a6", "#4c8dff"
SUBDIRS = ("", "dist", "publish")  # où chercher <Outil>.exe dans le dossier de l'outil
COLS = 3


def here():
    return os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))


def describe(folder):
    """Première phrase du README, après le titre."""
    try:
        lines = open(os.path.join(folder, "README.md"), encoding="utf-8").read().splitlines()
    except OSError:
        return ""
    for l in lines:
        l = l.strip()
        if l and not l.startswith(("#", "!", "[", "<", "`", "|")):
            l = re.sub(r"[*_`]", "", l).split(" : ", 1)[-1]
            l = l[:1].upper() + l[1:]
            return l if len(l) <= 110 else l[:107].rstrip() + "…"
    return ""


def find_tools(root):
    """Chaque sous-dossier qui contient <NomDuDossier>.exe devient un outil."""
    tools = []
    for name in sorted(os.listdir(root), key=str.lower):
        folder = os.path.join(root, name)
        if name == "HubOutils" or not os.path.isdir(folder):
            continue
        for sub in SUBDIRS:
            exe = os.path.join(folder, sub, name + ".exe")
            if os.path.isfile(exe):
                tools.append({"name": re.sub(r"(?<=[a-zé])(?=[A-Z])", " ", name), "exe": exe,
                              "desc": describe(folder)})
                break
    return tools


def launch(tool, status):
    try:
        # startfile passe par le shell : gère les outils qui demandent les droits admin
        os.startfile(tool["exe"], cwd=os.path.dirname(tool["exe"]))
        status.config(text="Lancé : " + tool["name"], fg=MUTED)
    except OSError as e:
        status.config(text="Impossible de lancer %s : %s" % (tool["name"], e.strerror or e), fg="#ff6b6b")


def main():
    root_dir = os.path.dirname(here())  # le hub vit dans Outils\HubOutils
    win = tk.Tk()
    win.title("Hub Outils")
    win.configure(bg=BG)
    try:
        win.iconbitmap(os.path.join(here(), "icone.ico"))
    except tk.TclError:
        pass
    tk.Label(win, text="Mes outils", bg=BG, fg=TEXT, font=("Segoe UI Semibold", 18)).pack(anchor="w", padx=20, pady=(16, 4))
    grid = tk.Frame(win, bg=BG)
    grid.pack(padx=14, pady=6)
    status = tk.Label(win, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))

    tools = find_tools(root_dir)
    if not tools:
        tk.Label(grid, text="Aucun outil trouvé dans\n" + root_dir, bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(pady=30)
    for i, t in enumerate(tools):
        card = tk.Frame(grid, bg=CARD, width=250, height=110, cursor="hand2")
        card.grid(row=i // COLS, column=i % COLS, padx=6, pady=6)
        card.pack_propagate(False)
        badge = tk.Label(card, text=t["name"][0], bg=ACCENT, fg="white", font=("Segoe UI Semibold", 14), width=2)
        badge.pack(side="left", anchor="n", padx=(12, 8), pady=12)
        body = tk.Frame(card, bg=CARD)
        body.pack(side="left", fill="both", expand=True, pady=10, padx=(0, 10))
        title = tk.Label(body, text=t["name"], bg=CARD, fg=TEXT, font=("Segoe UI Semibold", 11), anchor="w")
        title.pack(fill="x")
        desc = tk.Label(body, text=t["desc"], bg=CARD, fg=MUTED, font=("Segoe UI", 8), anchor="nw",
                        justify="left", wraplength=170)
        desc.pack(fill="both", expand=True)
        parts = (card, body, title, desc)
        for w in parts + (badge,):
            w.bind("<Button-1>", lambda e, t=t: launch(t, status))
            w.bind("<Enter>", lambda e, p=parts: [x.config(bg=HOVER) for x in p])
            w.bind("<Leave>", lambda e, p=parts: [x.config(bg=CARD) for x in p])
    status.pack(anchor="w", padx=20, pady=(0, 12))
    win.resizable(False, False)
    win.mainloop()


if __name__ == "__main__":
    main()
