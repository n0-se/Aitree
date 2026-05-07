import os
import sys
import fnmatch
from datetime import datetime

# Handle Windows emoji encoding issues
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Try to import yaml, but fail gracefully if the user hasn't installed it
try:
    import yaml
except ImportError:
    print("❌ Error: The 'pyyaml' library is not installed.")
    print("💡 Please install it by running: pip install pyyaml")
    sys.exit(1)

def print_header():
    header = r"""
 $$$$$$\  $$$$$$\        $$$$$$$$\                                
$$  __$$\ \_$$  _|      \__$$  __|                               
$$ /  $$ |  $$ |           $$ | $$$$$$\   $$$$$$\   $$$$$$\  
$$$$$$$$ |  $$ |           $$ |$$  __$$\ $$  __$$\ $$  __$$\ 
$$  __$$ |  $$ |           $$ |$$ |  \__|$$$$$$$$ |$$$$$$$$ |
$$ |  $$ |  $$ |           $$ |$$ |      $$   ____|$$   ____|
$$ |  $$ |$$$$$$\          $$ |$$ |      \$$$$$$$\ \$$$$$$$\ 
\__|  \__|\______|         \__|\__|       \_______| \_______|
    """
    print(header)

def print_help():
    print_header()
    print("Usage: aitree <command> [config_file]\n")
    print("Commands:")
    print("  generate    Build the context file (defaults to aitree_config.yaml)")
    print("  dry         Preview files to be added (defaults to aitree_config.yaml)")
    print("  init        Create a default config file (defaults to aitree_config.yaml)")
    print("  help        Show this help message\n")
    print("Example:")
    print("  aitree generate custom_config.yaml\n")

def get_human_readable_size(size_in_bytes):
    """Converts raw bytes into a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def generate_tree_string(paths, line_ranges=None):
    """Takes a list of file paths and generates an ASCII tree string."""
    if not paths:
        return ""
    
    # Build a nested dictionary representing the folder structure
    tree = {}
    for path in paths:
        parts = path.split('/')
        current = tree
        for part in parts:
            current = current.setdefault(part, {})
    
    def format_tree(current_node, prefix="", current_path=""):
        lines = []
        # Sort so directories (nodes with children) appear first, then alphabetically
        entries = sorted(current_node.keys(), key=lambda x: (not bool(current_node[x]), x))
        
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            
            # Construct the relative path to match against line_ranges
            full_rel_path = f"{current_path}/{entry}" if current_path else entry
            
            line_info = ""
            if line_ranges and full_rel_path in line_ranges:
                start, end = line_ranges[full_rel_path]
                line_info = f" (L{start}-L{end})"
            
            lines.append(prefix + connector + entry + line_info)
            
            if current_node[entry]:
                extension = "    " if is_last else "│   "
                lines.extend(format_tree(current_node[entry], prefix + extension, full_rel_path))
        return lines

    return "\n".join(["."] + format_tree(tree))

def create_default_config(config_name='aitree_config.yaml'):
    print_header()
    
    if os.path.exists(config_name):
        print(f"⚠️  {config_name} already exists in this directory.")
        return

    default_yaml = """# aitree Configuration File

# Optional: The name of your project
project_title: ""

# Optional: A brief description of what the project is, its goals, or its stack.
# This gives the AI crucial high-level context before it reads the code.
project_info: ""

# The root directory to start scanning from ("." is the current folder)
initial_folder: "."

# Automatically skip any file or folder starting with a dot (e.g., .git, .vscode)
ignore_hidden_files: true

# Generate an ASCII file tree at the top of the output document to help AI understand the project structure
include_file_tree: true

# The name of the final markdown file generated
output_file: "ai_tree.md"

# List of folders to explicitly include (leave empty to include everything not blacklisted)
folder_whitelist: []

# List of folders to completely ignore
folder_blacklist:
  - "test"
  - "vendor"

# Smart File Whitelist:
# If you list files in a specific folder here (e.g., 'assets/css/style.css'),
# ONLY those listed files will be included from that specific folder.
# Other folders without whitelist rules are processed normally.
filepath_whitelist: []

# Explicitly ignore these specific files
filepath_blacklist: []

# Only include files with these exact extensions
extension_whitelist:
  - ".bat"
  - ".py"
  - ".json"
  - ".yaml"
  - ".js"
  - ".css"
  - ".php"
