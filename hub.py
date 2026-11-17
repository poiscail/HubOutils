"""Hub : tous les outils du dossier Outils dans une seule fenêtre, un onglet par outil.

Chaque outil reste son propre programme (Python, C#, PowerShell…) : le hub le lance puis
accroche sa fenêtre dans l'onglet (SetParent de Windows), quel que soit son langage.
"""
import ctypes, os, re, subprocess, sys, time, tkinter as tk
from ctypes import wintypes as w

BG, SIDE, CARD, HOVER, TEXT, MUTED, ACCENT = "#0f1115", "#14171d", "#181b22", "#232836", "#e8eaf0", "#8a93a6", "#4c8dff"
SUBDIRS = ("", "dist", "publish")  # où chercher <Outil>.exe dans le dossier de l'outil
POLL = 300  # ms entre deux recherches de fenêtres
WAIT = 20  # s d'attente de la fenêtre d'un outil qu'on vient d'ouvrir

# --- Win32 -------------------------------------------------------------------------------------
u32 = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
ENUM = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
LONG_PTR = ctypes.c_ssize_t
for fn, res, args in (
        (u32.EnumWindows, w.BOOL, [ENUM, w.LPARAM]),
        (u32.GetWindowThreadProcessId, w.DWORD, [w.HWND, ctypes.POINTER(w.DWORD)]),
        (u32.GetWindowLongPtrW, LONG_PTR, [w.HWND, ctypes.c_int]),
        (u32.SetWindowLongPtrW, LONG_PTR, [w.HWND, ctypes.c_int, LONG_PTR]),
        (u32.SetParent, w.HWND, [w.HWND, w.HWND]),
        (u32.GetParent, w.HWND, [w.HWND]),
        (u32.GetWindow, w.HWND, [w.HWND, w.UINT]),
        (u32.IsWindow, w.BOOL, [w.HWND]),
        (u32.IsWindowVisible, w.BOOL, [w.HWND]),
        (u32.IsIconic, w.BOOL, [w.HWND]),
        (u32.ShowWindow, w.BOOL, [w.HWND, ctypes.c_int]),
        (u32.MoveWindow, w.BOOL, [w.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, w.BOOL]),
        (u32.SetWindowPos, w.BOOL, [w.HWND, w.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, w.UINT]),
        (u32.PostMessageW, w.BOOL, [w.HWND, w.UINT, w.WPARAM, w.LPARAM]),
        (u32.SetForegroundWindow, w.BOOL, [w.HWND]),
        (k32.OpenProcess, w.HANDLE, [w.DWORD, w.BOOL, w.DWORD]),
        (k32.QueryFullProcessImageNameW, w.BOOL, [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]),
        (k32.CloseHandle, w.BOOL, [w.HANDLE])):
    fn.restype, fn.argtypes = res, args

GWL_STYLE, GWL_EXSTYLE, GW_OWNER = -16, -20, 4
WS_CHILD, WS_POPUP, WS_CAPTION = 0x40000000, 0x80000000, 0x00C00000
FRAME = WS_POPUP | WS_CAPTION | 0x00040000 | 0x00080000 | 0x00020000 | 0x00010000  # + bord, menu, réduire, agrandir
WS_EX_TOOLWINDOW, WS_EX_TOPMOST, WS_EX_APPWINDOW = 0x80, 0x8, 0x40000
SW_HIDE, SW_SHOWNOACTIVATE, SW_SHOW, SW_RESTORE = 0, 4, 5, 9
SWP_REFRESH = 0x1 | 0x2 | 0x4 | 0x20  # NOSIZE | NOMOVE | NOZORDER | FRAMECHANGED
WM_TRAY = 0x800  # message de l'icône de notification des applis .NET (NotifyIcon)


def style(h, idx):
    return u32.GetWindowLongPtrW(h, idx) & 0xFFFFFFFF


def set_style(h, idx, v):
    u32.SetWindowLongPtrW(h, idx, v - (1 << 32) if v >= 1 << 31 else v)


def top_windows():
    """Toutes les fenêtres de premier niveau : [(hwnd, pid)]."""
    out = []

    def cb(h, _):
        pid = w.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        out.append((h, pid.value))
        return True
    u32.EnumWindows(ENUM(cb), 0)
    return out


_exe_cache = {}


def exe_of(pid):
    if pid not in _exe_cache:
        path = ""
        h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if h:
            buf, n = ctypes.create_unicode_buffer(1024), w.DWORD(1024)
            if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                path = os.path.normcase(buf.value)
            k32.CloseHandle(h)
        _exe_cache[pid] = path
    return _exe_cache[pid]


