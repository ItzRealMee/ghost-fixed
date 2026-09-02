import sys
import time
import ttkbootstrap as ttk
import tkinter.font as tkFont

from gui.helpers.style import Style


class NotificationEntry:
    MAX_ENTRIES = 100

    def __init__(self, parent, root, event_type, title, description, timestamp=None, color=None):
        self.parent = parent
        self.root = root
        self.event_type = event_type
        self.title = title
        self.description = description
        self.timestamp = timestamp or time.strftime("%H:%M:%S")
        self.color = color or self._get_color_for_type(event_type)
        self.frame = None
        self._draw()

    def _get_color_for_type(self, event_type):
        colors = {
            "friend_add": "#4fee4c",
            "friend_remove": "#ff6464",
            "relationship_add": "#4fee4c",
            "relationship_remove": "#ff6464",
            "relationship_update": "#eceb18",
            "guild_remove": "#ff6464",
            "guild_join": "#4fee4c",
            "nitro_snipe": "#0b91ff",
            "nitro_snipe_success": "#4fee4c",
            "nitro_snipe_fail": "#ff6464",
            "privnote_snipe": "#a07cff",
            "privnote_snipe_success": "#4fee4c",
            "privnote_snipe_fail": "#ff6464",
            "info": "#2aefef",
            "warning": "#eceb18",
            "error": "#ff6464",
            "success": "#4fee4c",
        }
        return colors.get(event_type, Style.LIGHT_GREY.value)

    def _draw(self):
        self.frame = ttk.Frame(self.parent, style="dark.TFrame")
        self.frame.pack(fill=ttk.X, padx=(0, 5), pady=(0, 4))

        inner = ttk.Frame(self.frame, style="dark.TFrame")
        inner.pack(fill=ttk.BOTH, padx=10, pady=6)

        top_row = ttk.Frame(inner, style="dark.TFrame")
        top_row.pack(fill=ttk.X)

        indicator = ttk.Canvas(top_row, width=4, height=4,
                               highlightthickness=0,
                               background=self.root.style.colors.get("dark"))
        indicator.pack(side=ttk.LEFT, padx=(0, 6), pady=(5, 0))
        indicator.create_oval(0, 0, 4, 4, fill=self.color, outline=self.color)

        type_label = ttk.Label(top_row, text=self.event_type.replace("_", " ").title(),
                               font=("Host Grotesk", 9, "bold"))
        type_label.configure(background=self.root.style.colors.get("dark"),
                            foreground=self.color)
        type_label.pack(side=ttk.LEFT)

        time_label = ttk.Label(top_row, text=self.timestamp,
                               font=("Host Grotesk", 8))
        time_label.configure(background=self.root.style.colors.get("dark"),
                            foreground=Style.DARK_GREY.value)
        time_label.pack(side=ttk.RIGHT)

        title_label = ttk.Label(inner, text=self.title,
                                font=("Host Grotesk", 11, "bold"), wraplength=350)
        title_label.configure(background=self.root.style.colors.get("dark"))
        title_label.pack(anchor=ttk.W, pady=(3, 0))

        if self.description:
            desc_label = ttk.Label(inner, text=self.description,
                                   font=("Host Grotesk", 10), wraplength=350)
            desc_label.configure(background=self.root.style.colors.get("dark"),
                                foreground=Style.LIGHT_GREY.value)
            desc_label.pack(anchor=ttk.W, pady=(1, 0))


class NotificationFeed:
    MAX_NOTIFICATIONS = 80

    def __init__(self, root, max_visible=50):
        self.root = root
        self.canvas = None
        self.scroll_frame = None
        self.wrapper = None
        self.notifications = []
        self.max_visible = max_visible

    def _on_mousewheel(self, event):
        if self.canvas is None:
            return
        if sys.platform == 'darwin':
            self.canvas.yview_scroll(-1 * int(event.delta), "units")
        else:
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def draw(self, parent):
        self.wrapper = ttk.Frame(parent, style="dark.TFrame")

        self.canvas = ttk.Canvas(self.wrapper,
                                 background=self.root.style.colors.get("dark"),
                                 highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.wrapper, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas, style="dark.TFrame")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        def resize_canvas(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind("<Configure>", resize_canvas)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>",
                         lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>",
                         lambda e: self.canvas.unbind_all("<MouseWheel>"))

        return self.wrapper

    def add_notification(self, event_type, title, description="", timestamp=None, color=None):
        if self.scroll_frame is None:
            return
        try:
            if not self.scroll_frame.winfo_exists():
                return
        except Exception:
            return

        entry = NotificationEntry(
            self.scroll_frame, self.root,
            event_type, title, description,
            timestamp=timestamp, color=color
        )
        self.notifications.append(entry)

        if len(self.notifications) > self.MAX_NOTIFICATIONS:
            old = self.notifications.pop(0)
            if old.frame:
                old.frame.destroy()

        self.root.after(50, self._scroll_to_bottom)

    def clear(self):
        if self.scroll_frame is None:
            return
        for notif in self.notifications:
            if notif.frame:
                notif.frame.destroy()
        self.notifications.clear()

    def _scroll_to_bottom(self):
        try:
            if self.canvas and self.canvas.winfo_exists():
                self.canvas.yview_moveto(1.0)
        except Exception:
            pass
