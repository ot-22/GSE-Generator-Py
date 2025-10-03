# GSE Generator Py

A stable Goldberg Steam Emulator configuration generation tool

## Interface

![img1](https://img.cdn1.vip/i/68de658658cc5_1759405446.webp)

## Features

- Retrieve game information and DLC list based on AppID
- Parse SteamDB pages to generate GSE-compatible achievement images and `achievements.json` for in-game overlay achievement functionality
- Generate `steam_settings` configuration files based on parameters
- Provide GUI for parameter input, achievement list display, and game information viewing
- Embed game executable icons or custom .ico icons into `steamclient_loader.exe`



## Required Files

```
source
├── GSE_DLL
│   ├── experimental
│   │   ├── steam_api.dll
│   │   └── steam_api64.dll
│   └── regular
│       ├── steam_api.dll
│       └── steam_api64.dll
├── GameOverlayRenderer.dll
├── GameOverlayRenderer64.dll
├── steamclient.dll
├── steamclient64.dll
└── steamclient_loader_x64.exe
```

These files can be obtained from GSE [Releases](https://github.com/Detanup01/gbe_fork/releases)

## How to Use

### Information Retrieval Modes:

Since certain essential information must be retrieved from SteamDB, and accessing the SteamDB website often encounters verification challenges—which significantly increases the likelihood of retrieval failures for both achievement lists and their corresponding images — the solution involves manually downloading offline .htmlpages via a browser (Chrome or Edge) for parsing and extracting the required data. Additionally, some information is also available through online retrieval modes for convenience.

- **Application Main Information:**
  - Online Mode: Provide AppID, and the generator will parse game name and DLC list from Steam Store API, but the DLC list may not be accurate
  - Local Mode: Generator automatically parse AppID, game name, and DLC list from local HTML files. This method is more accurate and stable. Download the local webpage from specific SteamDB pages. You can rename the downloaded Info Page to `dlc.html` and place it in the application root directory to enable offline retrieval mode, or specify your Info Page HTML file in the Info HTML File text box (Please make sure to clear the AppID text box before parse game information.).

- **Achievement List:**
  - Achievement lists must be obtained from local HTML pages downloaded from specific SteamDB pages. You can rename the SteamDB achievement HTML file to `achdb.html` and place it in the application root directory to enable offline retrieval mode, or specify your Achievement Page HTML file in the Achievement HTML File text box
  - The achievement information is obtained from the SteamDB page. You need to use a web browser to download the SteamDB achievement page for the given game. The achievement information on this page is defaulted to English. You can also use the browser's (such as Firefox) translation function to download the already translated SteamDB localized achievement page, and use this tool to parse the achievement list from the translated page to complete the achievement localization.

    the Generator also provides another achievement translation method. Some games on the Steam Community provide official achievement translations. The generator has the option to fetch achievement translations online from the Steam Community. If there are network issues and the Steam Community cannot be accessed, you can also place the local Steam Community page renamed as "`achs.html`" in the program's root directory.
  
- **Achievement Images:**
  - Achievement images will be placed in the cache folder saved from SteamDB's achievement page. Rename the cache folder to `imgs` and place it in the application root directory

![img3](https://img.cdn1.vip/i/68de65bab2263_1759405498.webp)

### How to Download Local Web Pages

1. Use a browser to open specific information pages. Links to the local pages mentioned above will be provided in the generator interface

![img2](https://img.cdn1.vip/i/68de65aaa480c_1759405482.png)

2. After opening the webpage, press `Ctrl+S` in your browser (Chrome or Edge) to save the page. This will generate the `{html_name}.html` page file and the image cache `html_name` folder

The image cache folder is only needed when retrieving achievement images. Please rename the cache folder to `imgs` and place it in the application root directory.

### Generate Patch

When "Generate Patch" is checked, you'll be prompted for the game's original `steamapi.dll` file path. The tool will then generate the `steam_settings` files and GSE's `steamapi.dll` files relative to the game's root directory and package them into `Patch.zip`.

### Generate Configuration Files

After obtaining game information and entering necessary parameters in the interface, configuration files can be generated. Output is placed in the `Output/{Game Name}` folder.

The Output directory contains `steam_settings` configuration files and `ColdClientLoader` files. The generated patch output includes:

```
Output
└── {Game_Name}
    ├── steam_settings
    │   ├── achievement_images
    │   ├── fonts
    │   │   ├── Roboto-Medium-LICENSE.txt
    │   │   └── Roboto-Medium.ttf
    │   ├── sounds
    │   │   └── overlay_achievement_notification.wav
    │   ├── achievements.json
    │   ├── configs.app.ini
    │   ├── configs.overlay.ini
    │   ├── configs.user.ini
    │   ├── header.jpg
    │   ├── library_600x900.jpg
    │   ├── logo.png
    │   └── steam_appid.txt
    ├── ColdClientLoader.ini
    ├── GameOverlayRenderer.dll
    ├── GameOverlayRenderer64.dll
    ├── Patch.zip
    ├── steamclient.dll
    ├── steamclient64.dll
    └── {Game_Name}.exe
```

Note: The game executable path in ColdClientLoader.ini is 

```
{Game Name}/{Game Executable Relative Path}/{Game Executable}.exe
```

