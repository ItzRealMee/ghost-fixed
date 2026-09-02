import sys
import os
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from utils.files import get_application_support
from gui.helpers.images import Images
from gui.helpers.style import Style, get_current_theme_str
from gui.components.rounded_frame import RoundedFrame

try:
    from cupcake import Editor, Languages
    HAS_CUPCAKE = True
except ImportError:
    HAS_CUPCAKE = False


class ScriptPage:
    def __init__(self, root, script):
        self.gui = root
        self.root = root.root
        self.script = script
        self.images = Images()
        self.editor = None
        self.text_widget = None
        self.linenumbers = None
        self.text_scrollbar = None
        self._dirty = False
        self._script_path = os.path.join(get_application_support(), "scripts", self.script)
        self._original_content = ""
        self._title_label = None

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
            with open(self._script_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            return f"# Error reading script: {e}\n"

    def _save_script(self):
        try:
            content = self._get_editor_content()
            with open(self._script_path, "w", encoding="utf-8") as file:
                file.write(content)
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
        self._set_editor_content(content)
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

    def _get_editor_content(self):
        if HAS_CUPCAKE and self.editor:
            return self.editor.content.get("1.0", "end-1c")
        elif self.text_widget:
            return self.text_widget.get("1.0", "end-1c")
        return ""

    def _set_editor_content(self, content):
        if HAS_CUPCAKE and self.editor:
            self.editor.content.delete("1.0", "end")
            self.editor.content.insert("1.0", content)
        elif self.text_widget:
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", content)

    def _on_content_change(self, event=None):
        content = self._get_editor_content()
        self._dirty = content != self._original_content
        self._update_title()

    def _update_title(self):
        if self._title_label:
            dirty_marker = " *" if self._dirty else ""
            self._title_label.configure(text=f"{self.script}{dirty_marker}")

    def _show_save_status(self, text):
        if hasattr(self, "_status_label") and self._status_label:
            self._status_label.configure(text=text)
            self.root.after(2000, lambda: self._status_label.configure(text=""))

    def _draw_header(self, parent):
        wrapper = ttk.Frame(parent)

        back_button = ttk.Label(wrapper, image=self.images.get("left-chevron"))
        back_button.grid(row=0, column=0, sticky=ttk.W, padx=(0, 10))
        back_button.bind("<Button-1>", lambda e: self._go_back())
        back_button.bind("<Enter>", lambda e: back_button.configure(foreground=Style.LIGHT_GREY.value))
        back_button.bind("<Leave>", lambda e: back_button.configure(foreground=""))

        self._title_label = ttk.Label(wrapper, text=self.script, font=("Host Grotesk", 16, "bold"))
        self._title_label.grid(row=0, column=1, sticky=ttk.W)

        self._status_label = ttk.Label(wrapper, text="", font=("Host Grotesk", 11))
        self._status_label.configure(foreground="#4fee4c")
        self._status_label.grid(row=0, column=2, sticky=ttk.W, padx=(10, 0))

        toolbar = ttk.Frame(wrapper, style="dark.TFrame")

        save_btn = self._make_tool_button(toolbar, "Save", self._save_script)
        save_btn.grid(row=0, column=0, padx=(0, 5))

        reload_btn = self._make_tool_button(toolbar, "Reload", self._reload_script)
        reload_btn.grid(row=0, column=1, padx=(0, 5))

        new_btn = self._make_tool_button(toolbar, "New", self._new_script)
        new_btn.grid(row=0, column=2)

        toolbar.grid(row=0, column=3, sticky=ttk.E, padx=(15, 0))

        wrapper.columnconfigure(2, weight=1)

        return wrapper

    def _make_tool_button(self, parent, text, command):
        btn = ttk.Label(
            parent,
            text=text,
            font=("Host Grotesk", 11),
            style="secondary.TLabel",
            cursor="hand2"
        )
        btn.configure(foreground=Style.LIGHT_GREY.value)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(foreground="white"))
        btn.bind("<Leave>", lambda e: btn.configure(foreground=Style.LIGHT_GREY.value))
        return btn

    def draw(self, parent):
        header = self._draw_header(parent)
        header.pack(fill=ttk.X, pady=(0, 10))

        editor_wrapper = RoundedFrame(parent, radius=(15, 15, 15, 15), bootstyle="dark.TFrame")
        editor_wrapper.pack(fill=ttk.BOTH, expand=True)

        if HAS_CUPCAKE:
            self.editor = Editor(
                editor_wrapper,
                language=Languages.PYTHON,
                darkmode=True,
                font=("JetBrainsMono NF Regular", 10 if sys.platform != "darwin" else 12),
                path=self._script_path,
                showpath=False
            )
            self.editor.pack(fill=ttk.BOTH, expand=True)
            content = self._get_script_content()
            self.editor.content.insert("1.0", content)
            self._original_content = content
            self.editor.content.bind("<<Modified>>", self._on_content_change)
            self.editor.content.bind("<Key>", lambda e: self.root.after(50, self._on_content_change))
        else:
            self._draw_fallback_editor(editor_wrapper)

    def _draw_fallback_editor(self, parent):
        content = self._get_script_content()

        self.text_widget = ttk.Text(
            parent,
            wrap="none",
            font=("JetBrainsMono NF", 10 if sys.platform != "darwin" else 12),
            undo=True,
            autoseparators=True,
            maxundo=-1,
        )
        self.text_widget.configure(
            border=0,
            background=self.root.style.colors.get("dark"),
            foreground=Style.LIGHT_GREY.value,
            insertbackground="white",
            highlightcolor=self.root.style.colors.get("dark"),
            highlightbackground=self.root.style.colors.get("dark"),
            selectbackground="#3d3d5c",
        )

        v_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.text_widget.yview)
        h_scroll = ttk.Scrollbar(parent, orient="horizontal", command=self.text_widget.xview)
        self.text_widget.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.text_widget.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.text_widget.insert("1.0", content)
        self.text_widget.mark_set("insert", "1.0")
        self.text_widget.edit_reset()
        self.text_widget.edit_modified(False)
        self._original_content = content

        self.text_widget.bind("<<Modified>>", self._on_content_change)
        self.text_widget.bind("<Key>", lambda e: self.root.after(50, self._on_content_change))

        self.text_widget.bind("<Control-s>", lambda e: self._save_script())
        self.text_widget.bind("<Control-r>", lambda e: self._reload_script())

        self.text_widget.focus_set()
