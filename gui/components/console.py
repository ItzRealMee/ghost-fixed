import sys
import ttkbootstrap as ttk
from gui.components.rounded_frame import RoundedFrame
from gui.helpers.images import Images
from gui.helpers.style import Style
from utils.console import get_formatted_time

class Console:
    MAX_LOG_ENTRIES = 500

    def __init__(self, root, bot_controller):
        self.root = root
        self.bot = bot_controller
        self.images = Images()
        
        self.console = []
        self.textarea = None
        self.avatar = None
        self.darwin_font_size = 12
        self.non_darwin_font_size = 12
        
    def update(self):
        if self.textarea is None:
            return
        try:
            self.textarea.delete("1.0", "end")
            
            visible = self.console[-self.MAX_LOG_ENTRIES:] if len(self.console) > self.MAX_LOG_ENTRIES else self.console

            for time, prefix, text in visible:
                if prefix.lower() == "sniper":
                    content = text
                    type_name = content.get("type")
                    title = content.get("title")
                    description = content.get("description")
                    success = content.get("success", True)
                    
                    self.textarea.insert("end", "\n", "log_text")
                    self.textarea.insert("end", f"  {time} ", "timestamp")
                    
                    if success:
                        self.textarea.insert("end", f" {type_name.upper()} ", "prefix_sniper_success")
                    else:
                        self.textarea.insert("end", f" {type_name.upper()} ", "prefix_sniper_fail")
                    
                    self.textarea.insert("end", f"{title}\n", "log_text")
                    
                    for key, value in description.items():
                        self.textarea.insert("end", f"         {key}: ", "sniper_key")
                        self.textarea.insert("end", f"{value}\n", "log_text")
                else:
                    self.textarea.insert("end", f"[{time}] ", "timestamp")
                    self.textarea.insert("end", f"[{prefix}] ", f"prefix_{prefix.lower()}")
                    self.textarea.insert("end", f"{text}\n", "log_text")
            
            self.textarea.yview_moveto(1)
        except:
            pass
            
    def clear(self):
        self.console = []
        try:
            self.textarea.delete("1.0", "end")
        except:
            pass
    
    def add_sniper(self, sniper_obj):
        self.add_log("sniper", sniper_obj)
        self._notify_home_feed(sniper_obj)
    
    def _notify_home_feed(self, sniper_obj):
        try:
            from gui.pages.home import HomePage
            gui = self.bot.gui if hasattr(self.bot, 'gui') else None
            if gui and hasattr(gui, 'home_page'):
                event_type = sniper_obj.get("type", "sniper")
                title = sniper_obj.get("title", "Sniper Event")
                desc_parts = sniper_obj.get("description", {})
                description = "\n".join(f"{k}: {v}" for k, v in desc_parts.items())
                success = "success" not in title.lower() or "failed" not in title.lower()
                gui.home_page._add_notification(
                    f"{event_type.lower()}_snipe",
                    title,
                    description,
                    color="#4fee4c" if success else "#ff6464"
                )
        except Exception:
            pass
    
    def add_log(self, prefix, text):
        time = get_formatted_time()
        self.console.append((time, prefix, text))
        self.update()
        
    def _load_tags(self):
        font_size = self.non_darwin_font_size if sys.platform != "darwin" else self.darwin_font_size
        mono_font = ("JetBrainsMono NF", font_size, "bold")
        
        self.textarea.tag_config("timestamp", foreground=Style.DARK_GREY.value, font=mono_font)
        self.textarea.tag_config("log_text",  foreground=Style.LIGHT_GREY.value, font=mono_font)
        
        self.textarea.tag_config("prefix_sniper",        foreground="red",     font=mono_font)
        self.textarea.tag_config("prefix_sniper_success", foreground="#4fee4c", font=mono_font)
        self.textarea.tag_config("prefix_sniper_fail",   foreground="#ff6464", font=mono_font)
        self.textarea.tag_config("sniper_key",           foreground="#eceb18", font=mono_font)
        self.textarea.tag_config("prefix_command",       foreground="#0b91ff", font=mono_font)
        self.textarea.tag_config("prefix_info",          foreground="#2aefef", font=mono_font)
        self.textarea.tag_config("prefix_success",       foreground="#4fee4c", font=mono_font)
        self.textarea.tag_config("prefix_warning",       foreground="#eceb18", font=mono_font)
        self.textarea.tag_config("prefix_error",         foreground="red",     font=mono_font)
        self.textarea.tag_config("prefix_cli",           foreground="pink",    font=mono_font)
        self.textarea.tag_config("prefix_rpc",           foreground="pink",    font=mono_font)
        self.textarea.tag_config("prefix_captcha",       foreground="#eceb18", font=mono_font)
        self.textarea.tag_config("prefix_nitro",         foreground="#0b91ff", font=mono_font)
    
    def _draw_footer(self, parent):
        """ Draw the footer with user info and clear button. """
        wrapper = RoundedFrame(parent, radius=(0, 0, 15, 15), bootstyle="secondary.TFrame")
        wrapper.pack(fill="both", expand=False)
        
        user = self.bot.get_user()
        
        if self.avatar:
            avatar_label = ttk.Label(wrapper, image=self.avatar)
            avatar_label.configure(background=self.root.style.colors.get("secondary"))
            avatar_label.grid(row=0, column=0, sticky=ttk.W, padx=(10, 5), pady=5)
        
        username = ttk.Label(wrapper, text=f"Logged in as {user.name}" if user else "Failed to get user info...", font=("Host Grotesk", 12, "italic"))
        username.configure(background=self.root.style.colors.get("secondary"))
        username.grid(row=0, column=1, pady=5, sticky="w")
        
        wrapper.grid_columnconfigure(2, weight=1)
        
        clear_btn = ttk.Label(wrapper, image=self.images.get("trash"))
        clear_btn.configure(background=self.root.style.colors.get("secondary"))
        clear_btn.bind("<Button-1>", lambda e: self.clear())
        clear_btn.grid(row=0, column=3, padx=(10, 8), pady=5, sticky="e")

    def _draw_main(self, parent):
        wrapper = RoundedFrame(parent, radius=15, bootstyle="dark.TFrame")
        wrapper.pack(side="top", fill="both", expand=True)

        self.textarea = ttk.Text(wrapper, wrap="word", height=20,
            font=("JetBrainsMono NF", self.non_darwin_font_size if sys.platform != "darwin" else self.darwin_font_size, "bold")
        )
        self.textarea.config(
            border=0,
            background=self.root.style.colors.get("dark"),
            foreground=Style.LIGHT_GREY.value,
            highlightcolor=self.root.style.colors.get("dark"),
            highlightbackground=self.root.style.colors.get("dark"),
            state="normal"
        )

        try:
            self.textarea.bind_all(
                "<Control-c>" if sys.platform != "darwin" else "<Command-c>", 
                lambda _: self.textarea.event_generate("<<Copy>>")
            )
        except:
            pass

        self.textarea.pack(fill="both", expand=True, padx=5, pady=5)
        self._load_tags()

    def draw(self, parent):
        self.avatar = self.bot.get_avatar(size=15, radius=2)
        self._draw_main(parent)
        # if self.bot.running:
        #     self._draw_footer(parent)
        self.update()