import tkinter as tk
import ttkbootstrap as ttk

from gui.components import RoundedFrame
from gui.helpers.style import Style

class DropdownMenu:
    def __init__(self, parent, options, command=None):
        self.parent = parent
        self.options = options
        self.selected_option = ttk.StringVar(value=options[0] if options else "")
        self.command = command
        self.style = None
        self.overlay = None
        self.overlay_canvas = None
        self.overlay_items_frame = None
        self.overlay_canvas_window = None
        self._reposition_after_id = None
        self._mousewheel_bound = False
        self._outside_click_bound = False
        
        # see if parent has root attribute, if so use it to get the style, otherwise get the style from the parent itself
        if hasattr(parent, "root") and parent.root and hasattr(parent.root, "style"):
            self.style = parent.root.style
        elif hasattr(parent, "style"):
            self.style = parent.style
        else:
            raise ValueError("Parent must have a style attribute or a root attribute with a style")
        
    def _hover_enter(self, wrapper, label):
        wrapper.set_background(Style.DROPDOWN_OPTION_HOVER.value)
        label.configure(background=Style.DROPDOWN_OPTION_HOVER.value)
        
    def _hover_leave(self, wrapper, label):
        wrapper.set_background(self.parent.style.colors.get("secondary"))
        label.configure(background=self.parent.style.colors.get("secondary"))
        
    def _rearrange_options(self):
        selected = self.selected_option.get()
        if selected in self.options:
            self.options.remove(selected)
            self.options.insert(0, selected)

    def _close_overlay(self):
        if self._reposition_after_id is not None:
            try:
                self.parent.winfo_toplevel().after_cancel(self._reposition_after_id)
            except Exception:
                pass
        self._reposition_after_id = None

        if self.overlay is not None and self.overlay.winfo_exists():
            self.overlay.destroy()

        self.overlay = None
        self.overlay_canvas = None
        self.overlay_items_frame = None
        self.overlay_canvas_window = None

    def _reposition_overlay(self):
        if self.overlay is None or not self.overlay.winfo_exists() or not self._alive():
            self._reposition_after_id = None
            return

        root = self.parent.winfo_toplevel()
        popup_width = max(self.frame.winfo_width(), 96)
        x = self.frame.winfo_rootx() - root.winfo_rootx()
        y = self.frame.winfo_rooty() - root.winfo_rooty() + self.frame.winfo_height()

        self.overlay.place_configure(x=x, y=y, width=popup_width)
        self._reposition_after_id = root.after(16, self._reposition_overlay)

    def _scroll_overlay(self, delta):
        if self.overlay_canvas is None or not self.overlay_canvas.winfo_exists():
            return

        self.overlay_canvas.yview_scroll(delta, "units")

    def _event_in_overlay(self, widget):
        current = widget
        while current is not None:
            if current is self.overlay:
                return True
            current = getattr(current, "master", None)
        return False

    def _on_mousewheel(self, event):
        if self.overlay is None or not self.overlay.winfo_exists():
            return

        if not self._event_in_overlay(event.widget):
            return

        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1

        self._scroll_overlay(delta)

    def _bind_overlay_scroll(self):
        if self._mousewheel_bound:
            return

        root = self.parent.winfo_toplevel()
        root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        root.bind_all("<Button-4>", self._on_mousewheel, add="+")
        root.bind_all("<Button-5>", self._on_mousewheel, add="+")
        self._mousewheel_bound = True

    def _render_closed_menu(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        label = ttk.Label(self.frame, textvariable=self.selected_option, anchor="w", background=self.parent.style.colors.get("secondary"))
        label.pack(fill=ttk.X, padx=10, pady=5)
        label.bind("<Button-1>", self._toggle_menu)
        self.frame.bind("<Button-1>", self._toggle_menu)

        self.down_arrow = ttk.Label(self.frame, text="▼", background=self.parent.style.colors.get("secondary"), font=("Host Grotesk", 10))
        self.down_arrow.place(relx=1.0, rely=0.5, x=-10, y=0, anchor="e")
        self.down_arrow.bind("<Button-1>", self._toggle_menu)

    def _build_overlay(self):
        self._close_overlay()

        root = self.parent.winfo_toplevel()
        self.overlay = RoundedFrame(
            root,
            radius=8,
            background=self.parent.style.colors.get("secondary"),
            parent_background=self.parent.style.colors.get("secondary"),
        )

        self.overlay_canvas = tk.Canvas(self.overlay, highlightthickness=0, bd=0, background=self.parent.style.colors.get("secondary"))
        self.overlay_canvas.pack(fill=ttk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.overlay, orient="vertical", command=self.overlay_canvas.yview)
        scrollbar.place(relx=1.0, rely=0, relheight=1.0, x=-2, y=0, anchor="ne")
        self.overlay_canvas.configure(yscrollcommand=scrollbar.set)

        self.overlay_items_frame = ttk.Frame(self.overlay_canvas, style="TFrame")
        self.overlay_canvas_window = self.overlay_canvas.create_window((0, 0), window=self.overlay_items_frame, anchor="nw")

        def _sync_scrollregion(_event=None):
            self.overlay_canvas.configure(scrollregion=self.overlay_canvas.bbox("all"))

        def _sync_width(event):
            self.overlay_canvas.itemconfigure(self.overlay_canvas_window, width=event.width)

        self.overlay_items_frame.bind("<Configure>", _sync_scrollregion)
        self.overlay_canvas.bind("<Configure>", _sync_width)

        max_visible_height = 220
        popup_width = max(self.frame.winfo_width(), 96)

        for index, option in enumerate(self.options):
            wrapper = RoundedFrame(self.overlay_items_frame, radius=8, background=self.parent.style.colors.get("secondary"))
            wrapper.pack(fill=ttk.X, padx=5, pady=(4, 5 if index == len(self.options) - 1 else 0))
            wrapper.bind("<Button-1>", lambda e, opt=option: self._on_option_selected(opt))

            label = ttk.Label(wrapper, text=option, background=self.parent.style.colors.get("secondary"), anchor="w")
            label.pack(fill=ttk.X, padx=5, pady=2)
            label.bind("<Button-1>", lambda e, opt=option: self._on_option_selected(opt))

            label.bind("<Enter>", lambda e, w=wrapper, l=label: self._hover_enter(w, l))
            label.bind("<Leave>", lambda e, w=wrapper, l=label: self._hover_leave(w, l))
            wrapper.bind("<Enter>", lambda e, w=wrapper, l=label: self._hover_enter(w, l))
            wrapper.bind("<Leave>", lambda e, w=wrapper, l=label: self._hover_leave(w, l))

        self.overlay.update_idletasks()
        content_height = self.overlay_items_frame.winfo_reqheight()
        popup_height = min(content_height, max_visible_height)
        self.overlay_canvas.configure(height=popup_height)

        x = self.frame.winfo_rootx() - root.winfo_rootx()
        y = self.frame.winfo_rooty() - root.winfo_rooty() + self.frame.winfo_height()
        self.overlay.place(x=x, y=y, width=popup_width, height=popup_height)
        self.overlay.lift()
        self._reposition_overlay()
        self._bind_overlay_scroll()

    def _bind_outside_click(self):
        if self._outside_click_bound:
            return

        self.parent.winfo_toplevel().bind_all("<Button-1>", self._outside_click, add="+")
        self._outside_click_bound = True
        
    def _open_menu(self, event):
        if not self._alive():
            return
        
        self._rearrange_options()
        self._build_overlay()
        self._bind_outside_click()

    def _toggle_menu(self, event):
        if not self._alive():
            return

        if self.overlay is not None and self.overlay.winfo_exists():
            self._close_menu()
            return

        self._open_menu(event)
        
    def _close_menu(self):
        if not self._alive():
            return
        
        self._close_overlay()
        self._render_closed_menu()
        
    def _on_option_selected(self, option):
        if not self._alive():
            return

        self.selected_option.set(option)
        if self.command:
            self.command(option)

        self._close_menu()
        
    def _outside_click(self, event):
        if not self._alive() or self.overlay is None or not self.overlay.winfo_exists():
            return
        if self.overlay.winfo_containing(event.x_root, event.y_root):
            return

        if self.frame.winfo_containing(event.x_root, event.y_root):
            return

        self._close_menu()
        
    def draw(self):
        self.frame = RoundedFrame(self.parent, radius=5, bootstyle="secondary.TFrame")
        self._render_closed_menu()

        return self.frame
    
    def value(self):
        return self.selected_option.get()
    
    def set_selected(self, option):
        if option in self.options:
            self.selected_option.set(option)
            if self._alive():
                self._close_menu()
    
    def destroy(self):
        self._close_overlay()
        if self._alive():
            self.frame.destroy()
        
    def _alive(self):
        return hasattr(self, "frame") and self.frame.winfo_exists()
