"""Parser for macOS resource fork (.rsrc) files containing PIPL data."""

import struct
from typing import List, Dict, Optional, Tuple, Any
from pipl_types import PiplProperty, PIPL_PROPERTY_TYPES

class ResourceForkParser:
    """Parse macOS resource fork files to extract PIPL data."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = b''
        self._load_file()

    def _load_file(self) -> None:
        """Load the entire resource file into memory."""
        try:
            with open(self.file_path, 'rb') as f:
                self.data = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Resource file not found: {self.file_path}")
        except Exception as e:
            raise Exception(f"Error loading resource file: {e}")

    def _read_big_endian_uint32(self, offset: int) -> int:
        """Read a big-endian 32-bit unsigned integer."""
        if offset + 4 > len(self.data):
            raise ValueError(f"Cannot read uint32 at offset {offset}")
        return struct.unpack('>I', self.data[offset:offset+4])[0]

    def _read_big_endian_uint16(self, offset: int) -> int:
        """Read a big-endian 16-bit unsigned integer."""
        if offset + 2 > len(self.data):
            raise ValueError(f"Cannot read uint16 at offset {offset}")
        return struct.unpack('>H', self.data[offset:offset+2])[0]

    def _find_pipl_in_binary(self) -> List[Dict]:
        """Find PIPL data in binary by looking for 8BIM signatures."""
        pipl_data_blocks = []
        offset = 0

        while offset < len(self.data) - 12:
            # Look for '8BIM' signature
            if self.data[offset:offset+4] == b'8BIM':
                # Found potential PIPL property
                try:
                    property_type = self.data[offset+4:offset+8]

                    # Skip 4 null bytes (standard in this format)
                    null_bytes_offset = offset + 8
                    if null_bytes_offset + 4 <= len(self.data):
                        # Read length at offset + 12
                        length_offset = null_bytes_offset + 4
                        if length_offset + 4 <= len(self.data):
                            length = self._read_big_endian_uint32(length_offset)
                            data_start = length_offset + 4

                            if data_start + length <= len(self.data):
                                property_data = self.data[data_start:data_start + length]
                                pipl_data_blocks.append({
                                    'type': property_type,
                                    'length': length,
                                    'data': property_data
                                })
                                # Move to next property (align to next 8BIM)
                                offset = data_start + length
                            else:
                                offset += 1
                        else:
                            offset += 1
                    else:
                        offset += 1
                except Exception as e:
                    offset += 1
            else:
                offset += 1

        return pipl_data_blocks

    def parse_pipl_properties(self) -> List[PiplProperty]:
        """Parse PIPL properties from the resource fork."""
        properties = []

        # First try to find PIPL data by looking for 8BIM signatures
        pipl_blocks = self._find_pipl_in_binary()

        for block in pipl_blocks:
            prop_type = block['type'].decode('ascii', errors='ignore')

            # Map property type codes
            if block['type'] in PIPL_PROPERTY_TYPES:
                properties.append(PiplProperty(
                    property_type=prop_type,
                    data=block['data'],
                    length=block['length']
                ))

        return properties

    def extract_resource_data(self) -> Optional[bytes]:
        """Extract raw resource data for debugging purposes."""
        if not self.data:
            return None

        # Look for PIPL resource marker
        pipl_marker = b'PiPL'
        pipl_pos = self.data.find(pipl_marker)

        if pipl_pos >= 0:
            # Return data starting from PIPL marker
            return self.data[pipl_pos:]

        return self.data

    def get_file_info(self) -> Dict:
        """Get basic information about the resource file."""
        return {
            'file_path': self.file_path,
            'file_size': len(self.data),
            'has_pipl_marker': b'PiPL' in self.data,
            'has_8bim_signatures': b'8BIM' in self.data,
            'num_8bim_blocks': self.data.count(b'8BIM')
        }

    def debug_hex_dump(self, start: int = 0, length: int = 256) -> str:
        """Create a hex dump of the file for debugging."""
        end = min(start + length, len(self.data))
        result = []

        for i in range(start, end, 16):
            hex_part = ' '.join(f'{b:02x}' for b in self.data[i:i+16])
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in self.data[i:i+16])
            result.append(f'{i:08x}  {hex_part:<48} |{ascii_part}|')

        return '\n'.join(result)