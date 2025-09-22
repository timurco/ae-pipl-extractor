#!/usr/bin/env python3
"""Analyzer to extract Config.h style information from PIPL files."""

import struct
from typing import Dict, Any
from resource_fork_parser import ResourceForkParser
from rcp_parser import RcpParser
from pipl_types import decode_string, decode_flags, AE_OUT_FLAGS, AE_OUT_FLAGS_2

def decode_effect_version(version_value: int) -> Dict[str, Any]:
    """Decode effect version from integer value using AE format."""
    # AE version format: MAJOR_VERSION * 524288 + MINOR_VERSION * 32768 + BUG_VERSION * 2048 + STAGE_VERSION * 512 + BUILD_VERSION

    major = version_value // 524288
    remainder = version_value % 524288

    minor = remainder // 32768
    remainder = remainder % 32768

    bug = remainder // 2048
    remainder = remainder % 2048

    stage = remainder // 512
    build = remainder % 512

    stage_names = {
        0: "PF_Stage_DEVELOP",
        1: "PF_Stage_ALPHA",
        2: "PF_Stage_BETA",
        3: "PF_Stage_RELEASE"
    }

    return {
        'major': major,
        'minor': minor,
        'bug': bug,
        'stage': stage,
        'stage_name': stage_names.get(stage, f"Unknown({stage})"),
        'build': build,
        'version_string': f"{major}.{minor}.{bug}",
        'full_string': f"{major}.{minor}.{bug} {stage_names.get(stage, 'Unknown')} (Build {build})"
    }

def analyze_pipl_file(file_path: str) -> Dict[str, Any]:
    """Analyze PIPL file and extract Config.h style information."""

    # Determine file type and parse
    if file_path.endswith('.rsrc'):
        parser = ResourceForkParser(file_path)
        properties = parser.parse_pipl_properties()
    elif file_path.endswith('.rcp'):
        parser = RcpParser(file_path)
        properties = parser.parse_pipl_properties()
    else:
        raise ValueError("Unsupported file type. Use .rsrc or .rcp files.")

    # Initialize config data
    config_data = {
        'FX_NAME': 'Unknown Plugin',
        'FX_CATEGORY': 'Utility',
        'FX_UNIQUEID': 'UNKNOWN',
        'MAJOR_VERSION': 1,
        'MINOR_VERSION': 0,
        'BUG_VERSION': 0,
        'STAGE_VERSION': 0,
        'BUILD_VERSION': 1,
        'FX_OUT_FLAGS': [],
        'FX_OUT_FLAGS2': [],
        'entry_points': {},
        'raw_properties': []
    }

    # Process each property
    for prop in properties:
        prop_info = {
            'type': prop.property_type,
            'length': prop.length,
            'data_hex': prop.data.hex()[:40] + ('...' if len(prop.data) > 20 else ''),
            'decoded_value': None
        }

        # Map reversed property types from RCP
        actual_type = prop.property_type

        # Handle reversed 4-character strings from RCP format
        if len(prop.property_type) == 4 and not prop.property_type.startswith('e'):
            # Try reversing the property type
            reversed_type = prop.property_type[::-1]
            if reversed_type in ['kind', 'name', 'catg', '8664']:
                actual_type = reversed_type

        # Handle specific mappings
        type_mappings = {
            'dnik': 'kind',
            'eman': 'name',
            'gtac': 'catg',
            '4668': '8664',
            'ANMe': 'eMNA',
            'RVPe': 'ePVR',
            'RVSe': 'eSVR',
            'OLGe': 'eGLO',
            '2LGe': 'eGL2'
        }

        if prop.property_type in type_mappings:
            actual_type = type_mappings[prop.property_type]

        if actual_type == 'kind':
            # Plugin kind
            if len(prop.data) >= 4:
                kind_bytes = prop.data[:4]
                prop_info['decoded_value'] = f"Kind: {kind_bytes.decode('ascii', errors='ignore')}"

        elif actual_type == 'name':
            # Plugin name -> FX_NAME
            name = decode_string(prop.data)
            if name:
                config_data['FX_NAME'] = name
                prop_info['decoded_value'] = f'FX_NAME: "{name}"'

        elif actual_type == 'catg':
            # Category -> FX_CATEGORY
            category = decode_string(prop.data)
            if category:
                config_data['FX_CATEGORY'] = category
                prop_info['decoded_value'] = f'FX_CATEGORY: "{category}"'

        elif actual_type == 'eMNA':
            # Match name -> FX_UNIQUEID
            unique_id = decode_string(prop.data)
            if unique_id:
                config_data['FX_UNIQUEID'] = unique_id
                prop_info['decoded_value'] = f'FX_UNIQUEID: "{unique_id}"'

        elif actual_type in ['8664', 'mi64', 'ma64']:
            # Entry points
            entry_point = decode_string(prop.data)
            config_data['entry_points'][actual_type] = entry_point
            platform_map = {
                '8664': 'Windows 64-bit',
                'mi64': 'macOS Intel 64-bit',
                'ma64': 'macOS ARM 64-bit'
            }
            prop_info['decoded_value'] = f'{platform_map[actual_type]}: "{entry_point}"'

        elif actual_type == 'eVER':
            # Effect version -> MAJOR_VERSION, MINOR_VERSION, etc.
            if len(prop.data) >= 4:
                version_value = struct.unpack('>I', prop.data[:4])[0]
                version_info = decode_effect_version(version_value)

                config_data['MAJOR_VERSION'] = version_info['major']
                config_data['MINOR_VERSION'] = version_info['minor']
                config_data['BUG_VERSION'] = version_info['bug']
                config_data['STAGE_VERSION'] = version_info['stage']
                config_data['BUILD_VERSION'] = version_info['build']

                prop_info['decoded_value'] = f"Version: {version_info['full_string']} (raw: 0x{version_value:08x})"

        elif actual_type == 'eGLO':
            # Global flags -> FX_OUT_FLAGS
            if len(prop.data) >= 4:
                flags_value = struct.unpack('>I', prop.data[:4])[0]
                active_flags = []
                for flag_bit, flag_name in AE_OUT_FLAGS.items():
                    if flags_value & flag_bit:
                        active_flags.append(flag_name)

                config_data['FX_OUT_FLAGS'] = active_flags
                prop_info['decoded_value'] = f"FX_OUT_FLAGS: {' + '.join(active_flags[:3])}{'...' if len(active_flags) > 3 else ''}"

        elif actual_type == 'eGL2':
            # Global flags 2 -> FX_OUT_FLAGS2
            if len(prop.data) >= 4:
                flags_value = struct.unpack('>I', prop.data[:4])[0]
                active_flags = []
                for flag_bit, flag_name in AE_OUT_FLAGS_2.items():
                    if flags_value & flag_bit:
                        active_flags.append(flag_name)

                config_data['FX_OUT_FLAGS2'] = active_flags
                prop_info['decoded_value'] = f"FX_OUT_FLAGS2: {' + '.join(active_flags[:3])}{'...' if len(active_flags) > 3 else ''}"

        elif actual_type == 'ePVR':
            # AE PiPL Version
            if len(prop.data) >= 4:
                major, minor = struct.unpack('>HH', prop.data[:4])
                prop_info['decoded_value'] = f"AE PiPL Version: {major}.{minor}"

        elif actual_type == 'eSVR':
            # AE Effect Spec Version
            if len(prop.data) >= 4:
                major, minor = struct.unpack('>HH', prop.data[:4])
                prop_info['decoded_value'] = f"AE Effect Spec Version: {major}.{minor}"

        elif actual_type == 'eINF':
            # Effect Info Flags
            if len(prop.data) >= 4:
                flags = struct.unpack('>I', prop.data[:4])[0]
                prop_info['decoded_value'] = f"Effect Info Flags: {flags}"

        elif actual_type == 'aeFL':
            # Reserved Info
            if len(prop.data) >= 4:
                reserved = struct.unpack('>I', prop.data[:4])[0]
                prop_info['decoded_value'] = f"Reserved Info: {reserved}"

        else:
            # Unknown property
            prop_info['decoded_value'] = f"Unknown property type: {actual_type}"

        config_data['raw_properties'].append(prop_info)

    # Calculate RESSOURCEVERSION
    config_data['RESSOURCEVERSION'] = (
        config_data['MAJOR_VERSION'] * 524288 +
        config_data['MINOR_VERSION'] * 32768 +
        config_data['BUG_VERSION'] * 2048 +
        config_data['STAGE_VERSION'] * 512 +
        config_data['BUILD_VERSION']
    )

    return config_data

