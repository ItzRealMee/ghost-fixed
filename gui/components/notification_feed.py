import sys
import time
import ttkbootstrap as ttk

from gui.helpers.style import Style


class Toast:
    def __init__(self, parent, root, event_type, title, description="", timestamp=None, color=None, on_dismiss=None):
        from utils.config import Config
        self.parent = parent
        self.root = root
        self.on_dismiss = on_dismiss
        self.color = color or self._get_color(event_type)
        self.timestamp = timestamp or time.strftime("%H:%M:%S")

        timeout_sec = Config().get("notification_timeout")
        self.AUTO_DISMISS_MS = (timeout_sec if isinstance(timeout_sec, (int, float)) and timeout_sec > 0 else 5) * 1000

        self.frame = ttk.Frame(parent, style="dark.TFrame")
        self.frame.pack(fill=ttk.X, padx=4, pady=(0, 4))

        card = ttk.Frame(self.frame, style="dark.TFrame")
        card.pack(fill=ttk.X)

        accent = ttk.Canvas(card, width=3, height=3, highlightthickness=0,
                            background=self.root.style.colors.get("dark"))
        accent.pack(side=ttk.LEFT, fill="y", padx=(0, 8))
        accent.create_rectangle(0, 0, 3, 500, fill=self.color, outline=self.color)

        content = ttk.Frame(card, style="dark.TFrame")
        content.pack(side=ttk.LEFT, fill=ttk.X, expand=True, pady=6)

        top = ttk.Frame(content, style="dark.TFrame")
        top.pack(fill=ttk.X)

        type_lbl = ttk.Label(top, text=event_type.replace("_", " ").title(),
                             font=("Host Grotesk", 9, "bold"), foreground=self.color)
        type_lbl.configure(background=self.root.style.colors.get("dark"))
        type_lbl.pack(side=ttk.LEFT)

        time_lbl = ttk.Label(top, text=self.timestamp, font=("Host Grotesk", 8),
                             foreground=Style.DARK_GREY.value)
        time_lbl.configure(background=self.root.style.colors.get("dark"))
        time_lbl.pack(side=ttk.RIGHT)

        title_lbl = ttk.Label(content, text=title, font=("Host Grotesk", 10, "bold"))
        title_lbl.configure(background=self.root.style.colors.get("dark"))
        title_lbl.pack(anchor=ttk.W)

        if description:
            desc_lbl = ttk.Label(content, text=description, font=("Host Grotesk", 9),
                                 foreground=Style.LIGHT_GREY.value, wraplength=400)
            desc_lbl.configure(background=self.root.style.colors.get("dark"))
            desc_lbl.pack(anchor=ttk.W)

        dismiss = ttk.Label(card, text="\u00d7", font=("Host Grotesk", 14, "bold"),
                            cursor="hand2", foreground=Style.DARK_GREY.value)
        dismiss.configure(background=self.root.style.colors.get("dark"))
        dismiss.pack(side=ttk.RIGHT, padx=8, anchor=ttk.N)
        dismiss.bind("<Button-1>", lambda e: self.dismiss())
        dismiss.bind("<Enter>", lambda e: dismiss.configure(foreground="white"))
        dismiss.bind("<Leave>", lambda e: dismiss.configure(foreground=Style.DARK_GREY.value))

        self._timer = self.root.after(self.AUTO_DISMISS_MS, self.dismiss)

    def _get_color(self, event_type):
        colors = {
            "friend_add": "#4fee4c", "friend_remove": "#ff6464",
            "relationship_add": "#4fee4c", "relationship_remove": "#ff6464",
            "relationship_update": "#eceb18", "guild_remove": "#ff6464",
            "guild_join": "#4fee4c", "nitro_snipe": "#0b91ff",
            "privnote_snipe": "#a07cff", "info": "#2aefef",
            "warning": "#eceb18", "error": "#ff6464", "success": "#4fee4c",
        }
        return colors.get(event_type, Style.LIGHT_GREY.value)

    def dismiss(self):
        try:
            if self._timer:
                self.root.after_cancel(self._timer)
        except Exception:
            pass
        try:
            if self.frame and self.frame.winfo_exists():
                self.frame.destroy()
        except Exception:
            pass
        if self.on_dismiss:
            self.on_dismiss(self)


class NotificationFeed:
    MAX_VISIBLE = 5

    def __init__(self, root):
        self.root = root
        self.wrapper = None
        self.toasts = []
        self.history = []
        self._logger_page = None

    def set_logger(self, logger_page):
        self._logger_page = logger_page

    def draw(self, parent):
        self.wrapper = ttk.Frame(parent, style="dark.TFrame")
        return self.wrapper

    def add_notification(self, event_type, title, description="", timestamp=None, color=None):
        ts = timestamp or time.strftime("%H:%M:%S")
        clr = color or self._get_color(event_type)

        self.history.append({
            "event_type": event_type,
            "title": title,
            "description": description,
            "timestamp": ts,
            "color": clr,
        })

        if self._logger_page:
            self._logger_page.add_entry(event_type, title, description, timestamp=ts, color=clr)

        if not self.wrapper or not self.wrapper.winfo_exists():
            return

        toast = Toast(self.wrapper, self.root, event_type, title, description,
                      timestamp=ts, color=clr, on_dismiss=self._on_dismiss)
        self.toasts.append(toast)

        while len(self.toasts) > self.MAX_VISIBLE:
            old = self.toasts.pop(0)
            old.dismiss()

    def _get_color(self, event_type):
        colors = {
            "friend_add": "#4fee4c", "friend_remove": "#ff6464",
            "relationship_add": "#4fee4c", "relationship_remove": "#ff6464",
            "relationship_update": "#eceb18", "guild_remove": "#ff6464",
            "guild_join": "#4fee4c", "nitro_snipe": "#0b91ff",
            "privnote_snipe": "#a07cff", "info": "#2aefef",
            "warning": "#eceb18", "error": "#ff6464", "success": "#4fee4c",
        }
        return colors.get(event_type, Style.LIGHT_GREY.value)

    def _on_dismiss(self, toast):
        if toast in self.toasts:
            self.toasts.remove(toast)

    def clear(self):
        for t in self.toasts[:]:
            t.dismiss()
        self.toasts.clear()