"""

    try:
        with open(config_name, 'w', encoding='utf-8') as f:
            f.write(default_yaml)
        print(f"✅ Success! Created default {config_name} in the current directory.")
    except Exception as e:
        print(f"❌ Error creating config: {e}")

def generate_context(config_path='aitree_config.yaml', dry_run=False):
    print_header()

    if dry_run:
        print("=== DRY RUN MODE: No files will be generated ===\n")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"❌ Error: {config_path} not found.")
        print(f"💡 Tip: Run 'aitree init {config_path}' to generate a default configuration file.")
        return
    except yaml.YAMLError as e:
        print(f"❌ Error parsing {config_path}: Invalid YAML format.")
        print(f"   Details: {e}")
        return

    project_title = config.get("project_title", "").strip()
    project_info = config.get("project_info", "").strip()

    initial_folder = config.get("initial_folder", ".")
    output_file = config.get("output_file", "output.txt")
    extension_whitelist = config.get("extension_whitelist", [])
    
    ignore_hidden = config.get("ignore_hidden_files", True)
    include_tree = config.get("include_file_tree", True)
    
    folder_whitelist_raw = config.get("folder_whitelist") or []
    folder_blacklist_raw = config.get("folder_blacklist") or []
    filepath_whitelist_raw = config.get("filepath_whitelist") or []
    filepath_blacklist_raw = config.get("filepath_blacklist") or []

    folder_whitelist = [os.path.normpath(p).replace("\\", "/") for p in folder_whitelist_raw]
    folder_blacklist = [os.path.normpath(p).replace("\\", "/") for p in folder_blacklist_raw]
    filepath_whitelist = [os.path.normpath(p).replace("\\", "/") for p in filepath_whitelist_raw]
    filepath_blacklist = [os.path.normpath(p).replace("\\", "/") for p in filepath_blacklist_raw]

    whitelisted_file_dirs = set()
    for p in filepath_whitelist:
        dir_name = p.rsplit('/', 1)[0] if '/' in p else ""
        whitelisted_file_dirs.add(dir_name)

    total_bytes = 0  
    
    # Store processed data in memory before writing
    processed_files_data = [] 
    processed_paths = []

    for root, dirs, files in os.walk(initial_folder):
        current_dir_relpath = os.path.relpath(root, initial_folder).replace("\\", "/")

        # --- DIRECTORY PRUNING LOGIC ---
        valid_dirs = []
        for d in dirs:
            if ignore_hidden and d.startswith('.'):
                continue

            dir_relpath = os.path.relpath(os.path.join(root, d), initial_folder).replace("\\", "/")
            
            is_blacklisted = False
            for b in folder_blacklist:
                if dir_relpath == b or dir_relpath.startswith(b + "/"):
                    is_blacklisted = True
                    break
            
            if is_blacklisted:
                continue 
            
            if folder_whitelist:
                keep = False
                for w in folder_whitelist:
                    if w.startswith(dir_relpath + "/") or w == dir_relpath or dir_relpath.startswith(w + "/"):
                        keep = True
                        break
                if not keep:
                    continue
            
            valid_dirs.append(d)
        
        dirs[:] = valid_dirs 

        # --- DETERMINE IF WE SHOULD PROCESS FILES HERE ---
        process_files = False
        if not folder_whitelist:
            process_files = True
        else:
            dir_to_check = "." if current_dir_relpath == "" else current_dir_relpath
            if dir_to_check == "." and "." in folder_whitelist:
                process_files = True
            else:
                for w in folder_whitelist:
                    if dir_to_check == w or dir_to_check.startswith(w + "/"):
                        process_files = True
                        break

        if not process_files:
            continue

        # --- FILE PROCESSING LOGIC ---
        for file in files:
            if ignore_hidden and file.startswith('.'):
                continue

            ext = os.path.splitext(file)[1]
            if ext in extension_whitelist:
                file_path = os.path.join(root, file)
                file_relpath = os.path.relpath(file_path, initial_folder).replace("\\", "/")

                # Check if file matches any pattern in filepath_blacklist
                if any(fnmatch.fnmatch(file_relpath, pattern) for pattern in filepath_blacklist):
                    continue 

                if filepath_whitelist:
                    file_dir = file_relpath.rsplit('/', 1)[0] if '/' in file_relpath else ""
                    # Check if this directory is covered by any whitelist pattern
                    is_dir_whitelisted = any(fnmatch.fnmatch(file_dir, d_pattern) for d_pattern in whitelisted_file_dirs)
                    
                    if is_dir_whitelisted:
                        # If the directory is covered by a whitelist, the file MUST match a pattern
                        if not any(fnmatch.fnmatch(file_relpath, f_pattern) for f_pattern in filepath_whitelist):
                            continue

                if dry_run:
                    try:
                        file_size = os.path.getsize(file_path)
                        total_bytes += file_size
                        human_size = get_human_readable_size(file_size)
                        
                        action_text = f"[DRY RUN] Would add: {file_relpath}"
                        print(f"{action_text:<60} ({human_size:>9})")
                    except OSError:
                        action_text = f"[DRY RUN] Would add: {file_relpath}"
                        print(f"{action_text:<60} (Error reading)")
                else:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as in_f:
                            content = in_f.read()
                        
                        # Store in memory for writing later
                        processed_files_data.append((file_relpath, content))
                        processed_paths.append(file_relpath)
                        print(f"Added: {file_relpath}")
                        
                    except Exception as e:
                        print(f"Skipped {file_relpath} due to error: {e}")

    # --- WRITING THE FINAL FILE ---
    if not dry_run:
        output_content = []
        
        # 1. Generate Header
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"# 🌲 AITree Context Document\n"
        header += f"> **Generated by AITree by n0-se** on `{now}`  \n"
        header += f"> **Total files included:** `{len(processed_files_data)}`\n\n"
        header += "The following document contains the file structure and source code for a project. Please use this context to answer subsequent questions.\n\n"
        header += "---\n\n"
        
        if project_title or project_info:
            header += "### Project Context\n"
            if project_title:
                header += f"**Project Title:** {project_title}\n\n"
            if project_info:
                header += f"**Description:**\n{project_info}\n\n"
            header += "---\n\n"
        
        output_content.append(header)
        
        # 2. Placeholder for Tree
        tree_placeholder_index = -1
        if include_tree and processed_paths:
            output_content.append("### Project File Tree\n```text\n")
            tree_placeholder_index = len(output_content)
            output_content.append("") # Placeholder for tree string
            output_content.append("\n```\n\n---\n\n")

        # 3. Process files and track line numbers
        # Calculate current_line for the first file block by simulating the prefix
        dummy_tree = generate_tree_string(processed_paths)
        prefix_parts = output_content[:]
        if tree_placeholder_index != -1:
            prefix_parts[tree_placeholder_index] = dummy_tree
        
        current_line = "".join(prefix_parts).count('\n') + 1
        line_ranges = {}

        file_blocks = []
        for file_relpath, content in processed_files_data:
            file_header = f"### File: `{file_relpath}`\n```\n"
            
            # Start is the line with "### File:"
            start_line = current_line
            
            # Calculate content line count
            if not content:
                c_lines = 0
                file_footer = "\n```\n\n"
            else:
                c_lines = content.count('\n') + (1 if not content.endswith('\n') else 0)
                # If content ends with a newline, the footer backticks can go on the next line immediately.
                # Otherwise, we need a newline before the backticks.
                if content.endswith('\n'):
                    file_footer = "```\n\n"
                else:
                    file_footer = "\n```\n\n"
            
            # end_line is the line with the closing ```
            # Header takes 2 lines, then c_lines of code, then 1 line for closing ```
            end_line = start_line + 2 + c_lines
            
            line_ranges[file_relpath] = (start_line, end_line)
            
            block = file_header + content + file_footer
            file_blocks.append(block)
            current_line += block.count('\n')
        
        # 4. Finalize Tree with line numbers
        if tree_placeholder_index != -1:
            tree_str = generate_tree_string(processed_paths, line_ranges)
            output_content[tree_placeholder_index] = tree_str

        # 5. Write to file
        with open(output_file, 'w', encoding='utf-8') as out_f:
            for part in output_content:
                out_f.write(part)
            for block in file_blocks:
                out_f.write(block)

    if dry_run:
        print("\n" + "="*73)
        total_text = "Total estimated source size:"
        print(f"{total_text:<60}  {get_human_readable_size(total_bytes):>9} ")
        print("="*73)
        print(f"\nDry run complete. Run 'aitree generate' to save data to {output_file}.")
    else:
        print(f"\nDone! Context successfully saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        config_file = sys.argv[2] if len(sys.argv) > 2 else 'aitree_config.yaml'
        
        if command == "init":
            create_default_config(config_file)
        elif command == "dry":
            generate_context(config_path=config_file, dry_run=True)
        elif command == "generate":
            generate_context(config_path=config_file, dry_run=False)
        elif command in ["help", "-h", "--help"]:
            print_help()
        else:
            print(f"❌ Unknown command: '{command}'")
            print("💡 Run 'aitree help' or just 'aitree' to see available commands.")
    else:
        print_help()