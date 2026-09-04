import os
import json
import time
import asyncio
import threading
import discord
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

from gui.components import ToolPage, RoundedFrame
from gui.helpers import Style
from utils.files import get_application_support


class BackupsPage(ToolPage):
    def __init__(self, toolspage, root, bot_controller, images, layout):
        super().__init__(toolspage, root, bot_controller, images, layout, title="Backups", frame=None)
        self.images = images
        self.cfg = bot_controller.cfg
        self.backups_dir = os.path.join(get_application_support(), "backups")
        self.backup_list_frame = None
        self.status_label = None

    def _ensure_backups_dir(self):
        os.makedirs(self.backups_dir, exist_ok=True)

    def _get_backups(self):
        self._ensure_backups_dir()
        backups = []
        for f in os.listdir(self.backups_dir):
            if f.endswith(".json"):
                path = os.path.join(self.backups_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    stat = os.stat(path)
                    backups.append({
                        "name": f,
                        "path": path,
                        "type": data.get("type", f.replace(".json", "")),
                        "created_at": data.get("created_at"),
                        "size": stat.st_size,
                        "time": stat.st_mtime,
                        "data": data,
                    })
                except Exception:
                    pass
        backups.sort(key=lambda b: b["time"], reverse=True)
        return backups

    def _format_time(self, timestamp):
        if timestamp:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        return "Unknown"

    def _set_status(self, text):
        if self.status_label:
            self.status_label.configure(text=text)

    def _run_async(self, coro):
        def _worker():
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(coro)
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Error: {e}"))
            finally:
                loop.close()
        threading.Thread(target=_worker, daemon=True).start()

    def _get_available_bots(self):
        bots = []
        main_bot = getattr(self.bot_controller, "bot", None)
        if main_bot and main_bot.is_ready():
            bots.append({
                "label": f"Main — {main_bot.user.name}",
                "bot": main_bot,
                "token": self.cfg.get("token"),
            })
        if hasattr(self, 'toolspage') and hasattr(self.toolspage, 'multi_token_page'):
            for session in self.toolspage.multi_token_page.sessions:
                if session.running and session.bot and session.bot.is_ready():
                    bots.append({
                        "label": f"Multi — {session.bot.user.name}",
                        "bot": session.bot,
                        "token": session.token,
                    })
        return bots

    def _pick_account(self, backup_type, callback):
        bots = self._get_available_bots()
        if not bots:
            self._set_status("No bots connected. Start the bot first.")
            return
        if len(bots) == 1:
            callback(bots[0]["bot"], bots[0]["token"])
            return

        dialog = ttk.Toplevel(self.root)
        dialog.title(f"Backup {backup_type.title()}")
        dialog.geometry("350x250")
        dialog.resizable(False, False)
        dialog.configure(background=self.root.style.colors.get("dark"))
        dialog.transient(self.root)

        wrapper = ttk.Frame(dialog, style="dark.TFrame")
        wrapper.pack(fill=ttk.BOTH, expand=True, padx=15, pady=15)

        title = ttk.Label(wrapper, text=f"Select account to backup {backup_type}:",
                          font=("Host Grotesk", 11, "bold"))
        title.configure(background=self.root.style.colors.get("dark"), foreground="white")
        title.pack(anchor=ttk.W, pady=(0, 10))

        for bot_info in bots:
            card = RoundedFrame(wrapper, radius=(8, 8, 8, 8), bootstyle="dark.TFrame")
            card.pack(fill=ttk.X, pady=(0, 5))

            lbl = ttk.Label(card, text=bot_info["label"],
                            font=("Host Grotesk", 11), cursor="hand2",
                            foreground="#5865f2")
            lbl.configure(background=self.root.style.colors.get("dark"))
            lbl.pack(padx=12, pady=8, anchor=ttk.W)
            lbl.bind("<Button-1>", lambda e, b=bot_info["bot"], t=bot_info["token"], d=dialog: (
                d.destroy(), callback(b, t)))
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(foreground="white"))
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(foreground="#5865f2"))

        cancel = ttk.Label(wrapper, text="Cancel", font=("Host Grotesk", 10),
                           cursor="hand2", foreground=Style.LIGHT_GREY.value)
        cancel.configure(background=self.root.style.colors.get("dark"))
        cancel.pack(anchor=ttk.W, pady=(5, 0))
        cancel.bind("<Button-1>", lambda e: dialog.destroy())
        cancel.bind("<Enter>", lambda e: cancel.configure(foreground="white"))
        cancel.bind("<Leave>", lambda e: cancel.configure(foreground=Style.LIGHT_GREY.value))

    def _create_backup_account(self):
        self._pick_account("account", self._do_backup_account)

    def _do_backup_account(self, bot, token):
        self._set_status("Backing up account...")
        async def _do():
            try:
                user = bot.user
                data = {
                    "created_at": time.time(),
                    "type": "account",
                    "info": {
                        "id": user.id,
                        "name": user.name,
                        "display_name": user.display_name,
                        "accent_colour": str(user.accent_colour) if user.accent_colour else None,
                        "avatar": str(user.avatar.url) if user.avatar else None,
                        "banner": str(user.banner.url) if user.banner else None,
                        "bio": user.bio or None,
                    },
                }
                self._ensure_backups_dir()
                name = user.name.lower().replace(" ", "_")
                path = os.path.join(self.backups_dir, f"account_{name}.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                self.root.after(0, lambda: self._set_status(f"Account backed up ({user.name})"))
                self.root.after(0, self._refresh_backup_list)
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Failed: {e}"))
        self._run_async(_do())

    def _create_backup_friends(self):
        self._pick_account("friends", self._do_backup_friends)

    def _do_backup_friends(self, bot, token):
        self._set_status("Backing up friends...")
        async def _do():
            try:
                friends = []
                for relationship in bot.friends:
                    if relationship.type == 1:
                        friends.append({"username": relationship.user.name, "id": relationship.user.id})
                data = {
                    "created_at": time.time(),
                    "type": "friends",
                    "list": friends,
                }
                self._ensure_backups_dir()
                name = bot.user.name.lower().replace(" ", "_")
                path = os.path.join(self.backups_dir, f"friends_{name}.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                self.root.after(0, lambda: self._set_status(f"Friends backed up ({len(friends)} friends)"))
                self.root.after(0, self._refresh_backup_list)
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Failed: {e}"))
        self._run_async(_do())

    def _create_backup_guilds(self):
        self._pick_account("guilds", self._do_backup_guilds)

    def _do_backup_guilds(self, bot, token):
        self._set_status("Backing up guilds...")
        async def _do():
            try:
                guilds = []
                for guild in bot.guilds:
                    invite = None
                    try:
                        invite = guild.vanity_url
                    except Exception:
                        pass
                    if not invite:
                        for channel in guild.channels:
                            if isinstance(channel, discord.TextChannel) and channel.permissions_for(guild.me).create_instant_invite:
                                try:
                                    invite = await channel.create_invite(max_age=0, max_uses=1, unique=True)
                                except Exception:
                                    break
                                if invite:
                                    break
                    guilds.append({"name": guild.name, "id": guild.id, "invite": str(invite) if invite else "None"})
                    await asyncio.sleep(0.75)
                data = {
                    "created_at": time.time(),
                    "type": "guilds",
                    "list": guilds,
                }
                self._ensure_backups_dir()
                name = bot.user.name.lower().replace(" ", "_")
                path = os.path.join(self.backups_dir, f"guilds_{name}.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                self.root.after(0, lambda: self._set_status(f"Guilds backed up ({len(guilds)} servers)"))
                self.root.after(0, self._refresh_backup_list)
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Failed: {e}"))
        self._run_async(_do())

    def _view_backup(self, backup_info):
        data = backup_info["data"]
        display = json.dumps(data, indent=2)
        win = ttk.Toplevel(self.root)
        win.title(f"Backup - {backup_info['name']}")
        win.geometry("500x400")
        win.configure(bg=self.root.style.colors.get("bg"))
        text = ttk.ScrolledText(win, wrap=ttk.WORD, font=("Consolas", 10))
        text.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", display)
        text.configure(state="disabled")

    def _restore_backup(self, backup_info):
        btype = backup_info["type"]
        if btype == "account":
            Messagebox.show_info("Account backups are for reference only.\nNo restore action needed.", title="Restore")
            return
        if btype == "friends":
            result = str(Messagebox.yesno(
                "This will send friend requests to all users in the backup.\n\n"
                "This could result in a ban. Continue?",
                title="Restore Friends"
            )).lower()
            if result != "yes":
                return
            self._pick_account("friends", lambda bot, token: self._do_restore_friends(backup_info, bot, token))
            return
        elif btype == "guilds":
            invites = [g["invite"] for g in backup_info["data"].get("list", []) if g.get("invite") and g["invite"] != "None"]
            if not invites:
                Messagebox.show_info("No invite links found in this backup.", title="Restore Guilds")
                return
            msg = "Join these servers manually:\n\n" + "\n".join(invites)
            win = ttk.Toplevel(self.root)
            win.title("Guild Invites")
            win.geometry("500x350")
            win.configure(bg=self.root.style.colors.get("bg"))
            text = ttk.ScrolledText(win, wrap=ttk.WORD, font=("Consolas", 10))
            text.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
            text.insert("1.0", msg)
            text.configure(state="disabled")

    def _do_restore_friends(self, backup_info, bot, token):
        self._set_status("Restoring friends...")
        async def _do():
            try:
                import requests as _req
                headers = {
                    "Authorization": token,
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                restored = 0
                for entry in backup_info["data"].get("list", []):
                    try:
                        user_resp = _req.get(f"https://discord.com/api/v9/users/{entry['id']}", headers=headers)
                        if user_resp.status_code == 200:
                            user = discord.User(state=bot._connection, data=user_resp.json())
                            user.send_friend_request()
                            restored += 1
                        await asyncio.sleep(1)
                    except Exception:
                        pass
                self.root.after(0, lambda: self._set_status(f"Restored {restored} friend requests"))
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Failed: {e}"))
        self._run_async(_do())

    def _delete_backup(self, backup_info):
        result = str(Messagebox.yesno(
            f"Delete backup '{backup_info['name']}'?",
            title="Delete Backup"
        )).lower()
        if result != "yes":
            return
        try:
            os.remove(backup_info["path"])
            self._set_status(f"Deleted: {backup_info['name']}")
            self._refresh_backup_list()
        except Exception as e:
            self._set_status(f"Delete failed: {e}")

    def _refresh_backup_list(self):
        if not self.backup_list_frame:
            return
        for child in self.backup_list_frame.winfo_children():
            child.destroy()
        self._draw_backup_entries()

    def _draw_backup_entries(self):
        backups = self._get_backups()
        if not backups:
            empty = ttk.Label(self.backup_list_frame,
                              text="No backups yet. Create one above.",
                              font=("Host Grotesk", 11))
            empty.configure(background=self.root.style.colors.get("dark"),
                            foreground=Style.DARK_GREY.value)
            empty.pack(pady=20)
            return

        type_colors = {"account": "#5865f2", "friends": "#4fee4c", "guilds": "#fee75c"}
        for backup in backups:
            card = RoundedFrame(self.backup_list_frame, radius=(8, 8, 8, 8),
                                bootstyle="dark.TFrame")
            card.pack(fill=ttk.X, pady=(0, 5))

            inner = ttk.Frame(card, style="dark.TFrame")
            inner.pack(fill=ttk.BOTH, padx=12, pady=8)

            name_frame = ttk.Frame(inner, style="dark.TFrame")
            name_frame.grid(row=0, column=0, sticky=ttk.W)

            btype = backup.get("type", "unknown")
            color = type_colors.get(btype, Style.LIGHT_GREY.value)
            type_label = ttk.Label(name_frame, text=btype.upper(),
                                   font=("Host Grotesk", 9, "bold"),
                                   foreground=color)
            type_label.configure(background=self.root.style.colors.get("dark"))
            type_label.pack(side=ttk.LEFT, padx=(0, 8))

            name_label = ttk.Label(name_frame, text=backup["name"],
                                   font=("Host Grotesk", 11, "bold"))
            name_label.configure(background=self.root.style.colors.get("dark"))
            name_label.pack(side=ttk.LEFT)

            info_text = self._format_time(backup["created_at"])
            info_label = ttk.Label(inner, text=info_text,
                                   font=("Host Grotesk", 9))
            info_label.configure(background=self.root.style.colors.get("dark"),
                                 foreground=Style.LIGHT_GREY.value)
            info_label.grid(row=1, column=0, sticky=ttk.W)

            btn_frame = ttk.Frame(inner, style="dark.TFrame")
            btn_frame.grid(row=0, column=1, rowspan=2, sticky=ttk.E)

            view_btn = ttk.Label(btn_frame, text="View",
                                 font=("Host Grotesk", 10),
                                 cursor="hand2", foreground="#5865f2")
            view_btn.pack(side=ttk.LEFT, padx=(0, 10))
            view_btn.bind("<Button-1>", lambda e, b=backup: self._view_backup(b))
            view_btn.bind("<Enter>", lambda e, b=view_btn: b.configure(foreground="white"))
            view_btn.bind("<Leave>", lambda e, b=view_btn: b.configure(foreground="#5865f2"))

            restore_btn = ttk.Label(btn_frame, text="Restore",
                                    font=("Host Grotesk", 10, "bold"),
                                    cursor="hand2", foreground="#4fee4c")
            restore_btn.pack(side=ttk.LEFT, padx=(0, 10))
            restore_btn.bind("<Button-1>", lambda e, b=backup: self._restore_backup(b))
            restore_btn.bind("<Enter>", lambda e, b=restore_btn: b.configure(foreground="white"))
            restore_btn.bind("<Leave>", lambda e, b=restore_btn: b.configure(foreground="#4fee4c"))

            delete_btn = ttk.Label(btn_frame, text="Delete",
                                   font=("Host Grotesk", 10),
                                   cursor="hand2", foreground="#ff6464")
            delete_btn.pack(side=ttk.LEFT)
            delete_btn.bind("<Button-1>", lambda e, b=backup: self._delete_backup(b))
            delete_btn.bind("<Enter>", lambda e, b=delete_btn: b.configure(foreground="white"))
            delete_btn.bind("<Leave>", lambda e, b=delete_btn: b.configure(foreground="#ff6464"))

            inner.grid_columnconfigure(0, weight=1)

    def draw_content(self, wrapper):
        create_label = ttk.Label(wrapper, text="Create Backup",
                                 font=("Host Grotesk", 14, "bold"))
        create_label.configure(background=self.root.style.colors.get("dark"))
        create_label.pack(anchor=ttk.W, pady=(0, 5))

        btn_row = ttk.Frame(wrapper, style="dark.TFrame")
        btn_row.pack(fill=ttk.X, pady=(0, 10))

        for text, cmd in [("Account", self._create_backup_account),
                          ("Friends", self._create_backup_friends),
                          ("Guilds", self._create_backup_guilds)]:
            btn_frame = RoundedFrame(btn_row, radius=(8, 8, 8, 8),
                                     bootstyle="dark.TFrame")
            btn_frame.pack(side=ttk.LEFT, padx=(0, 8))

            btn = ttk.Label(btn_frame, text=text,
                            font=("Host Grotesk", 10, "bold"),
                            cursor="hand2", foreground="#5865f2")
            btn.configure(background=self.root.style.colors.get("dark"))
            btn.pack(padx=12, pady=6)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: b.configure(foreground="white"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(foreground="#5865f2"))

        self.status_label = ttk.Label(btn_row, text="",
                                      font=("Host Grotesk", 10))
        self.status_label.configure(background=self.root.style.colors.get("dark"),
                                    foreground=Style.LIGHT_GREY.value)
        self.status_label.pack(side=ttk.RIGHT)

        backups_label = ttk.Label(wrapper, text="Available Backups",
                                  font=("Host Grotesk", 14, "bold"))
        backups_label.configure(background=self.root.style.colors.get("dark"))
        backups_label.pack(anchor=ttk.W, pady=(5, 5))

        self.backup_list_frame = ScrolledFrame(wrapper, bootstyle="dark.TFrame", autohide=True)
        self.backup_list_frame.container.configure(style="dark.TFrame")
        self.backup_list_frame.pack(fill=ttk.BOTH, expand=True)

        self._draw_backup_entries()
