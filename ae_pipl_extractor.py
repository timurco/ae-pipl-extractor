#!/usr/bin/env python3
"""AE PIPL Extractor - Extract and decompile Adobe After Effects PIPL resources."""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional

from resource_fork_parser import ResourceForkParser
from rcp_parser import RcpParser
from r_generator import RGenerator
from pipl_types import PiplProperty
from aex_resource_extractor import AexResourceExtractor

def detect_file_type(file_path: str) -> Optional[str]:
    """Detect the type of input file based on extension and content."""
    path = Path(file_path)

    if not path.exists():
        return None

    extension = path.suffix.lower()

    # Direct file type detection
    if extension == '.rsrc':
        return 'rsrc'
    elif extension == '.rcp':
        return 'rcp'
    elif extension == '.aex':
        return 'aex'
    elif extension == '.plugin':
        return 'plugin'

    # Check if it's a directory (plugin bundle)
    if path.is_dir() and path.name.endswith('.plugin'):
        return 'plugin'

    # Try to detect by content
    try:
        with open(file_path, 'rb') as f:
            header = f.read(1024)

        # Check for RCP text format
        if b'PiPL' in header and b'BEGIN' in header:
            return 'rcp'

        # Check for PE executable (AEX)
        if header[:2] == b'MZ':
            return 'aex'

        # Check for resource fork binary format
        if b'8BIM' in header or len(header) > 256:
            return 'rsrc'

    except Exception:
        pass

    return None

def find_rsrc_in_plugin(plugin_path: str) -> Optional[str]:
    """Find .rsrc file inside a .plugin bundle."""
    plugin_dir = Path(plugin_path)

    # Look for .rsrc files in Resources directory
    resources_dir = plugin_dir / "Contents" / "Resources"
    if resources_dir.exists():
        for rsrc_file in resources_dir.glob("*.rsrc"):
            return str(rsrc_file)

    # Look for .rsrc files anywhere in the bundle
    for rsrc_file in plugin_dir.rglob("*.rsrc"):
        return str(rsrc_file)

    return None

def parse_file(file_path: str, file_type: str) -> List[PiplProperty]:
    """Parse the input file and extract PIPL properties."""
    properties = []

    if file_type == 'rsrc':
        try:
            parser = ResourceForkParser(file_path)
            properties = parser.parse_pipl_properties()

            if not properties:
                print(f"Warning: No PIPL properties found in {file_path}")
                # Print debug info
                info = parser.get_file_info()
                print(f"File info: {info}")

        except Exception as e:
            print(f"Error parsing .rsrc file: {e}")
            return []

    elif file_type == 'rcp':
        try:
            parser = RcpParser(file_path)
            properties = parser.parse_pipl_properties()

            if not properties:
                print(f"Warning: No PIPL properties found in {file_path}")
                info = parser.get_file_info()
                print(f"File info: {info}")

        except Exception as e:
            print(f"Error parsing .rcp file: {e}")
            return []

    elif file_type == 'aex':
        try:
            extractor = AexResourceExtractor(file_path)
            properties = extractor.extract_pipl_properties()

            if not properties:
                print(f"Warning: No PIPL properties found in {file_path}")

        except Exception as e:
            print(f"Error parsing .aex file: {e}")
            return []

    elif file_type == 'plugin':
        try:
            # Find .rsrc file inside plugin bundle
            rsrc_path = find_rsrc_in_plugin(file_path)
            if rsrc_path:
                print(f"Found .rsrc file: {rsrc_path}")
                parser = ResourceForkParser(rsrc_path)
                properties = parser.parse_pipl_properties()

                if not properties:
                    print(f"Warning: No PIPL properties found in {rsrc_path}")
            else:
                print(f"Error: No .rsrc file found in plugin bundle {file_path}")
                return []

        except Exception as e:
            print(f"Error parsing .plugin bundle: {e}")
            return []

    return properties

def main():
    parser = argparse.ArgumentParser(
        description="Extract and decompile Adobe After Effects PIPL resources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s plugin.rsrc -o plugin.r              # Extract from macOS .rsrc file
  %(prog)s plugin.rcp -o plugin.r               # Extract from Windows .rcp file
  %(prog)s plugin.aex -o plugin.r               # Extract from Windows .aex file
  %(prog)s plugin.plugin -o plugin.r            # Extract from macOS .plugin bundle
  %(prog)s plugin.rsrc --info                   # Show plugin information only
        """
    )

    parser.add_argument(
        'input_file',
        help='Input file (.rsrc, .rcp, .aex, or .plugin bundle)'
    )

    parser.add_argument(
        '--force-type',
        choices=['rsrc', 'rcp', 'aex', 'plugin'],
        help='Force file type detection (rsrc, rcp, aex, or plugin)'
    )

    args = parser.parse_args()

    # Check input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)

    # Detect file type
    if args.force_type:
        file_type = args.force_type
    else:
        file_type = detect_file_type(args.input_file)

    if not file_type:
        print(f"Error: Could not detect file type for '{args.input_file}'.")
        print("Use --force-type to specify the file type manually.")
        sys.exit(1)

    print(f"Detected file type: {file_type}")

    # Parse the file
    print(f"Parsing {args.input_file}...")
    properties = parse_file(args.input_file, file_type)

    if not properties:
        print("No PIPL properties found. Exiting.")
        sys.exit(1)

    print(f"Found {len(properties)} PIPL properties: ")

    # Generate .r file
    generator = RGenerator(properties)
    generator.print_info()

if __name__ == '__main__':
    main()