def print_config_analysis(file_path: str):
    """Print detailed Config.h style analysis."""
    try:
        config = analyze_pipl_file(file_path)

        print("=" * 80)
        print("CONFIG.H STYLE ANALYSIS")
        print("=" * 80)

        print("\n// Plugin Information")
        print(f'#define FX_NAME "{config["FX_NAME"]}"')
        print(f'#define FX_CATEGORY "{config["FX_CATEGORY"]}"')
        print(f'#define FX_UNIQUEID "{config["FX_UNIQUEID"]}"')

        print("\n// Version Information")
        print(f'#define MAJOR_VERSION {config["MAJOR_VERSION"]}')
        print(f'#define MINOR_VERSION {config["MINOR_VERSION"]}')
        print(f'#define BUG_VERSION {config["BUG_VERSION"]}')
        print(f'#define STAGE_VERSION {config["STAGE_VERSION"]}  // PF_Stage_DEVELOP')
        print(f'#define BUILD_VERSION {config["BUILD_VERSION"]}')
        print()
        print(f'#define RESSOURCEVERSION {config["RESSOURCEVERSION"]}')
        print(f'// Calculated version: {config["MAJOR_VERSION"]}.{config["MINOR_VERSION"]}.{config["BUG_VERSION"]} (Build {config["BUILD_VERSION"]})')

        print("\n// Entry Points")
        for platform, entry_point in config['entry_points'].items():
            platform_map = {
                '8664': 'Windows 64-bit',
                'mi64': 'macOS Intel 64-bit',
                'ma64': 'macOS ARM 64-bit'
            }
            print(f'// {platform_map.get(platform, platform)}: "{entry_point}"')

        if config['FX_OUT_FLAGS']:
            print("\n// Output Flags")
            print("#define FX_OUT_FLAGS    (   " + " + \\\n                            ".join(config['FX_OUT_FLAGS']) + " )")

        if config['FX_OUT_FLAGS2']:
            print("\n// Output Flags 2")
            print("#define FX_OUT_FLAGS2   (   " + " + \\\n                            ".join(config['FX_OUT_FLAGS2']) + " )")

        print("\n" + "=" * 80)
        print("DETAILED PROPERTY ANALYSIS")
        print("=" * 80)

        for i, prop in enumerate(config['raw_properties'], 1):
            print(f"\n[{i:2d}] Property Type: '{prop['type']}'")
            print(f"     Length: {prop['length']} bytes")
            print(f"     Data: {prop['data_hex']}")
            if prop['decoded_value']:
                print(f"     → {prop['decoded_value']}")

        print(f"\nTotal properties found: {len(config['raw_properties'])}")

    except Exception as e:
        print(f"Error analyzing file: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 config_analyzer.py <pipl_file>")
        sys.exit(1)

    print_config_analysis(sys.argv[1])