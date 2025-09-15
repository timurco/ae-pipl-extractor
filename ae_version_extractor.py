#!/usr/bin/env python3
"""
AE Version Extractor - Python version
Extracts version information from After Effects plugin .rsrc files
"""

import struct
import sys
import argparse
from pathlib import Path
from enum import IntEnum
from typing import Optional, Tuple


class Stage(IntEnum):
    """Version stage enumeration"""
    DEVELOP = 0
    ALPHA = 1
    BETA = 2
    RELEASE = 3


class VersionInfo:
    """Version information container"""
    def __init__(self, version: int, subversion: int, bugversion: int, stage: Stage, build: int):
        self.version = version
        self.subversion = subversion
        self.bugversion = bugversion
        self.stage = stage
        self.build = build
    
    def __str__(self):
        stage_names = {Stage.DEVELOP: "Develop", Stage.ALPHA: "Alpha", 
                      Stage.BETA: "Beta", Stage.RELEASE: "Release"}
        return f"{self.version}.{self.subversion}.{self.bugversion} {stage_names[self.stage]} (Build {self.build})"


def extract_pf_version(encoded: int) -> VersionInfo:
    """Extract version information from encoded version value"""
    # PF_VERS constants
    PF_VERS_BUILD_BITS = 0x1ff
    PF_VERS_BUILD_SHIFT = 0
    PF_VERS_STAGE_BITS = 0x3
    PF_VERS_STAGE_SHIFT = 9
    PF_VERS_BUGFIX_BITS = 0xf
    PF_VERS_BUGFIX_SHIFT = 11
    PF_VERS_SUBVERS_BITS = 0xf
    PF_VERS_SUBVERS_SHIFT = 15
    PF_VERS_VERS_BITS = 0x7
    PF_VERS_VERS_SHIFT = 19
    PF_VERS_VERS_HIGH_BITS = 0xf
    PF_VERS_VERS_HIGH_SHIFT = 26
    PF_VERS_VERS_LOW_SHIFT = 3

    build = (encoded >> PF_VERS_BUILD_SHIFT) & PF_VERS_BUILD_BITS
    stage_num = (encoded >> PF_VERS_STAGE_SHIFT) & PF_VERS_STAGE_BITS
    bugversion = (encoded >> PF_VERS_BUGFIX_SHIFT) & PF_VERS_BUGFIX_BITS
    subversion = (encoded >> PF_VERS_SUBVERS_SHIFT) & PF_VERS_SUBVERS_BITS
    
    version_low = (encoded >> PF_VERS_VERS_SHIFT) & PF_VERS_VERS_BITS
    version_high = (encoded >> PF_VERS_VERS_HIGH_SHIFT) & PF_VERS_VERS_HIGH_BITS
    version = (version_high << PF_VERS_VERS_LOW_SHIFT) | version_low

    stage = Stage(stage_num) if stage_num in [0, 1, 2, 3] else Stage.DEVELOP

    return VersionInfo(version, subversion, bugversion, stage, build)


def parse_mac_resource_fork(data: bytes) -> Optional[int]:
    """Parse Mac resource fork format"""
    if len(data) < 16:
        return None
    
    # Parse resource fork header
    data_offset, map_offset, data_length, map_length = struct.unpack('>IIII', data[:16])
    
    # Check if we have enough data for the map
    if map_offset + 16 >= len(data):
        return None
    
    # Jump to the resource map
    pos = map_offset + 16
    
    # Check if we have enough data for the next fields
    if pos + 10 >= len(data):
        return None
    
    # Skip next handle, next file, file ref
    pos += 10
    
    # Read type list offset and name list offset
    type_list_offset, name_list_offset = struct.unpack('>HH', data[pos:pos+4])
    pos += 4
    
    # Check if we have enough data for the type list
    type_list_pos = map_offset + type_list_offset
    if type_list_pos + 2 >= len(data):
        return None
    
    # Read number of types
    num_types = struct.unpack('>H', data[type_list_pos:type_list_pos+2])[0] + 1
    pos = type_list_pos + 2
    
    # Look for PiPL resource type
    for i in range(num_types):
        if pos + 8 >= len(data):
            break
        
        type_code, num_resources, resource_list_offset = struct.unpack('>IHH', data[pos:pos+8])
        pos += 8
        
        # Check if this is PiPL type (0x5069504C = "PiPL" in big endian)
        if type_code == 0x5069504C:
            # Jump to resource list
            resource_list_pos = map_offset + type_list_offset + resource_list_offset
            if resource_list_pos >= len(data):
                continue
            
            # Read first resource (assuming ID 16000)
            for j in range(num_resources):
                if resource_list_pos + 12 >= len(data):
                    break
                
                resource_id, name_offset, attributes_and_offset, handle = struct.unpack('>hHII', 
                    data[resource_list_pos:resource_list_pos+12])
                resource_list_pos += 12
                
                # Extract resource data offset
                resource_data_offset = attributes_and_offset & 0x00FFFFFF
                resource_pos = data_offset + resource_data_offset
                
                # Check if resource position is valid
                if resource_pos + 4 >= len(data):
                    continue
                
                # Read resource data length
                resource_length = struct.unpack('>I', data[resource_pos:resource_pos+4])[0]
                
                if resource_pos + 4 + resource_length > len(data):
                    continue
                
                # Read the PiPL data
                pipl_data = data[resource_pos + 4:resource_pos + 4 + resource_length]
                
                # Parse PiPL properties to find ae_effect_version
                version = parse_pipl_data(pipl_data)
                if version is not None:
                    return version
    
    return None


