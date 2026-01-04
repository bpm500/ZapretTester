import sys
import os
import subprocess
import threading
import time
import psutil
import json
import winreg
import ctypes
from pathlib import Path
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import queue
import math
from PIL import Image, ImageTk, ImageDraw
import pystray
from pystray import MenuItem as item
import ping3


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class ZapretTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Zapret Tester")
        self.root.geometry("420x600")
        self.root.configure(bg='#0a0a0a')
        

        self.root.withdraw()
        
   
        icon_path = resource_path("1.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
                self.app_icon = icon_path
            except:
                self.app_icon = None
        else:
            self.app_icon = None
        
  
        self.process = None
        self.current_bat = None
        self.is_connected = False
        self.bat_files = []
        self.zapret_dir = self.find_zapret_dir()
        self.console_queue = queue.Queue()
        self.testing = False
        self.stop_testing = False 
        self.test_thread = None  
        self.tray_icon = None
        self.in_tray = False
        self.auto_connect_enabled = False
        self.auto_start_enabled = False
        self.tray_menu_items = []
        
    
        self.settings_file = self.zapret_dir.parent / "zapret_settings.json"
        self.load_settings()
        
     
        self.font_normal = ("Times New Roman", 10)
        self.font_bold = ("Times New Roman", 10, "bold")
        self.font_title = ("Times New Roman", 14, "bold")
        self.font_status = ("Times New Roman", 16, "bold")
        

        self.load_images()
        

        self.interfaces()
        

        self.load_bat_files()
        
  
        self.process_console_queue()
        
    
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        

        if self.auto_connect_enabled and self.current_bat:
            self.root.after(1000, self.auto_connect)
        

        self.root.deiconify()
        self.center_window()
        

        self.check_connection_state()
    
    def find_zapret_dir(self) -> Path:
        app_dir = Path(sys.executable).parent if hasattr(sys, 'frozen') else Path(__file__).parent
        zapret_path = app_dir / "zapret"
        
        if not zapret_path.exists():
            zapret_path.mkdir(exist_ok=True)
            
        for item in zapret_path.iterdir():
            if item.is_dir():
                return item
        
        return zapret_path
    
    def load_images(self):
        """Загружает изображения из файлов"""
        try:
 
            on_path = resource_path("on.png")
            off_path = resource_path("off.png")
            
            if os.path.exists(on_path) and os.path.exists(off_path):

                on_img = Image.open(on_path)
                off_img = Image.open(off_path)
                
      
                if on_img.size != (216, 216):
                    on_img = on_img.resize((216, 216), Image.Resampling.LANCZOS)
                if off_img.size != (216, 216):
                    off_img = off_img.resize((216, 216), Image.Resampling.LANCZOS)
                
                self.power_icon_on = ImageTk.PhotoImage(on_img)
                self.power_icon_off = ImageTk.PhotoImage(off_img)
            else:
           
                self.create_images()
        except:
      
            self.create_images()
    
    def create_images(self):
        
        try:
          
            circle_size = 216
            icon_size = 80
            
     
            img_off = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
            draw_off = ImageDraw.Draw(img_off)
            
       
            for i in range(4):
                offset = i * 0.5
                draw_off.ellipse([offset, offset, circle_size-1-offset, circle_size-1-offset], 
                               fill='white', outline='white', width=1)
            
         
            icon_x = (circle_size - icon_size) // 2
            icon_y = (circle_size - icon_size) // 2
            
    
            for i in range(3):
                offset = i * 0.5
                draw_off.ellipse([icon_x+offset, icon_y+offset, icon_x+icon_size-1-offset, icon_y+icon_size-1-offset], 
                               fill='black', outline='black', width=1)
            
   
            center_x = circle_size // 2
            center_y = circle_size // 2
            
           
            triangle_size = 25
            points = [
                (center_x, center_y - triangle_size//2),
                (center_x - triangle_size//2, center_y + triangle_size//3),
                (center_x + triangle_size//2, center_y + triangle_size//3)
            ]
            
            draw_off.polygon(points, fill='white', outline='white')
            
          
            rect_width = 6
            rect_height = 15
            draw_off.rectangle([
                center_x - rect_width//2, center_y + triangle_size//3,
                center_x + rect_width//2, center_y + triangle_size//3 + rect_height
            ], fill='white', outline='white')
            
            self.power_icon_off = ImageTk.PhotoImage(img_off)
            
       
            img_on = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
            draw_on = ImageDraw.Draw(img_on)
            
      
            for i in range(4):
                offset = i * 0.5
                draw_on.ellipse([offset, offset, circle_size-1-offset, circle_size-1-offset], 
                              fill='#666666', outline='#666666', width=1)
            
       
            for i in range(3):
                offset = i * 0.5
                draw_on.ellipse([icon_x+offset, icon_y+offset, icon_x+icon_size-1-offset, icon_y+icon_size-1-offset], 
                              fill='white', outline='white', width=1)
            
          
            draw_on.polygon(points, fill='black', outline='black')
            draw_on.rectangle([
                center_x - rect_width//2, center_y + triangle_size//3,
                center_x + rect_width//2, center_y + triangle_size//3 + rect_height
            ], fill='black', outline='black')
            
            self.power_icon_on = ImageTk.PhotoImage(img_on)
            
        except Exception as e:
            print(f"Image error: {e}")
            self.power_icon_off = None
            self.power_icon_on = None
    
    def check_connection_state(self):
      
        if self.is_winws_running():
            self.is_connected = True
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Connected", fg='#28a745')
            if hasattr(self, 'connect_btn') and self.power_icon_on:
                self.connect_btn.config(image=self.power_icon_on)
            self.append_to_console("Detected active connection", "yellow")
    
    def is_winws_running(self):
        
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] and 'winws' in proc.info['name'].lower():
                    return True
            return False
        except:
            return False
    
    def load_settings(self):
        
        default_settings = {
            "last_bat": None,
            "auto_connect": False,
            "auto_start": False
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.current_bat = settings.get("last_bat")
                    self.auto_connect_enabled = settings.get("auto_connect", False)
                    self.auto_start_enabled = settings.get("auto_start", False)
                    
                    
                    self.update_auto_start()
            except:
                self.current_bat = None
                self.auto_connect_enabled = False
                self.auto_start_enabled = False
        else:
            self.current_bat = None
            self.auto_connect_enabled = False
            self.auto_start_enabled = False
    
    def save_settings(self):
    
        settings = {
            "last_bat": self.current_bat,
            "auto_connect": self.auto_connect_enabled,
            "auto_start": self.auto_start_enabled
        }
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def update_auto_start(self):
     
        try:
           
            startup_path = os.path.join(os.getenv('APPDATA'), 
                                      'Microsoft', 'Windows', 'Start Menu', 
                                      'Programs', 'Startup', 'ZapretTester.lnk')
            
            if self.auto_start_enabled:
        
                if hasattr(sys, 'frozen'):
                    exe_path = sys.executable
                else:
                    exe_path = sys.argv[0]
                
              
                vbs_script = f"""
Set shell = CreateObject("WScript.Shell")
Set shortcut = shell.CreateShortcut("{startup_path}")
shortcut.TargetPath = "{exe_path}"
shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"
shortcut.Save
"""
                
                vbs_file = self.zapret_dir.parent / "create_shortcut.vbs"
                with open(vbs_file, 'w') as f:
                    f.write(vbs_script)
                
                subprocess.run(['wscript.exe', str(vbs_file)], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
                
                try:
                    os.remove(vbs_file)
                except:
                    pass
                    
            else:
    
                if os.path.exists(startup_path):
                    os.remove(startup_path)
                    
        except Exception as e:
            print(f"Auto-start error: {e}")
    
    def interfaces(self):

        self.main_container = tk.Frame(self.root, bg='#0a0a0a')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.create_custom_tabs()
        

        self.content_container = tk.Frame(self.main_container, bg='#0a0a0a')
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
  
        self.connect_frame = None
        self.settings_frame = None
        
        self.show_connect_tab()
    
    def create_custom_tabs(self):

        tabs_frame = tk.Frame(self.main_container, bg='#1a1a1a', height=50)
        tabs_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        tabs_frame.pack_propagate(False)
        
        tk.Frame(tabs_frame, bg='#333', height=1).pack(fill=tk.X)
        
        self.tabs_buttons_frame = tk.Frame(tabs_frame, bg='#1a1a1a')
        self.tabs_buttons_frame.pack(fill=tk.BOTH, expand=True, padx=1)
        
        self.connect_tab_btn = tk.Button(self.tabs_buttons_frame,
                                        text="Connect",
                                        font=self.font_bold,
                                        bg='#2a2a2a',
                                        fg='#d0d0d0',
                                        activebackground='#2a2a2a',
                                        activeforeground='#d0d0d0',
                                        relief='flat',
                                        borderwidth=0,
                                        padx=40,
                                        pady=15,
                                        cursor='hand2',
                                        command=self.show_connect_tab)
        self.connect_tab_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Frame(self.tabs_buttons_frame, bg='#333', width=1).pack(side=tk.LEFT, fill=tk.Y, padx=0)
        
        self.settings_tab_btn = tk.Button(self.tabs_buttons_frame,
                                         text="Settings",
                                         font=self.font_bold,
                                         bg='#1a1a1a',
                                         fg='#8a8a8a',
                                         activebackground='#2a2a2a',
                                         activeforeground='#d0d0d0',
                                         relief='flat',
                                        borderwidth=0,
                                        padx=40,
                                        pady=15,
                                        cursor='hand2',
                                        command=self.show_settings_tab)
        self.settings_tab_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Frame(tabs_frame, bg='#333', height=1).pack(fill=tk.X, side=tk.BOTTOM)
    
    def show_connect_tab(self):
      
        self.connect_tab_btn.config(bg='#2a2a2a', fg='#d0d0d0')
        self.settings_tab_btn.config(bg='#1a1a1a', fg='#8a8a8a')
        
        if self.settings_frame:
            self.settings_frame.pack_forget()
        
        if not self.connect_frame:
            self.connect_frame = tk.Frame(self.content_container, bg='#0a0a0a')
            self.setup_connect_tab()
        
        self.connect_frame.pack(fill=tk.BOTH, expand=True)
    
    def show_settings_tab(self):
 
        self.settings_tab_btn.config(bg='#2a2a2a', fg='#d0d0d0')
        self.connect_tab_btn.config(bg='#1a1a1a', fg='#8a8a8a')
        
        if self.connect_frame:
            self.connect_frame.pack_forget()
        
        if not self.settings_frame:
            self.settings_frame = tk.Frame(self.content_container, bg='#0a0a0a')
            self.setup_settings_tab()
        
        self.settings_frame.pack(fill=tk.BOTH, expand=True)
    
    def setup_connect_tab(self):
   
        center_frame = tk.Frame(self.connect_frame, bg='#0a0a0a')
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
 
        if self.power_icon_off:
            self.connect_btn = tk.Label(center_frame,
                                      image=self.power_icon_off,
                                      bg='#0a0a0a',
                                      cursor='hand2')
            self.connect_btn.pack(pady=(0, 30))
            self.connect_btn.bind('<Button-1>', lambda e: self.toggle_connection())
        else:
  
            self.connect_canvas = tk.Canvas(center_frame, 
                                          width=216, 
                                          height=216, 
                                          bg='#0a0a0a',
                                          highlightthickness=0)
            self.connect_canvas.pack(pady=(0, 30))
            
            self.circle_id = self.connect_canvas.create_oval(0, 0, 215, 215,
                                                           fill='white',
                                                           outline='',
                                                           width=0)
            
            center = 108
            self.connect_canvas.create_text(center, center,
                                          text="●",
                                          font=("Arial", 72, "bold"),
                                          fill='black')
            
            self.connect_canvas.bind('<Button-1>', lambda e: self.toggle_connection())
        

        self.status_label = tk.Label(center_frame,
                                   text="Disconnected",
                                   font=self.font_status,
                                   fg='white',
                                   bg='#0a0a0a')
        self.status_label.pack(pady=(0, 20))
        
  
        select_frame = tk.Frame(center_frame, bg='#0a0a0a')
        select_frame.pack(pady=10)
        
        tk.Label(select_frame,
                text="Select zapret:",
                font=self.font_bold,
                fg='#8a8a8a',
                bg='#0a0a0a').pack(side=tk.LEFT, padx=(0, 10))
        
        self.method_var = tk.StringVar()
        
    
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
       
        self.method_combo = ttk.Combobox(select_frame,
                                        textvariable=self.method_var,
                                        state='readonly',
                                        font=self.font_normal,
                                        width=25)
        
    
        self.style.configure('TCombobox', 
                           fieldbackground='#1a1a1a',
                           background='#1a1a1a',
                           foreground='white',
                           borderwidth=1,
                           relief='flat',
                           arrowsize=12)
        
        self.style.map('TCombobox',
                     fieldbackground=[('readonly', '#1a1a1a')],
                     selectbackground=[('readonly', '#333')],
                     selectforeground=[('readonly', 'white')])
        
        self.method_combo.pack(side=tk.LEFT)
        self.method_combo.bind('<<ComboboxSelected>>', self.on_method_changed)
        

        check_frame = tk.Frame(center_frame, bg='#0a0a0a')
        check_frame.pack(pady=20)
        
  
        self.auto_start_var = tk.BooleanVar(value=self.auto_start_enabled)
        self.auto_start_check = tk.Checkbutton(check_frame,
                                             text="Автозапуск",
                                             variable=self.auto_start_var,
                                             font=self.font_normal,
                                             fg='#8a8a8a',
                                             bg='#0a0a0a',
                                             selectcolor='#1a1a1a',
                                             activebackground='#0a0a0a',
                                             activeforeground='#8a8a8a',
                                             command=self.on_auto_start_changed)
        self.auto_start_check.pack(side=tk.LEFT, padx=10)
        
     
        self.auto_connect_var = tk.BooleanVar(value=self.auto_connect_enabled)
        self.auto_connect_check = tk.Checkbutton(check_frame,
                                               text="Автоподключение",
                                               variable=self.auto_connect_var,
                                               font=self.font_normal,
                                               fg='#8a8a8a',
                                               bg='#0a0a0a',
                                               selectcolor='#1a1a1a',
                                               activebackground='#0a0a0a',
                                               activeforeground='#8a8a8a',
                                               command=self.on_auto_connect_changed)
        self.auto_connect_check.pack(side=tk.LEFT, padx=10)
        
      
        if self.bat_files:
            self.method_combo['values'] = self.bat_files
            if self.current_bat and self.current_bat in self.bat_files:
                self.method_combo.set(self.current_bat)
            elif self.bat_files:
                self.method_combo.current(0)
                if self.bat_files[0]:
                    self.current_bat = self.bat_files[0]
        
  
        self.update_connect_button_state()
    
    def update_connect_button_state(self):
        
        if hasattr(self, 'connect_btn') and self.power_icon_off and self.power_icon_on:
            if self.is_connected:
                self.connect_btn.config(image=self.power_icon_on)
                self.status_label.config(text="Connected", fg='#28a745')
            else:
                self.connect_btn.config(image=self.power_icon_off)
                self.status_label.config(text="Disconnected", fg='white')
    
    def setup_settings_tab(self):
  
        main_frame = tk.Frame(self.settings_frame, bg='#0a0a0a')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
 
        console_label = tk.Label(main_frame,
                               text="Console:",
                               font=self.font_bold,
                               fg='#8a8a8a',
                               bg='#0a0a0a')
        console_label.pack(anchor=tk.W, pady=(0, 8))
        
        console_frame = tk.Frame(main_frame, bg='#1a1a1a')
        console_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.console_text = tk.Text(console_frame,
                                   height=10,
                                   bg='#1a1a1a',
                                   fg='white',
                                   font=self.font_normal,
                                   insertbackground='white',
                                   wrap=tk.WORD,
                                   relief='flat',
                                   borderwidth=0,
                                   padx=10,
                                   pady=10)
        
  
        console_scrollbar = tk.Scrollbar(console_frame, 
                                        command=self.console_text.yview,
                                        bg='#0a0a0a',
                                        troughcolor='#0a0a0a',
                                        activebackground='#333')
        self.console_text.configure(yscrollcommand=console_scrollbar.set)
        
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.console_text.config(state=tk.DISABLED)
        

        button_frame = tk.Frame(main_frame, bg='#0a0a0a')
        button_frame.pack(fill=tk.X, pady=10)
        
        self.clear_btn = self.create_rounded_button(button_frame, "Clear Console", self.clear_console)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.service_btn = self.create_rounded_button(button_frame, "Run service.bat", self.run_service)
        self.service_btn.pack(side=tk.LEFT, padx=5)
        

        self.test_btn = self.create_rounded_button(button_frame, "Test All Configs", self.toggle_testing)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        

        results_label = tk.Label(main_frame,
                               text="Results:",
                               font=self.font_bold,
                               fg='#8a8a8a',
                               bg='#0a0a0a')
        results_label.pack(anchor=tk.W, pady=(10, 8))
        
        results_frame = tk.Frame(main_frame, bg='#1a1a1a')
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = tk.Text(results_frame,
                                   height=8,
                                   bg='#1a1a1a',
                                   fg='white',
                                   font=self.font_normal,
                                   wrap=tk.WORD,
                                   relief='flat',
                                   borderwidth=0,
                                   padx=10,
                                   pady=10)
        

        results_scrollbar = tk.Scrollbar(results_frame,
                                        command=self.results_text.yview,
                                        bg='#0a0a0a',
                                        troughcolor='#0a0a0a',
                                        activebackground='#333')
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text.config(state=tk.DISABLED)
    
    def create_rounded_button(self, parent, text, command):

        btn = tk.Button(parent,
                       text=text,
                       font=self.font_normal,
                       bg='#333',
                       fg='white',
                       activebackground='#444',
                       activeforeground='white',
                       relief='flat',
                       borderwidth=0,
                       padx=20,
                       pady=8,
                       cursor='hand2',
                       command=command)
        return btn
    
    def load_bat_files(self):
    
        if self.zapret_dir.exists():
            self.bat_files = []
            for file in self.zapret_dir.glob("*.bat"):
                if file.name.lower() != "service.bat":
                    self.bat_files.append(file.name)
            
      
            if hasattr(self, 'method_combo') and self.bat_files:
                self.method_combo['values'] = self.bat_files
                if self.current_bat and self.current_bat in self.bat_files:
                    self.method_combo.set(self.current_bat)
                elif self.bat_files:
                    self.method_combo.current(0)
                    self.current_bat = self.bat_files[0]
    
    def on_method_changed(self, event):
    
        if hasattr(self, 'method_var'):
            self.current_bat = self.method_var.get()
            self.save_settings()
            self.append_to_console(f"Selected: {self.current_bat}", "white")
    
    def on_auto_start_changed(self):
   
        self.auto_start_enabled = self.auto_start_var.get()
        self.update_auto_start()
        self.save_settings()
        status = "enabled" if self.auto_start_enabled else "disabled"
        self.append_to_console(f"Auto-start {status}", "yellow")
    
    def on_auto_connect_changed(self):

        self.auto_connect_enabled = self.auto_connect_var.get()
        self.save_settings()
        status = "enabled" if self.auto_connect_enabled else "disabled"
        self.append_to_console(f"Auto-connect {status}", "yellow")
    
    def auto_connect(self):

        if self.auto_connect_enabled and self.current_bat and not self.is_connected:
            self.append_to_console("Auto-connecting...", "yellow")
            self.connect()
    
    def toggle_connection(self):
    
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
   
        if not self.current_bat:
            self.status_label.config(text="Error: No config", fg='red')
            return
        
        bat_path = self.zapret_dir / self.current_bat
        if not bat_path.exists():
            self.status_label.config(text="Error: File not found", fg='red')
            return
        
        try:
            self.status_label.config(text="Connecting...", fg='yellow')
            self.root.update()
            
     
            self.process = self.run_silent_admin(bat_path)
            time.sleep(2)
            
       
            self.hide_winws_from_taskbar()
            
            self.is_connected = True
            
         
            self.update_connect_button_state()
            
            self.append_to_console(f"Connected: {self.current_bat}", "green")
            
       
            self.update_tray_menu()
            
        except Exception as e:
            self.status_label.config(text="Error", fg='red')
            self.append_to_console(f"Connection error: {str(e)}", "red")
    
    def run_silent_admin(self, bat_path):
     
       
        vbs_script = f"""
Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "{bat_path}", "", "", "runas", 0
"""
        
        vbs_file = self.zapret_dir.parent / "silent_run.vbs"
        with open(vbs_file, 'w') as f:
            f.write(vbs_script)
        
      
        process = subprocess.Popen(
            ['wscript.exe', str(vbs_file)],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
     
        time.sleep(0.5)
        try:
            os.remove(vbs_file)
        except:
            pass
        
        return process
    
    def hide_winws_from_taskbar(self):
    
        try:
        
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] and 'winws' in proc.info['name'].lower():
                    try:
              
                        import ctypes
                        from ctypes import wintypes
                        
                        EnumWindows = ctypes.windll.user32.EnumWindows
                        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
                        GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
                        ShowWindow = ctypes.windll.user32.ShowWindow
                        
                        def hide_window(hwnd, lParam):
                            pid = ctypes.c_ulong()
                            GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            if pid.value == proc.info['pid']:
                                ShowWindow(hwnd, 0)  
                            return True
                        
                        EnumWindows(EnumWindowsProc(hide_window), 0)
                    except:
                        pass
        except:
            pass
    
    def kill_winws_processes(self):
    
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] and 'winws' in proc.info['name'].lower():
                    try:
                        psutil.Process(proc.info['pid']).terminate()
                        time.sleep(0.1)
                    except:
                        try:
                            psutil.Process(proc.info['pid']).kill()
                        except:
                            pass
        except:
            pass
    
    def disconnect(self):

        if self.process:
            try:
                self.kill_winws_processes()
                self.process.terminate()
                self.append_to_console("Disconnected", "yellow")
            except:
                pass
            finally:
                self.process = None
        
        self.is_connected = False
        

        self.update_connect_button_state()
        

        self.update_tray_menu()
    
    def append_to_console(self, text, color="white"):

        self.console_queue.put((text, color))
    
    def process_console_queue(self):
    
        try:
            while True:
                text, color = self.console_queue.get_nowait()
                self._append_text_to_console(text, color)
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_console_queue)
    
    def _append_text_to_console(self, text, color):

        colors = {
            "white": "#ffffff",
            "red": "#dc3545", 
            "green": "#28a745",
            "yellow": "#ffc107",
            "blue": "#17a2b8",
            "cyan": "#0dcaf0",
        }
        
        if hasattr(self, 'console_text') and self.console_text.winfo_ismapped():
            self.console_text.config(state=tk.NORMAL)
            self.console_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] ", "time")
            self.console_text.insert(tk.END, f"{text}\n", color)
            self.console_text.config(state=tk.DISABLED)
            self.console_text.see(tk.END)
            
            for color_name, hex_color in colors.items():
                self.console_text.tag_config(color_name, foreground=hex_color)
            self.console_text.tag_config("time", foreground="#666", font=self.font_normal)
    
    def clear_console(self):

        if hasattr(self, 'console_text'):
            self.console_text.config(state=tk.NORMAL)
            self.console_text.delete(1.0, tk.END)
            self.console_text.config(state=tk.DISABLED)
    
    def run_service(self):

        service_path = self.zapret_dir / "service.bat"
        if not service_path.exists():
            self.append_to_console("ERROR: service.bat not found!", "red")
            return
        
        self.append_to_console("Starting service.bat...", "yellow")
        
        def run_in_thread():
            try:
                process = subprocess.Popen(
                    ['cmd.exe', '/c', str(service_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        self.append_to_console(line.strip(), "cyan")
                
                process.stdout.close()
                process.wait()
                
                self.append_to_console("service.bat completed", "green")
                    
            except Exception as e:
                self.append_to_console(f"Error: {str(e)}", "red")
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
    
    def toggle_testing(self):

        if self.testing:
 
            self.stop_testing = True
            self.append_to_console("Stopping tests...", "yellow")
            self.test_btn.config(state=tk.DISABLED)
        else:

            self.run_tests()
    
    def run_tests(self):

        if self.testing:
            return
            
        if not self.bat_files:
            self.append_to_console("No .bat files to test!", "red")
            return
        
        self.testing = True
        self.stop_testing = False
        self.test_btn.config(text="Stop Testing")
        
        if hasattr(self, 'results_text'):
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.config(state=tk.DISABLED)
        
        self.append_to_console("\n" + "="*51, "yellow")
        self.append_to_console("Starting tests...", "yellow")
        
        self.test_thread = threading.Thread(target=self.perform_tests, daemon=True)
        self.test_thread.start()
    
    def perform_tests(self):

        results = []
        
        ping_targets = {
            "Yandex": "yandex.com",
            "Discord": "discord.com",
            "YouTube": "youtube.com",
            "Roblox": "roblox.com"
        }
        
        for i, bat_file in enumerate(self.bat_files):

            if self.stop_testing:
                self.append_to_console("Tests stopped by user", "red")
                break
            
            bat_path = self.zapret_dir / bat_file
            
            self.append_to_console(f"\nTesting: {bat_file}", "white")
            
            try:
      
                self.append_to_console("  Closing old processes...", "yellow")
                self.kill_winws_processes()
                time.sleep(1)
                
   
                if self.stop_testing:
                    break
                

                self.append_to_console("  Starting...", "yellow")
                process = self.run_silent_admin(bat_path)
                time.sleep(3)
                
       
                if self.stop_testing:
                    self.kill_winws_processes()
                    break
                
                test_result = {
                    'name': bat_file,
                    'services': {},
                    'ping_results': {},
                    'average_ping': 0,
                }
                
   
                self.append_to_console("  Checking service availability...", "yellow")
                http_services = [
                    ("YouTube", "https://www.youtube.com"),
                    ("Discord", "https://discord.com"),
                    ("Roblox", "https://www.roblox.com"),
                ]
                
                for service_name, service_url in http_services:

                    if self.stop_testing:
                        break
                    
                    is_available = self.test_service(service_url)
                    test_result['services'][service_name] = is_available
                    status = "✓" if is_available else "✗"
                    color = "green" if is_available else "red"
                    self.append_to_console(f"    {service_name}: {status}", color)
                

                if self.stop_testing:
                    self.kill_winws_processes()
                    break
                

                self.append_to_console("  Testing pings...", "yellow")
                ping_values = []
                
                for service_name, service_host in ping_targets.items():
       
                    if self.stop_testing:
                        break
                    
                    try:
                      
                        delay = ping3.ping(service_host, timeout=2)
                        
                        if delay is not None:
                        
                            ms = int(delay * 1000)
                            test_result['ping_results'][service_name] = ms
                            ping_values.append(ms)
                            
                  
                            if service_name == "Yandex":
                                self.append_to_console(f"    Ping: {ms} ms", "cyan")
                            else:
                                self.append_to_console(f"    {service_name} ping: {ms} ms", "cyan")
                        else:
                            test_result['ping_results'][service_name] = 999
                            if service_name == "Yandex":
                                self.append_to_console(f"    Ping: failed (999 ms)", "red")
                            else:
                                self.append_to_console(f"    {service_name} ping: failed", "red")
                            
                    except Exception as e:
                        test_result['ping_results'][service_name] = 999
                        if service_name == "Yandex":
                            self.append_to_console(f"    Ping: error", "red")
                        else:
                            self.append_to_console(f"    {service_name} ping: error", "red")
                

                valid_pings = [p for p in ping_values if p < 999]
                if valid_pings:
                    test_result['average_ping'] = sum(valid_pings) / len(valid_pings)
                else:
                    test_result['average_ping'] = 999
                
                results.append(test_result)
                
 
                if self.stop_testing:
                    self.kill_winws_processes()
                    break
                
            
                self.append_to_console("  Closing...", "yellow")
                self.kill_winws_processes()
                time.sleep(1)
                
            except Exception as e:
                self.append_to_console(f"  Error: {str(e)}", "red")
          
                self.kill_winws_processes()
        
    
        if not self.stop_testing and results:
            self.show_top_results(results)
        
    
        self.testing = False
        self.stop_testing = False
        self.root.after(0, lambda: self.test_btn.config(text="Test All Configs", state=tk.NORMAL))
        
        if self.stop_testing:
            self.append_to_console("\nTests stopped by user", "yellow")
        else:
            self.append_to_console("\nTests completed!", "green")
    
    def test_service(self, url):
        """Проверяет доступность сервиса"""
        try:
            response = requests.get(url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            return response.status_code == 200
        except:
            return False
    
    def show_top_results(self, results):
        """Показывает топ-3 результатов"""
      
        def sort_key(x):
            available = sum(1 for s in x['services'].values() if s)
            avg_ping = x['average_ping'] if x['average_ping'] < 999 else 999
            return (avg_ping, -available)
        
        sorted_results = sorted(results, key=sort_key)[:3]
        
        text = "\n" + "="*50 + "\n"
        text += "TOP 3 RESULTS\n"
        text += "="*50 + "\n\n"
        
        for i, result in enumerate(sorted_results, 1):
            available = sum(1 for s in result['services'].values() if s)
            total = len(result['services'])
            
            text += f"{i}. {result['name']} - {available}/{total}, "
            text += f"avg ping: {result['average_ping']:.0f} ms\n"
            
      
            for service_name, ping_value in result['ping_results'].items():
                if service_name == "Yandex":
                    text += f"     Ping: {ping_value} ms\n"
                else:
                    text += f"     {service_name} ping: {ping_value} ms\n"
            text += "\n"
        
        self.root.after(0, lambda t=text: self._insert_result(t))
        
        self.append_to_console("\n" + "="*60, "yellow")
        self.append_to_console("TOP 3 RESULTS:", "yellow")
        for i, result in enumerate(sorted_results, 1):
            available = sum(1 for s in result['services'].values() if s)
            self.append_to_console(
                f"{i}. {result['name']} - {available}/3, "
                f"avg ping: {result['average_ping']:.0f} ms",
                "green" if i == 1 else "cyan"
            )
    
    def _insert_result(self, text):
  
        if hasattr(self, 'results_text') and self.results_text.winfo_ismapped():
            self.results_text.config(state=tk.NORMAL)
            self.results_text.insert(tk.END, text)
            self.results_text.config(state=tk.DISABLED)
            self.results_text.see(tk.END)
    
    def center_window(self):
  
        self.root.update_idletasks()
        width = 420
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def minimize_to_tray(self):
 
        self.in_tray = True
        self.root.withdraw()
        self.create_tray_icon()
    
    def update_tray_menu(self):
     
        if self.tray_icon:
            self.tray_icon.menu = self.create_tray_menu()
    
    def create_tray_menu(self):
       
        menu_items = []
        
        menu_items.append(item('Open', self.restore_from_tray))
        
        if self.is_connected:
            menu_items.append(item('Disconnect', self.toggle_connection_from_tray))
        else:
            menu_items.append(item('Connect', self.toggle_connection_from_tray))
        
        menu_items.append(item('Exit', self.exit_from_tray))
        
        return pystray.Menu(*menu_items)
    
    def create_tray_icon(self):
      
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        
        try:
            from PIL import Image, ImageDraw
            
           
            image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
         
            if self.is_connected:
          
                draw.ellipse([4, 4, 60, 60], fill='#28a745', outline='white', width=2)
            else:
         
                draw.ellipse([4, 4, 60, 60], fill='#666666', outline='white', width=2)
            
            draw.ellipse([20, 20, 44, 44], fill='white', outline='white', width=2)
            
       
            menu = self.create_tray_menu()
            
            self.tray_icon = pystray.Icon("ZapretTester", image, "Zapret Tester", menu)
            
            
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
        except Exception as e:
            print(f"Tray error: {e}")
    
    def restore_from_tray(self, icon=None, item=None):
       
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        
        self.in_tray = False
        self.root.deiconify()
        self.center_window()
    
    def toggle_connection_from_tray(self, icon=None, item=None):
    
        self.toggle_connection()
    
    def exit_from_tray(self, icon=None, item=None):

        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        
        self.disconnect()
        self.root.quit()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ZapretTester(root)
    root.mainloop()

if __name__ == "__main__":
    main()