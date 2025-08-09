from bs4 import BeautifulSoup
import json
import re
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import requests
import subprocess
import zipfile


def replace_exe_icon_with_ico(ico_file: str, target_exe: str, output_exe: str) -> bool:
    """
    Embed ICO icon file into target exe file

    Args:
        ico_file: ICO icon file path
        target_exe: Target exe file path (icon to be replaced)
        output_exe: Output exe file path

    Returns:
        bool: Whether the operation was successful
    """

    # Tool path
    resource_hacker_path = "./tool/ResourceHacker.exe"

    # Check if tool exists
    if not os.path.exists(resource_hacker_path):
        print(f"ResourceHacker tool not found: {resource_hacker_path}")
        return False

    # Check input files
    if not os.path.exists(ico_file):
        print(f"ICO file not found: {ico_file}")
        return False

    if not os.path.exists(target_exe):
        print(f"Target file not found: {target_exe}")
        return False

    if not os.path.splitext(ico_file)[1].lower() == '.ico':
        messagebox.showerror("Warning",
                             "Please select ICO file type, icon replacement operation is invalid"
                             )
        return False

    try:
        # Copy target file to output path
        shutil.copy2(target_exe, output_exe)

        # Use ResourceHacker to replace icon
        print("Replacing icon...")
        replace_cmd = [
            resource_hacker_path,
            "-open", os.path.abspath(output_exe),
            "-save", os.path.abspath(output_exe),
            "-action", "addoverwrite",
            "-res", os.path.abspath(ico_file),
            "-mask", "ICONGROUP,MAINICON,"
        ]

        result = subprocess.run(replace_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("Icon replacement successful!")
            return True
        else:
            print(f"ResourceHacker replacement failed: {result.stderr}")
            print(f"ResourceHacker output: {result.stdout}")
            return False

    except Exception as e:
        print(f"Operation failed: {e}")
        return False


def replace_exe_icon(source_exe: str, target_exe: str, output_exe: str) -> bool:
    """
    Replace icon from source exe file to target exe file

    Args:
        source_exe: Source exe file path (extract icon)
        target_exe: Target exe file path (icon to be replaced)
        output_exe: Output exe file path

    Returns:
        bool: Whether the operation was successful
    """

    # Tool path
    resource_hacker_path = "./tool/ResourceHacker.exe"

    # Temporary icon directory
    temp_icon_dir = "./temp_icon"

    # Check if tool exists
    if not os.path.exists(resource_hacker_path):
        print(f"ResourceHacker tool not found: {resource_hacker_path}")
        return False

    # Check input files
    if not os.path.exists(source_exe):
        print(f"Source file not found: {source_exe}")
        return False

    if not os.path.exists(target_exe):
        print(f"Target file not found: {target_exe}")
        return False

    # Create temporary icon directory
    if not os.path.exists(temp_icon_dir):
        os.makedirs(temp_icon_dir)

    try:
        # Use ResourceHacker to extract icon resources
        res_path = os.path.join(temp_icon_dir, "extracted_icon.res")

        print("Extracting icon resources...")
        extract_cmd = [
            resource_hacker_path,
            "-open", os.path.abspath(source_exe),
            "-save", os.path.abspath(res_path),
            "-action", "extract",
            "-mask", "ICONGROUP,,"
        ]

        result = subprocess.run(extract_cmd, capture_output=True, text=True)

        # Check if resource extraction was successful
        if not os.path.exists(res_path) or os.path.getsize(res_path) == 0:
            print("Icon resource extraction failed")
            print(f"ResourceHacker output: {result.stdout}")
            print(f"ResourceHacker error: {result.stderr}")
            return False

        print("Icon resource extraction successful")

        # Copy target file to output path
        shutil.copy2(target_exe, output_exe)

        # Use ResourceHacker to replace icon
        print("Replacing icon...")
        replace_cmd = [
            resource_hacker_path,
            "-open", os.path.abspath(output_exe),
            "-save", os.path.abspath(output_exe),
            "-action", "addoverwrite",
            "-res", os.path.abspath(res_path)
        ]

        result = subprocess.run(replace_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("Icon replacement successful!")
            return True
        else:
            print(f"ResourceHacker replacement failed: {result.stderr}")
            print(f"ResourceHacker output: {result.stdout}")
            return False

    except Exception as e:
        print(f"Operation failed: {e}")
        return False

    finally:
        # Clean up temporary icon directory
        if os.path.exists(temp_icon_dir):
            shutil.rmtree(temp_icon_dir, ignore_errors=True)


def get_game_dlc_info(appid):
    """
    Get DLC information for a game based on its appid

    Args:
        appid (int): Steam game application ID

    Returns:
        dict: Dictionary containing game information and DLC information
    """
    # Steam Store API URL
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english"

    try:
        # Send request
        response = requests.get(url)
        response.raise_for_status()

        # Parse JSON data
        data = response.json()

        # Check if data was successfully retrieved
        if str(appid) not in data or not data[str(appid)]['success']:
            print(f"Unable to get information for appid {appid}")
            return {}

        game_data = data[str(appid)]['data']
        game_name = game_data.get('name', 'Unknown Game')

        print(f"Game Name: {game_name}")
        print(f"Game ID: {appid}")
        print("-" * 50)

        # Get DLC list
        dlc_list = game_data.get('dlc', [])

        if not dlc_list:
            print("This game has no DLC")
            return {
                'game_name': game_name,
                'game_id': appid,
                'dlc_list': {}
            }

        print(f"Found {len(dlc_list)} DLC(s):")

        # Dictionary to store DLC information
        dlc_info = {}

        # Get detailed information for each DLC
        for dlc_id in dlc_list:
            dlc_url = f"https://store.steampowered.com/api/appdetails?appids={dlc_id}&l=english"

            try:
                dlc_response = requests.get(dlc_url)
                dlc_response.raise_for_status()
                dlc_data = dlc_response.json()

                if str(dlc_id) in dlc_data and dlc_data[str(dlc_id)]['success']:
                    dlc_name = dlc_data[str(dlc_id)]['data'].get(
                        'name', f'DLC_{dlc_id}')
                    dlc_info[dlc_id] = dlc_name
                    print(f"DLC ID: {dlc_id} - Name: {dlc_name}")
                else:
                    dlc_info[dlc_id] = f'Unknown DLC_{dlc_id}'
                    print(f"DLC ID: {dlc_id} - Name: Unknown DLC_{dlc_id}")

            except requests.RequestException as e:
                print(f"Error getting DLC {dlc_id} information: {e}")
                dlc_info[dlc_id] = f'Failed to retrieve_{dlc_id}'

        return {
            'game_name': game_name,
            'game_id': appid,
            'dlc_list': dlc_info
        }

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        return {}
    except Exception as e:
        print(f"Error occurred: {e}")
        return {}


class AchievementDisplayWindow:
    def __init__(self, achievements, game_name):
        self.achievements = achievements
        self.game_name = game_name
        self.window = tk.Toplevel()
        self.window.title(
            f"Achievement List - Total {len(achievements)} achievements")
        self.window.geometry("1000x800")

        self.setup_ui()
        self.display_achievements()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text=f"Achievement List ({len(self.achievements)} achievements)",
                                font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # Create scroll frame
        self.canvas = tk.Canvas(main_frame, bg="white")
        self.scrollbar = ttk.Scrollbar(
            main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind mouse wheel
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.canvas.bind("<MouseWheel>", _on_mousewheel)

        # Layout scroll components
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bottom button bar
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="Close Window", command=self.window.destroy).pack(
            side=tk.RIGHT, padx=5)

    def display_achievements(self):
        """Display achievement list"""
        if not self.achievements:
            ttk.Label(self.scrollable_frame,
                      text="No achievement data available").pack(pady=20)
            return

        # Display each achievement
        for i, achievement in enumerate(self.achievements):
            self.create_achievement_widget(
                self.scrollable_frame, achievement, i)

    def create_achievement_widget(self, parent, achievement, index):
        """Create display widget for a single achievement"""
        # Main frame
        achievement_frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1)
        achievement_frame.pack(fill=tk.X, padx=5, pady=5)

        # Left side: Image area
        image_frame = ttk.Frame(achievement_frame)
        image_frame.pack(side=tk.LEFT, padx=10, pady=10)

        # Get game name to construct path
        game_name = self.game_name
        safe_game_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)

        # Load and display normal icon
        icon_path = achievement.get('icon', '')
        if icon_path:
            full_icon_path = os.path.join(
                "Output", safe_game_name, "steam_settings", "achievement_images", icon_path)
            if os.path.exists(full_icon_path):
                try:
                    img = Image.open(full_icon_path)
                    img = img.resize((64, 64), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                    icon_label = ttk.Label(image_frame, image=photo)
                    icon_label.image = photo  # Keep reference
                    icon_label.pack(side=tk.TOP, pady=2)

                    ttk.Label(image_frame, text="Normal Icon",
                              font=("Arial", 8)).pack()
                except Exception as e:
                    ttk.Label(image_frame, text="Normal Icon\nLoad Failed",
                              width=12, anchor=tk.CENTER).pack(pady=2)
            else:
                ttk.Label(image_frame, text="No Normal Icon", width=12,
                          anchor=tk.CENTER).pack(pady=2)
        else:
            ttk.Label(image_frame, text="No Normal Icon", width=12,
                      anchor=tk.CENTER).pack(pady=2)

        # Separator
        ttk.Label(image_frame, text="").pack(pady=5)

        # Load and display gray icon
        icon_gray_path = achievement.get(
            'icongray', achievement.get('icon_gray', ''))
        if icon_gray_path:
            full_icon_gray_path = os.path.join(
                "Output", safe_game_name, "steam_settings", "achievement_images", icon_gray_path)
            if os.path.exists(full_icon_gray_path):
                try:
                    img_gray = Image.open(full_icon_gray_path)
                    img_gray = img_gray.resize(
                        (64, 64), Image.Resampling.LANCZOS)
                    photo_gray = ImageTk.PhotoImage(img_gray)

                    icon_gray_label = ttk.Label(image_frame, image=photo_gray)
                    icon_gray_label.image = photo_gray  # Keep reference
                    icon_gray_label.pack(side=tk.TOP, pady=2)

                    ttk.Label(image_frame, text="Gray Icon",
                              font=("Arial", 8)).pack()
                except Exception as e:
                    ttk.Label(image_frame, text="Gray Icon\nLoad Failed",
                              width=12, anchor=tk.CENTER).pack(pady=2)
            else:
                ttk.Label(image_frame, text="No Gray Icon", width=12,
                          anchor=tk.CENTER).pack(pady=2)
        else:
            ttk.Label(image_frame, text="No Gray Icon", width=12,
                      anchor=tk.CENTER).pack(pady=2)

        # Right side: Text information
        text_frame = ttk.Frame(achievement_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=10, pady=10)

        # Achievement number and name
        title_text = f"#{index + 1} - name: {achievement.get('name', 'N/A')}"
        if achievement.get('hidden'):
            title_text += " [Hidden Achievement]"

        title_label = ttk.Label(
            text_frame, text=title_text, font=("Arial", 12, "bold"))
        title_label.pack(anchor=tk.W)

        # Display name
        display_name = achievement.get('displayName', 'N/A')
        ttk.Label(text_frame, text=f"Display Name: {display_name}", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=(5, 0))

        # Description
        description = achievement.get('description', 'N/A')
        desc_label = ttk.Label(
            text_frame, text=f"Description: {description}", font=("Arial", 9), wraplength=500)
        desc_label.pack(anchor=tk.W, pady=(2, 0))

        # Default value
        defaultvalue = achievement.get('defaultvalue', 0)
        ttk.Label(text_frame, text=f"Default Value: {defaultvalue}", font=(
            "Arial", 8), foreground="blue").pack(anchor=tk.W, pady=(5, 0))

        # Image path information
        if icon_path:
            ttk.Label(text_frame, text=f"Normal Icon Path: Output/{safe_game_name}/steam_settings/achievement_images/{icon_path}", font=(
                "Arial", 8), foreground="gray").pack(anchor=tk.W, pady=(2, 0))

        if icon_gray_path:
            ttk.Label(text_frame, text=f"Gray Icon Path: Output/{safe_game_name}/steam_settings/achievement_images/{icon_gray_path}", font=(
                "Arial", 8), foreground="gray").pack(anchor=tk.W, pady=(0, 0))

        # Separator line
        ttk.Separator(parent, orient='horizontal').pack(
            fill=tk.X, padx=5, pady=5)


class GSEGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(
            "GSE Generator - Steam Game Configuration File Generator")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)

        # Language mapping
        self.language_mapping = {
            "Arabic": "arabic",
            "Bulgarian": "bulgarian",
            "Simplified Chinese": "schinese",
            "Traditional Chinese": "tchinese",
            "Czech": "czech",
            "Danish": "danish",
            "Dutch": "dutch",
            "English": "english",
            "Finnish": "finnish",
            "French": "french",
            "German": "german",
            "Greek": "greek",
            "Hungarian": "hungarian",
            "Indonesian": "indonesian",
            "Italian": "italian",
            "Japanese": "japanese",
            "Korean": "koreana",
            "Norwegian": "norwegian",
            "Polish": "polish",
            "Portuguese - Portugal": "portuguese",
            "Portuguese - Brazil": "brazilian",
            "Romanian": "romanian",
            "Russian": "russian",
            "Spanish - Spain": "spanish",
            "Spanish - Latin America": "latam",
            "Swedish": "swedish",
            "Thai": "thai",
            "Turkish": "turkish",
            "Ukrainian": "ukrainian",
            "Vietnamese": "vietnamese"
        }

        self.game_language = tk.StringVar(value="english")
        self.game_info = {}
        self.game_info_fetched = False
        self.custom_ico_path = ""

        # Error handling flags
        self.missing_core_files = []
        self.missing_overlay_files = []
        self.has_resource_hacker = True
        self.icon_replacement_failed = False
        self.achievement_processing_failed = False
        self.overlay_files_missing = False
        self.exe_valid = True

        # New patch related variables
        self.generate_patch_var = tk.BooleanVar(value=False)
        self.game_root_path_var = tk.StringVar()
        self.steamapi_dll_path = ""
        self.patch_type = ""  # "regular" or "experimental"

        # Check directory integrity on program startup
        self.check_directory_integrity()

        self.setup_ui()

    def check_directory_integrity(self):
        """Check program directory integrity"""
        # Check core files
        core_files = [
            "ColdClientLoader.ini",
            "GameOverlayRenderer.dll",
            "GameOverlayRenderer64.dll",
            "steamclient.dll",
            "steamclient_loader_x64.exe",
            "steamclient64.dll"
        ]

        for file in core_files:
            if not os.path.exists(os.path.join("source", file)):
                self.missing_core_files.append(file)

        # Check overlay files
        overlay_files = [
            "steam_settings/configs.overlay.ini",
            "steam_settings/sounds/overlay_achievement_notification.wav",
            "steam_settings/fonts/Roboto-Medium.ttf"
        ]

        for file in overlay_files:
            if not os.path.exists(os.path.join("source", file)):
                self.missing_overlay_files.append(file)

        # Check ResourceHacker
        if not os.path.exists("tool/ResourceHacker.exe"):
            self.has_resource_hacker = False

        # If core files are missing, show warning
        if self.missing_core_files:
            missing_files_str = ", ".join(self.missing_core_files)
            messagebox.showerror(
                "Core Files Missing",
                f"Core files {missing_files_str} etc. are missing, cannot generate configuration, please read README file for details"
            )

        # If overlay files are missing, show warning
        if self.missing_overlay_files:
            missing_files_str = ", ".join(self.missing_overlay_files)
            messagebox.showwarning(
                "Overlay Files Missing",
                f"In-game overlay core files {missing_files_str} etc. are missing, in-game overlay interface cannot work properly, please read README file for details"
            )
            self.overlay_files_missing = True

    def check_patch_files(self):
        """Check if patch related files exist"""
        regular_files = [
            "source/GSE_DLL/regular/steam_api.dll",
            "source/GSE_DLL/regular/steam_api64.dll"
        ]

        experimental_files = [
            "source/GSE_DLL/experimental/steam_api.dll",
            "source/GSE_DLL/experimental/steam_api64.dll"
        ]

        missing_files = []

        for file in regular_files + experimental_files:
            if not os.path.exists(file):
                missing_files.append(file)

        if missing_files:
            missing_files_str = "\n".join(missing_files)
            messagebox.showerror(
                "Patch Files Missing",
                f"The following patch files are missing, cannot generate patch:\n{missing_files_str}"
            )
            return False

        return True

    def get_relative_path(self, base_path, target_path):
        """Get relative path"""
        base_path = os.path.normpath(base_path)
        target_path = os.path.normpath(target_path)

        # Use os.path.relpath to get relative path
        try:
            relative_path = os.path.relpath(target_path, base_path)
            # If relative path starts with .., it means target_path is not under base_path
            if relative_path.startswith('..'):
                return target_path
            return relative_path
        except ValueError:
            # Different drive case
            return target_path

    def setup_ui(self):
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left configuration area - adjust width
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        left_frame.config(width=1000)

        # Right information panel - increase width
        self.right_frame = ttk.LabelFrame(
            main_container, text="Game Information", padding="15")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH,
                              expand=True, padx=(10, 0))
        self.right_frame.config(width=500)

        self.setup_left_panel(left_frame)
        self.setup_right_panel()

    def setup_left_panel(self, parent):
        # Create main scroll frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(
            parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Main frame - adjust padding
        main_frame = ttk.Frame(scrollable_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="GSE Generator",
                                font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))

        subtitle_label = ttk.Label(
            main_frame, text="Steam Game Configuration File Generator", font=("Arial", 12))
        subtitle_label.pack(pady=(0, 30))

        # Game configuration area
        config_frame = ttk.LabelFrame(
            main_frame, text="Game Configuration", padding="15")
        config_frame.pack(fill=tk.X, pady=(0, 20))

        # AppID
        appid_frame = ttk.Frame(config_frame)
        appid_frame.grid(row=0, column=0, columnspan=2,
                         sticky=tk.W+tk.E, pady=5)

        ttk.Label(appid_frame, text="AppID:", font=(
            "Arial", 10, "bold")).pack(side=tk.LEFT)
        self.appid_var = tk.StringVar()
        appid_entry = ttk.Entry(
            appid_frame, textvariable=self.appid_var, font=("Arial", 10), width=15)
        appid_entry.pack(side=tk.LEFT, padx=(10, 10))

        # Get game information button
        self.fetch_button = ttk.Button(
            appid_frame, text="Get Game Info", command=self.fetch_game_info)
        self.fetch_button.pack(side=tk.LEFT)

        # Username
        ttk.Label(config_frame, text="Username:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar(value="O.T")
        ttk.Entry(config_frame, textvariable=self.username_var, font=(
            "Arial", 10), width=25).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # User ID
        ttk.Label(config_frame, text="User ID:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        self.userid_var = tk.StringVar(value="76561198964222222")
        ttk.Entry(config_frame, textvariable=self.userid_var, font=(
            "Arial", 10), width=25).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # Language selection
        ttk.Label(config_frame, text="Language:", font=("Arial", 10, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=5)
        self.language_var = tk.StringVar(value="English")
        language_combo = ttk.Combobox(config_frame, textvariable=self.language_var,
                                      values=list(
                                          self.language_mapping.keys()),
                                      state="readonly", width=22)
        language_combo.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        language_combo.bind('<<ComboboxSelected>>', self.on_language_change)

        # Local save
        self.local_storage_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable Local Save", variable=self.local_storage_var).grid(
            row=4, column=5, columnspan=2, sticky=tk.W, pady=5)

        # In-game overlay
        self.overlay_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable In-Game Overlay", variable=self.overlay_var).grid(
            row=5, column=5, columnspan=2, sticky=tk.W, pady=5)

        # Custom ICO icon option
        self.use_custom_ico_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(config_frame, text="Use Custom ICO Icon", variable=self.use_custom_ico_var).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Generate patch option
        ttk.Checkbutton(config_frame, text="Generate Patch", variable=self.generate_patch_var,
                        command=self.on_patch_checkbox_change).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

        # File selection area
        file_frame = ttk.LabelFrame(
            main_frame, text="File Selection", padding="15")
        file_frame.pack(fill=tk.X, pady=(0, 20))

        # Game root directory selection
        ttk.Label(file_frame, text="Game Root Directory:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W)

        root_select_frame = ttk.Frame(file_frame)
        root_select_frame.pack(fill=tk.X, pady=(5, 15))

        root_entry = ttk.Entry(
            root_select_frame, textvariable=self.game_root_path_var, width=50)
        root_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(root_select_frame, text="Browse...",
                   command=self.browse_game_root_folder).pack(side=tk.RIGHT)

        # Game EXE file selection
        ttk.Label(file_frame, text="Game EXE File:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W)

        exe_select_frame = ttk.Frame(file_frame)
        exe_select_frame.pack(fill=tk.X, pady=(5, 15))

        self.exe_path_var = tk.StringVar()
        exe_entry = ttk.Entry(
            exe_select_frame, textvariable=self.exe_path_var, width=50)
        exe_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(exe_select_frame, text="Browse...",
                   command=self.browse_exe_file).pack(side=tk.RIGHT)

        # HTML file selection
        ttk.Label(file_frame, text="Achievement HTML File:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))

        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X, pady=(5, 15))

        self.html_path_var = tk.StringVar()
        entry = ttk.Entry(file_select_frame,
                          textvariable=self.html_path_var, width=50)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(file_select_frame, text="Browse...",
                   command=self.browse_html_file).pack(side=tk.RIGHT)

        # Image folder description
        info_frame = ttk.Frame(file_frame)
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text="📁 Please ensure there is an 'imgs' folder containing achievement images in the current directory",
                  foreground="blue").pack(anchor=tk.W)

        # Operation buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Initial state of generate configuration file button is disabled based on core file check results
        initial_state = 'disabled' if self.missing_core_files else 'disabled'
        self.extract_button = ttk.Button(button_frame, text="Generate Configuration File",
                                         command=self.extract_achievements, state=initial_state)
        self.extract_button.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="Exit Program",
                   command=self.root.quit).pack(side=tk.RIGHT)

        # Status bar
        initial_status = "Core files missing, cannot generate configuration" if self.missing_core_files else "Please get game information first"
        self.status_var = tk.StringVar(value=initial_status)
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Label(status_frame, text="Status:", font=(
            "Arial", 9, "bold")).pack(side=tk.LEFT)
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                 foreground="green", wraplength=600)
        status_label.pack(side=tk.LEFT, padx=(5, 0))

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(10, 0))

        # Layout canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

    def on_patch_checkbox_change(self):
        """Handle patch checkbox state change"""
        if self.generate_patch_var.get():
            # Check patch files
            if not self.check_patch_files():
                self.generate_patch_var.set(False)

    def browse_game_root_folder(self):
        """Browse game root directory"""
        folder = filedialog.askdirectory(title="Select Game Root Directory")
        if folder:
            self.game_root_path_var.set(folder)
            # Check if generate configuration file button can be enabled
            self.check_enable_extract_button()

    def setup_right_panel(self):
        """Setup right information panel"""
        # Game Header image display area
        self.header_frame = ttk.Frame(self.right_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        self.header_label = ttk.Label(self.header_frame, text="No game information\nPlease enter AppID and click\n'Get Game Info'",
                                      anchor=tk.CENTER, background="lightgray", width=40)
        self.header_label.pack(fill=tk.X, pady=5)

        # Game Logo display area
        self.logo_frame = ttk.Frame(self.right_frame)
        self.logo_frame.pack(fill=tk.X, pady=(0, 10))

        self.logo_label = ttk.Label(self.logo_frame, text="Game Logo",
                                    anchor=tk.CENTER, background="lightgray", width=40)
        self.logo_label.pack(fill=tk.X, pady=5)

        # Game name
        self.game_name_var = tk.StringVar(value="Not retrieved")
        ttk.Label(self.right_frame, text="Game Name:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=(5, 0))
        self.game_name_label = ttk.Label(self.right_frame, textvariable=self.game_name_var,
                                         font=("Arial", 9), wraplength=400)
        self.game_name_label.pack(anchor=tk.W, padx=(10, 0))

        # DLC information title
        ttk.Label(self.right_frame, text="DLC Information:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))

        # DLC scroll list
        dlc_container = ttk.Frame(self.right_frame)
        dlc_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # DLC listbox
        self.dlc_listbox = tk.Listbox(
            dlc_container, height=12, font=("Arial", 9))
        dlc_scrollbar = ttk.Scrollbar(
            dlc_container, orient="vertical", command=self.dlc_listbox.yview)
        self.dlc_listbox.configure(yscrollcommand=dlc_scrollbar.set)

        self.dlc_listbox.pack(side="left", fill="both", expand=True)
        dlc_scrollbar.pack(side="right", fill="y")

        # DLC count display
        self.dlc_count_var = tk.StringVar(value="DLC Count: 0")
        ttk.Label(self.right_frame, textvariable=self.dlc_count_var,
                  font=("Arial", 9)).pack(anchor=tk.W)

    def browse_exe_file(self):
        """Browse game EXE file"""
        filename = filedialog.askopenfilename(
            title="Select Game EXE File",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.exe_path_var.set(filename)
            # Check if generate configuration file button can be enabled
            self.check_enable_extract_button()

    def select_custom_ico(self):
        """Select custom ICO file"""
        filename = filedialog.askopenfilename(
            title="Select ICO Icon File",
            filetypes=[("Icon files", "*.ico"), ("All files", "*.*")]
        )
        if filename:
            self.custom_ico_path = filename
            return True
        return False

    def select_steamapi_dll_folder(self):
        """Select folder containing steamapi dll files"""
        folder = filedialog.askdirectory(
            title="Select folder containing steamapi dll files")
        if folder:
            self.steamapi_dll_path = folder
            return True
        return False

    def select_patch_type(self):
        """Select patch type"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Patch Type")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center display
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() +
                        50, self.root.winfo_rooty() + 50))

        result = tk.StringVar(value="")

        # Prompt text
        ttk.Label(dialog, text="Please select the type to apply to steamapi dll:",
                  font=("Arial", 9)).pack(pady=20)

        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def select_regular():
            result.set("regular")
            dialog.destroy()

        def select_experimental():
            result.set("experimental")
            dialog.destroy()

        ttk.Button(button_frame, text="Regular", command=select_regular,
                   width=12).pack(side=tk.LEFT, padx=20)
        ttk.Button(button_frame, text="Experimental", command=select_experimental,
                   width=12).pack(side=tk.LEFT, padx=20)

        dialog.wait_window()

        return result.get()

    def fetch_game_info(self):
        """Get game information"""
        appid = self.appid_var.get().strip()
        if not appid:
            messagebox.showerror("Error", "Please enter AppID first")
            return

        try:
            appid = int(appid)
        except ValueError:
            messagebox.showerror("Error", "AppID must be a number")
            return

        # Disable button
        self.fetch_button.config(state='disabled')
        self.fetch_button.config(text="Getting...")

        # Get information in new thread
        threading.Thread(target=self._fetch_game_info_worker,
                         args=(appid,), daemon=True).start()

    def _fetch_game_info_worker(self, appid):
        """Worker thread for getting game information"""
        try:
            # Get game and DLC information
            self.game_info = get_game_dlc_info(appid)

            # Download game images to _temp directory
            if self.game_info:
                self.download_game_images(appid)

            # Update UI
            self.root.after(0, self._update_game_info_ui)

        except Exception as e:
            self.root.after(0, lambda: self._handle_fetch_error(str(e)))

    def download_game_images(self, appid):
        """Download game images to _temp directory"""
        temp_dir = "_temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        try:
            # Download Header image
            header_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
            header_response = requests.get(header_url)
            if header_response.status_code == 200:
                header_path = os.path.join(temp_dir, "header.jpg")
                with open(header_path, "wb") as f:
                    f.write(header_response.content)
                print("Header image download successful")

            # Download Logo
            logo_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/logo.png"
            logo_response = requests.get(logo_url)
            if logo_response.status_code == 200:
                logo_path = os.path.join(temp_dir, "logo.png")
                with open(logo_path, "wb") as f:
                    f.write(logo_response.content)
                print("Logo download successful")

            # Download library cover
            library_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
            library_response = requests.get(library_url)
            if library_response.status_code == 200:
                library_path = os.path.join(temp_dir, "library_600x900.jpg")
                with open(library_path, "wb") as f:
                    f.write(library_response.content)
                print("Library cover download successful")

        except Exception as e:
            print(f"Image download failed: {e}")

    def _update_game_info_ui(self):
        """Update game information UI"""
        self.fetch_button.config(state='normal')
        self.fetch_button.config(text="Get Game Info")

        if not self.game_info:
            messagebox.showerror(
                "Error", "Failed to get game information, please check network or use network proxy")
            return

        # Mark game information as retrieved
        self.game_info_fetched = True

        # Check if generate configuration file button can be enabled
        self.check_enable_extract_button()

        # Update game name
        game_name = self.game_info.get('game_name', 'Unknown Game')
        self.game_name_var.set(game_name)

        # Update Header image display
        self.update_header_display()

        # Update Logo display
        self.update_logo_display()

        # Update DLC list
        self.update_dlc_display()

        # Update status
        self.status_var.set("Game information retrieved successfully!")

        messagebox.showinfo(
            "Success", "Game information retrieved successfully!")

    def check_enable_extract_button(self):
        """Check if generate configuration file button can be enabled"""
        # If core files are missing, always disable button
        if self.missing_core_files:
            self.extract_button.config(state='disabled')
            return

        # If game root directory is not selected or empty, always disable button
        game_root_path = self.game_root_path_var.get().strip()
        if not game_root_path:
            self.extract_button.config(state='disabled')
            self.status_var.set("Please select game root directory")
            return

        # Must meet one of the following conditions to enable button:
        # 1. Retrieved game information and selected EXE file
        # 2. Retrieved game information and no ResourceHacker tool (can use default EXE directly)
        if self.game_info_fetched:
            exe_path = self.exe_path_var.get().strip()

            # If ResourceHacker tool exists, need to select EXE file or custom ICO
            if self.has_resource_hacker:
                if exe_path and os.path.exists(exe_path):
                    self.extract_button.config(state='normal')
                    self.status_var.set(
                        "Ready, can generate configuration file")
                elif self.use_custom_ico_var.get():
                    self.extract_button.config(state='normal')
                    self.status_var.set(
                        "Ready, can generate configuration file (using custom ICO)")
                else:
                    self.extract_button.config(state='disabled')
                    self.status_var.set("Please select game EXE file")
            else:
                # No ResourceHacker tool, can generate directly
                self.extract_button.config(state='normal')
                self.status_var.set(
                    "Ready, can generate configuration file (will use default EXE)")
        else:
            self.extract_button.config(state='disabled')
            self.status_var.set("Please get game information first")

    def update_header_display(self):
        """Update Header image display"""
        header_path = os.path.join("_temp", "header.jpg")
        if os.path.exists(header_path):
            try:
                img = Image.open(header_path)
                # Adjust image size to fit display area
                img.thumbnail((450, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                self.header_label.config(image=photo, text="")
                self.header_label.image = photo  # Keep reference
            except Exception as e:
                self.header_label.config(
                    text=f"Header image load failed\n{str(e)}")
        else:
            self.header_label.config(text="Header image download failed")

    def update_logo_display(self):
        """Update Logo display"""
        logo_path = os.path.join("_temp", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                # Adjust image size to fit display area
                img.thumbnail((400, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                self.logo_label.config(image=photo, text="")
                self.logo_label.image = photo  # Keep reference
            except Exception as e:
                self.logo_label.config(text=f"Logo load failed\n{str(e)}")
        else:
            self.logo_label.config(text="Logo download failed")

    def update_dlc_display(self):
        """Update DLC display"""
        # Clear list
        self.dlc_listbox.delete(0, tk.END)

        dlc_list = self.game_info.get('dlc_list', {})

        if not dlc_list:
            self.dlc_listbox.insert(tk.END, "This game has no DLC")
            self.dlc_count_var.set("DLC Count: 0")
        else:
            for dlc_id, dlc_name in dlc_list.items():
                self.dlc_listbox.insert(tk.END, f"{dlc_id}: {dlc_name}")
            self.dlc_count_var.set(f"DLC Count: {len(dlc_list)}")

    def _handle_fetch_error(self, error_msg):
        """Handle fetch information error"""
        self.fetch_button.config(state='normal')
        self.fetch_button.config(text="Get Game Info")
        messagebox.showerror(
            "Error", "Failed to get game information, please check network or use network proxy")

    def on_language_change(self, event=None):
        """Update game_language variable when language selection changes"""
        selected_language = self.language_var.get()
        if selected_language in self.language_mapping:
            self.game_language.set(self.language_mapping[selected_language])

    def browse_html_file(self):
        filename = filedialog.askopenfilename(
            title="Select HTML File",
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*.*")]
        )
        if filename:
            self.html_path_var.set(filename)

    def extract_achievements(self):
        # First validate required fields
        if not self.username_var.get().strip():
            messagebox.showerror("Error", "Please fill in username")
            return

        if not self.userid_var.get().strip():
            messagebox.showerror("Error", "Please fill in user ID")
            return

        if not self.appid_var.get().strip():
            messagebox.showerror("Error", "Please enter AppID")
            return

        # Verify if game information has been retrieved
        if not self.game_info_fetched:
            messagebox.showerror("Error", "Please get game information first")
            return

        # If generate patch is checked, perform patch related validation and configuration
        if self.generate_patch_var.get():
            # Check patch files
            if not self.check_patch_files():
                return

            # Select folder containing steamapi dll files
            if not self.select_steamapi_dll_folder():
                messagebox.showwarning(
                    "Warning", "Steamapi dll folder not selected, operation cancelled")
                return

            # Select patch type
            self.patch_type = self.select_patch_type()
            if not self.patch_type:
                messagebox.showwarning(
                    "Warning", "Patch type not selected, operation cancelled")
                return

        html_path = self.html_path_var.get()

        # Check if HTML file is provided
        if not html_path or not os.path.exists(html_path):
            self.achievement_processing_failed = True
            messagebox.showwarning(
                "Warning", "Missing SteamDB achievement HTML page, cannot display achievement configuration, please read README file for details")

        # Check html file type
        if html_path:
            if not os.path.splitext(html_path)[1].lower() == '.html':
                self.achievement_processing_failed = True
                messagebox.showerror("Warning",
                                     "Not an HTML file type, achievement retrieval failed"
                                     )
            else:
                self.achievement_processing_failed = False

        # If custom ICO icon is selected, show selection dialog
        if self.use_custom_ico_var.get():
            if not self.select_custom_ico():
                messagebox.showwarning(
                    "Warning", "ICO file not selected, operation cancelled")
                return

        # Disable button and start progress bar
        self.extract_button.config(state='disabled')
        self.progress.start()

        # Execute extraction operation in new thread
        threading.Thread(target=self._extract_worker,
                         args=(html_path,), daemon=True).start()

    def _extract_worker(self, html_path):
        game_root_path = self.game_root_path_var.get().strip()
        cmp_path = game_root_path.replace('/', '\\')
        exe_path = self.exe_path_var.get().strip()

        if not game_root_path or not os.path.exists(game_root_path):
            messagebox.showerror(
                "Error", "Please select a valid game root directory")
            self.progress.stop()
            self.status_var.set("Please reselect game root directory")
            return

        if not exe_path or not os.path.isfile(exe_path) or not exe_path.endswith(".exe"):
            messagebox.showerror("Error", "Please select an EXE file type")
            self.progress.stop()
            self.status_var.set("Please reselect game EXE file")
            return

        if not exe_path or not os.path.isfile(exe_path) or not os.path.commonpath([game_root_path, exe_path]) == cmp_path:
            messagebox.showerror(
                "Error", "Please select a valid game EXE file located within the game root directory")
            self.status_var.set(
                "Please reselect game EXE file or game root directory")
            self.progress.stop()
            return

        try:
            # Get game name
            game_name = self.game_info.get('game_name', 'Game')
            safe_game_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)

            # First copy source folder to Output/{game name} folder
            self.status_var.set("Copying source folder...")
            self.copy_source_to_output(safe_game_name)

            # Process game EXE file and icon replacement
            self.status_var.set("Processing game EXE file...")
            self.process_game_exe(safe_game_name)

            achievements = []

            # Only process achievements if HTML file is provided and not marked as failed
            if html_path and os.path.exists(html_path) and not self.achievement_processing_failed:
                self.status_var.set("Parsing HTML file...")
                # Extract achievement data
                achievements = self.extract_achievements_from_html(html_path)

                # Check achievement count
                if len(achievements) == 0:
                    messagebox.showwarning(
                        "Warning", "HTML file provided but no achievement data retrieved\nPlease get a valid SteamDB achievement HTML page, see README file for details")
                    self.achievement_processing_failed = True

                # Copy images
                if achievements:
                    self.status_var.set("Copying image files...")
                    self.copy_achievement_images(achievements, safe_game_name)

                    # Auto save JSON file
                    self.status_var.set("Saving configuration file...")
                    self.save_json_file(achievements, safe_game_name)

            # Generate configuration files
            self.status_var.set("Generating configuration files...")
            self.generate_config_files(safe_game_name)

            # Copy game images to Output folder
            self.status_var.set("Copying game images...")
            self.copy_game_images_to_output(safe_game_name)

            # Modify ColdClientLoader.ini
            self.status_var.set("Configuring launcher...")
            self.update_cold_client_loader_ini(safe_game_name)

            # Delete steamclient_loader_x64.exe
            self.status_var.set("Cleaning files...")
            self.remove_steamclient_loader(safe_game_name)

            # If generate patch is checked, execute patch generation operation
            if self.generate_patch_var.get():
                self.status_var.set("Generating patch...")
                self.generate_patch(safe_game_name)

            # Clean _temp directory
            self.status_var.set("Cleaning temporary files...")
            self.cleanup_temp_directory()

            # Update UI in main thread
            self.root.after(0, self._show_results,
                            achievements, safe_game_name)

        except Exception as e:
            messagebox.showerror("Error",
                                 "Not a valid HTML file, or not a valid SteamDB achievement page, for more information please visit README file",
                                 )
            self.progress.stop()
            self.extract_button.config(state='enable')
            self.root.after(0, lambda: self._handle_error(str(e)))

    def generate_patch(self, safe_game_name):
        """Generate patch"""

        game_root_path = self.game_root_path_var.get().strip()
        if not game_root_path or not os.path.exists(game_root_path):
            messagebox.showerror(
                "Error", "Please select a valid game root directory")
            return
        cmp_path = game_root_path.replace('/', '\\')
        if not os.path.commonpath([game_root_path, self.steamapi_dll_path]) == cmp_path:
            messagebox.showerror(
                "Error", "Please select the steamapi dll folder located within the game root directory")
            return

        try:
            # Get relative path of game root directory and steamapi dll
            game_root_path = self.game_root_path_var.get().strip()
            if not game_root_path:
                messagebox.showerror(
                    "Error", "Please select game root directory")
                return

            # Get relative path of steamapi dll files
            dll_relative_path = self.get_relative_path(
                game_root_path, self.steamapi_dll_path)

            # Create folder structure with relative path in _temp
            temp_dir = "_temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            temp_dll_path = os.path.join(temp_dir, dll_relative_path)
            if not os.path.exists(temp_dll_path):
                os.makedirs(temp_dll_path)

            # Copy corresponding DLL files based on selected type
            source_dll_dir = os.path.join("source", "GSE_DLL", self.patch_type)

            # Copy all files to temp relative path
            for item in os.listdir(source_dll_dir):
                source_item = os.path.join(source_dll_dir, item)
                target_item = os.path.join(temp_dll_path, item)

                if os.path.isfile(source_item):
                    shutil.copy2(source_item, target_item)
                    print(f"Copied DLL file: {item}")
                elif os.path.isdir(source_item):
                    if os.path.exists(target_item):
                        shutil.rmtree(target_item)
                    shutil.copytree(source_item, target_item)
                    print(f"Copied DLL folder: {item}")

            # Move steam_settings folder to relative path
            output_steam_settings = os.path.join(
                "Output", safe_game_name, "steam_settings")
            temp_steam_settings = os.path.join(temp_dll_path, "steam_settings")

            if os.path.exists(output_steam_settings):
                if os.path.exists(temp_steam_settings):
                    shutil.rmtree(temp_steam_settings)
                shutil.copytree(output_steam_settings, temp_steam_settings)
                print("Moved steam_settings folder to patch path")

            # Pack into Patch.zip
            zip_path = os.path.join("Output", safe_game_name, "Patch.zip")

            # Get the root folder name (first level of relative path)
            relative_parts = dll_relative_path.split(os.sep)
            if relative_parts:
                root_folder_name = relative_parts[0]
                root_folder_path = os.path.join(temp_dir, root_folder_name)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(root_folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Get relative path to temp_dir as zip internal path
                            arc_path = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arc_path)

                print(f"Patch generated: {zip_path}")

        except Exception as e:
            print(f"Failed to generate patch: {e}")
            messagebox.showerror("Error", f"Failed to generate patch: {e}")

    def update_cold_client_loader_ini(self, safe_game_name):
        """Modify ColdClientLoader.ini file"""
        ini_path = os.path.join(
            "Output", safe_game_name, "ColdClientLoader.ini")

        if not os.path.exists(ini_path):
            print(f"Warning: ColdClientLoader.ini file not found: {ini_path}")
            return

        try:
            # Get game name and AppID
            appid = self.appid_var.get().strip()

            # Read INI file content
            with open(ini_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Calculate game relative path
            game_relative_path = ""
            game_root_path = self.game_root_path_var.get().strip()
            game_exe_path = self.exe_path_var.get().strip()

            if game_root_path and game_exe_path and os.path.exists(game_exe_path):
                game_relative_path = self.get_relative_path(
                    game_root_path, game_exe_path)
            else:
                # If root directory or EXE path is not set, use the original logic
                if game_exe_path and os.path.exists(game_exe_path):
                    game_relative_path = os.path.basename(game_exe_path)
                else:
                    game_relative_path = f"{safe_game_name}.exe"

            # Modify Exe path
            game_relative_path = self.get_relative_path(
                game_root_path, game_exe_path).replace('\\', '/')
            exe_pattern = r'^Exe=.*$'
            new_exe_line = f"Exe={safe_game_name}"+"/"+f"{game_relative_path}"
            content = re.sub(exe_pattern, new_exe_line,
                             content, flags=re.MULTILINE)

            # Modify AppId
            appid_pattern = r'^AppId=.*$'
            new_appid_line = f"AppId={appid}"
            content = re.sub(appid_pattern, new_appid_line,
                             content, flags=re.MULTILINE)

            # Write back to file
            with open(ini_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(
                f"ColdClientLoader.ini updated: Exe: {new_exe_line}, AppId: {new_appid_line}")

        except Exception as e:
            print(f"Failed to modify ColdClientLoader.ini: {e}")

    def remove_steamclient_loader(self, safe_game_name):
        """Delete steamclient_loader_x64.exe file in Output folder"""
        loader_path = os.path.join(
            "Output", safe_game_name, "steamclient_loader_x64.exe")

        if os.path.exists(loader_path):
            try:
                os.remove(loader_path)
                print("steamclient_loader_x64.exe deleted")
            except Exception as e:
                print(f"Failed to delete steamclient_loader_x64.exe: {e}")
        else:
            print("steamclient_loader_x64.exe file does not exist, no need to delete")

    def process_game_exe(self, safe_game_name):
        """Process game EXE file and icon replacement"""
        # Check if ResourceHacker is available
        if not self.has_resource_hacker:
            # Directly copy steamclient_loader_x64.exe and rename it
            source_loader = os.path.join(
                "source", "steamclient_loader_x64.exe")
            if os.path.exists(source_loader):
                output_dir = os.path.join("Output", safe_game_name)
                final_exe_path = os.path.join(
                    output_dir, f"{safe_game_name}.exe")
                shutil.copy2(source_loader, final_exe_path)
                print(
                    f"Directly copied steamclient_loader_x64.exe to: {final_exe_path}")
                self.icon_replacement_failed = True
                messagebox.showwarning(
                    "Warning", "Unable to replace EXE icon, please check the integrity of the tool folder, see README file for details")
            return
        else:
            self.icon_replacement_failed = False

        exe_path = self.exe_path_var.get().strip()
        if not exe_path or not os.path.exists(exe_path):
            self.exe_valid = False
            print("Warning: Game EXE file not selected or file does not exist")
            # If no game EXE file is selected, also directly copy steamclient_loader_x64.exe
            source_loader = os.path.join(
                "source", "steamclient_loader_x64.exe")
            if os.path.exists(source_loader):
                output_dir = os.path.join("Output", safe_game_name)
                final_exe_path = os.path.join(
                    output_dir, f"{safe_game_name}.exe")
                shutil.copy2(source_loader, final_exe_path)
                print(
                    f"Directly copied steamclient_loader_x64.exe to: {final_exe_path}")
            return
        else:
            self.exe_valid = True

        temp_dir = "_temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Copy game EXE to _temp directory
        game_exe_temp = os.path.join(temp_dir, "game.exe")
        shutil.copy2(exe_path, game_exe_temp)
        print(f"Game EXE copied to: {game_exe_temp}")

        # Copy steamclient_loader_x64.exe to _temp directory
        source_loader = os.path.join("source", "steamclient_loader_x64.exe")
        if os.path.exists(source_loader):
            loader_temp = os.path.join(temp_dir, "steamclient_loader_x64.exe")
            shutil.copy2(source_loader, loader_temp)
            print(f"steamclient_loader_x64.exe copied to: {loader_temp}")

            # Decide which icon replacement method to use based on using custom ICO icon
            output_exe = os.path.join(temp_dir, "output.exe")
            success = False

            if self.use_custom_ico_var.get() and self.custom_ico_path:
                # Use custom ICO file
                print(f"Using custom ICO file: {self.custom_ico_path}")
                success = replace_exe_icon_with_ico(
                    self.custom_ico_path, loader_temp, output_exe)
            else:
                # Use the original icon extraction method
                print("Using game EXE icon extraction method")
                success = replace_exe_icon(
                    game_exe_temp, loader_temp, output_exe)

            if success and os.path.exists(output_exe):
                # Copy directly to Output folder
                output_dir = os.path.join("Output", safe_game_name)
                final_exe_path = os.path.join(
                    output_dir, f"{safe_game_name}.exe")
                shutil.copy2(output_exe, final_exe_path)
                print(f"Final EXE file generated: {final_exe_path}")
                self.icon_replacement_failed = False
            else:
                print("Icon replacement failed")
                self.icon_replacement_failed = True
        else:
            print(
                f"Warning: steamclient_loader_x64.exe not found in source folder: {source_loader}")

    def cleanup_temp_directory(self):
        """Clean up _temp directory"""
        temp_dir = "_temp"
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print("_temp directory cleaned up")
            except Exception as e:
                print(f"Failed to clean up _temp directory: {e}")

    def copy_source_to_output(self, safe_game_name):
        """Copy content of source folder to Output/{game name} folder, excluding GSE_DLL folder"""
        source_dir = "source"
        output_dir = os.path.join("Output", safe_game_name)

        # Create Output/{game name} folder
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # If source folder exists, copy all files and folders (excluding GSE_DLL)
        if os.path.exists(source_dir):
            for item in os.listdir(source_dir):
                # Exclude GSE_DLL folder
                if item == "GSE_DLL":
                    print(f"Skipping folder: {item}")
                    continue

                source_path = os.path.join(source_dir, item)
                target_path = os.path.join(output_dir, item)

                if os.path.isfile(source_path):
                    shutil.copy2(source_path, target_path)
                    print(f"Copied file: {item}")
                elif os.path.isdir(source_path):
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
                    print(f"Copied folder: {item}")
            overlay_config_path = os.path.join(
                output_dir, "steam_settings", "configs.overlay.ini")
            if os.path.exists(overlay_config_path) and not self.overlay_var.get():
                os.remove(overlay_config_path)
                print("Deleted file: steam_settings/configs.overlay.ini")

        else:
            print("Warning: source folder does not exist")

    def copy_game_images_to_output(self, safe_game_name):
        """Copy game images to Output/{game name}/steam_settings folder"""
        temp_dir = "_temp"
        output_steam_settings = os.path.join(
            "Output", safe_game_name, "steam_settings")

        # Ensure target folder exists
        if not os.path.exists(output_steam_settings):
            os.makedirs(output_steam_settings)

        # Copy three game images
        game_images = ["header.jpg", "logo.png", "library_600x900.jpg"]

        for image_file in game_images:
            temp_image_path = os.path.join(temp_dir, image_file)
            if os.path.exists(temp_image_path):
                target_path = os.path.join(output_steam_settings, image_file)
                try:
                    shutil.copy2(temp_image_path, target_path)
                    print(f"Copied game image successfully: {image_file}")
                except Exception as e:
                    print(f"Failed to copy game image: {image_file} - {e}")
            else:
                print(f"Game image does not exist: {temp_image_path}")

    def _show_results(self, achievements, safe_game_name):
        """Show results"""
        self.progress.stop()
        self.extract_button.config(state='normal')

        # Build result message
        result_message = f"Configuration file generation completed!\n"

        if achievements:
            result_message += f"Number of achievements: {len(achievements)}\n"
            # Set game name in achievement display window
            game_name = self.game_info.get('game_name', 'Game')
            achievement_window = AchievementDisplayWindow(
                achievements, game_name)

        # Build list of generated files
        generated_files = ["steam_settings folder"]

        # EXE file status
        if self.icon_replacement_failed:
            messagebox.showerror("Warning",
                                 "Icon replacement failed, check if game EXE file is valid and has an icon, or if the ICO icon is valid"
                                 )
        if not self.exe_valid:
            messagebox.showerror("Warning",
                                 "Please check if the game EXE file exists or is valid"
                                 )

        if self.icon_replacement_failed or not self.exe_valid:
            generated_files.append("Game EXE file (no icon)")
        else:
            generated_files.append("Game EXE file")
        # Achievement configuration status
        if self.achievement_processing_failed or self.overlay_files_missing:
            generated_files.append(
                "Achievement and interface configuration generation failed")
        else:
            generated_files.append("Achievement and interface configuration")

        generated_files.append("ColdClientLoader.ini configured")

        # If patch was generated, add it to the list
        if self.generate_patch_var.get():
            generated_files.append("Patch.zip patch file")

        result_message += f"The following files have been generated in the Output/{safe_game_name} folder:\n"
        for file_info in generated_files:
            result_message += f"- {file_info}\n"

        self.status_var.set(f"Configuration file generation successful!")
        messagebox.showinfo("Success", result_message)

    def _handle_error(self, error_msg):
        """Handle error"""
        self.progress.stop()
        self.extract_button.config(state='normal')
        self.status_var.set("Processing failed")
        messagebox.showerror("Error", f"Processing failed: {error_msg}")

    def generate_config_files(self, safe_game_name):
        """Generate configuration files"""
        # Generate configs.user.ini
        self.generate_user_config(safe_game_name)

        # Generate configs.app.ini
        self.generate_app_config(safe_game_name)

        # Generate steam_appid.txt
        self.generate_steam_appid(safe_game_name)

    def generate_user_config(self, safe_game_name):
        """Generate configs.user.ini file"""
        config_content = "[user::general]\n"
        config_content += f"account_name={self.username_var.get().strip()}\n"
        config_content += f"account_steamid={self.userid_var.get().strip()}\n"
        config_content += f"language={self.game_language.get()}\n"

        # If local save is enabled, add related configurations
        if self.local_storage_var.get():
            config_content += "\n[user::saves]\n"
            config_content += "local_save_path=./GSE Saves\n"
            config_content += "saves_folder_name=Goldberg SteamEmu Saves\n"

        # Ensure target folder exists
        config_dir = os.path.join("Output", safe_game_name, "steam_settings")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_path = os.path.join(config_dir, "configs.user.ini")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)

    def generate_app_config(self, safe_game_name):
        """Generate configs.app.ini file"""
        config_content = ""

        # Add DLC configurations
        if self.game_info and self.game_info.get('dlc_list'):
            config_content += "[app::dlcs]\n"
            config_content += "unlock_all=0\n"
            for dlc_id, dlc_name in self.game_info['dlc_list'].items():
                config_content += f"{dlc_id}={dlc_name}\n"

        if config_content:
            # Ensure target folder exists
            config_dir = os.path.join(
                "Output", safe_game_name, "steam_settings")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            config_path = os.path.join(config_dir, "configs.app.ini")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)

    def generate_steam_appid(self, safe_game_name):
        """Generate steam_appid.txt file"""
        # Ensure target folder exists
        config_dir = os.path.join("Output", safe_game_name, "steam_settings")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        appid_path = os.path.join(config_dir, "steam_appid.txt")
        with open(appid_path, 'w', encoding='utf-8') as f:
            f.write(self.appid_var.get().strip())

    def save_json_file(self, achievements, safe_game_name):
        """Auto save JSON file"""
        # Ensure target folder exists
        config_dir = os.path.join("Output", safe_game_name, "steam_settings")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        json_path = os.path.join(config_dir, "achievements.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(achievements, f, ensure_ascii=False, indent=2)

    def extract_achievements_from_html(self, html_file_path):
        """Extract achievement data"""
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        achievements = []
        achievement_divs = soup.find_all('div', class_='achievement')

        for achievement_div in achievement_divs:
            try:
                # Extract achievement ID
                achievement_id = achievement_div.get('id', '')
                name = achievement_id.replace(
                    'achievement-', '') if achievement_id.startswith('achievement-') else achievement_id

                # Extract achievement name
                achievement_name_div = achievement_div.find(
                    'div', class_='achievement_name')
                display_name = achievement_name_div.get_text(
                    strip=True) if achievement_name_div else ""

                # Extract achievement description
                achievement_desc_div = achievement_div.find(
                    'div', class_='achievement_desc')
                description_raw = achievement_desc_div.get_text(
                    strip=True) if achievement_desc_div else ""

                # Check if it's a hidden achievement
                hidden = 0
                description_clean = description_raw

                if "Hidden achievement" in description_raw:
                    hidden = 1
                    description_clean = re.sub(
                        r'Hidden achievement:\s*', '', description_raw, flags=re.IGNORECASE)

                # Extract icon
                icon_img = achievement_div.find(
                    'img', class_='achievement_image')
                icon = ""
                if icon_img and icon_img.get('src'):
                    src = icon_img.get('src')
                    filename = src.split('/')[-1]
                    icon = filename

                # Extract gray icon
                icon_gray_img = achievement_div.find(
                    'img', class_='achievement_image_small')
                icongray = ""
                if icon_gray_img and icon_gray_img.get('src'):
                    src = icon_gray_img.get('src')
                    filename = src.split('/')[-1]
                    icongray = filename

                achievement_data = {
                    "name": name,
                    "defaultvalue": 0,
                    "displayName": display_name,
                    "hidden": hidden,
                    "description": description_clean,
                    "icon": icon,
                    "icongray": icongray,
                    "icon_gray": icongray
                }

                achievements.append(achievement_data)

            except Exception as e:
                print(f"Error processing achievement: {e}")
                continue

        return achievements

    def copy_achievement_images(self, achievements, safe_game_name):
        """Copy achievement images to Output/{game name}/steam_settings/achievement_images folder"""
        source_dir = "imgs"
        target_dir = os.path.join(
            "Output", safe_game_name, "steam_settings", "achievement_images")

        # Ensure target folder exists
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        if not os.path.exists(source_dir):
            print(f"Warning: Source image folder does not exist: {source_dir}")
            return

        # Collect the needed image file names
        image_files_needed = set()
        for achievement in achievements:
            if achievement.get('icon'):
                image_files_needed.add(achievement['icon'])
            if achievement.get('icongray'):
                image_files_needed.add(achievement['icongray'])

        # Copy files to achievement_images folder
        for filename in image_files_needed:
            source_path = os.path.join(source_dir, filename)
            target_path = os.path.join(target_dir, filename)

            if os.path.exists(source_path):
                try:
                    shutil.copy2(source_path, target_path)
                    print(f"Copy successful: {filename}")
                except Exception as e:
                    print(f"Copy failed: {filename} - {e}")
            else:
                print(f"Source file does not exist: {source_path}")


def main():
    root = tk.Tk()
    app = GSEGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