def parse_pipl_data(data: bytes) -> Optional[int]:
    """Parse PiPL data to find AE effect version"""
    if len(data) < 8:
        return None
    
    # Skip version (4 bytes) and read number of properties
    num_properties = struct.unpack('>I', data[4:8])[0]
    pos = 8
    
    # Parse each property
    for _ in range(num_properties):
        if pos + 16 >= len(data):
            break
        
        # Read property signature (4 bytes)
        signature = data[pos:pos+4]
        pos += 4
        
        # Read property key (4 bytes)
        key = data[pos:pos+4]
        pos += 4
        
        # Skip padding (4 bytes)
        pos += 4
        
        # Read property length
        length = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4
        
        # Check if this is the AE_Effect_Version property ("eVER")
        if key == b"eVER":
            # Read the encoded version value
            if pos + 4 <= len(data):
                encoded_version = struct.unpack('>I', data[pos:pos+4])[0]
                return encoded_version
        else:
            # Skip this property's data
            pos += length
            
            # Skip padding to align to 4-byte boundary on macOS
            padding = 0 if length % 4 == 0 else 4 - (length % 4)
            pos += padding
    
    return None


def parse_8bim_format(data: bytes) -> Optional[int]:
    """Parse 8BIM format (Photoshop plugin)"""
    pos = 0
    
    # Look for 8BIM chunks
    while pos < len(data) - 8:
        # Read chunk signature
        if pos + 4 > len(data):
            break
        
        signature = data[pos:pos+4]
        pos += 4
        
        # Check if this is an 8BIM chunk
        if signature == b"8BIM":
            # Read chunk key
            if pos + 4 > len(data):
                break
            
            key = data[pos:pos+4]
            pos += 4
            
            # Read chunk length (first length field)
            if pos + 4 > len(data):
                break
            
            length1 = struct.unpack('>I', data[pos:pos+4])[0]
            pos += 4
            
            # Check if this is the eVER chunk (AE effect version)
            if key == b"eVER":
                # Read the second length field
                if pos + 4 > len(data):
                    break
                
                length2 = struct.unpack('>I', data[pos:pos+4])[0]
                pos += 4
                
                # Read the encoded version value
                if pos + 4 <= len(data):
                    encoded_version = struct.unpack('>I', data[pos:pos+4])[0]
                    return encoded_version
            else:
                # Skip this chunk's data
                pos += length1
        else:
            # Skip this chunk
            pos -= 4  # Go back to before signature
            pos += 1  # Skip one byte and try again
    
    return None


def parse_rsrc_file(data: bytes) -> Optional[int]:
    """Parse .rsrc file to find encoded version"""
    # Check if this is a Mac resource fork (starts with data_offset, map_offset)
    if len(data) >= 16:
        data_offset = struct.unpack('>I', data[0:4])[0]
        map_offset = struct.unpack('>I', data[4:8])[0]
        
        # If this looks like a resource fork (reasonable offsets), try that format
        # But make sure there's enough space for the map header and some data
        if (data_offset < len(data) and map_offset < len(data) and 
            data_offset > 0 and map_offset > data_offset and 
            map_offset + 32 < len(data) and  # Need at least 32 bytes for map header
            map_offset - data_offset > 400):  # Need reasonable gap between data and map
            return parse_mac_resource_fork(data)
    
    # Otherwise, try parsing as 8BIM format (Photoshop plugin)
    return parse_8bim_format(data)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Extract version information from AE plugin .rsrc files')
    parser.add_argument('rsrc_file', type=Path, help='Path to the .rsrc file to extract version from')
    
    args = parser.parse_args()
    
    try:
        # Read the .rsrc file
        with open(args.rsrc_file, 'rb') as f:
            data = f.read()
        
        # Parse the resource file to find the encoded version
        encoded_version = parse_rsrc_file(data)
        if encoded_version is None:
            print("Error: AE effect version not found in file", file=sys.stderr)
            sys.exit(1)
        
        # Decode the version
        version_info = extract_pf_version(encoded_version)
        
        # Print the results
        print(f"Raw encoded version: 0x{encoded_version:08X}")
        print("Decoded version information:")
        print(f"  Version: {version_info.version}")
        print(f"  Subversion: {version_info.subversion}")
        print(f"  Bug version: {version_info.bugversion}")
        print(f"  Stage: {version_info.stage.name}")
        print(f"  Build: {version_info.build}")
        print(f"  Full version: {version_info}")
        
    except FileNotFoundError:
        print(f"Error: File '{args.rsrc_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
