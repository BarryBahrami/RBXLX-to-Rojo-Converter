#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
utils.py - Utility functions and helpers for the RBXLX to Rojo converter
"""

import os
import re
import sys
import logging
import string
from pathlib import Path

# Create logger
logger = logging.getLogger('rbxlx_to_rojo')

def setup_logger(verbose=False):
    """Setup logger with appropriate level and handlers."""
    # Set logger level
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logger.setLevel(level)
    
    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)

def get_version():
    """Return the current version of the tool."""
    return "1.0.0"

def normalize_name(name):
    """
    Normalize a name to be used as a filename.
    
    Args:
        name (str): The name to normalize.
        
    Returns:
        str: The normalized name.
    """
    # Replace spaces and special characters with underscores
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    normalized = ''.join(c if c in valid_chars else '_' for c in name)
    
    # Remove leading/trailing underscores, spaces
    normalized = normalized.strip('_').strip()
    
    # Ensure the name is not empty
    if not normalized:
        normalized = "unnamed"
    
    return normalized

def escape_lua_string(s):
    """
    Escape a string for Lua.
    
    Args:
        s (str): The string to escape.
        
    Returns:
        str: The escaped string.
    """
    if not s:
        return ""
    
    # Replace backslashes first
    s = s.replace('\\', '\\\\')
    
    # Replace other special characters
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')
    
    return s

def is_valid_roblox_script(content):
    """
    Check if content looks like a valid Roblox script.
    
    Args:
        content (str): The script content to check.
        
    Returns:
        bool: True if content appears to be a valid script, False otherwise.
    """
    if not content:
        return False
    
    # Check for common Lua keywords
    lua_keywords = ['function', 'local', 'end', 'if', 'then', 'else', 'for', 'while', 'do', 'return']
    
    for keyword in lua_keywords:
        if re.search(r'\b' + keyword + r'\b', content):
            return True
    
    return False

def convert_base64_to_string(base64_string):
    """
    Convert a base64 string to a normal string.
    
    Args:
        base64_string (str): The base64 string to convert.
        
    Returns:
        str: The decoded string or empty string if decoding fails.
    """
    if not base64_string:
        return ""
    
    try:
        import base64
        decoded = base64.b64decode(base64_string).decode('utf-8')
        return decoded
    except:
        return ""
