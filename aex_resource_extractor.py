#!/usr/bin/env python3
"""Extract PIPL resources from Windows .aex files."""

import sys
import struct
from aex_analyzer import AexAnalyzer
from pipl_types import PiplProperty

class AexResourceExtractor:
    """Extract PIPL data from AEX resource section."""

    def __init__(self, file_path: str):
        self.analyzer = AexAnalyzer(file_path)
        self.resource_data = None
        self._load_resources()

    def _load_resources(self):
        """Load resource section data."""
        self.resource_data = self.analyzer.extract_potential_rcp_data()

    def _find_pipl_data_in_resources(self):
        """Find PIPL data in the resource section."""
        if not self.resource_data:
            return None

        # Look for MIB8 sequences which indicate PIPL data
        offset = 0
        pipl_start = None

        # Find the start of PIPL data (look for the first MIB8)
        while offset < len(self.resource_data) - 4:
            if self.resource_data[offset:offset+4] == b'MIB8':
                pipl_start = offset
                break
            offset += 1

        if pipl_start is None:
            return None

        # Extract PIPL data from MIB8 start to end of section
        return self.resource_data[pipl_start:]

    def _normalize_aex_property(self, prop_type_bytes: bytes, prop_data: bytes) -> tuple[str, bytes]:
        """Normalize AEX property type (reverse 4CC) and convert little-endian values to big-endian bytes.
        This ensures downstream decoders (expecting big-endian like .rcp/.rsrc) behave consistently.
        """
        # Reverse 4CC like b'RVPe' -> 'ePVR'
        try:
            corrected_type = prop_type_bytes[::-1].decode('ascii', errors='ignore')
        except Exception:
            corrected_type = prop_type_bytes[::-1].hex()

        # For known numeric properties, convert little-endian to big-endian byte order
        if corrected_type in ('ePVR', 'eSVR'):
            # Two 16-bit values in little-endian → repack as big-endian
            if len(prop_data) >= 4:
                major_le, minor_le = struct.unpack('<HH', prop_data[:4])
                prop_data = struct.pack('>HH', major_le, minor_le)
        elif corrected_type in ('eVER', 'eINF', 'eGLO', 'eGL2', 'aeFL'):
            # Single 32-bit value little-endian → big-endian
            if len(prop_data) >= 4:
                value_le = struct.unpack('<I', prop_data[:4])[0]
                prop_data = struct.pack('>I', value_le)
        # Other types (strings/entry points) are left as-is

        return corrected_type, prop_data

    def extract_pipl_properties(self):
        """Extract PIPL properties from the resource section."""
        pipl_data = self._find_pipl_data_in_resources()
        if not pipl_data:
            return []

        properties = []
        offset = 0

        print(f"Analyzing {len(pipl_data)} bytes of PIPL data...")

        while offset < len(pipl_data) - 12:
            # Look for MIB8 signature
            if pipl_data[offset:offset+4] == b'MIB8':
                try:
                    # Read property type (4 bytes after MIB8)
                    prop_type = pipl_data[offset+4:offset+8]

                    # Skip null padding (usually 4 bytes)
                    length_offset = offset + 8
                    while (length_offset < len(pipl_data) and
                           length_offset < offset + 16 and
                           pipl_data[length_offset] == 0):
                        length_offset += 1

                    # Read length (little-endian for Windows resources)
                    if length_offset + 4 <= len(pipl_data):
                        length = struct.unpack('<I', pipl_data[length_offset:length_offset+4])[0]

                        # Validate length
                        if length > 0 and length < 10000:
                            data_start = length_offset + 4

                            if data_start + length <= len(pipl_data):
                                prop_data = pipl_data[data_start:data_start + length]

                                # Normalize type and data endianness for AEX
                                corrected_type, corrected_data = self._normalize_aex_property(prop_type, prop_data)

                                properties.append(PiplProperty(
                                    property_type=corrected_type,
                                    data=corrected_data,
                                    length=len(corrected_data)
                                ))

                                print(f"Found property '{corrected_type}' length={len(corrected_data)} at offset=0x{offset:04x}")

                                # Move to next property
                                offset = data_start + length
                                # Align to next MIB8
                                while (offset < len(pipl_data) - 4 and
                                       pipl_data[offset:offset+4] != b'MIB8'):
                                    offset += 1
                                continue

                except Exception as e:
                    print(f"Error parsing property at offset 0x{offset:04x}: {e}")

            offset += 1

        return properties

    def save_extracted_data(self, output_file: str):
        """Save the raw PIPL data to a file for analysis."""
        pipl_data = self._find_pipl_data_in_resources()
        if pipl_data:
            with open(output_file, 'wb') as f:
                f.write(pipl_data)
            print(f"Saved {len(pipl_data)} bytes of PIPL data to {output_file}")
        else:
            print("No PIPL data found to save")

    def extract_from_aex(aex_file: str):
        """Extract PIPL properties from AEX file and analyze them."""
        print("=" * 80)
        print(f"EXTRACTING PIPL FROM: {aex_file}")
        print("=" * 80)

        try:
            extractor = AexResourceExtractor(aex_file)
            properties = extractor.extract_pipl_properties()

            if properties:
                print(f"\nExtracted {len(properties)} PIPL properties:")

                # Use our existing analyzer
                from config_analyzer import analyze_pipl_file
                from r_generator import RGenerator

                # Create a temporary wrapper to analyze extracted properties
                class PropertyWrapper:
                    def __init__(self, props):
                        self.properties = props

                    def parse_pipl_properties(self):
                        return self.properties

                # Analyze the properties
                try:
                    generator = RGenerator(properties)
                    summary = generator.get_summary()

                    print(f"\n--- EXTRACTED PLUGIN INFO ---")
                    print(f"Plugin Name: {summary['plugin_name']}")
                    print(f"Category: {summary['category']}")
                    print(f"Unique ID: {summary['unique_id']}")
                    print(f"Entry Point: {summary['entry_point']}")
                    print(f"Total Properties: {summary['total_properties']}")

                    print(f"\n--- PROPERTY DETAILS ---")
                    for i, prop in enumerate(properties, 1):
                        print(f"[{i:2d}] '{prop.property_type}' - {prop.length} bytes")

                        # Show decoded values for key properties
                        if prop.property_type in ['name', 'catg', 'eMNA']:
                            from pipl_types import decode_string
                            decoded = decode_string(prop.data)
                            if decoded:
                                print(f"     → \"{decoded}\"")
                        elif prop.property_type == 'eVER':
                            if len(prop.data) >= 4:
                                version_be = struct.unpack('>I', prop.data[:4])[0]
                                print(f"     → Version: 0x{version_be:08x}")

                except Exception as e:
                    print(f"Error analyzing properties: {e}")

            else:
                print("No PIPL properties found in AEX file")

            # Save raw data for debugging
            extractor.save_extracted_data(f"{aex_file}_extracted_pipl.bin")

        except Exception as e:
            print(f"Error extracting from {aex_file}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 aex_resource_extractor.py <aex_file>")
        sys.exit(1)

    AexResourceExtractor.extract_from_aex(sys.argv[1])