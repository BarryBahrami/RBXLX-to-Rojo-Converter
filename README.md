# RBXLX to Rojo Converter

A powerful command-line tool that converts Roblox place files (.rbxlx) to fully structured Rojo projects for Visual Studio Code development.

## Features

- Converts Roblox XML place files (.rbxlx) to Rojo project structures
- Preserves full game hierarchy (including Workspace elements)
- Creates correct directory/file structure for all instances
- Extracts and preserves all scripts (Script, LocalScript, ModuleScript)
- Handles properties like CFrame, Size, Color, etc. properly
- Generates complete `default.project.json` for Rojo sync
- Works as a standalone Windows executable (no installation required)

## Installation

### Option 1: Download the Pre-built Executable (Windows)

1. Download the latest release from the releases section
2. Extract the ZIP file to a location of your choice
3. Run the executable from the command line

### Option 2: Run as a Python Script

1. Clone or download this repository
2. Make sure all these files are in the same directory:
   - `rbxlx_to_rojo.py` (main script)
   - `roblox_parser.py` (RBXLX file parser)
   - `rojo_project_generator.py` (Rojo project generator)
   - `utils.py` (utility functions)
3. Install the required dependencies:
   ```
   pip install lxml
   ```
4. Run the script directly:
   ```
   python rbxlx_to_rojo.py path/to/your/place.rbxlx -o output_directory
   ```

**Troubleshooting**: If you get a "No module named" error, make sure all the required files are in the same directory as the main script.

### Option 3: Build from Source

1. Clone this repository
2. Install required dependencies:
   ```
   pip install lxml pillow pyinstaller
   ```
3. Run the build script:
   ```
   python build.py
   ```
4. Find the executable in the `dist` folder

## Usage

### Using the Executable
```
rbxlx_to_rojo.exe path/to/your/place.rbxlx -o output_directory
```

### Using the Python Script
```
# Method 1: Using the -o option
python rbxlx_to_rojo.py path/to/your/place.rbxlx -o output_directory

# Method 2: Using positional arguments (simpler)
python rbxlx_to_rojo.py path/to/your/place.rbxlx output_directory
```

### Command-line Arguments

- `input_file`: Path to the Roblox place file (.rbxlx) to convert
- `-o, --output-dir`: Directory where the Rojo project should be created (default: current directory)
- `-v, --verbose`: Enable verbose output
- `--version`: Show the version number and exit

## Working with the Generated Project

After conversion, you'll have a complete Rojo project structure:

```
output_directory/
├── default.project.json
└── src/
    ├── ReplicatedStorage/
    ├── ServerScriptService/
    ├── StarterGui/
    ├── Workspace/
    └── ...
```

You can now:

1. Open the output directory in Visual Studio Code with the Rojo extension installed
2. Use the Rojo extension to sync changes back to Roblox Studio
3. Edit scripts and assets in your preferred code editor
4. Manage your game with version control (Git)

## How It Works

The converter:

1. Parses the .rbxlx file to extract all instances and their properties
2. Builds a hierarchical representation of the game structure
3. Creates appropriate directories and files for each instance
4. Generates meta files to store properties like CFrame, Size, etc.
5. Extracts script source code into proper .lua files
6. Creates a default.project.json file that maps the directory structure to Roblox instances

## Requirements

- Windows operating system or just Python
- No additional runtime dependencies (executable is self-contained)

## License

This project is released under the GNU License.
