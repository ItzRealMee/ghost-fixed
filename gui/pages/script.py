import sys
import os
import tkinter
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from utils.files import get_application_support
from gui.helpers.images import Images
from gui.helpers.style import Style


class ScriptPage:
    def __init__(self, root, script):
        self.gui = root
        self.root = root.root
        self.script = script
        self.images = Images()
        self.text_widget = None
        self.line_numbers = None
        self._dirty = False
        self._script_path = os.path.join(get_application_support(), "scripts", self.script)
        self._original_content = ""
        self._title_label = None
        self._status_label = None

    def _go_back(self):
        if self._dirty:
            result = str(Messagebox.yesnocancel(
                "You have unsaved changes. Do you want to save before leaving?",
                title="Unsaved Changes"
            )).lower()
            if result == "yes":
                self._save_script()
            elif result == "cancel":
                return
        self.gui.draw_scripts()

    def _get_script_content(self):
        try:
            with open(self._script_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"# Error reading script: {e}\n"

    def _save_script(self):
        try:
            content = self.text_widget.get("1.0", "end-1c") if self.text_widget else ""
            with open(self._script_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._original_content = content
            self._dirty = False
            self._update_title()
            self._show_save_status("Saved")
        except Exception as e:
            Messagebox.show_error(f"Failed to save: {e}", title="Save Error")

    def _reload_script(self):
        if self._dirty:
            result = str(Messagebox.yesno(
                "Discard unsaved changes and reload?",
                title="Reload Script"
            )).lower()
            if result != "yes":
                return
        content = self._get_script_content()
        self._set_content(content)
        self._original_content = content
        self._dirty = False
        self._update_title()

    def _new_script(self):
        if self._dirty:
            result = str(Messagebox.yesno(
                "Discard unsaved changes to create a new script?",
                title="New Script"
            )).lower()
            if result != "yes":
                return
        self.gui.draw_scripts()
        self.gui.scripts_page._create_script()

    def _set_content(self, content):
        if self.text_widget:
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", content)
            self._refresh_line_numbers()

    def _on_change(self, event=None):
        if not self.text_widget:
            return
        try:
            self.text_widget.edit_modified(False)
        except Exception:
            pass
        content = self.text_widget.get("1.0", "end-1c")
        self._dirty = content != self._original_content
        self._update_title()
        self.root.after(1, self._refresh_line_numbers)

    def _refresh_line_numbers(self):
        if not self.line_numbers or not self.text_widget:
            return
        try:
            self.line_numbers.config(state="normal")
            self.line_numbers.delete("1.0", "end")
            count = self.text_widget.index("end-1c").split(".")[0]
            self.line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, int(count) + 1)))
            self.line_numbers.config(state="disabled")
        except Exception:
            pass

    def _sync_scroll(self, *args):
        if self.line_numbers:
            self.line_numbers.yview_moveto(args[0])

    def _update_title(self):
        if self._title_label:
            self._title_label.configure(text=f"{self.script} {'*' if self._dirty else ''}")

    def _show_save_status(self, text):
        if self._status_label:
            self._status_label.configure(text=text)
            self.root.after(2000, lambda: self._status_label.configure(text="") if self._status_label.winfo_exists() else None)

    def _draw_header(self, parent):
        wrapper = ttk.Frame(parent)

        back = ttk.Label(wrapper, image=self.images.get("left-chevron"), cursor="hand2")
        back.grid(row=0, column=0, sticky=ttk.W, padx=(0, 10))
        back.bind("<Button-1>", lambda e: self._go_back())

        self._title_label = ttk.Label(wrapper, text=self.script, font=("Host Grotesk", 16, "bold"))
        self._title_label.grid(row=0, column=1, sticky=ttk.W)

        self._status_label = ttk.Label(wrapper, text="", font=("Host Grotesk", 11), foreground="#4fee4c")
        self._status_label.grid(row=0, column=2, sticky=ttk.W, padx=(10, 0))

        toolbar = ttk.Frame(wrapper)
        for i, (label, cmd) in enumerate([("Save", self._save_script), ("Reload", self._reload_script), ("New", self._new_script)]):
            btn = ttk.Label(toolbar, text=label, font=("Host Grotesk", 11), style="secondary.TLabel", cursor="hand2")
            btn.configure(foreground=Style.LIGHT_GREY.value)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: b.configure(foreground="white"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(foreground=Style.LIGHT_GREY.value))
            btn.grid(row=0, column=i, padx=(0, 8) if i < 2 else 0)
        toolbar.grid(row=0, column=3, sticky=ttk.E, padx=(15, 0))
        wrapper.columnconfigure(2, weight=1)
        return wrapper

    def draw(self, parent):
        header = self._draw_header(parent)
        header.pack(fill=ttk.X, pady=(0, 10))

        content = self._get_script_content()
        bg = self.root.style.colors.get("dark")
        fg = Style.LIGHT_GREY.value
        font_size = 10 if sys.platform != "darwin" else 12
        mono = ("JetBrainsMono NF", font_size)

        gutter_bg = "#181820"
        shared_opts = dict(
            font=mono, bd=0, highlightthickness=0, wrap="none",
            spacing1=0, spacing2=0, spacing3=0, padx=0, pady=0,
        )

        self.line_numbers = tkinter.Text(
            parent, width=4, state="disabled", cursor="arrow",
            bg=gutter_bg, fg="#4a4a5e",
            selectbackground=gutter_bg, takefocus=False,
            **shared_opts,
        )
        self.line_numbers.pack(side="left", fill="y", pady=5)
        self.line_numbers.config(padx=8)

        sep = ttk.Frame(parent, width=1)
        sep.pack(side="left", fill="y", pady=5)

        self.text_widget = tkinter.Text(
            parent, undo=True, autoseparators=True, maxundo=-1,
            bg=bg, fg=fg, insertbackground="white",
            selectbackground="#3d3d5c",
            **shared_opts,
        )
        self.text_widget.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)
        self.text_widget.config(padx=8)

        v_scroll = ttk.Scrollbar(parent, orient="vertical",
            command=lambda *a: (self.text_widget.yview(*a), self.line_numbers.yview(*a)))
        v_scroll.pack(side="right", fill="y", pady=5)
        self.text_widget.config(yscrollcommand=lambda *a: (v_scroll.set(*a), self.line_numbers.yview_moveto(a[0])))

        self.text_widget.insert("1.0", content)
        self.text_widget.mark_set("insert", "1.0")
        self.text_widget.edit_reset()
        self.text_widget.edit_modified(False)
        self._original_content = content
        self._refresh_line_numbers()

        self.text_widget.bind("<<Modified>>", self._on_change)
        self.text_widget.bind("<Key>", lambda e: self.root.after(50, self._on_change))
        self.text_widget.bind("<MouseWheel>", lambda e: self.root.after(1, self._refresh_line_numbers))
        self.text_widget.bind("<Control-s>", lambda e: self._save_script())
        self.text_widget.bind("<Control-r>", lambda e: self._reload_script())

        parent.bind("<Button-1>", lambda e: self.text_widget.focus_set())
        self.text_widget.focus_set()
