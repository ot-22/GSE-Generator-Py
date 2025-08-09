# GSE_Generator_Py

A stable Goldberg Steam Emulator configuration generation tool



## Interface

![tmp8E9B.png](https://youke1.picui.cn/s1/2025/08/09/68970f02508b9.png)

## Features

- Fetch game information and DLC lists by AppID.
- Parse SteamDB pages to generate GSE-compatible achievement images and `achievements.json`.
- Generate `steam_settings`configuration files based on parameters.
- Provide a GUI for parameter input, displaying achievement lists and game details.
- Embed game executable icons or custom `.ico`files into `steamclient_loader.exe`.



## Required Files

- Place the following files in the `../source/`directory:

  - `steamclient.dll`, `steamclient64.dll`, `steamclient_loader_x64.exe`
  - `GameOverlayRenderer64.dll`, `GameOverlayRenderer.dll`, `ColdClientLoader.ini`

- The `../source/GSE_DLL/`directory must contain:

  - `experimental/`and `regular/`subdirectories, each holding corresponding `steam_api.dll`and `steam_api64.dll`files.

    *(Note: These files can be Download from the GSE [Release](https://github.com/Detanup01/gbe_fork/releases).)*

    

## Usage

### Generating Configuration Files

1. Enter the AppID in the input field to fetch game details.
2. After providing necessary parameters in the GUI, the tool will generate configuration files under `Output/{Game Name}/`, including:
   - ColdClientLoader-style configs and DLLs.
   - Default `steam_api.dll`-style configs and DLLs.
3. Outputs are bundled as `Patch.zip`.

**Note**: The generated `ColdClientLoader.ini`will set the game executable path as:

```
{Game Name}/{Relative Path to Game Executable}/{Game Executable}.exe
```



### Generating Achievements

*(Achievement data is scraped from SteamDB, but CAPTCHAs may cause failures. Offline parsing is recommended.)*

1. Open the game’s SteamDB achievements page (`https://steamdb.info/app/{AppID}/stats/`) in Chrome or Edge.
2. After all achievement images load, save the page locally via `Ctrl+S`to the generator’s working directory. This creates:
   - `{html_name}.html`
   - An `html_name/`folder containing images.
3. Rename the `html_name/`folder to `imgs/`.
4. In the generator, specify the path to `{html_name}.html`.