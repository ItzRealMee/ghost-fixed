import time
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from gui.components import ToolPage, RoundedFrame
from gui.helpers import Style


class NotificationLoggerPage(ToolPage):
    def __init__(self, toolspage, root, bot_controller, images, layout):
        super().__init__(toolspage, root, bot_controller, images, layout, title="Notification Logger", frame=None)
        self.history = []
        self.log_frame = None

    def add_entry(self, event_type, title, description="", timestamp=None, color=None):
        ts = timestamp or time.strftime("%H:%M:%S")
        self.history.append({
            "event_type": event_type,
            "title": title,
            "description": description,
            "timestamp": ts,
            "color": color or self._get_color(event_type),
        })
        if self.log_frame and self.log_frame.winfo_exists():
            self.root.after(0, self._draw_last_entry)

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

    def _draw_last_entry(self):
        if not self.log_frame or not self.log_frame.winfo_exists():
            return
        if not self.history:
            return
        entry = self.history[-1]
        self._draw_entry(self.log_frame, entry)

    def _draw_entry(self, parent, entry):
        row = ttk.Frame(parent, style="dark.TFrame")
        row.pack(fill=ttk.X, padx=4, pady=(0, 2))

        accent = ttk.Canvas(row, width=3, height=3, highlightthickness=0,
                            background=self.root.style.colors.get("dark"))
        accent.pack(side=ttk.LEFT, fill="y", padx=(0, 6))
        accent.create_rectangle(0, 0, 3, 500, fill=entry["color"], outline=entry["color"])

        content = ttk.Frame(row, style="dark.TFrame")
        content.pack(side=ttk.LEFT, fill=ttk.X, expand=True, pady=4)

        top = ttk.Frame(content, style="dark.TFrame")
        top.pack(fill=ttk.X)

        type_lbl = ttk.Label(top, text=entry["event_type"].replace("_", " ").title(),
                             font=("Host Grotesk", 9, "bold"), foreground=entry["color"])
        type_lbl.configure(background=self.root.style.colors.get("dark"))
        type_lbl.pack(side=ttk.LEFT)

        time_lbl = ttk.Label(top, text=entry["timestamp"], font=("Host Grotesk", 8),
                             foreground=Style.DARK_GREY.value)
        time_lbl.configure(background=self.root.style.colors.get("dark"))
        time_lbl.pack(side=ttk.RIGHT)

        title_lbl = ttk.Label(content, text=entry["title"], font=("Host Grotesk", 10, "bold"))
        title_lbl.configure(background=self.root.style.colors.get("dark"))
        title_lbl.pack(anchor=ttk.W)

        if entry["description"]:
            desc_lbl = ttk.Label(content, text=entry["description"], font=("Host Grotesk", 9),
                                 foreground=Style.LIGHT_GREY.value, wraplength=450)
            desc_lbl.configure(background=self.root.style.colors.get("dark"))
            desc_lbl.pack(anchor=ttk.W)

    def _clear_log(self):
        self.history.clear()
        if self.log_frame and self.log_frame.winfo_exists():
            for child in self.log_frame.winfo_children():
                child.destroy()

    def draw_content(self, wrapper):
        header = ttk.Frame(wrapper, style="dark.TFrame")
        header.pack(fill=ttk.X, pady=(0, 8))

        title = ttk.Label(header, text="All Notifications",
                          font=("Host Grotesk", 14, "bold"))
        title.configure(background=self.root.style.colors.get("dark"))
        title.pack(side=ttk.LEFT)

        clear_btn = ttk.Label(header, text="Clear", font=("Host Grotesk", 10, "bold"),
                              cursor="hand2", foreground="#ff6464")
        clear_btn.configure(background=self.root.style.colors.get("dark"))
        clear_btn.pack(side=ttk.RIGHT)
        clear_btn.bind("<Button-1>", lambda e: self._clear_log())
        clear_btn.bind("<Enter>", lambda e: clear_btn.configure(foreground="white"))
        clear_btn.bind("<Leave>", lambda e: clear_btn.configure(foreground="#ff6464"))

        count_lbl = ttk.Label(header, text=f"{len(self.history)} entries",
                              font=("Host Grotesk", 9), foreground=Style.DARK_GREY.value)
        count_lbl.configure(background=self.root.style.colors.get("dark"))
        count_lbl.pack(side=ttk.RIGHT, padx=(0, 15))

        self.log_frame = ScrolledFrame(wrapper, bootstyle="dark.TFrame", autohide=True)
        self.log_frame.container.configure(style="dark.TFrame")
        self.log_frame.pack(fill=ttk.BOTH, expand=True)

        for entry in self.history:
            self._draw_entry(self.log_frame, entry)

        if not self.history:
            empty = ttk.Label(self.log_frame, text="No notifications yet.",
                              font=("Host Grotesk", 11), foreground=Style.DARK_GREY.value)
            empty.configure(background=self.root.style.colors.get("dark"))
            empty.pack(pady=30)
