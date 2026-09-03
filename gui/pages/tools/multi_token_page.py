import os
import sys
import time
import asyncio
import threading
import requests
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.dialogs import Messagebox

from gui.components import ToolPage, RoundedFrame
from gui.helpers import Style
from gui.helpers.images import Images
from utils.config import Config


class TokenInstance:
    def __init__(self, token_data, on_status_change=None):
        self.token = token_data.get("token", "")
        self.name = token_data.get("name", "Unnamed")
        self.bot = None
        self.loop = None
        self.thread = None
        self.running = False
        self.start_time = None
        self.on_status_change = on_status_change
        self._username = self.name

    def start(self):
        if self.running or not self.token:
            return

        try:
            resp = requests.get(
                "https://discord.com/api/v9/users/@me",
                headers={"Authorization": self.token},
                timeout=10,
            )
            if resp.status_code != 200:
                return
            self._username = resp.json().get("username", "Unknown")
        except Exception:
            return

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        from bot.bot import Ghost
        from bot.controller import BotController

        controller = BotController()
        controller.cfg.set("token", self.token)
        controller.loop = self.loop
        controller.running = True

        self.bot = Ghost(controller)

        async def _on_ready():
            self.start_time = time.time()
            self.running = True
            self._username = self.bot.user.name if self.bot.user else self.name
            if self.on_status_change:
                self.on_status_change(self)

        async def _on_disconnect():
            self.running = False
            if self.on_status_change:
                self.on_status_change(self)

        self.bot.add_listener(_on_ready, 'on_ready')
        self.bot.add_listener(_on_disconnect, 'on_disconnect')

        self.loop.create_task(self.bot.start(token=self.token, reconnect=True))
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running or not self.bot or not self.loop:
            return

        self.running = False

        async def shutdown():
            try:
                await self.bot.close()
            except Exception:
                pass

        asyncio.run_coroutine_threadsafe(shutdown(), self.loop)
        if self.on_status_change:
            self.on_status_change(self)

    def get_status(self):
        if not self.running:
            return "stopped"
        try:
            if self.bot and self.bot.is_ready():
                return "online"
        except Exception:
            pass
        return "connecting"

    def get_username(self):
        if self.bot and hasattr(self, "_username"):
            return self._username
        return self.name

    def get_uptime(self):
        if not self.start_time or not self.running:
            return "--"
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m {seconds}s"


