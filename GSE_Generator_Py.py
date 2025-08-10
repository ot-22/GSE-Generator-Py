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
import webbrowser


def replace_exe_icon_with_ico(ico_file: str, target_exe: str, output_exe: str) -> bool:
    resource_hacker_path = "./tool/ResourceHacker.exe"

    if not os.path.exists(resource_hacker_path):
        print(f"ResourceHacker tool not found: {resource_hacker_path}")
        return False

    if not os.path.exists(ico_file):
        print(f"ICO file not found: {ico_file}")
        return False

    if not os.path.exists(target_exe):
        print(f"Target file not found: {target_exe}")
        return False

    if not os.path.splitext(ico_file)[1].lower() == '.ico':
        messagebox.showerror(
            "Warning", "Please select an ICO file, icon replacement operation is invalid")
        return False

    try:
        shutil.copy2(target_exe, output_exe)

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
    resource_hacker_path = "./tool/ResourceHacker.exe"
    temp_icon_dir = "./temp_icon"

    if not os.path.exists(resource_hacker_path):
        print(f"ResourceHacker tool not found: {resource_hacker_path}")
        return False

    if not os.path.exists(source_exe):
        print(f"Source file not found: {source_exe}")
        return False

    if not os.path.exists(target_exe):
        print(f"Target file not found: {target_exe}")
        return False

    if not os.path.exists(temp_icon_dir):
        os.makedirs(temp_icon_dir)

    try:
        res_path = os.path.join(temp_icon_dir, "extracted_icon.res")

        print("Extracting icon resource...")
        extract_cmd = [
            resource_hacker_path,
            "-open", os.path.abspath(source_exe),
            "-save", os.path.abspath(res_path),
            "-action", "extract",
            "-mask", "ICONGROUP,,"
        ]

        result = subprocess.run(extract_cmd, capture_output=True, text=True)

        if not os.path.exists(res_path) or os.path.getsize(res_path) == 0:
            print("Icon resource extraction failed")
            print(f"ResourceHacker output: {result.stdout}")
            print(f"ResourceHacker error: {result.stderr}")
            return False

        print("Icon resource extraction successful")

        shutil.copy2(target_exe, output_exe)

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
        if os.path.exists(temp_icon_dir):
            shutil.rmtree(temp_icon_dir, ignore_errors=True)


