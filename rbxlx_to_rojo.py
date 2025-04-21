#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
rbxlx_to_rojo.py - Main application for converting Roblox place files to Rojo projects
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Add the current directory to the Python path to make sure we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from roblox_parser import RobloxParser
    from rojo_project_generator import RojoProjectGenerator
    from utils import logger, setup_logger, get_version
except ModuleNotFoundError:
    print("Error: Required modules not found!")
    print("Make sure roblox_parser.py, rojo_project_generator.py, and utils.py are in the same directory as this script.")
    sys.exit(1)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Roblox place files (.rbxlx) to Rojo project structures."
    )
    
    parser.add_argument(
        "input_file",
        help="Path to the Roblox place file (.rbxlx) to convert"
    )
    
    parser.add_argument(
        "output_dir",  # Make output_dir a positional argument for easier use
        nargs="?",     # Make it optional
        default=".",   # Default to current directory
        help="Directory where the Rojo project should be created (default: current directory)"
    )
    
    parser.add_argument(
        "-o", "--output-dir-option",
        dest="output_dir_option",
        help="Alternative way to specify output directory (overrides positional argument)",
        default=None
    )
    
    parser.add_argument(
        "-v", "--verbose",
        help="Enable verbose output",
        action="store_true"
    )
    
    parser.add_argument(
        "--version",
        help="Show the version number and exit",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # If output_dir_option is provided, use it instead of positional output_dir
    if args.output_dir_option:
        args.output_dir = args.output_dir_option
        
    return args


def validate_arguments(args):
    """Validate command line arguments."""
    # Check if showing version
    if args.version:
        print(f"RBXLX to Rojo Converter v{get_version()}")
        sys.exit(0)
    
    # Check if input file exists
    if not os.path.isfile(args.input_file):
        logger.error(f"Input file does not exist: {args.input_file}")
        sys.exit(1)
    
    # Check if input file is a .rbxlx file
    if not args.input_file.lower().endswith(".rbxlx"):
        logger.error(f"Input file is not a .rbxlx file: {args.input_file}")
        sys.exit(1)
    
    # Check if output directory exists, create it if it doesn't
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True)
            logger.info(f"Created output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
            sys.exit(1)
    elif not output_dir.is_dir():
        logger.error(f"Output path is not a directory: {output_dir}")
        sys.exit(1)
    
    # Check if we have write permissions to the output directory
    if not os.access(output_dir, os.W_OK):
        logger.error(f"No write permission to output directory: {output_dir}")
        sys.exit(1)
    
    return True


def main():
    """Main application function."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logger
    setup_logger(verbose=args.verbose)
    
    # Validate arguments
    validate_arguments(args)
    
    logger.info(f"RBXLX to Rojo Converter v{get_version()}")
    logger.info(f"Converting {args.input_file} to Rojo project in {args.output_dir}")
    
    start_time = time.time()
    
    try:
        # Parse the Roblox place file
        logger.info("Parsing Roblox place file...")
        roblox_parser = RobloxParser(args.input_file)
        game_data = roblox_parser.parse()
        
        # Log the game structure before generating
        logger.info(f"Game name: {game_data['name']}")
        logger.info(f"Total instances: {len(game_data['instances'])}")
        logger.info(f"Root instances: {len(game_data['root_instances'])}")
        
        # Check if Workspace exists in the game data
        workspace_found = False
        workspace_ref = None
        for ref_id in game_data['root_instances']:
            instance = game_data['instances'].get(ref_id)
            if instance and instance['class'] == 'Workspace':
                workspace_found = True
                workspace_ref = ref_id
                logger.info(f"Found Workspace with {len(instance['children'])} children")
                break
                
        if not workspace_found:
            logger.warning("No Workspace found in the RBXLX file!")
        elif workspace_ref and len(game_data['instances'][workspace_ref]['children']) == 0:
            logger.warning("Workspace exists but has no children!")
        
        # Generate the Rojo project
        logger.info("Generating Rojo project...")
        rojo_generator = RojoProjectGenerator(game_data, Path(args.output_dir))
        rojo_generator.generate_project()
        
        # Verify the output structure
        output_path = Path(args.output_dir)
        workspace_path = output_path / 'src' / 'Workspace'
        if workspace_path.exists() and not any(workspace_path.iterdir()):
            logger.warning(f"Workspace directory exists at {workspace_path}, but it's empty!")
            
            # If workspace directory is empty but there are children in the data,
            # there might be an issue with processing them
            if workspace_found and workspace_ref and len(game_data['instances'][workspace_ref]['children']) > 0:
                logger.warning("Workspace in game data has children, but they weren't processed properly!")
                
                # Try explicitly processing workspace children
                logger.info("Attempting to explicitly process Workspace children...")
                workspace_children = game_data['instances'][workspace_ref]['children']
                for child_ref in workspace_children:
                    child = game_data['instances'].get(child_ref)
                    if child:
                        child_name = child['properties'].get('Name', child['class'])
                        logger.info(f"Processing Workspace child: {child_name} ({child['class']})")
                        
                        # Manually process this child
                        rojo_generator._process_instance(child, workspace_path, False)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Conversion completed in {elapsed_time:.2f} seconds")
        logger.info(f"Rojo project created at: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