class MultiTokenPage(ToolPage):
    def __init__(self, toolspage, root, bot_controller, images, layout):
        super().__init__(toolspage, root, bot_controller, images, layout, title="Multi-Token", frame=None)
        self.images = images
        self.cfg = Config()
        self.sessions = []
        self.token_frames = []
        self.list_frame = None

    def _get_tokens(self):
        tokens = self.cfg.get("multi_tokens")
        return tokens if tokens else []

    def _save_tokens(self, tokens):
        self.cfg.set("multi_tokens", tokens)
        self.cfg.save(notify=False)

    def _add_token(self):
        dialog = ttk.Toplevel(self.root)
        dialog.title("Add Token")
        dialog.geometry("450x200")
        dialog.configure(background=self.root.style.colors.get("dark"))
        dialog.transient(self.root)
        dialog.grab_set()

        if sys.platform == "win32":
            try:
                import hPyT
                hPyT.title_bar.hide(dialog, no_span=True)
                hPyT.corner_radius.set(dialog, style="round")
                hPyT.window_dwm.toggle_dwm_transitions(dialog, enabled=True)
            except Exception:
                pass

        wrapper = ttk.Frame(dialog, style="dark.TFrame")
        wrapper.pack(fill=ttk.BOTH, expand=True, padx=20, pady=20)

        name_label = ttk.Label(wrapper, text="Name", font=("Host Grotesk", 11))
        name_label.configure(background=self.root.style.colors.get("dark"),
                            foreground=Style.LIGHT_GREY.value)
        name_label.pack(anchor=ttk.W)

        name_var = ttk.StringVar(value="Account 1")
        name_entry = ttk.Entry(wrapper, textvariable=name_var, font=("Host Grotesk", 11))
        name_entry.configure(foreground=self.root.style.colors.get("fg"))
        name_entry.pack(fill=ttk.X, pady=(0, 10))

        token_label = ttk.Label(wrapper, text="Token", font=("Host Grotesk", 11))
        token_label.configure(background=self.root.style.colors.get("dark"),
                             foreground=Style.LIGHT_GREY.value)
        token_label.pack(anchor=ttk.W)

        token_var = ttk.StringVar()
        token_entry = ttk.Entry(wrapper, textvariable=token_var, font=("Host Grotesk", 11), show="*")
        token_entry.configure(foreground=self.root.style.colors.get("fg"))
        token_entry.pack(fill=ttk.X, pady=(0, 10))

        btn_frame = ttk.Frame(wrapper, style="dark.TFrame")
        btn_frame.pack(fill=ttk.X)

        def confirm():
            name = name_var.get().strip()
            token = token_var.get().strip()
            if not token:
                Messagebox.show_error("Token cannot be empty.", title="Error")
                return
            if not name:
                name = "Account"

            tokens = self._get_tokens()
            tokens.append({"name": name, "token": token, "enabled": False})
            self._save_tokens(tokens)
            dialog.destroy()
            self._refresh_list()

        cancel_btn = ttk.Label(btn_frame, text="Cancel", font=("Host Grotesk", 11),
                               cursor="hand2")
        cancel_btn.configure(foreground=Style.LIGHT_GREY.value,
                             background=self.root.style.colors.get("dark"))
        cancel_btn.pack(side=ttk.LEFT)
        cancel_btn.bind("<Button-1>", lambda e: dialog.destroy())

        add_btn = ttk.Label(btn_frame, text="Add", font=("Host Grotesk", 11, "bold"),
                            cursor="hand2")
        add_btn.configure(foreground="#4fee4c",
                          background=self.root.style.colors.get("dark"))
        add_btn.pack(side=ttk.RIGHT)
        add_btn.bind("<Button-1>", lambda e: confirm())
        token_entry.bind("<Return>", lambda e: confirm())

    def _toggle_token(self, index):
        tokens = self._get_tokens()
        if index >= len(tokens):
            return

        token_data = tokens[index]
        session = self._find_session(token_data["token"])

        if session and session.running:
            session.stop()
            token_data["enabled"] = False
        else:
            if not session:
                session = TokenInstance(token_data, on_status_change=lambda s: self.root.after(0, self._refresh_list))
                self.sessions.append(session)
            session.start()
            token_data["enabled"] = True

        self._save_tokens(tokens)
        self.root.after(500, self._refresh_list)

    def _remove_token(self, index):
        tokens = self._get_tokens()
        if index >= len(tokens):
            return

        token_data = tokens[index]
        session = self._find_session(token_data["token"])
        if session:
            session.stop()
            self.sessions = [s for s in self.sessions if s.token != token_data["token"]]

        tokens.pop(index)
        self._save_tokens(tokens)
        self._refresh_list()

    def _find_session(self, token):
        for s in self.sessions:
            if s.token == token:
                return s
        return None

    def _refresh_list(self):
        if not self.list_frame or not self.list_frame.winfo_exists():
            return

        for child in self.list_frame.winfo_children():
            child.destroy()

        tokens = self._get_tokens()

        if not tokens:
            empty = ttk.Label(self.list_frame, text="No tokens added yet.\nClick + Add Token to get started.",
                              font=("Host Grotesk", 11), justify=ttk.CENTER)
            empty.configure(background=self.root.style.colors.get("dark"),
                           foreground=Style.DARK_GREY.value)
            empty.pack(pady=40)
            return

        for i, token_data in enumerate(tokens):
            self._draw_token_card(self.list_frame, token_data, i)

    def _draw_token_card(self, parent, token_data, index):
        session = self._find_session(token_data["token"])
        status = session.get_status() if session else "stopped"
        username = session.get_username() if session else token_data.get("name", "Unknown")
        uptime = session.get_uptime() if session else "--"

        card = RoundedFrame(parent, radius=(10, 10, 10, 10), bootstyle="dark.TFrame")
        card.pack(fill=ttk.X, pady=(0, 5))

        inner = ttk.Frame(card, style="dark.TFrame")
        inner.pack(fill=ttk.BOTH, padx=12, pady=10)

        status_colors = {"online": "#4fee4c", "connecting": "#eceb18", "stopped": "#ff6464"}
        status_color = status_colors.get(status, Style.DARK_GREY.value)

        dot = ttk.Canvas(inner, width=8, height=8, highlightthickness=0,
                         background=self.root.style.colors.get("dark"))
        dot.grid(row=0, column=0, rowspan=2, sticky=ttk.N, pady=(4, 0))
        dot.create_oval(0, 0, 8, 8, fill=status_color, outline=status_color)

        name_label = ttk.Label(inner, text=username, font=("Host Grotesk", 12, "bold"))
        name_label.configure(background=self.root.style.colors.get("dark"))
        name_label.grid(row=0, column=1, sticky=ttk.W, padx=(8, 0))

        detail_text = f"{status.title()}"
        if status == "online":
            detail_text += f"  |  Uptime: {uptime}"
        detail_label = ttk.Label(inner, text=detail_text, font=("Host Grotesk", 9))
        detail_label.configure(background=self.root.style.colors.get("dark"),
                              foreground=Style.LIGHT_GREY.value)
        detail_label.grid(row=1, column=1, sticky=ttk.W, padx=(8, 0))

        btn_frame = ttk.Frame(inner, style="dark.TFrame")
        btn_frame.grid(row=0, column=2, rowspan=2, sticky=ttk.E)

        toggle_text = "Stop" if status in ("online", "connecting") else "Start"
        toggle_color = "#ff6464" if status in ("online", "connecting") else "#4fee4c"

        toggle_btn = ttk.Label(btn_frame, text=toggle_text, font=("Host Grotesk", 10, "bold"),
                               cursor="hand2")
        toggle_btn.configure(foreground=toggle_color, background=self.root.style.colors.get("dark"))
        toggle_btn.pack(side=ttk.LEFT, padx=(0, 10))
        toggle_btn.bind("<Button-1>", lambda e, i=index: self._toggle_token(i))
        toggle_btn.bind("<Enter>", lambda e: toggle_btn.configure(foreground="white"))
        toggle_btn.bind("<Leave>", lambda e: toggle_btn.configure(foreground=toggle_color))

        remove_btn = ttk.Label(btn_frame, text="Remove", font=("Host Grotesk", 10),
                               cursor="hand2")
        remove_btn.configure(foreground="#ff6464", background=self.root.style.colors.get("dark"))
        remove_btn.pack(side=ttk.LEFT)
        remove_btn.bind("<Button-1>", lambda e, i=index: self._remove_token(i))
        remove_btn.bind("<Enter>", lambda e: remove_btn.configure(foreground="white"))
        remove_btn.bind("<Leave>", lambda e: remove_btn.configure(foreground="#ff6464"))

        inner.grid_columnconfigure(1, weight=1)

    def draw_content(self, wrapper):
        add_btn_frame = RoundedFrame(wrapper, radius=(10, 10, 10, 10),
                                     bootstyle="primary.TFrame")
        add_btn_frame.pack(fill=ttk.X, pady=(0, 10))

        add_inner = ttk.Frame(add_btn_frame, style="primary.TFrame")
        add_inner.pack(fill=ttk.BOTH, padx=12, pady=8)

        add_label = ttk.Label(add_inner, text="+ Add Token",
                              font=("Host Grotesk", 12, "bold"),
                              cursor="hand2")
        add_label.configure(background=self.root.style.colors.get("primary"))
        add_label.pack(side=ttk.LEFT)
        add_label.bind("<Button-1>", lambda e: self._add_token())
        add_btn_frame.bind("<Button-1>", lambda e: self._add_token())

        self.status_label = ttk.Label(add_inner, text="",
                                      font=("Host Grotesk", 10))
        self.status_label.configure(background=self.root.style.colors.get("primary"),
                                   foreground="#ffffff")
        self.status_label.pack(side=ttk.RIGHT)

        tokens_label = ttk.Label(wrapper, text="Active Tokens",
                                 font=("Host Grotesk", 14, "bold"))
        tokens_label.configure(background=self.root.style.colors.get("dark"))
        tokens_label.pack(anchor=ttk.W, pady=(5, 5))

        self.list_frame = ScrolledFrame(wrapper, bootstyle="dark.TFrame", autohide=True)
        self.list_frame.container.configure(style="dark.TFrame")
        self.list_frame.pack(fill=ttk.BOTH, expand=True)

        self._refresh_list()
