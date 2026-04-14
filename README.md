# KSP Moder

A local web-based mod manager for Kerbal Space Program. Browse and toggle mods in your `GameData` folder, detect file conflicts, scan logs for mod errors, manage save game backups, and export your mod list — all from a browser UI.

**Features**
- Enable / disable / remove mods
- Conflict detection between mods
- Mod notes and profiles (save & restore mod sets)
- Log viewer with error/warning filters
- Mod error scan — groups log errors by the mod that caused them
- Save game browser with one-click backups
- Export your full mod list to a `.txt` file

---

## Setup

**Requirements:** Python 3.8+

### 1. Clone the repo
```bash
git clone https://github.com/matthewsawatzky/KSP-moder.git
cd KSP-moder
```

### 2. Create a virtual environment
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run
```bash
python main.py
```

The app will open automatically at **http://localhost:5050**.  
On first launch, go to the **Settings** tab and point it at your KSP install folder.