def embed(hwnd, parent):
    """Accroche une fenêtre d'un autre programme dans `parent`. Renvoie ses styles d'origine, ou None."""
    st, ex = style(hwnd, GWL_STYLE), style(hwnd, GWL_EXSTYLE)
    set_style(hwnd, GWL_STYLE, (st & ~FRAME) | WS_CHILD)
    set_style(hwnd, GWL_EXSTYLE, ex & ~(WS_EX_TOPMOST | WS_EX_APPWINDOW))
    if not u32.SetParent(hwnd, parent):
        set_style(hwnd, GWL_STYLE, st)
        set_style(hwnd, GWL_EXSTYLE, ex)
        return None
    u32.SetWindowPos(hwnd, None, 0, 0, 0, 0, SWP_REFRESH)
    return st, ex


def release(hwnd, styles, show):
    """Rend la fenêtre au bureau, telle qu'elle était."""
    if not u32.IsWindow(hwnd):
        return
    u32.SetParent(hwnd, None)
    set_style(hwnd, GWL_STYLE, styles[0])
    set_style(hwnd, GWL_EXSTYLE, styles[1])
    u32.SetWindowPos(hwnd, None, 0, 0, 0, 0, SWP_REFRESH)
    u32.ShowWindow(hwnd, SW_SHOW if show else SW_HIDE)


# --- Outils ------------------------------------------------------------------------------------
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
            return l[:1].upper() + l[1:]
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


