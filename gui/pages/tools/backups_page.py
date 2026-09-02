import os
import sys
import time
import shutil
import zipfile
import threading
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

from gui.components import ToolPage, RoundedFrame, RoundedSwitch
from gui.helpers import Style
from gui.helpers.images import Images
from utils.files import get_application_support, get_config_path, get_scripts_path, get_themes_path, get_data_path


class BackupsPage(ToolPage):
    def __init__(self, toolspage, root, bot_controller, images, layout):
        super().__init__(toolspage, root, bot_controller, images, layout, title="Backups", frame=None)
        self.images = images
        self.cfg = bot_controller.cfg
        self.backups_dir = os.path.join(get_application_support(), "backups")
        self.backup_list_frame = None
        self._backup_frames = []
        self.status_label = None
        self._progress_label = None

    def _ensure_backups_dir(self):
        os.makedirs(self.backups_dir, exist_ok=True)

    def _get_backups(self):
        self._ensure_backups_dir()
        backups = []
        for f in os.listdir(self.backups_dir):
            if f.endswith(".zip"):
                path = os.path.join(self.backups_dir, f)
                stat = os.stat(path)
                backups.append({
                    "name": f,
                    "path": path,
                    "size": stat.st_size,
                    "time": stat.st_mtime,
                })
        backups.sort(key=lambda b: b["time"], reverse=True)
        return backups

    def _format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _format_time(self, timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    def _create_backup(self):
        self._ensure_backups_dir()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"ghost_backup_{timestamp}.zip"
        backup_path = os.path.join(self.backups_dir, backup_name)

        self._set_status("Creating backup...")

        def _do_backup():
            try:
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    config_path = get_config_path()
                    if os.path.exists(config_path):
                        zf.write(config_path, "config.json")

                    scripts_dir = get_scripts_path()
                    if os.path.exists(scripts_dir):
                        for root_dir, dirs, files in os.walk(scripts_dir):
                            for file in files:
                                file_path = os.path.join(root_dir, file)
                                arcname = os.path.relpath(file_path, get_application_support())
                                zf.write(file_path, arcname)

                    themes_dir = get_themes_path()
                    if os.path.exists(themes_dir):
                        for root_dir, dirs, files in os.walk(themes_dir):
                            for file in files:
                                file_path = os.path.join(root_dir, file)
                                arcname = os.path.relpath(file_path, get_application_support())
                                zf.write(file_path, arcname)

                    data_dir = get_data_path()
                    if os.path.exists(data_dir):
                        for item in os.listdir(data_dir):
                            if item in ("cache", "surveillance"):
                                continue
                            item_path = os.path.join(data_dir, item)
                            if os.path.isfile(item_path):
                                arcname = os.path.relpath(item_path, get_application_support())
                                zf.write(item_path, arcname)

                self.root.after(0, lambda: self._set_status(f"Backup created: {backup_name}"))
                self.root.after(0, self._refresh_backup_list)
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Backup failed: {e}"))

        threading.Thread(target=_do_backup, daemon=True).start()

    def _restore_backup(self, backup_info):
        result = str(Messagebox.yesno(
            f"Restoring '{backup_info['name']}' will replace your current configuration, scripts, and themes.\n\n"
            "A safety backup of your current data will be created first.\n\n"
            "Do you want to continue?",
            title="Restore Backup"
        )).lower()

        if result != "yes":
            return

        self._set_status("Creating safety backup before restore...")

        def _do_restore():
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                safety_name = f"ghost_pre_restore_{timestamp}.zip"
                safety_path = os.path.join(self.backups_dir, safety_name)
                with zipfile.ZipFile(safety_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    config_path = get_config_path()
                    if os.path.exists(config_path):
                        zf.write(config_path, "config.json")
                    scripts_dir = get_scripts_path()
                    if os.path.exists(scripts_dir):
                        for root_dir, dirs, files in os.walk(scripts_dir):
                            for file in files:
                                file_path = os.path.join(root_dir, file)
                                arcname = os.path.relpath(file_path, get_application_support())
                                zf.write(file_path, arcname)
                    themes_dir = get_themes_path()
                    if os.path.exists(themes_dir):
                        for root_dir, dirs, files in os.walk(themes_dir):
                            for file in files:
                                file_path = os.path.join(root_dir, file)
                                arcname = os.path.relpath(file_path, get_application_support())
                                zf.write(file_path, arcname)

                with zipfile.ZipFile(backup_info['path'], 'r') as zf:
                    zf.extractall(get_application_support())

                self.root.after(0, lambda: self._set_status(f"Restored: {backup_info['name']}"))
                self.root.after(0, self._refresh_backup_list)
            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"Restore failed: {e}"))

        threading.Thread(target=_do_restore, daemon=True).start()

    def _delete_backup(self, backup_info):
        result = str(Messagebox.yesno(
            f"Delete backup '{backup_info['name']}'?",
            title="Delete Backup"
        )).lower()

        if result != "yes":
            return

        try:
            os.remove(backup_info['path'])
            self._set_status(f"Deleted: {backup_info['name']}")
            self._refresh_backup_list()
        except Exception as e:
            self._set_status(f"Delete failed: {e}")

    def _set_status(self, text):
        if self.status_label:
            self.status_label.configure(text=text)

    def _refresh_backup_list(self):
        for frame_info in self._backup_frames:
            if frame_info["frame"].winfo_exists():
                frame_info["frame"].destroy()
        self._backup_frames.clear()
        self._draw_backup_entries()

    def _draw_backup_entries(self):
        backups = self._get_backups()

        if not backups:
            empty_label = ttk.Label(self.backup_list_frame,
                                    text="No backups yet. Create one above.",
                                    font=("Host Grotesk", 11))
            empty_label.configure(background=self.root.style.colors.get("dark"),
                                foreground=Style.DARK_GREY.value)
            empty_label.pack(pady=20)
            return

        for backup in backups:
            card = RoundedFrame(self.backup_list_frame, radius=(8, 8, 8, 8),
                               bootstyle="dark.TFrame")
            card.pack(fill=ttk.X, pady=(0, 5))

            inner = ttk.Frame(card, style="dark.TFrame")
            inner.pack(fill=ttk.BOTH, padx=12, pady=8)

            name_label = ttk.Label(inner, text=backup["name"],
                                   font=("Host Grotesk", 11, "bold"))
            name_label.configure(background=self.root.style.colors.get("dark"))
            name_label.grid(row=0, column=0, sticky=ttk.W)

            info_text = f"{self._format_size(backup['size'])}  |  {self._format_time(backup['time'])}"
            info_label = ttk.Label(inner, text=info_text,
                                   font=("Host Grotesk", 9))
            info_label.configure(background=self.root.style.colors.get("dark"),
                               foreground=Style.LIGHT_GREY.value)
            info_label.grid(row=1, column=0, sticky=ttk.W)

            btn_frame = ttk.Frame(inner, style="dark.TFrame")
            btn_frame.grid(row=0, column=1, rowspan=2, sticky=ttk.E)

            restore_btn = ttk.Label(btn_frame, text="Restore",
                                    font=("Host Grotesk", 10, "bold"),
                                    cursor="hand2")
            restore_btn.configure(foreground="#4fee4c")
            restore_btn.pack(side=ttk.LEFT, padx=(0, 10))
            restore_btn.bind("<Button-1>", lambda e, b=backup: self._restore_backup(b))
            restore_btn.bind("<Enter>", lambda e: restore_btn.configure(foreground="white"))
            restore_btn.bind("<Leave>", lambda e: restore_btn.configure(foreground="#4fee4c"))

            delete_btn = ttk.Label(btn_frame, text="Delete",
                                   font=("Host Grotesk", 10),
                                   cursor="hand2")
            delete_btn.configure(foreground="#ff6464")
            delete_btn.pack(side=ttk.LEFT)
            delete_btn.bind("<Button-1>", lambda e, b=backup: self._delete_backup(b))
            delete_btn.bind("<Enter>", lambda e: delete_btn.configure(foreground="white"))
            delete_btn.bind("<Leave>", lambda e: delete_btn.configure(foreground="#ff6464"))

            inner.grid_columnconfigure(0, weight=1)

            self._backup_frames.append({"frame": card, "backup": backup})

    def draw_content(self, wrapper):
        create_btn_frame = RoundedFrame(wrapper, radius=(10, 10, 10, 10),
                                        bootstyle="primary.TFrame")
        create_btn_frame.pack(fill=ttk.X, pady=(0, 10))

        create_inner = ttk.Frame(create_btn_frame, style="primary.TFrame")
        create_inner.pack(fill=ttk.BOTH, padx=12, pady=8)

        create_label = ttk.Label(create_inner, text="Create New Backup",
                                font=("Host Grotesk", 12, "bold"),
                                cursor="hand2")
        create_label.configure(background=self.root.style.colors.get("primary"))
        create_label.pack(side=ttk.LEFT)
        create_label.bind("<Button-1>", lambda e: self._create_backup())
        create_btn_frame.bind("<Button-1>", lambda e: self._create_backup())

        self.status_label = ttk.Label(create_inner, text="",
                                      font=("Host Grotesk", 10))
        self.status_label.configure(background=self.root.style.colors.get("primary"),
                                  foreground="#ffffff")
        self.status_label.pack(side=ttk.RIGHT)

        backup_label = ttk.Label(wrapper, text="Available Backups",
                                 font=("Host Grotesk", 14, "bold"))
        backup_label.configure(background=self.root.style.colors.get("dark"))
        backup_label.pack(anchor=ttk.W, pady=(5, 5))

        self.backup_list_frame = ScrolledFrame(wrapper, bootstyle="dark.TFrame", autohide=True)
        self.backup_list_frame.container.configure(style="dark.TFrame")
        self.backup_list_frame.pack(fill=ttk.BOTH, expand=True)

        self._draw_backup_entries()
