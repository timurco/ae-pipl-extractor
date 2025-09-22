#!/usr/bin/env python3
"""Test script for AE PIPL Extractor."""

import sys
from resource_fork_parser import ResourceForkParser
from rcp_parser import RcpParser
from r_generator import RGenerator

def test_rsrc_parser():
    """Test the .rsrc parser."""
    print("Testing .rsrc parser...")
    try:
        parser = ResourceForkParser("/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/PssPlugin/PssPlugin.plugin/Contents/Resources/PssPlugin.rsrc")
        properties = parser.parse_pipl_properties()

        print(f"✓ Found {len(properties)} properties in .rsrc file")

        generator = RGenerator(properties)
        summary = generator.get_summary()
        print(f"✓ Plugin: {summary['plugin_name']}")
        print(f"✓ Category: {summary['category']}")
        print(f"✓ Match Name: {summary['unique_id']}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_rcp_parser():
    """Test the .rcp parser."""
    print("\nTesting .rcp parser...")
    try:
        parser = RcpParser("/Users/timurko/Downloads/Telegram/PssPlugin.rcp")
        properties = parser.parse_pipl_properties()

        print(f"✓ Found {len(properties)} properties in .rcp file")

        # Show actual property types found
        types_found = {}
        for prop in properties:
            if prop.property_type in types_found:
                types_found[prop.property_type] += 1
            else:
                types_found[prop.property_type] = 1

        print(f"✓ Property types: {list(types_found.keys())}")

        generator = RGenerator(properties)
        summary = generator.get_summary()
        print(f"✓ Plugin: {summary['plugin_name']}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def compare_results():
    """Compare results from both parsers."""
    print("\nComparing parser results...")

    try:
        rsrc_parser = ResourceForkParser("/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/PssPlugin/PssPlugin.plugin/Contents/Resources/PssPlugin.rsrc")
        rsrc_properties = rsrc_parser.parse_pipl_properties()

        rcp_parser = RcpParser("/Users/timurko/Downloads/Telegram/PssPlugin.rcp")
        rcp_properties = rcp_parser.parse_pipl_properties()

        print(f"RSRC found: {len(rsrc_properties)} properties")
        print(f"RCP found: {len(rcp_properties)} properties")

        # Compare property types
        rsrc_types = set(prop.property_type for prop in rsrc_properties)
        rcp_types = set(prop.property_type for prop in rcp_properties)

        print(f"RSRC types: {sorted(rsrc_types)}")
        print(f"RCP types: {sorted(rcp_types)}")

        # Generate summaries
        rsrc_gen = RGenerator(rsrc_properties)
        rcp_gen = RGenerator(rcp_properties)

        rsrc_summary = rsrc_gen.get_summary()
        rcp_summary = rcp_gen.get_summary()

        print("\nRSRC Plugin Info:")
        print(f"  Name: {rsrc_summary['plugin_name']}")
        print(f"  Category: {rsrc_summary['category']}")
        print(f"  Match Name: {rsrc_summary['unique_id']}")

        print("\nRCP Plugin Info:")
        print(f"  Name: {rcp_summary['plugin_name']}")
        print(f"  Category: {rcp_summary['category']}")
        print(f"  Match Name: {rcp_summary['unique_id']}")

    except Exception as e:
        print(f"✗ Error during comparison: {e}")

if __name__ == "__main__":
    print("AE PIPL Extractor Test Suite")
    print("=" * 40)

    rsrc_ok = test_rsrc_parser()
    rcp_ok = test_rcp_parser()

    if rsrc_ok and rcp_ok:
        compare_results()
        print("\n✓ All tests completed")
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)