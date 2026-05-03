## ⚙️ Installation

AITree requires **Python 3.x** and the `pyyaml` library.

**1. Clone the repository:**
```bash
git clone https://github.com/n0-se/Aitree
cd aitree
```

**2. Install dependencies:**
```bash
pip install pyyaml
```

**3. (Optional) Make it a global command:**
To run `aitree` from any folder on your system without typing `python path/to/aitree.py`, you can set up an alias in your terminal profile (e.g., `.bashrc` or `.zshrc`):
```bash
alias aitree="python /path/to/your/cloned/aitree.py"
```

---

## 🚀 Quick Start

Using AITree is a simple three-step process. Navigate to the root folder of the project you want to document and run the following commands:

### Step 1: Initialize
```bash
aitree init
```
This generates a default `aitree_config.yaml` file in your current directory. Open this file to customize your project title, description, and configure your whitelist/blacklist rules to exclude folders like `node_modules`, `vendor`, or `.git`.

### Step 2: Test Your Config
```bash
aitree dry
```
Run a "Dry Run" before generating your document. AITree will simulate the scan and print a list of every file it plans to include, along with the estimated total file size, without writing anything to your disk.

### Step 3: Generate the Context
```bash
aitree generate
```
AITree will instantly build an ASCII file tree and compile all your targeted source code into a single `ai_tree.md` file. 

You can now upload or paste this `.md` file directly into ChatGPT, Claude, or Gemini to give the AI complete, instant context of your entire project architecture!

---

## 📁 Configuration (`aitree_config.yaml`)

When you run `aitree init`, the generated configuration file gives you total control over what the AI sees. 

* **Project Metadata:** Add a `project_title` and `project_info` so the AI understands your overarching goals before reading the code.
* **Blacklists/Whitelists:** Easily ignore massive folders (`folder_blacklist: ["test", "vendor"]`) or isolate specific files (`extension_whitelist: [".py", ".json"]`).
* **Smart Hidden File Detection:** Automatically ignores hidden system files and folders (like `.vscode` or `.DS_Store`) by default.