def get_game_dlc_info(appid, web_language, use_html_mode=False, html_file_path=None):
    try:
        if use_html_mode:
            if not html_file_path:
                print("HTML mode requires html_file_path parameter")
                return {
                    'game_name': game_name,
                    'game_id': appid,
                    'dlc_list': {}
                }

            print("Using HTML file mode to get DLC information...")
            with open(html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            for td in soup.find_all('td'):
                if td.get_text() and 'App ID' in td.get_text():
                    next_td = td.find_next_sibling('td')
                    if next_td:
                        appid = next_td.get_text().strip()
                        break

            app_name_element = soup.find('h1', itemprop='name')
            if app_name_element:
                game_name = app_name_element.text.strip()

            app_rows = soup.find_all(
                'tr', class_='app', attrs={'data-appid': True})

            dlc_info = {}

            for row in app_rows:
                app_id = row.get('data-appid')
                td_tags = row.find_all('td')
                if len(td_tags) >= 2:
                    app_name_td = td_tags[1]
                    app_name = app_name_td.get_text(strip=True)
                    dlc_info[int(app_id)] = app_name

            print(f"Game name: {game_name}")
            print(f"Game ID: {appid}")
            print("-" * 50)

            if not dlc_info:
                print("No related DLC found from HTML file")
            else:
                print(f"Found {len(dlc_info)} related DLC from HTML file:")
                for dlc_id, dlc_name in dlc_info.items():
                    print(f"DLC ID: {dlc_id} - Name: {dlc_name}")

            return {
                'game_name': game_name,
                'game_id': appid,
                'dlc_list': dlc_info
            }
        else:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={web_language}"

            response = requests.get(url)
            response.raise_for_status()

            data = response.json()

            if str(appid) not in data or not data[str(appid)]['success']:
                print(f"Unable to get information for appid {appid}")
                return {}

            game_data = data[str(appid)]['data']
            game_name = game_data.get('name', 'Unknown Game')

            print(f"Game name: {game_name}")
            print(f"Game ID: {appid}")
            print("-" * 50)
            dlc_list = game_data.get('dlc', [])

            if not dlc_list:
                print("This game has no DLC")
                return {
                    'game_name': game_name,
                    'game_id': appid,
                    'dlc_list': {}
                }

            print(f"Found {len(dlc_list)} DLC:")

            dlc_info = {}

            for dlc_id in dlc_list:
                dlc_url = f"https://store.steampowered.com/api/appdetails?appids={dlc_id}&l={web_language}"

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
                    dlc_info[dlc_id] = f'Failed_{dlc_id}'

            return {
                'game_name': game_name,
                'game_id': appid,
                'dlc_list': dlc_info
            }
    except FileNotFoundError:
        print(f"HTML file {html_file_path} not found")
        return {}
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
            f"Achievement List - {len(achievements)} achievements")
        self.window.geometry("1000x800")

        self.setup_ui()
        self.display_achievements()

    def setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text=f"Achievement List ({len(self.achievements)} achievements)",
                                font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

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

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.canvas.bind("<MouseWheel>", _on_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="Close Window", command=self.window.destroy).pack(
            side=tk.RIGHT, padx=5)

    def display_achievements(self):
        if not self.achievements:
            ttk.Label(self.scrollable_frame,
                      text="No achievement data available").pack(pady=20)
            return

        for i, achievement in enumerate(self.achievements):
            self.create_achievement_widget(
                self.scrollable_frame, achievement, i)

    def create_achievement_widget(self, parent, achievement, index):
        achievement_frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1)
        achievement_frame.pack(fill=tk.X, padx=5, pady=5)

        image_frame = ttk.Frame(achievement_frame)
        image_frame.pack(side=tk.LEFT, padx=10, pady=10)

        game_name = self.game_name
        safe_game_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)

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
                    icon_label.image = photo
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

        ttk.Label(image_frame, text="").pack(pady=5)

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
                    icon_gray_label.image = photo_gray
                    icon_gray_label.pack(side=tk.TOP, pady=2)

                    ttk.Label(image_frame, text="Grayscale Icon",
                              font=("Arial", 8)).pack()
                except Exception as e:
                    ttk.Label(image_frame, text="Grayscale Icon\nLoad Failed",
                              width=12, anchor=tk.CENTER).pack(pady=2)
            else:
                ttk.Label(image_frame, text="No Grayscale Icon", width=12,
                          anchor=tk.CENTER).pack(pady=2)
        else:
            ttk.Label(image_frame, text="No Grayscale Icon", width=12,
                      anchor=tk.CENTER).pack(pady=2)

        text_frame = ttk.Frame(achievement_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=10, pady=10)

        title_text = f"#{index + 1} - name: {achievement.get('name', 'N/A')}"
        if achievement.get('hidden'):
            title_text += " [Hidden Achievement]"

        title_label = ttk.Label(
            text_frame, text=title_text, font=("Arial", 12, "bold"))
        title_label.pack(anchor=tk.W)

        display_name = achievement.get('displayName', 'N/A')
        ttk.Label(text_frame, text=f"Display Name: {display_name}", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=(5, 0))

        description = achievement.get('description', 'N/A')
        desc_label = ttk.Label(text_frame, text=f"Description: {description}", font=(
            "Arial", 9), wraplength=500)
        desc_label.pack(anchor=tk.W, pady=(2, 0))

        defaultvalue = achievement.get('defaultvalue', 0)
        ttk.Label(text_frame, text=f"Default Value: {defaultvalue}", font=(
            "Arial", 8), foreground="blue").pack(anchor=tk.W, pady=(5, 0))

        if icon_path:
            ttk.Label(text_frame, text=f"Normal Icon Path: Output/{safe_game_name}/steam_settings/achievement_images/{icon_path}", font=(
                "Arial", 8), foreground="gray").pack(anchor=tk.W, pady=(2, 0))

        if icon_gray_path:
            ttk.Label(text_frame, text=f"Grayscale Icon Path: Output/{safe_game_name}/steam_settings/achievement_images/{icon_gray_path}", font=(
                "Arial", 8), foreground="gray").pack(anchor=tk.W, pady=(0, 0))

        ttk.Separator(parent, orient='horizontal').pack(
            fill=tk.X, padx=5, pady=5)


class GSEGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(
            "GSE Generator - Steam Game Configuration File Generator")
        self.root.geometry("1300x880")
        self.root.resizable(True, True)

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
        self.community_achievement_html = ""

        self.missing_core_files = []
        self.missing_overlay_files = []
        self.has_resource_hacker = True
        self.icon_replacement_failed = False
        self.achievement_processing_failed = False
        self.overlay_files_missing = False
        self.exe_valid = True

        self.generate_patch_var = tk.BooleanVar(value=False)
        self.game_root_path_var = tk.StringVar()
        self.steamapi_dll_path = ""
        self.patch_type = ""

        self.check_directory_integrity()

        self.setup_ui()
        if os.path.isfile("dlc.html"):
            self.info_html_path_var.set("dlc.html")
        if os.path.isfile("achdb.html"):
            self.achievement_html_path_var.set("achdb.html")
        if os.path.isfile("achs.html"):
            self.community_achievement_html = "achs.html"

    def check_directory_integrity(self):
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

        overlay_files = [
            "steam_settings/configs.overlay.ini",
            "steam_settings/sounds/overlay_achievement_notification.wav",
            "steam_settings/fonts/Roboto-Medium.ttf"
        ]

        for file in overlay_files:
            if not os.path.exists(os.path.join("source", file)):
                self.missing_overlay_files.append(file)

        if not os.path.exists("tool/ResourceHacker.exe"):
            self.has_resource_hacker = False

        if self.missing_core_files:
            missing_files_str = ", ".join(self.missing_core_files)
            messagebox.showerror(
                "Missing Core Files",
                f"The following core files are missing: {missing_files_str}, unable to generate configuration, please read the README file for details"
            )

        if self.missing_overlay_files:
            missing_files_str = ", ".join(self.missing_overlay_files)
            messagebox.showwarning(
                "Missing Overlay Files",
                f"The following overlay core files are missing: {missing_files_str}, the in-game overlay may not work properly, please read the README file for details"
            )
            self.overlay_files_missing = True

    def check_patch_files(self):
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
                "Missing Patch Files",
                f"The following patch files are missing, unable to generate the patch:\n{missing_files_str}"
            )
            return False

        return True

    def get_relative_path(self, base_path, target_path):
        base_path = os.path.normpath(base_path)
        target_path = os.path.normpath(target_path)

        try:
            relative_path = os.path.relpath(target_path, base_path)
            if relative_path.startswith('..'):
                return target_path
            return relative_path
        except ValueError:
            return target_path

    def setup_ui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        left_frame.config(width=1000)

        self.right_frame = ttk.LabelFrame(
            main_container, text="Game Information", padding="15")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH,
                              expand=True, padx=(10, 0))
        self.right_frame.config(width=500)

        self.setup_left_panel(left_frame)
        self.setup_right_panel()

    def setup_left_panel(self, parent):
        # Create main scrollable frame
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

        # Main frame
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

        # Fetch game info button
        self.fetch_button = ttk.Button(
            appid_frame, text="Fetch Game Info", command=self.fetch_game_info)
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

        # Local Save
        self.local_storage_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable Local Save", variable=self.local_storage_var).grid(
            row=4, column=5, columnspan=2, sticky=tk.W, pady=5)

        # In-game overlay
        self.overlay_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable In-game Overlay", variable=self.overlay_var).grid(
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
        root_select_frame.pack(fill=tk.X, pady=2)

        root_entry = ttk.Entry(
            root_select_frame, textvariable=self.game_root_path_var, width=50)
        root_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        ttk.Button(root_select_frame, text="Browse...",
                   command=self.browse_game_root_folder).pack(side=tk.RIGHT)

        # Game EXE file selection
        ttk.Label(file_frame, text="Game EXE File:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W)

        exe_select_frame = ttk.Frame(file_frame)
        exe_select_frame.pack(fill=tk.X, pady=2)

        self.exe_path_var = tk.StringVar()
        exe_entry = ttk.Entry(
            exe_select_frame, textvariable=self.exe_path_var, width=50)
        exe_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        ttk.Button(exe_select_frame, text="Browse...",
                   command=self.browse_exe_file).pack(side=tk.RIGHT)

        # Game info HTML file selection
        ttk.Label(file_frame, text="Game Info HTML File:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=2)

        file_select_frame = ttk.Frame(file_frame, width=20)
        file_select_frame.pack(fill=tk.X, pady=2)

        self.info_html_path_var = tk.StringVar()
        entry = ttk.Entry(file_select_frame,
                          textvariable=self.info_html_path_var, width=30)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        ttk.Button(file_select_frame, text="Browse...",
                   command=self.browse_info_html_file).pack(side=tk.RIGHT)

        # Achievement HTML file selection
        ttk.Label(file_frame, text="Achievement HTML File:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=2)

        file_select_frame = ttk.Frame(file_frame, width=20)
        file_select_frame.pack(fill=tk.X, pady=2)

        self.achievement_html_path_var = tk.StringVar()
        entry = ttk.Entry(file_select_frame,
                          textvariable=self.achievement_html_path_var, width=30)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        ttk.Button(file_select_frame, text="Browse...",
                   command=self.browse_achievement_html_file).pack(side=tk.RIGHT)

        # Image folder instruction
        info_frame = ttk.Frame(file_frame)
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text="📁 Please ensure there is an 'imgs' folder with achievement images in current directory",
                  foreground="red").pack(anchor=tk.W)

        # Info page hyperlink
        info_link = ttk.Label(
            info_frame,
            text="Info Page",
            foreground="blue",
            cursor="hand2"
        )
        info_link.pack(side=tk.LEFT, padx=(0, 20))
        info_link.bind(
            "<Button-1>", lambda e: self.open_url(f"https://steamdb.info/app/{self.appid_var.get()}/dlc/"))

        # SteamDB achievement page hyperlink
        achievement_link = ttk.Label(
            info_frame,
            text="SteamDB Achievement Page",
            foreground="blue",
            cursor="hand2"
        )
        achievement_link.pack(side=tk.LEFT, padx=(0, 20))
        achievement_link.bind(
            "<Button-1>", lambda e: self.open_url(f"https://steamdb.info/app/{self.appid_var.get()}/stats/"))

        # Community achievement page hyperlink
        achievement_link = ttk.Label(
            info_frame,
            text="Steam Community Achievement Page",
            foreground="blue",
            cursor="hand2"
        )
        achievement_link.pack(side=tk.LEFT, padx=(0, 20))
        achievement_link.bind(
            "<Button-1>", lambda e: self.open_url(f"https://steamcommunity.com/stats/{self.appid_var.get()}/achievements/?l={self.game_language.get()}"))

        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        initial_state = 'disabled' if self.missing_core_files else 'disabled'
        self.extract_button = ttk.Button(button_frame, text="Generate Config File",
                                         command=self.extract_achievements, state=initial_state)
        self.extract_button.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="Exit Program",
                   command=self.root.quit).pack(side=tk.RIGHT)

        # Status bar
        initial_status = "Core files missing, cannot generate config" if self.missing_core_files else "Please fetch game info: provide AppID (required), game info HTML file (optional, improves DLC list accuracy)"
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
            if not self.check_patch_files():
                self.generate_patch_var.set(False)

    def browse_game_root_folder(self):
        """Browse game root directory"""
        folder = filedialog.askdirectory(title="Select Game Root Directory")
        if folder:
            self.game_root_path_var.set(folder)
            self.check_enable_extract_button()

    def setup_right_panel(self):
        """Setup right information panel"""
        # Game Header image display area
        self.header_frame = ttk.Frame(self.right_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        self.header_label = ttk.Label(self.header_frame, text="No game info\nPlease enter AppID and click\n'Fetch Game Info'",
                                      anchor=tk.CENTER, background="lightgray", width=40)
        self.header_label.pack(fill=tk.X, pady=5)

        # Game Logo display area
        self.logo_frame = ttk.Frame(self.right_frame)
        self.logo_frame.pack(fill=tk.X, pady=(0, 10))

        self.logo_label = ttk.Label(self.logo_frame, text="Game Logo",
                                    anchor=tk.CENTER, background="lightgray", width=40)
        self.logo_label.pack(fill=tk.X, pady=5)

        # Game name
        self.game_name_var = tk.StringVar(value="Not fetched")
        ttk.Label(self.right_frame, text="Game Name:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=(5, 0))
        self.game_name_label = ttk.Label(self.right_frame, textvariable=self.game_name_var,
                                         font=("Arial", 9), wraplength=400)
        self.game_name_label.pack(anchor=tk.W, padx=(10, 0))

        # DLC info title
        ttk.Label(self.right_frame, text="DLC Info:", font=(
            "Arial", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))

        # DLC scrollable list
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
        """Select folder containing steamapi dll file"""
        folder = filedialog.askdirectory(
            title="Select Folder Containing Steamapi DLL File")
        if folder:
            self.steamapi_dll_path = folder
            return True
        return False

    def select_patch_type(self):
        """Select patch type"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Patch Type")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() +
                        50, self.root.winfo_rooty() + 50))

        result = tk.StringVar(value="")

        ttk.Label(dialog, text="Please select the type to apply to steamapi dll:",
                  font=("Arial", 9)).pack(pady=20)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def select_regular():
            result.set("regular")
            dialog.destroy()

        def select_experimental():
            result.set("experimental")
            dialog.destroy()

        ttk.Button(button_frame, text="Regular", command=select_regular,
                   width=10).pack(side=tk.LEFT, padx=20)
        ttk.Button(button_frame, text="Experimental", command=select_experimental,
                   width=10).pack(side=tk.LEFT, padx=20)

        dialog.wait_window()

        return result.get()

    def select_local_achievement(self):
        response = messagebox.askyesno(
            title="Question",
            message="Use local\nSteam Community achievement html?",
            icon="question"
        )
        if response:
            success = self.select_community_achievement_html()
            if success:
                return True
            else:
                messagebox.showwarning(
                    "Warning", "Cannot generate localized achievements")
                return False
        else:
            return False

    def select_community_achievement_html(self):
        """Select Steam Community achievement html"""
        filename = filedialog.askopenfilename(
            title="Steam Community Achievement HTML File",
            filetypes=[("HTML files", "*.html *.htm")]
        )
        if filename:
            self.community_achievement_html = filename
            return True
        messagebox.showwarning(
            "Warning", "Selection cancelled, cannot generate localized achievements")
        return False

    def fetch_game_info(self):
        """Fetch game information"""
        appid = self.appid_var.get().strip()
        if not self.info_html_path_var.get().strip() and not self.appid_var.get().strip():
            messagebox.showerror("Error", "Please enter AppID first")
            return

        if not self.info_html_path_var.get().strip():
            try:
                appid = int(appid)
            except ValueError:
                messagebox.showerror("Error", "AppID must be numeric")
                return

        self.fetch_button.config(state='disabled')
        self.fetch_button.config(text="Fetching...")

        threading.Thread(target=self._fetch_game_info_worker,
                         args=(appid,), daemon=True).start()

    def _fetch_game_info_worker(self, appid):
        """Game info fetching worker thread"""
        html_path = self.info_html_path_var.get()

        if not html_path or not os.path.exists(html_path):
            html_mode = False
        else:
            html_mode = True

        if html_path:
            if not os.path.splitext(html_path)[1].lower() == '.html':
                html_mode = False
                messagebox.showerror("Warning",
                                     "SteamDB game info HTML file is not HTML type, will fetch possibly inaccurate game info from Steam (especially DLC info)"
                                     )

        try:
            web_language = self.game_language.get()
            self.game_info = get_game_dlc_info(
                appid, web_language, html_mode, html_path)
            id = self.game_info.get('game_id', '')
            self.appid_var.set(id)

            if self.game_info:
                self.download_game_images(id)

            self.root.after(0, self._update_game_info_ui)

        except Exception as e:
            print(e)

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
                print("Header image downloaded successfully")

            # Download Logo
            logo_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/logo.png"
            logo_response = requests.get(logo_url)
            if logo_response.status_code == 200:
                logo_path = os.path.join(temp_dir, "logo.png")
                with open(logo_path, "wb") as f:
                    f.write(logo_response.content)
                print("Logo downloaded successfully")

            # Download library cover
            library_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
            library_response = requests.get(library_url)
            if library_response.status_code == 200:
                library_path = os.path.join(temp_dir, "library_600x900.jpg")
                with open(library_path, "wb") as f:
                    f.write(library_response.content)
                print("Library cover downloaded successfully")

        except Exception as e:
            print(f"Failed to download images: {e}")

    def _update_game_info_ui(self):
        """Update game info UI"""
        self.fetch_button.config(state='normal')
        self.fetch_button.config(text="Fetch Game Info")

        if not self.game_info:
            messagebox.showerror(
                "Error", "Failed to fetch game info, please check network or use network proxy")
            return

        self.game_info_fetched = True
        self.check_enable_extract_button()

        # Update game name
        game_name = self.game_info.get('game_name', 'Unknown Game')
        self.game_name_var.set(game_name)

        self.update_header_display()
        self.update_logo_display()
        self.update_dlc_display()

        self.status_var.set("Game info fetched successfully!")
        messagebox.showinfo("Success", "Game info fetched successfully!")

    def check_enable_extract_button(self):
        """Check if generate config file button can be enabled"""
        if self.missing_core_files:
            self.extract_button.config(state='disabled')
            return

        game_root_path = self.game_root_path_var.get().strip()
        if not game_root_path:
            self.extract_button.config(state='disabled')
            self.status_var.set("Please select game root directory")
            return

        if self.game_info_fetched:
            exe_path = self.exe_path_var.get().strip()

            if self.has_resource_hacker:
                if exe_path and os.path.exists(exe_path):
                    self.extract_button.config(state='normal')
                    self.status_var.set("Ready to generate config file")
                elif self.use_custom_ico_var.get():
                    self.extract_button.config(state='normal')
                    self.status_var.set(
                        "Ready to generate config file (using custom ICO)")
                else:
                    self.extract_button.config(state='disabled')
                    self.status_var.set("Please select game EXE file")
            else:
                self.extract_button.config(state='normal')
                self.status_var.set(
                    "Ready to generate config file (will use default EXE)")
        else:
            self.extract_button.config(state='disabled')
            self.status_var.set("Please fetch game info first")

    def update_header_display(self):
        """Update Header image display"""
        header_path = os.path.join("_temp", "header.jpg")
        if os.path.exists(header_path):
            try:
                img = Image.open(header_path)
                img.thumbnail((450, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                self.header_label.config(image=photo, text="")
                self.header_label.image = photo
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
                img.thumbnail((400, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                self.logo_label.config(image=photo, text="")
                self.logo_label.image = photo
            except Exception as e:
                self.logo_label.config(text=f"Logo load failed\n{str(e)}")
        else:
            self.logo_label.config(text="Logo download failed")

    def update_dlc_display(self):
        """Update DLC display"""
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
        """Handle fetch info error"""
        self.fetch_button.config(state='normal')
        self.fetch_button.config(text="Fetch Game Info")
        messagebox.showerror(
            "Error", "Failed to fetch game info, please check network or use network proxy")

    def on_language_change(self, event=None):
        """Update game_language variable when language selection changes"""
        selected_language = self.language_var.get()
        if selected_language in self.language_mapping:
            self.game_language.set(self.language_mapping[selected_language])

    def browse_achievement_html_file(self):
        filename = filedialog.askopenfilename(
            title="Select Achievement HTML File",
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*.*")]
        )
        if filename:
            self.achievement_html_path_var.set(filename)

    def open_url(self, url):
        if self.appid_var.get().strip():
            webbrowser.open(url)
        else:
            messagebox.showwarning("Warning", "Please enter AppID")

    def browse_info_html_file(self):
        filename = filedialog.askopenfilename(
            title="Select Game Info HTML File",
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*.*")]
        )
        if filename:
            self.info_html_path_var.set(filename)

    def extract_achievements(self):
        # Validate required fields
        if not self.username_var.get().strip():
            messagebox.showerror("Error", "Please fill in username")
            return

        if not self.userid_var.get().strip():
            messagebox.showerror("Error", "Please fill in user ID")
            return

        if not self.info_html_path_var.get().strip() and not self.appid_var.get().strip():
            messagebox.showerror("Error", "Please enter AppID")
            return

        # Verify game info has been fetched
        if not self.game_info_fetched:
            messagebox.showerror("Error", "Please fetch game info first")
            return

        # If generate patch is checked, perform patch-related validation and configuration
        if self.generate_patch_var.get():
            if not self.check_patch_files():
                return

            if not self.select_steamapi_dll_folder():
                messagebox.showwarning(
                    "Warning", "Steamapi dll folder not selected, operation cancelled")
                return

            self.patch_type = self.select_patch_type()
            if not self.patch_type:
                messagebox.showwarning(
                    "Warning", "Patch type not selected, operation cancelled")
                return

        html_path = self.achievement_html_path_var.get()

        if not html_path or not os.path.exists(html_path):
            self.achievement_processing_failed = True
            messagebox.showwarning(
                "Warning", "Missing SteamDB achievement HTML page, cannot display achievement configuration, please read README file for details")

        if html_path:
            if not os.path.splitext(html_path)[1].lower() == '.html':
                self.achievement_processing_failed = True
                messagebox.showerror("Warning",
                                     "Not HTML file type, achievement fetch failed"
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

        # Execute extraction in new thread
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
            self.status_var.set("Please reselect the game root directory")
            return

        if not exe_path or not os.path.isfile(exe_path) or not exe_path.endswith(".exe"):
            messagebox.showerror("Error", "Please select an EXE file")
            self.progress.stop()
            self.status_var.set("Please reselect the game EXE file")
            return

        if not exe_path or not os.path.isfile(exe_path) or not os.path.commonpath([game_root_path, exe_path]) == cmp_path:
            messagebox.showerror(
                "Error", "Please select a valid game EXE file within the game root directory")
            self.status_var.set(
                "Please reselect the game EXE file or the game root directory")
            self.progress.stop()
            return

        try:
            game_name = self.game_info.get('game_name', 'Game')
            safe_game_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)

            self.status_var.set("Copying source folder...")
            self.copy_source_to_output(safe_game_name)

            self.status_var.set("Processing game EXE file...")
            self.process_game_exe(safe_game_name)

            achievements = []

            if html_path and os.path.exists(html_path) and not self.achievement_processing_failed:
                self.status_var.set("Parsing HTML file...")
                achievements = self.extract_achievements_from_html(html_path)

                if len(achievements) == 0:
                    messagebox.showwarning(
                        "Warning", "HTML file provided but no achievement data extracted\nPlease get a valid SteamDB achievements HTML page, see README for details")
                    self.achievement_processing_failed = True

                if achievements:
                    self.status_var.set("Copying image files...")
                    self.copy_achievement_images(achievements, safe_game_name)

                    self.status_var.set("Saving configuration file...")
                    self.save_json_file(achievements, safe_game_name)

            self.status_var.set("Generating configuration files...")
            self.generate_config_files(safe_game_name)

            self.status_var.set("Copying game images...")
            self.copy_game_images_to_output(safe_game_name)

            self.status_var.set("Configuring the launcher...")
            self.update_cold_client_loader_ini(safe_game_name)

            self.status_var.set("Cleaning up files...")
            self.remove_steamclient_loader(safe_game_name)

            if self.generate_patch_var.get():
                self.status_var.set("Generating patch...")
                self.generate_patch(safe_game_name)

            self.status_var.set("Cleaning up temporary files...")
            self.cleanup_temp_directory()

            self.root.after(0, self._show_results,
                            achievements, safe_game_name)

        except Exception as e:
            messagebox.showerror("Error",
                                 f"Invalid HTML file, or not a valid SteamDB achievements page, see README for more information\nInfo: {e}",
                                 )
            self.progress.stop()
            self.extract_button.config(state='enable')

    def generate_patch(self, safe_game_name):
        game_root_path = self.game_root_path_var.get().strip()
        if not game_root_path or not os.path.exists(game_root_path):
            messagebox.showerror(
                "Error", "Please select a valid game root directory")
            return
        cmp_path = game_root_path.replace('/', '\\')
        if not os.path.commonpath([game_root_path, self.steamapi_dll_path]) == cmp_path:
            messagebox.showerror(
                "Error", "Please select the steamapi dll folder within the game root directory")
            return

        try:
            game_root_path = self.game_root_path_var.get().strip()
            if not game_root_path:
                messagebox.showerror(
                    "Error", "Please select the game root directory")
                return

            dll_relative_path = self.get_relative_path(
                game_root_path, self.steamapi_dll_path)

            temp_dir = "_temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            temp_dll_path = os.path.join(temp_dir, dll_relative_path)
            if not os.path.exists(temp_dll_path):
                os.makedirs(temp_dll_path)

            source_dll_dir = os.path.join("source", "GSE_DLL", self.patch_type)

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

            output_steam_settings = os.path.join(
                "Output", safe_game_name, "steam_settings")
            temp_steam_settings = os.path.join(temp_dll_path, "steam_settings")

            if os.path.exists(output_steam_settings):
                if os.path.exists(temp_steam_settings):
                    shutil.rmtree(temp_steam_settings)
                shutil.copytree(output_steam_settings, temp_steam_settings)
                print("Moved steam_settings folder to patch path")

            zip_path = os.path.join("Output", safe_game_name, "Patch.zip")

            relative_parts = dll_relative_path.split(os.sep)
            if relative_parts:
                root_folder_name = relative_parts[0]
                root_folder_path = os.path.join(temp_dir, root_folder_name)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(root_folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arc_path)

                print(f"Patch generated: {zip_path}")

        except Exception as e:
            print(f"Failed to generate patch: {e}")
            messagebox.showerror("Error", f"Failed to generate patch: {e}")

    def update_cold_client_loader_ini(self, safe_game_name):
        ini_path = os.path.join(
            "Output", safe_game_name, "ColdClientLoader.ini")

        if not os.path.exists(ini_path):
            print(
                f"Warning: ColdClientLoader.ini file does not exist: {ini_path}")
            return

        try:
            appid = self.appid_var.get().strip()

            with open(ini_path, 'r', encoding='utf-8') as f:
                content = f.read()

            game_relative_path = ""
            game_root_path = self.game_root_path_var.get().strip()
            game_exe_path = self.exe_path_var.get().strip()

            if game_root_path and game_exe_path and os.path.exists(game_exe_path):
                game_relative_path = self.get_relative_path(
                    game_root_path, game_exe_path)
            else:
                if game_exe_path and os.path.exists(game_exe_path):
                    game_relative_path = os.path.basename(game_exe_path)
                else:
                    game_relative_path = f"{safe_game_name}.exe"

            game_relative_path = self.get_relative_path(
                game_root_path, game_exe_path).replace('\\', '/')
            exe_pattern = r'^Exe=.*$'
            new_exe_line = f"Exe={safe_game_name}"+"/"+f"{game_relative_path}"
            content = re.sub(exe_pattern, new_exe_line,
                             content, flags=re.MULTILINE)

            appid_pattern = r'^AppId=.*$'
            new_appid_line = f"AppId={appid}"
            content = re.sub(appid_pattern, new_appid_line,
                             content, flags=re.MULTILINE)

            if self.overlay_var.get():
                appid_pattern = r'^ForceInjectGameOverlayRenderer=.*$'
                new_appid_line = f"ForceInjectGameOverlayRenderer=1"
                content = re.sub(appid_pattern, new_appid_line,
                                 content, flags=re.MULTILINE)

            with open(ini_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(
                f"ColdClientLoader.ini updated: Exe: {new_exe_line}, AppId: {new_appid_line}")

        except Exception as e:
            print(f"Failed to modify ColdClientLoader.ini: {e}")

    def remove_steamclient_loader(self, safe_game_name):
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
        if not self.has_resource_hacker:
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
                    "Warning", "Failed to replace EXE icon, please check the integrity of the tool folder, see README for details")
            return
        else:
            self.icon_replacement_failed = False

        exe_path = self.exe_path_var.get().strip()
        if not exe_path or not os.path.exists(exe_path):
            self.exe_valid = False
            print("Warning: Game EXE file not selected or does not exist")
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

        game_exe_temp = os.path.join(temp_dir, "game.exe")
        shutil.copy2(exe_path, game_exe_temp)
        print(f"Game EXE copied to: {game_exe_temp}")

        source_loader = os.path.join("source", "steamclient_loader_x64.exe")
        if os.path.exists(source_loader):
            loader_temp = os.path.join(temp_dir, "steamclient_loader_x64.exe")
            shutil.copy2(source_loader, loader_temp)
            print(f"steamclient_loader_x64.exe copied to: {loader_temp}")

            output_exe = os.path.join(temp_dir, "output.exe")
            success = False

            if self.use_custom_ico_var.get() and self.custom_ico_path:
                print(f"Using custom ICO file: {self.custom_ico_path}")
                success = replace_exe_icon_with_ico(
                    self.custom_ico_path, loader_temp, output_exe)
            else:
                print("Using game EXE icon extraction method")
                success = replace_exe_icon(
                    game_exe_temp, loader_temp, output_exe)

            if success and os.path.exists(output_exe):
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
                f"Warning: steamclient_loader_x64.exe does not exist in the source folder: {source_loader}")

    def cleanup_temp_directory(self):
        temp_dir = "_temp"
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print("_temp directory cleaned up")
            except Exception as e:
                print(f"Failed to clean up _temp directory: {e}")

    def copy_source_to_output(self, safe_game_name):
        source_dir = "source"
        output_dir = os.path.join("Output", safe_game_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if os.path.exists(source_dir):
            for item in os.listdir(source_dir):
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
        temp_dir = "_temp"
        output_steam_settings = os.path.join(
            "Output", safe_game_name, "steam_settings")

        if not os.path.exists(output_steam_settings):
            os.makedirs(output_steam_settings)

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
        self.progress.stop()
        self.extract_button.config(state='normal')

        result_message = f"Configuration files generated successfully!\n"

        if achievements:
            result_message += f"Number of achievements: {len(achievements)}\n"
            game_name = self.game_info.get('game_name', 'Game')
            achievement_window = AchievementDisplayWindow(
                achievements, game_name)

        generated_files = ["steam_settings folder"]

        if self.icon_replacement_failed:
            messagebox.showerror("Warning",
                                 "Failed to replace the icon, please check if the game EXE file is valid and has an icon, or if the ICO file is valid"
                                 )
        if not self.exe_valid:
            messagebox.showerror("Warning",
                                 "Please check if the game EXE file exists or is valid"
                                 )

        if self.icon_replacement_failed or not self.exe_valid:
            generated_files.append("Game EXE file (no icon)")
        else:
            generated_files.append("Game EXE file")

        if self.achievement_processing_failed or self.overlay_files_missing:
            generated_files.append(
                "Failed to generate achievements and UI configuration")
        else:
            generated_files.append("Achievements and UI configuration")

        generated_files.append("Configured ColdClientLoader.ini")

        if self.generate_patch_var.get():
            generated_files.append("Patch.zip patch file")

        result_message += f"The following files have been generated in the Output/{safe_game_name} folder:\n"
        for file_info in generated_files:
            result_message += f"- {file_info}\n"

        self.status_var.set(f"Configuration files generated successfully!")
        messagebox.showinfo("Success", result_message)

    def generate_config_files(self, safe_game_name):
        self.generate_user_config(safe_game_name)
        self.generate_app_config(safe_game_name)
        self.generate_steam_appid(safe_game_name)

    def generate_user_config(self, safe_game_name):
        config_content = "[user::general]\n"
        config_content += f"account_name={self.username_var.get().strip()}\n"
        config_content += f"account_steamid={self.userid_var.get().strip()}\n"
        config_content += f"language={self.game_language.get()}\n"

        if self.local_storage_var.get():
            config_content += "\n[user::saves]\n"
            config_content += "local_save_path=./GSE Saves\n"
            config_content += "saves_folder_name=Goldberg SteamEmu Saves\n"

        config_dir = os.path.join("Output", safe_game_name, "steam_settings")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_path = os.path.join(config_dir, "configs.user.ini")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)

    def generate_app_config(self, safe_game_name):
        config_content = ""

        if self.game_info and self.game_info.get('dlc_list'):
            config_content += "[app::dlcs]\n"
            config_content += "unlock_all=0\n"
            for dlc_id, dlc_name in self.game_info['dlc_list'].items():
                config_content += f"{dlc_id}={dlc_name}\n"

        if config_content:
            config_dir = os.path.join(
                "Output", safe_game_name, "steam_settings")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            config_path = os.path.join(config_dir, "configs.app.ini")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)

    def generate_steam_appid(self, safe_game_name):
        config_dir = os.path.join("Output", safe_game_name, "steam_settings")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        appid_path = os.path.join(config_dir, "steam_appid.txt")
        with open(appid_path, 'w', encoding='utf-8') as f:
            f.write(self.appid_var.get().strip())

    def save_json_file(self, achievements, safe_game_name):
        config_dir = os.path.join("Output", safe_game_name, "steam_settings")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        json_path = os.path.join(config_dir, "achievements.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(achievements, f, ensure_ascii=False, indent=2)

    def extract_achievements_from_html(self, html_file_path):
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        achievements = []
        achievement_divs = soup.find_all('div', class_='achievement')

        sc_accesible = True
        enable_local_html = False

        if not os.path.isfile("achs.html"):
            steamcommunity_url = f"https://steamcommunity.com/stats/{self.appid_var.get()}/achievements/?l={self.game_language.get()}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            try:
                steamcommunity_response = requests.get(
                    steamcommunity_url, headers=headers, timeout=10)
                steamcommunity_response.raise_for_status()
                community_html_file = steamcommunity_response.content
            except requests.RequestException as e:
                print(f"Failed to access SteamCommunity page: {e}")
                messagebox.showwarning(
                    "Warning", f"Unable to access SteamCommunity, please check your network connection\nError: {e}")
                success = self.select_local_achievement()
                if not success:
                    sc_accesible = False
                else:
                    enable_local_html = True
        else:
            enable_local_html = True

        if enable_local_html:
            path = self.community_achievement_html
            with open(path, 'r', encoding='utf-8') as file:
                community_html_file = file.read()

        for achievement_div in achievement_divs:
            try:
                achievement_id = achievement_div.get('id', '')
                name = achievement_id.replace(
                    'achievement-', '') if achievement_id.startswith('achievement-') else achievement_id

                achievement_name_div = achievement_div.find(
                    'div', class_='achievement_name')
                display_name = achievement_name_div.get_text(
                    strip=True) if achievement_name_div else ""

                achievement_desc_div = achievement_div.find(
                    'div', class_='achievement_desc')
                description_raw = achievement_desc_div.get_text(
                    strip=True) if achievement_desc_div else ""

                hidden = 0
                description_clean = description_raw

                if "Hidden achievement" in description_raw:
                    hidden = 1
                    description_clean = re.sub(
                        r'Hidden achievement:\s*', '', description_raw, flags=re.IGNORECASE)

                icon_img = achievement_div.find(
                    'img', class_='achievement_image')
                icon = ""
                if icon_img and icon_img.get('src'):
                    src = icon_img.get('src')
                    filename = src.split('/')[-1]
                    icon = filename

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
                messagebox.showwarning(
                    "Warning", "Error processing achievement")
                continue

        if sc_accesible:
            steamcommunity_soup = BeautifulSoup(
                community_html_file, 'html.parser')
            achievement_rows = steamcommunity_soup.find_all(
                'div', class_='achieveRow')

            for achievement_row, achievement in zip(achievement_rows, achievements):
                try:
                    achieve_txt_div = achievement_row.find(
                        'div', class_='achieveTxt')
                    if achieve_txt_div:
                        h3_tag = achieve_txt_div.find('h3')
                        h5_tag = achieve_txt_div.find('h5')
                        if h3_tag and h5_tag:
                            display_name = h3_tag.text.strip()
                            description = h5_tag.text.strip()
                    if achievement_name_div and achievement_desc_div:
                        achievement['displayName'] = display_name
                        achievement['description'] = description
                except Exception as e:
                    print(
                        f"Error getting achievement info from SteamCommunity page: {e}")
                    messagebox.showwarning(
                        "Warning", "Error getting achievement info from SteamCommunity page")

        return achievements

    def copy_achievement_images(self, achievements, safe_game_name):
        source_dir = "imgs"
        target_dir = os.path.join(
            "Output", safe_game_name, "steam_settings", "achievement_images")

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        if not os.path.exists(source_dir):
            print(f"Warning: Source image folder does not exist: {source_dir}")
            return

        image_files_needed = set()
        for achievement in achievements:
            if achievement.get('icon'):
                image_files_needed.add(achievement['icon'])
            if achievement.get('icongray'):
                image_files_needed.add(achievement['icongray'])

        for filename in image_files_needed:
            source_path = os.path.join(source_dir, filename)
            target_path = os.path.join(target_dir, filename)

            if os.path.exists(source_path):
                try:
                    shutil.copy2(source_path, target_path)
                    print(f"Copied successfully: {filename}")
                except Exception as e:
                    print(f"Failed to copy: {filename} - {e}")
            else:
                print(f"Source file does not exist: {source_path}")


def main():
    root = tk.Tk()
    app = GSEGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
