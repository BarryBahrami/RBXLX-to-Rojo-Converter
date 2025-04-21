#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
rojo_project_generator.py - Generates Rojo project structure from parsed Roblox game data
"""

import os
import json
import re
from pathlib import Path
from utils import logger, normalize_name, escape_lua_string


class RojoProjectGenerator:
    """Generates a Rojo project from parsed Roblox game data."""

    def __init__(self, game_data, output_dir):
        """Initialize the generator with parsed game data and output directory."""
        self.game_data = game_data
        self.output_dir = Path(output_dir)
        self.script_extensions = {
            'Script': '.server.lua',
            'LocalScript': '.client.lua',
            'ModuleScript': '.lua'
        }
        self.created_paths = set()
        
    def generate_project(self):
        """Generate the complete Rojo project structure."""
        # Create the src directory structure
        src_dir = self.output_dir / 'src'
        if not src_dir.exists():
            src_dir.mkdir(parents=True)
            logger.info(f"Created source directory: {src_dir}")
        
        # Generate the project.json file
        self._generate_project_json()
        
        # Process all instances and create the file structure
        logger.info("Generating file structure...")
        
        # Keep track of the workspace path and instance for special handling
        workspace_path = None
        workspace_instance = None
        
        # Process each root instance
        for ref_id in self.game_data['root_instances']:
            instance = self.game_data['instances'].get(ref_id)
            if not instance:
                continue
                
            # Special handling for Workspace - save it for later processing
            if instance['class'] == 'Workspace':
                workspace_instance = instance
                # Create workspace directory but don't process children yet
                workspace_path = src_dir / 'Workspace'
                if not workspace_path.exists():
                    workspace_path.mkdir(parents=True)
                    self.created_paths.add(str(workspace_path))
                # Create workspace meta file
                self._create_meta_file(instance, workspace_path)
                logger.info(f"Created Workspace directory: {workspace_path}")
                logger.info(f"Workspace has {len(instance['children'])} children")
            else:
                # Process other root instances normally
                self._process_instance(instance, src_dir)
        
        # Now explicitly process Workspace children to ensure they're captured
        if workspace_instance and workspace_path:
            logger.info("Processing Workspace children explicitly...")
            for child_ref in workspace_instance['children']:
                child = self.game_data['instances'].get(child_ref)
                if child:
                    child_name = child['properties'].get('Name', child['class'])
                    logger.info(f"Processing Workspace child: {child_name} ({child['class']})")
                    self._process_instance(child, workspace_path, False)
        
        logger.info(f"Created {len(self.created_paths)} files/directories")

    def _generate_project_json(self):
        """Generate the default.project.json file for the Rojo project."""
        logger.info("Generating default.project.json...")
        
        # Set the project name from the game data
        game_name = self.game_data['name']
        
        # Create the project template
        project = {
            "name": game_name,
            "tree": {
                "$className": "DataModel",
                "ReplicatedStorage": {
                    "$className": "ReplicatedStorage",
                    "$path": "src/ReplicatedStorage"
                },
                "ServerScriptService": {
                    "$className": "ServerScriptService",
                    "$path": "src/ServerScriptService"
                },
                "ServerStorage": {
                    "$className": "ServerStorage",
                    "$path": "src/ServerStorage"
                },
                "StarterGui": {
                    "$className": "StarterGui",
                    "$path": "src/StarterGui"
                },
                "StarterPack": {
                    "$className": "StarterPack",
                    "$path": "src/StarterPack"
                },
                "StarterPlayer": {
                    "$className": "StarterPlayer",
                    "StarterPlayerScripts": {
                        "$className": "StarterPlayerScripts",
                        "$path": "src/StarterPlayer/StarterPlayerScripts"
                    },
                    "StarterCharacterScripts": {
                        "$className": "StarterCharacterScripts",
                        "$path": "src/StarterPlayer/StarterCharacterScripts"
                    }
                },
                "Workspace": {
                    "$className": "Workspace",
                    "$path": "src/Workspace"
                },
                "Lighting": {
                    "$className": "Lighting",
                    "$path": "src/Lighting"
                },
                "SoundService": {
                    "$className": "SoundService",
                    "$path": "src/SoundService"
                }
            }
        }
        
        # Create additional standard service paths for completeness
        standard_services = [
            "ReplicatedFirst", "Players", "Chat", "LocalizationService",
            "TestService", "MarketplaceService", "HttpService"
        ]
        
        for service in standard_services:
            project["tree"][service] = {
                "$className": service,
                "$path": f"src/{service}"
            }
        
        # Write the project file
        project_file = self.output_dir / 'default.project.json'
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project, f, indent=4)
        
        logger.info(f"Created project file: {project_file}")
        
        # Create all the standard directories mentioned in the project.json
        self._create_standard_directories(project["tree"])

    def _create_standard_directories(self, tree, base_path=None):
        """Create the standard directory structure based on the project.json."""
        if base_path is None:
            base_path = self.output_dir
        
        for key, value in tree.items():
            if key.startswith('$'):
                continue
                
            if '$path' in value:
                dir_path = Path(base_path) / value['$path']
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.created_paths.add(str(dir_path))
            
            # Recursively process nested structures
            if isinstance(value, dict):
                self._create_standard_directories(value, base_path)

    def _process_instance(self, instance, parent_path, is_root=True):
        """Process a Roblox instance and create corresponding files/directories."""
        instance_class = instance['class']
        instance_name = instance['properties'].get('Name', instance_class)
        
        logger.debug(f"Processing instance: {instance_name} ({instance_class})")
        
        # Handle specific instance types
        if instance_class in ['Script', 'LocalScript', 'ModuleScript']:
            # Create a script file
            return self._create_script_file(instance, parent_path)
        
        # For non-script instances, create a directory
        dir_name = normalize_name(instance_name)
        instance_path = parent_path / dir_name
        
        # If the instance has children or is a root instance or has important properties, create a directory for it
        if instance['children'] or is_root or instance['properties']:
            # Don't create redundant directories for root services that are already created
            if is_root and instance_class in parent_path.parts:
                instance_path = parent_path
            else:
                # For class instances that are Roblox primitives (Part, Model, etc.), 
                # we should create the appropriate directories and meta files
                if not instance_path.exists():
                    instance_path.mkdir(parents=True, exist_ok=True)
                    self.created_paths.add(str(instance_path))
                    logger.debug(f"Created directory: {instance_path}")
            
            # Create a meta.json file for this instance to define properties
            self._create_meta_file(instance, instance_path)
            
            # Process all children
            for child_ref in instance['children']:
                child = self.game_data['instances'].get(child_ref)
                if child:
                    self._process_instance(child, instance_path, False)
        
        return instance_path

    def _create_script_file(self, instance, parent_path):
        """Create a script file from a Script, LocalScript, or ModuleScript instance."""
        instance_class = instance['class']
        instance_name = instance['properties'].get('Name', instance_class)
        
        # Get the script source code
        source_code = ""
        if 'Source' in instance['properties']:
            source_code = instance['properties']['Source']
        
        # Determine file extension based on script type
        extension = self.script_extensions.get(instance_class, '.lua')
        
        # Create the script file
        file_name = f"{normalize_name(instance_name)}{extension}"
        script_path = parent_path / file_name
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(source_code)
        
        self.created_paths.add(str(script_path))
        
        # Create meta file if script has children
        if instance['children']:
            self._create_meta_file(instance, script_path.parent)
            
            # Process all children
            for child_ref in instance['children']:
                child = self.game_data['instances'].get(child_ref)
                if child:
                    child_dir = parent_path / normalize_name(instance_name)
                    if not child_dir.exists():
                        child_dir.mkdir(parents=True, exist_ok=True)
                        self.created_paths.add(str(child_dir))
                    self._process_instance(child, child_dir, False)
        
        return script_path

    def _create_meta_file(self, instance, path):
        """Create a meta file to define instance properties."""
        instance_class = instance['class']
        instance_name = instance['properties'].get('Name', instance_class)
        
        # Copy relevant properties to the meta file
        meta = {
            "className": instance_class,
            "properties": {}
        }
        
        # Include specific properties we want to preserve
        # Expanded to include more properties relevant to Roblox instances
        important_properties = [
            # Physical properties
            'Anchored', 'CanCollide', 'CastShadow', 'CollisionGroupId', 'Massless',
            'Material', 'Transparency', 'Reflectance', 'Locked',
            
            # Size and position properties
            'Size', 'CFrame', 'Position', 'Rotation', 'RotVelocity', 'Velocity',
            
            # UI properties
            'BackgroundColor3', 'BackgroundTransparency', 'BorderColor3', 'BorderSizePixel',
            'TextColor3', 'Font', 'TextSize', 'Text', 'TextWrapped', 'TextXAlignment', 'TextYAlignment',
            'Image', 'ImageColor3', 'ImageTransparency', 'ScaleType',
            
            # Behavior properties
            'Enabled', 'Visible', 'Value', 'MaxValue', 'MinValue', 'Sound', 'Volume', 'Pitch',
            'CanBeDropped', 'RequiresHandle', 'Looped', 'Playing', 'TimePosition',
            
            # Lighting properties
            'Ambient', 'Brightness', 'ColorShift_Bottom', 'ColorShift_Top', 'GlobalShadows',
            'OutdoorAmbient', 'TimeOfDay', 'FogColor', 'FogEnd', 'FogStart',
            
            # Special properties
            'MeshId', 'TextureId', 'SoundId', 'CollisionGroup', 'AttachmentPoint', 'PrimaryPart'
        ]
        
        for prop_name, prop_value in instance['properties'].items():
            # Include all properties for a more complete conversion, except for internal properties
            if prop_name != 'Name' and not prop_name.startswith('_') and (
                prop_name in important_properties or 
                prop_name.endswith('Color3') or
                prop_name.endswith('Size') or
                prop_name.endswith('Offset') or
                prop_name.endswith('Position')
            ):
                # Process different property types appropriately
                if isinstance(prop_value, dict):
                    # Handle color values
                    if all(k in prop_value for k in ['R', 'G', 'B']):
                        meta['properties'][prop_name] = [
                            prop_value['R'], prop_value['G'], prop_value['B']
                        ]
                    # Handle Vector3 values
                    elif all(k in prop_value for k in ['X', 'Y', 'Z']):
                        meta['properties'][prop_name] = [
                            prop_value['X'], prop_value['Y'], prop_value['Z']
                        ]
                    # Handle Vector2 values
                    elif all(k in prop_value for k in ['X', 'Y']) and len(prop_value) == 2:
                        meta['properties'][prop_name] = [
                            prop_value['X'], prop_value['Y']
                        ]
                    # Handle CFrame/CoordinateFrame values
                    elif 'X' in prop_value and 'Y' in prop_value and 'Z' in prop_value and 'R00' in prop_value:
                        # For CFrame, we need position and rotation matrix
                        meta['properties'][prop_name] = [
                            prop_value['X'], prop_value['Y'], prop_value['Z'],
                            prop_value.get('R00', 1), prop_value.get('R01', 0), prop_value.get('R02', 0),
                            prop_value.get('R10', 0), prop_value.get('R11', 1), prop_value.get('R12', 0),
                            prop_value.get('R20', 0), prop_value.get('R21', 0), prop_value.get('R22', 1)
                        ]
                    else:
                        # For other complex properties, convert to a simpler format if possible
                        try:
                            # Try to convert to a simplified representation
                            meta['properties'][prop_name] = {k: v for k, v in prop_value.items() 
                                                             if not k.startswith('_') and not callable(v)}
                        except:
                            # If conversion fails, use string representation
                            meta['properties'][prop_name] = str(prop_value)
                else:
                    # For simple property values, use as is
                    meta['properties'][prop_name] = prop_value
        
        # Create the meta file if it has properties or it's not a standard container
        # Always create meta files for certain instance types regardless of properties
        always_create_meta = instance_class not in ['Folder'] or len(meta['properties']) > 0
        
        if always_create_meta:
            meta_path = path / f"{normalize_name(instance_name)}.meta.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=4)
            
            self.created_paths.add(str(meta_path))
            logger.debug(f"Created meta file: {meta_path}")
