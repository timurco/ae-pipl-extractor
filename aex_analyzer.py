#!/usr/bin/env python3
"""Analyzer for Windows .aex files to extract PIPL resources."""

import struct
import sys
from typing import List, Dict, Optional, Tuple

class AexAnalyzer:
    """Analyze Windows .aex files (PE format) to extract PIPL resources."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = b''
        self.pe_header_offset = 0
        self.resource_table_offset = 0
        self._load_file()

    def _load_file(self) -> None:
        """Load the entire AEX file into memory."""
        try:
            with open(self.file_path, 'rb') as f:
                self.data = f.read()
        except Exception as e:
            raise Exception(f"Error loading AEX file: {e}")

    def _read_uint32(self, offset: int, little_endian: bool = True) -> int:
        """Read a 32-bit unsigned integer."""
        if offset + 4 > len(self.data):
            raise ValueError(f"Cannot read uint32 at offset {offset}")

        if little_endian:
            return struct.unpack('<I', self.data[offset:offset+4])[0]
        else:
            return struct.unpack('>I', self.data[offset:offset+4])[0]

    def _read_uint16(self, offset: int, little_endian: bool = True) -> int:
        """Read a 16-bit unsigned integer."""
        if offset + 2 > len(self.data):
            raise ValueError(f"Cannot read uint16 at offset {offset}")

        if little_endian:
            return struct.unpack('<H', self.data[offset:offset+2])[0]
        else:
            return struct.unpack('>H', self.data[offset:offset+2])[0]

    def _find_pe_header(self) -> bool:
        """Find the PE header in the file."""
        # Check for DOS header
        if len(self.data) < 64:
            return False

        if self.data[:2] != b'MZ':
            return False

        # Get PE header offset from DOS header
        self.pe_header_offset = self._read_uint32(60)

        # Verify PE signature
        if (self.pe_header_offset + 4 <= len(self.data) and
            self.data[self.pe_header_offset:self.pe_header_offset+4] == b'PE\x00\x00'):
            return True

        return False

    def _parse_pe_sections(self) -> List[Dict]:
        """Parse PE section headers."""
        sections = []

        if not self._find_pe_header():
            return sections

        # Skip PE signature (4 bytes) and COFF header (20 bytes)
        optional_header_offset = self.pe_header_offset + 24

        # Read number of sections from COFF header
        num_sections = self._read_uint16(self.pe_header_offset + 6)

        # Read optional header size
        optional_header_size = self._read_uint16(self.pe_header_offset + 20)

        # Section headers start after optional header
        section_headers_offset = optional_header_offset + optional_header_size

        for i in range(num_sections):
            section_offset = section_headers_offset + (i * 40)  # Each section header is 40 bytes

            if section_offset + 40 > len(self.data):
                break

            # Read section name (8 bytes)
            name = self.data[section_offset:section_offset+8].rstrip(b'\x00').decode('ascii', errors='ignore')

            # Read section info
            virtual_size = self._read_uint32(section_offset + 8)
            virtual_address = self._read_uint32(section_offset + 12)
            raw_size = self._read_uint32(section_offset + 16)
            raw_offset = self._read_uint32(section_offset + 20)

            sections.append({
                'name': name,
                'virtual_size': virtual_size,
                'virtual_address': virtual_address,
                'raw_size': raw_size,
                'raw_offset': raw_offset
            })

        return sections

    def _find_resource_section(self) -> Optional[Dict]:
        """Find the .rsrc section containing resources."""
        sections = self._parse_pe_sections()

        for section in sections:
            if section['name'] == '.rsrc':
                return section

        return None

    def _search_for_pipl_data(self) -> List[Dict]:
        """Search for PIPL data in the entire file."""
        pipl_blocks = []
        offset = 0

        # Look for PiPL resource markers
        while offset < len(self.data) - 16:
            # Look for resource type "PiPL"
            if self.data[offset:offset+4] == b'PiPL':
                print(f"Found 'PiPL' at offset 0x{offset:08x}")

                # Try to extract some data around it
                start = max(0, offset - 32)
                end = min(len(self.data), offset + 512)
                context = self.data[start:end]

                pipl_blocks.append({
                    'offset': offset,
                    'context_start': start,
                    'context_data': context
                })

            # Also look for reversed "LPiP"
            elif self.data[offset:offset+4] == b'LPiP':
                print(f"Found 'LPiP' (reversed) at offset 0x{offset:08x}")

                start = max(0, offset - 32)
                end = min(len(self.data), offset + 512)
                context = self.data[start:end]

                pipl_blocks.append({
                    'offset': offset,
                    'context_start': start,
                    'context_data': context
                })

            offset += 1

        return pipl_blocks

    def _search_for_8bim_signatures(self) -> List[Dict]:
        """Search for 8BIM signatures that might contain PIPL data."""
        bim_blocks = []
        offset = 0

        while offset < len(self.data) - 16:
            if self.data[offset:offset+4] == b'8BIM':
                # Get property type and length
                prop_type = self.data[offset+4:offset+8]

                try:
                    # Skip padding and read length
                    length_offset = offset + 8
                    while (length_offset < len(self.data) and
                           self.data[length_offset] == 0):
                        length_offset += 1

                    if length_offset + 4 <= len(self.data):
                        length = self._read_uint32(length_offset, little_endian=False)  # Big-endian for 8BIM

                        if length < 10000:  # Reasonable length
                            data_start = length_offset + 4
                            if data_start + length <= len(self.data):
                                prop_data = self.data[data_start:data_start + length]

                                bim_blocks.append({
                                    'offset': offset,
                                    'type': prop_type,
                                    'length': length,
                                    'data': prop_data
                                })
                except:
                    pass

            offset += 1

        return bim_blocks

    def analyze_file(self) -> Dict:
        """Analyze the AEX file and return findings."""
        results = {
            'file_path': self.file_path,
            'file_size': len(self.data),
            'is_pe_file': False,
            'sections': [],
            'resource_section': None,
            'pipl_blocks': [],
            'bim_blocks': []
        }

        # Check if it's a valid PE file
        results['is_pe_file'] = self._find_pe_header()

        if results['is_pe_file']:
            results['sections'] = self._parse_pe_sections()
            results['resource_section'] = self._find_resource_section()

        # Search for PIPL data
        results['pipl_blocks'] = self._search_for_pipl_data()
        results['bim_blocks'] = self._search_for_8bim_signatures()

        return results

    def extract_potential_rcp_data(self) -> Optional[bytes]:
        """Try to extract data that looks like RCP content."""
        # Look for resource data that might contain the compiled RCP
        resource_section = self._find_resource_section()

        if resource_section:
            start = resource_section['raw_offset']
            end = start + resource_section['raw_size']

            if end <= len(self.data):
                return self.data[start:end]

        return None

def analyze_aex_file(file_path: str):
    """Analyze an AEX file and print detailed information."""
    try:
        analyzer = AexAnalyzer(file_path)
        results = analyzer.analyze_file()

        print("=" * 80)
        print(f"AEX FILE ANALYSIS: {file_path}")
        print("=" * 80)

        print(f"File size: {results['file_size']:,} bytes")
        print(f"Valid PE file: {results['is_pe_file']}")

        if results['sections']:
            print(f"\nPE Sections ({len(results['sections'])}):")
            for section in results['sections']:
                print(f"  {section['name']:<8} - Virtual: 0x{section['virtual_address']:08x} "
                      f"Raw: 0x{section['raw_offset']:08x} Size: {section['raw_size']:,}")

        if results['resource_section']:
            print(f"\nResource section found:")
            rsrc = results['resource_section']
            print(f"  Offset: 0x{rsrc['raw_offset']:08x}")
            print(f"  Size: {rsrc['raw_size']:,} bytes")

        if results['pipl_blocks']:
            print(f"\nPiPL markers found: {len(results['pipl_blocks'])}")
            for i, block in enumerate(results['pipl_blocks']):
                print(f"  [{i+1}] Offset: 0x{block['offset']:08x}")

        if results['bim_blocks']:
            print(f"\n8BIM blocks found: {len(results['bim_blocks'])}")
            for i, block in enumerate(results['bim_blocks'][:10]):  # Show first 10
                prop_type = block['type'].decode('ascii', errors='ignore')
                print(f"  [{i+1:2d}] Type: '{prop_type}' Length: {block['length']} "
                      f"Offset: 0x{block['offset']:08x}")

                # Try to decode some common properties
                if prop_type in ['name', 'catg', 'eMNA']:
                    try:
                        from pipl_types import decode_string
                        decoded = decode_string(block['data'])
                        if decoded:
                            print(f"       → \"{decoded}\"")
                    except:
                        pass

        # Try to extract resource data
        resource_data = analyzer.extract_potential_rcp_data()
        if resource_data:
            print(f"\nResource section data: {len(resource_data):,} bytes")

            # Look for text patterns that might indicate RCP content
            if b'PiPL' in resource_data:
                print("  Contains 'PiPL' strings")
            if b'MIB8' in resource_data:
                print("  Contains 'MIB8' strings")
            if b'RSCS32' in resource_data:
                print("  Contains 'RSCS32' strings - likely compiled RCP!")

        print()
        return results

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 aex_analyzer.py <aex_file>")
        sys.exit(1)

    analyze_aex_file(sys.argv[1])