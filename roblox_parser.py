#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
roblox_parser.py - Parses Roblox place files (.rbxlx) to extract game data
"""

import os
import re
from lxml import etree
from pathlib import Path
from utils import logger


class RobloxParser:
    """Parser for Roblox place files (.rbxlx)."""

    def __init__(self, rbxlx_path):
        """Initialize the parser with the path to the Roblox place file."""
        self.rbxlx_path = Path(rbxlx_path)
        self.tree = None
        self.root = None
        self.instances = {}
        self.root_instances = []

    def parse(self):
        """Parse the Roblox place file and return structured game data."""
        logger.info(f"Parsing file: {self.rbxlx_path}")
        
        try:
            # XML parsing can be memory-intensive for large files, so use iterparse
            context = etree.iterparse(str(self.rbxlx_path), events=('end',), huge_tree=True)
            
            # First, find all Items
            logger.info("First pass: finding all instances...")
            for _, elem in context:
                if elem.tag == 'Item':
                    ref_id = elem.get('referent')
                    class_name = elem.get('class')
                    if ref_id and class_name:
                        self.instances[ref_id] = {
                            'class': class_name,
                            'referent': ref_id,
                            'properties': {},
                            'children': [],
                            'parent': None
                        }
                    # Clear the element to save memory
                    elem.clear()
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]
            
            logger.info(f"Found {len(self.instances)} instances")
            
            # Second pass to build the hierarchy and extract properties
            logger.info("Second pass: building instance hierarchy...")
            self.tree = etree.parse(str(self.rbxlx_path))
            self.root = self.tree.getroot()
            
            # Extract hierarchy first - we'll process each Item and find its direct children
            logger.info("Building instance hierarchy...")
            # This set will track all instances that have been identified as children
            child_instances = set()
            
            # Find all Item elements
            for item_elem in self.root.findall('.//Item'):
                ref_id = item_elem.get('referent')
                if ref_id not in self.instances:
                    continue
                
                instance = self.instances[ref_id]
                
                # Extract properties
                properties_elem = item_elem.find('Properties')
                if properties_elem is not None:
                    for prop_elem in properties_elem:
                        prop_name = prop_elem.get('name')
                        prop_value = self._extract_property_value(prop_elem)
                        instance['properties'][prop_name] = prop_value
                
                # Find direct children in the XML tree
                for child_item in item_elem.findall('./Item'):
                    child_ref = child_item.get('referent')
                    if child_ref in self.instances:
                        instance['children'].append(child_ref)
                        self.instances[child_ref]['parent'] = ref_id
                        child_instances.add(child_ref)
            
            # Now determine root instances - those not identified as children
            logger.info(f"Found {len(child_instances)} instances that are children")
            for ref_id, instance in self.instances.items():
                if ref_id not in child_instances and instance['parent'] is None:
                    self.root_instances.append(ref_id)
                    
            logger.info(f"Identified {len(self.root_instances)} root instances")
            
            # Print some info about important root instances
            for ref_id in self.root_instances:
                instance = self.instances.get(ref_id)
                if instance:
                    name = instance['properties'].get('Name', instance['class'])
                    logger.debug(f"Root instance: {name} ({instance['class']}) with {len(instance['children'])} children")
            
            logger.info(f"Found {len(self.root_instances)} root instances")
            
            # Build the game structure
            game_data = {
                'name': self._get_game_name(),
                'instances': self.instances,
                'root_instances': self.root_instances
            }
            
            return game_data
            
        except Exception as e:
            logger.error(f"Error parsing Roblox file: {e}")
            raise

    def _extract_property_value(self, prop_elem):
        """Extract the value from a property element based on its type."""
        tag = prop_elem.tag
        
        # Handle different property types
        if tag == 'string':
            return prop_elem.text or ""
        elif tag == 'int' or tag == 'int64':
            return int(prop_elem.text or 0)
        elif tag == 'float' or tag == 'double':
            return float(prop_elem.text or 0)
        elif tag == 'bool':
            return prop_elem.text.lower() == 'true'
        elif tag == 'Content':
            return prop_elem.text or ""
        elif tag == 'BinaryString':
            # For scripts, convert BinaryString to usable content
            if prop_elem.text:
                try:
                    # Binary strings in rbxlx can contain Lua code
                    import base64
                    decoded = base64.b64decode(prop_elem.text).decode('utf-8')
                    return decoded
                except:
                    return prop_elem.text
            return ""
        elif tag == 'ProtectedString':
            # For scripts, convert ProtectedString to usable content
            if prop_elem.text:
                try:
                    import base64
                    decoded = base64.b64decode(prop_elem.text).decode('utf-8')
                    return decoded
                except:
                    return prop_elem.text
            return ""
        elif tag == 'UniqueId':
            return prop_elem.text or ""
        elif tag == 'SecurityCapabilities':
            return prop_elem.text or "0"
        elif tag == 'Ref':
            return prop_elem.text or "null"
        elif tag == 'token':
            return int(prop_elem.text or 0)
        elif tag == 'Color3' or tag == 'Color3uint8':
            # For colors, combine RGB values
            r = prop_elem.find('R')
            g = prop_elem.find('G')
            b = prop_elem.find('B')
            if r is not None and g is not None and b is not None:
                return {
                    'R': float(r.text or 0),
                    'G': float(g.text or 0),
                    'B': float(b.text or 0)
                }
            return {"R": 0, "G": 0, "B": 0}
        elif tag == 'Vector2' or tag == 'Vector3':
            # For vectors, combine components
            x = prop_elem.find('X')
            y = prop_elem.find('Y')
            z = prop_elem.find('Z') if tag == 'Vector3' else None
            
            result = {
                'X': float(x.text or 0) if x is not None else 0,
                'Y': float(y.text or 0) if y is not None else 0
            }
            
            if z is not None:
                result['Z'] = float(z.text or 0)
                
            return result
        elif tag == 'CFrame' or tag == 'CoordinateFrame':
            # For CFrames, extract all components
            components = {}
            for component in prop_elem:
                components[component.tag] = float(component.text or 0)
            return components
        elif tag == 'PhysicalProperties':
            # Physical properties have sub-elements
            return {"CustomPhysics": prop_elem.find('CustomPhysics').text.lower() == 'true'}
        else:
            # For unknown types, just return the XML as string
            return etree.tostring(prop_elem, encoding='unicode')

    def _get_game_name(self):
        """Extract the game name from the place file."""
        # Try to find a suitable name from DataModel or root elements
        for ref_id in self.root_instances:
            instance = self.instances.get(ref_id)
            if instance and instance['class'] == 'DataModel':
                if 'Name' in instance['properties']:
                    return instance['properties']['Name']
        
        # Fall back to workspace name
        for ref_id, instance in self.instances.items():
            if instance['class'] == 'Workspace':
                if 'Name' in instance['properties']:
                    return instance['properties']['Name']
        
        # Use the filename as a last resort
        return self.rbxlx_path.stem