# --- Fenêtre du hub ----------------------------------------------------------------------------
class Hub:
    def __init__(self, win, tools):
        self.win, self.tools, self.current, self.auto_min = win, tools, None, None
        self.by_exe = {os.path.normcase(t["exe"]): t for t in tools}
        win.title("Hub Outils")
        win.configure(bg=BG)
        win.geometry("1280x800")
        try:
            win.iconbitmap(os.path.join(here(), "icone.ico"))
        except tk.TclError:
            pass
        side = tk.Frame(win, bg=SIDE, width=260)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="Mes outils", bg=SIDE, fg=TEXT, font=("Segoe UI Semibold", 15)).pack(anchor="w", padx=16, pady=(16, 10))
        self.content = tk.Frame(win, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        if not tools:
            tk.Label(self.content, text="Aucun outil trouvé.", bg=BG, fg=MUTED, font=("Segoe UI", 12)).pack(pady=40)
        for t in tools:
            t.update(wins=[], wait_until=0, sizes=None)
            t["btn"] = b = tk.Label(side, text=t["name"], bg=SIDE, fg=MUTED, font=("Segoe UI", 11), anchor="w",
                                    padx=16, pady=7, cursor="hand2")
            b.pack(fill="x")
            b.bind("<Button-1>", lambda e, t=t: self.select(t))
            t["box"] = box = tk.Frame(self.content, bg=BG)  # l'outil est accroché dans ce cadre
            t["info"] = info = tk.Frame(box, bg=BG)
            tk.Label(info, text=t["name"], bg=BG, fg=TEXT, font=("Segoe UI Semibold", 20)).pack(anchor="w")
            tk.Label(info, text=t["desc"], bg=BG, fg=MUTED, font=("Segoe UI", 11), wraplength=700,
                     justify="left").pack(anchor="w", pady=(6, 18))
            t["status"] = tk.Label(info, text="", bg=BG, fg=MUTED, font=("Segoe UI", 10), justify="left")
            t["status"].pack(anchor="w")
            open_btn = tk.Label(info, text="Ouvrir", bg=ACCENT, fg="white", font=("Segoe UI Semibold", 11),
                                padx=18, pady=6, cursor="hand2")
            open_btn.pack(anchor="w", pady=12)
            open_btn.bind("<Button-1>", lambda e, t=t: self.open(t))
            info.place(x=40, y=40)
        win.protocol("WM_DELETE_WINDOW", self.quit)
        if tools:
            self.select(tools[0], start=False)
        win.after(POLL, self.poll)

    # Onglets
    def select(self, t, start=True):
        if self.current is t:
            return self.open(t) if start and not self.visible(t) else None
        if self.current:
            old = self.current
            old["box"].pack_forget()
            old["btn"].config(bg=SIDE, fg=MUTED)
        self.current = t
        t["btn"].config(bg=HOVER, fg=TEXT)
        t["box"].pack(fill="both", expand=True)
        t["sizes"] = None
        if start:
            self.open(t)

    def visible(self, t):
        return any(u32.IsWindowVisible(x["hwnd"]) for x in t["wins"])

    def pids(self, t):
        exe = os.path.normcase(t["exe"])
        return {pid for _, pid in top_windows() if exe_of(pid) == exe}

    def open(self, t):
        if self.visible(t):
            return
        pids = self.pids(t)
        t["wait_until"] = time.time() + WAIT
        if not pids:
            try:
                subprocess.Popen([t["exe"]], cwd=os.path.dirname(t["exe"]))
                t["status"].config(text="Démarrage…", fg=MUTED)
            except OSError as e:
                if getattr(e, "winerror", 0) == 740:  # l'outil exige les droits admin et le hub ne les a pas
                    os.startfile(t["exe"], cwd=os.path.dirname(t["exe"]))
                    t["status"].config(text="Ouvert dans une fenêtre à part : lance le hub en administrateur pour l'intégrer.", fg=MUTED)
                else:
                    t["status"].config(text="Impossible de lancer : %s" % (e.strerror or e), fg="#ff6b6b")
            return
        # Déjà lancé mais sans fenêtre : outil de la zone de notification -> on « clique » sur son icône
        for h, pid in top_windows():
            if pid in pids and not u32.IsWindowVisible(h):
                u32.PostMessageW(h, WM_TRAY, 0, 0x201)
                u32.PostMessageW(h, WM_TRAY, 0, 0x202)
        t["status"].config(text="Ouverture…", fg=MUTED)

    # Boucle : accroche les nouvelles fenêtres, suit la taille, nettoie
    def poll(self):
        try:
            self.capture()
            for t in self.tools:
                self.tidy(t)
            self.fit()
        finally:
            self.win.after(POLL, self.poll)

    def capture(self):
        for h, pid in top_windows():
            t = self.by_exe.get(exe_of(pid))
            if not t or not u32.IsWindowVisible(h) or u32.GetWindow(h, GW_OWNER):
                continue  # boîtes de dialogue (avec propriétaire) : restent des fenêtres normales
            st, ex = style(h, GWL_STYLE), style(h, GWL_EXSTYLE)
            if st & WS_CAPTION != WS_CAPTION or ex & WS_EX_TOOLWINDOW:
                continue  # menus, overlays, popups qui se cachent dès qu'elles perdent le focus (presse-papiers)
            styles = embed(h, t["box"].winfo_id())
            if not styles:
                t["status"].config(text="Cette fenêtre ne peut pas être intégrée (droits admin ?).", fg="#ff6b6b")
                continue
            t["wins"].append({"hwnd": h, "styles": styles})
            t["wait_until"], t["sizes"] = 0, None
            if self.current is not t:
                self.select(t, start=False)
            if self.win.state() == "iconic" and not self.auto_min:
                self.win.deiconify()

    def tidy(self, t):
        for x in list(t["wins"]):
            h = x["hwnd"]
            if not u32.IsWindow(h) or u32.GetParent(h) != t["box"].winfo_id():
                t["wins"].remove(x)
            elif u32.IsIconic(h):
                self.on_minimized(h)
        if self.auto_min and not u32.IsWindow(self.auto_min):
            self.auto_min = None
        live = self.visible(t)
        if live and t["info"].winfo_ismapped():
            t["info"].place_forget()
        elif not live and not t["info"].winfo_ismapped():
            t["info"].place(x=40, y=40)
            if t["wait_until"] < time.time():
                t["status"].config(text="Fermé." if t["status"].cget("text") else "", fg=MUTED)
        if t["wait_until"] and time.time() > t["wait_until"] and not live:
            t["wait_until"] = 0
            if self.pids(t):
                t["status"].config(text="Outil de la zone de notification : sa fenêtre s'ouvre par-dessus le hub (ou avec son raccourci).")

    def on_minimized(self, h):
        """Un outil se réduit (ex. le coffre avant de remplir un site) : on réduit le hub à sa place."""
        if self.auto_min is None and self.win.state() != "iconic":
            self.auto_min = h
            self.win.iconify()

    def fit(self):
        if self.auto_min:
            h = self.auto_min
            if not u32.IsIconic(h):  # l'outil revient : le hub aussi
                self.auto_min = None
                self.win.deiconify()
                self.win.lift()
            elif self.win.state() != "iconic":  # l'utilisateur a rouvert le hub lui-même
                self.auto_min = None
                u32.ShowWindow(h, SW_RESTORE)
        t = self.current
        if not t or not t["wins"]:
            return
        size = (t["box"].winfo_width(), t["box"].winfo_height())
        if size != t["sizes"]:
            t["sizes"] = size
            for x in t["wins"]:
                u32.MoveWindow(x["hwnd"], 0, 0, size[0], size[1], True)
                u32.ShowWindow(x["hwnd"], SW_SHOWNOACTIVATE)

    def quit(self):
        # Les outils continuent de tourner (serveur Minecraft…) : on leur rend leur fenêtre
        for t in self.tools:
            for x in t["wins"]:
                release(x["hwnd"], x["styles"], show=True)
        self.win.destroy()


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # mêmes pixels que les outils intégrés
    except (AttributeError, OSError):
        pass
    win = tk.Tk()
    Hub(win, find_tools(os.path.dirname(here())))  # le hub vit dans Outils\HubOutils
    win.mainloop()


if __name__ == "__main__":
    main()
