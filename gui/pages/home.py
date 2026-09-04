import sys
import ttkbootstrap as ttk
import tkinter.font as tkFont

from gui.components import RoundedFrame, RoundedButton
from gui.components.notification_feed import NotificationFeed
from gui.helpers import Images
from gui.helpers.style import Style, get_current_theme_str
from utils.config import VERSION, Config


class HomePage:
    def __init__(self, root, bot_controller, _restart_bot, console):
        self.root = root
        self.bot_controller = bot_controller
        self._restart_bot = _restart_bot
        self.console = console
        self.restart = False
        self.avatar = None
        self.images = Images()
        self.cfg = Config()

        self.friends_label = None
        self.guilds_label = None
        self.uptime_label = None
        self.latency_label = None

        self.restart_title = None
        self.restart_title_elipsis = "..."
        self.restart_title_text = "Ghost is restarting"

        self.notification_feed = NotificationFeed(root)
        self._notification_feed_widget = None
        self._hooks_installed = False

    def _update_restart_title(self):
        try:
            if self.restart:
                if len(self.restart_title_elipsis) == 3:
                    self.restart_title_elipsis = "."
                else:
                    self.restart_title_elipsis += "."
                self.restart_title.config(text=f"{self.restart_title_text}{self.restart_title_elipsis}")
            self.restart_title.after(750, self._update_restart_title)
        except Exception:
            pass

    def _update_bot_details(self):
        try:
            if not self.restart and self.uptime_label and self.latency_label:
                self.uptime_label.config(text=f"Uptime: {self.bot_controller.get_uptime()}")
                self.latency_label.config(text=f"Latency: {self.bot_controller.get_latency()}")
            if self.uptime_label:
                self.uptime_label.after(1000, self._update_bot_details)
        except Exception:
            pass

    def _update_account_details(self):
        try:
            if not self.restart and self.friends_label and self.guilds_label:
                friends = self.bot_controller.get_friends()
                guilds = self.bot_controller.get_guilds()
                self.friends_label.config(text=str(len(friends)) if friends else "0")
                self.guilds_label.config(text=str(len(guilds)) if guilds else "0")
            if self.friends_label:
                self.friends_label.after(1000, self._update_account_details)
        except Exception:
            pass

    def _draw_header(self, parent):
        wrapper = RoundedFrame(parent, radius=(15, 15, 15, 15), bootstyle="secondary.TFrame")
        wrapper.pack(fill=ttk.X, pady=(0, 8))

        if self.restart:
            self.restart_title = ttk.Label(
                wrapper, text=f"{self.restart_title_text}...",
                font=("Host Grotesk", 20, "bold"), anchor="center"
            )
            self.restart_title.configure(background=self.root.style.colors.get("secondary"))
            self.restart_title.pack(pady=16, padx=15)
            self.root.after(750, self._update_restart_title)
            return

        content = ttk.Frame(wrapper, style="secondary.TFrame")
        content.pack(fill=ttk.BOTH, padx=12, pady=8)

        if self.avatar:
            avatar_label = ttk.Label(content, image=self.avatar)
            avatar_label.configure(background=self.root.style.colors.get("secondary"))
            avatar_label.grid(row=0, column=0, rowspan=2, sticky=ttk.W, padx=(0, 10))

        name_frame = ttk.Frame(content, style="secondary.TFrame")
        name_frame.grid(row=0, column=1, sticky=ttk.W)

        display_name = ttk.Label(
            name_frame, text=self.bot_controller.get_user().display_name,
            font=("Host Grotesk", 18, "bold")
        )
        display_name.configure(background=self.root.style.colors.get("secondary"))
        display_name.pack(anchor=ttk.W)

        username = ttk.Label(
            name_frame, text=self.bot_controller.get_user().name,
            font=("Host Grotesk", 11 if sys.platform != "darwin" else 13, "italic")
        )
        username.configure(background=self.root.style.colors.get("secondary"), foreground=Style.LIGHT_GREY.value)
        username.pack(anchor=ttk.W)

        content.grid_columnconfigure(1, weight=1)

        restart_img = self.images.get("restart")
        if get_current_theme_str() == "light":
            restart_img = self.images.change_image_colour("restart", "#ffffff", tk_image=True)
        restart_btn = RoundedButton(
            content, radius=18, bootstyle="primary.TButton",
            command=lambda _: self._restart_bot(), image=restart_img,
            padx=12, pady=4
        )
        restart_btn.grid(row=0, column=2, rowspan=2, sticky=ttk.E, padx=(8, 0))

    def _draw_stat_card(self, parent, title, row, col):
        card = RoundedFrame(parent, radius=(10, 10, 10, 10), bootstyle="dark.TFrame")
        card.grid(row=row, column=col, sticky=ttk.NSEW, padx=(0, 4), pady=(0, 4))

        inner = ttk.Frame(card, style="dark.TFrame")
        inner.pack(fill=ttk.BOTH, padx=10, pady=6)

        header = ttk.Frame(inner, style="dark.TFrame")
        header.pack(fill=ttk.X)

        title_lbl = ttk.Label(header, text=title, font=("Host Grotesk", 11, "bold"))
        title_lbl.configure(background=self.root.style.colors.get("dark"))
        title_lbl.pack(side=ttk.LEFT)

        ttk.Separator(inner, orient="horizontal").pack(fill=ttk.X, pady=(4, 6))

        return inner

    def _draw_details(self, parent):
        container = ttk.Frame(parent, style="default.TFrame")
        container.pack(fill=ttk.X, pady=(0, 8))
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        discord_card = self._draw_stat_card(container, "Discord", 0, 0)
        self.friends_label = ttk.Label(
            discord_card, text="0",
            font=("Host Grotesk", 18, "bold")
        )
        self.friends_label.configure(background=self.root.style.colors.get("dark"), foreground="#4fee4c")
        self.friends_label.pack(anchor=ttk.W)
        friends_sub = ttk.Label(
            discord_card, text="Friends",
            font=("Host Grotesk", 9)
        )
        friends_sub.configure(background=self.root.style.colors.get("dark"), foreground=Style.LIGHT_GREY.value)
        friends_sub.pack(anchor=ttk.W)

        ttk.Frame(discord_card, height=4, style="dark.TFrame").pack()

        self.guilds_label = ttk.Label(
            discord_card, text="0",
            font=("Host Grotesk", 18, "bold")
        )
        self.guilds_label.configure(background=self.root.style.colors.get("dark"), foreground="#5865f2")
        self.guilds_label.pack(anchor=ttk.W)
        guilds_sub = ttk.Label(
            discord_card, text="Guilds",
            font=("Host Grotesk", 9)
        )
        guilds_sub.configure(background=self.root.style.colors.get("dark"), foreground=Style.LIGHT_GREY.value)
        guilds_sub.pack(anchor=ttk.W)

        ghost_card = self._draw_stat_card(container, "Ghost", 0, 1)

        version_val = ttk.Label(ghost_card, text=f"v{VERSION}", font=("Host Grotesk", 18, "bold"))
        version_val.configure(background=self.root.style.colors.get("dark"), foreground="#fee75c")
        version_val.pack(anchor=ttk.W)
        version_sub = ttk.Label(ghost_card, text="Version", font=("Host Grotesk", 9))
        version_sub.configure(background=self.root.style.colors.get("dark"), foreground=Style.LIGHT_GREY.value)
        version_sub.pack(anchor=ttk.W)

        ttk.Frame(ghost_card, height=4, style="dark.TFrame").pack()

        self.uptime_label = ttk.Label(ghost_card, text="Uptime: 0s", font=("Host Grotesk", 11))
        self.uptime_label.configure(background=self.root.style.colors.get("dark"))
        self.uptime_label.pack(anchor=ttk.W)

        self.latency_label = ttk.Label(ghost_card, text="Latency: 0ms", font=("Host Grotesk", 11))
        self.latency_label.configure(background=self.root.style.colors.get("dark"))
        self.latency_label.pack(anchor=ttk.W)

    def draw(self, parent, restart=False, start=False):
        self.restart = restart or start
        self.restart_title_text = "Ghost is starting" if start else "Ghost is restarting"
        self.avatar = self.bot_controller.get_avatar(size=50) if not self.restart else None

        self._draw_header(parent)
        self._draw_details(parent)
        self._update_bot_details()

        if not self.restart:
            self._update_account_details()

            self._notification_feed_widget = self.notification_feed.draw(parent)
            self._notification_feed_widget.pack(fill=ttk.X)

            self.console.draw(parent)
            self._setup_event_hooks()
        else:
            self.console.draw(parent)

    def _setup_event_hooks(self):
        if self._hooks_installed:
            return
        if not self.bot_controller.bot:
            return
        try:
            self.bot_controller.bot.add_listener(self._on_relationship_add, 'on_relationship_add')
            self.bot_controller.bot.add_listener(self._on_relationship_remove, 'on_relationship_remove')
            self.bot_controller.bot.add_listener(self._on_relationship_update, 'on_relationship_update')
            self.bot_controller.bot.add_listener(self._on_guild_remove, 'on_guild_remove')
            self.bot_controller.bot.add_listener(self._on_guild_join, 'on_guild_join')
            self._hooks_installed = True
        except Exception:
            pass

    async def _on_relationship_add(self, relationship):
        try:
            user_name = getattr(relationship, 'user', relationship).name if hasattr(relationship, 'user') else str(relationship)
            self._add_notification(
                "friend_add",
                f"New {getattr(relationship, 'type', 'friend').name.replace('_', ' ').title() if hasattr(relationship, 'type') else 'friend'}",
                f"{user_name} has been added to your relationships."
            )
        except Exception:
            pass

    async def _on_relationship_remove(self, relationship):
        try:
            user_name = getattr(relationship, 'user', relationship).name if hasattr(relationship, 'user') else str(relationship)
            self._add_notification(
                "friend_remove",
                f"Removed {getattr(relationship, 'type', 'friend').name.replace('_', ' ').title() if hasattr(relationship, 'type') else 'friend'}",
                f"{user_name} has been removed from your relationships."
            )
        except Exception:
            pass

    async def _on_relationship_update(self, before, after):
        try:
            user_name = getattr(after, 'user', after).name if hasattr(after, 'user') else str(after)
            self._add_notification(
                "relationship_update",
                "Relationship Updated",
                f"Relationship with {user_name} has been updated."
            )
        except Exception:
            pass

    async def _on_guild_remove(self, guild):
        try:
            self._add_notification(
                "guild_remove",
                "Removed from Server",
                f"You were removed from {guild.name}."
            )
        except Exception:
            pass

    async def _on_guild_join(self, guild):
        try:
            self._add_notification(
                "guild_join",
                "Joined Server",
                f"You joined {guild.name}."
            )
        except Exception:
            pass

    def _add_notification(self, event_type, title, description="", color=None):
        import time as _time
        timestamp = _time.strftime("%H:%M:%S")
        try:
            if self.notification_feed.wrapper and self.notification_feed.wrapper.winfo_exists():
                self.root.after(0, lambda: self.notification_feed.add_notification(
                    event_type, title, description, timestamp=timestamp, color=color
                ))
        except Exception:
            pass
