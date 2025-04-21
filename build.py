#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
build.py - Script to build the RBXLX to Rojo converter into a standalone Windows executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import PyInstaller
        print("PyInstaller is installed.")
    except ImportError:
        print("PyInstaller is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Check other dependencies
    dependencies = ['lxml']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"{dep} is installed.")
        except ImportError:
            print(f"{dep} is not installed. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

def generate_icon():
    """Generate a simple icon for the application."""
    try:
        from PIL import Image, ImageDraw
        
        # Create a 64x64 image with a transparent background
        icon = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(icon)
        
        # Draw a simple icon representing file conversion
        # Main square (Roblox)
        draw.rectangle((10, 10, 30, 30), fill=(45, 125, 210, 255), outline=(25, 100, 180, 255))
        # Arrow
        draw.polygon([(35, 20), (45, 20), (40, 15), (45, 20), (40, 25)], fill=(100, 100, 100, 255))
        # Second square (Rojo)
        draw.rectangle((50, 10, 54, 30), fill=(220, 60, 60, 255), outline=(180, 40, 40, 255))
        
        # Save the icon
        icon_path = Path("generated-icon.png")
        icon.save(icon_path)
        print(f"Generated icon at {icon_path}")
        return icon_path
        
    except ImportError:
        print("PIL not installed. Using no icon for the executable.")
        return None

def build_executable():
    """Build the standalone executable."""
    print("Building executable...")
    
    # Create build directory if it doesn't exist
    build_dir = Path("build")
    if not build_dir.exists():
        build_dir.mkdir()
    
    # Create dist directory if it doesn't exist
    dist_dir = Path("dist")
    if not dist_dir.exists():
        dist_dir.mkdir()
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Generate or use icon
    icon_path = None
    try:
        icon_path = generate_icon()
        icon_param = f"--icon={icon_path}" if icon_path else "--icon=NONE"
    except Exception as e:
        print(f"Error generating icon: {e}")
        icon_param = "--icon=NONE"
    
    # Add version information
    version_file = Path("version.txt")
    with open(version_file, "w") as f:
        f.write("# UTF-8\n")
        f.write("VSVersionInfo(\n")
        f.write("  ffi=FixedFileInfo(\n")
        f.write("    filevers=(1, 0, 0, 0),\n")
        f.write("    prodvers=(1, 0, 0, 0),\n")
        f.write("    mask=0x3f,\n")
        f.write("    flags=0x0,\n")
        f.write("    OS=0x40004,\n")
        f.write("    fileType=0x1,\n")
        f.write("    subtype=0x0,\n")
        f.write("    date=(0, 0)\n")
        f.write("    ),\n")
        f.write("  kids=[\n")
        f.write("    StringFileInfo(\n")
        f.write("      [\n")
        f.write("      StringTable(\n")
        f.write("        u'040904B0',\n")
        f.write("        [StringStruct(u'CompanyName', u''),\n")
        f.write("        StringStruct(u'FileDescription', u'RBXLX to Rojo Project Converter'),\n")
        f.write("        StringStruct(u'FileVersion', u'1.0.0'),\n")
        f.write("        StringStruct(u'InternalName', u'rbxlx_to_rojo'),\n")
        f.write("        StringStruct(u'LegalCopyright', u''),\n")
        f.write("        StringStruct(u'OriginalFilename', u'rbxlx_to_rojo.exe'),\n")
        f.write("        StringStruct(u'ProductName', u'RBXLX to Rojo Converter'),\n")
        f.write("        StringStruct(u'ProductVersion', u'1.0.0')])\n")
        f.write("      ]),\n")
        f.write("    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])\n")
        f.write("  ]\n")
        f.write(")\n")
    
    # Create a spec file for PyInstaller
    spec_file = Path("rbxlx_to_rojo.spec")
    print("Creating PyInstaller spec file...")
    with open(spec_file, 'w') as f:
        f.write("# -*- mode: python ; coding: utf-8 -*-\n\n")
        f.write("import sys\n")
        f.write("import os\n\n")
        f.write("block_cipher = None\n\n")
        
        # Define data files
        f.write("datas = [\n")
        f.write("    # No data files needed\n")
        f.write("]\n\n")
        
        # Define hidden imports for all our modules
        f.write("hidden_imports = [\n")
        f.write("    'utils',\n")
        f.write("    'roblox_parser',\n")
        f.write("    'rojo_project_generator',\n")
        f.write("    'lxml',\n")
        f.write("    'lxml.etree',\n")
        f.write("    'pathlib',\n")
        f.write("    'json',\n")
        f.write("    'base64',\n")
        f.write("    're',\n")
        f.write("    'logging',\n")
        f.write("]\n\n")
        
        # Define the Analysis object
        f.write("a = Analysis(\n")
        f.write("    ['rbxlx_to_rojo.py'],\n")
        f.write("    pathex=[],\n")
        f.write("    binaries=[],\n")
        f.write("    datas=datas,\n")
        f.write("    hiddenimports=hidden_imports,\n")
        f.write("    hookspath=[],\n")
        f.write("    hooksconfig={},\n")
        f.write("    runtime_hooks=[],\n")
        f.write("    excludes=[],\n")
        f.write("    win_no_prefer_redirects=False,\n")
        f.write("    win_private_assemblies=False,\n")
        f.write("    cipher=block_cipher,\n")
        f.write("    noarchive=False,\n")
        f.write(")\n\n")
        
        # Define the PYZ and EXE objects
        f.write("pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)\n\n")
        
        f.write("exe = EXE(\n")
        f.write("    pyz,\n")
        f.write("    a.scripts,\n")
        f.write("    a.binaries,\n")
        f.write("    a.zipfiles,\n")
        f.write("    a.datas,\n")
        f.write("    [],\n")
        f.write(f"    name='rbxlx_to_rojo',\n")
        f.write("    debug=False,\n")
        f.write("    bootloader_ignore_signals=False,\n")
        f.write("    strip=False,\n")
        f.write("    upx=True,\n")
        f.write(f"    upx_exclude=[],\n")
        f.write("    runtime_tmpdir=None,\n")
        f.write(f"    console=True,\n")
        f.write(f"    disable_windowed_traceback=False,\n")
        f.write("    argv_emulation=False,\n")
        f.write("    target_arch=None,\n")
        f.write("    codesign_identity=None,\n")
        f.write("    entitlements_file=None,\n")
        f.write(f"    icon={repr(str(icon_path)) if icon_path else 'None'},\n")
        f.write(f"    version='version.txt',\n")
        f.write(")\n")
    
    # Build executable with PyInstaller using the spec file
    print("Building executable with PyInstaller...")
    try:
        cmd = [
            "pyinstaller",
            "--clean",
            "--distpath=dist",
            "--workpath=build",
            "rbxlx_to_rojo.spec"
        ]
        
        subprocess.check_call(cmd)
        
        # Clean up version file and spec file
        if version_file.exists():
            version_file.unlink()
        if spec_file.exists():
            spec_file.unlink()
        
        print("Build completed successfully!")
        print(f"Executable available at: {dist_dir / 'rbxlx_to_rojo.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        print("PyInstaller command failed. This is common in restricted environments.")
        print("To build on Windows, you need to:")
        print("1. Install Python 3.8 or newer")
        print("2. Install required packages: pip install lxml pillow pyinstaller")
        print("3. Run: python build.py")
        
        # Create a README.txt with build instructions
        with open("BUILD_INSTRUCTIONS.txt", "w") as f:
            f.write("RBXLX to Rojo Converter - Build Instructions\n")
            f.write("==========================================\n\n")
            f.write("To build the executable on Windows:\n\n")
            f.write("1. Install Python 3.8 or newer from https://www.python.org/downloads/\n")
            f.write("   - Make sure to check 'Add Python to PATH' during installation\n\n")
            f.write("2. Open Command Prompt and install required packages:\n")
            f.write("   pip install lxml pillow pyinstaller\n\n")
            f.write("3. Navigate to the directory containing these files and run:\n")
            f.write("   python build.py\n\n")
            f.write("4. The executable will be created in the 'dist' folder\n\n")
            f.write("Usage:\n")
            f.write("   rbxlx_to_rojo.exe path/to/your/place.rbxlx -o output_directory\n\n")
            f.write("Options:\n")
            f.write("   -o, --output-dir: Directory where the Rojo project should be created\n")
            f.write("   -v, --verbose: Enable verbose output\n")
        
        print(f"Created BUILD_INSTRUCTIONS.txt with detailed instructions")

def main():
    """Main build script function."""
    print("RBXLX to Rojo Converter Build Script")
    print("====================================")
    
    # Check for dependencies
    print("Checking dependencies...")
    check_dependencies()
    
    # Additional dependency for icon generation
    try:
        import PIL
        print("PIL is installed.")
    except ImportError:
        print("PIL is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    
    # Build the executable
    build_executable()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
