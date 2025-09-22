"""Parser for Windows resource compiler (.rcp) files containing PIPL data."""

import re
import struct
from typing import List, Dict, Optional
from pipl_types import PiplProperty

class RcpParser:
    """Parse Windows .rcp resource compiler files to extract PIPL data."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ''
        self._load_file()

    def _load_file(self) -> None:
        """Load the RCP file content."""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.content = f.read()
        except Exception:
            # Try with different encoding
            with open(self.file_path, 'r', encoding='latin-1') as f:
                self.content = f.read()

    def _parse_string_literal(self, text: str) -> bytes:
        """Parse a string literal with escape sequences."""
        # Handle hex escapes like \x12
        text = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), text)

        # Handle null terminators
        text = text.replace('\\0', '\x00')

        return text.encode('utf-8', errors='ignore')

    def _parse_long_value(self, text: str) -> int:
        """Parse long integer values from RCP format."""
        text = text.strip()

        if text.endswith('L'):
            text = text[:-1]

        if text.startswith('0x'):
            return int(text, 16)
        else:
            return int(text)

    def _extract_pipl_block(self) -> Optional[str]:
        """Extract the PIPL resource block from RCP content."""
        # Find the PiPL resource definition
        pipl_pattern = r'(\d+)\s+PiPL\s+DISCARDABLE\s*\n\s*BEGIN\s*\n(.*?)\nEND'
        match = re.search(pipl_pattern, self.content, re.DOTALL | re.MULTILINE)

        if match:
            resource_id, pipl_content = match.groups()
            return pipl_content.strip()

        return None

    def _parse_pipl_properties(self, pipl_content: str) -> List[Dict]:
        """Parse individual properties from PIPL block content."""
        properties = []
        lines = [line.strip() for line in pipl_content.split('\n')]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip comments, empty lines, and initial bytes
            if (line.startswith('/*') or line.startswith('//') or not line.strip() or
                line.startswith('0x0001') or 'kCurrentPiPLVersion' in line or 'Property Count' in line):
                i += 1
                continue

            # Look for property signatures like "MIB8"
            if line.strip() == '"MIB8",':
                # This starts a new property
                if i + 1 < len(lines):
                    i += 1
                    type_line = lines[i].strip()

                    # Extract property type
                    if type_line.startswith('"') and (',' in type_line or type_line.endswith('"')):
                        # Remove quotes and comma - DON'T reverse yet
                        if type_line.endswith(','):
                            prop_type_raw = type_line[1:-2]
                        else:
                            prop_type_raw = type_line[1:-1]

                        # Keep the original property type (will be mapped later)
                        prop_type = prop_type_raw

                        # Skip RSCS32(0) lines
                        i += 1
                        while i < len(lines) and 'RSCS32(0)' in lines[i]:
                            i += 1

                        # Look for length specification
                        if i < len(lines) and 'RSCS32(' in lines[i]:
                            length_match = re.search(r'RSCS32\(\s*(\d+)\s*\)', lines[i])
                            if length_match:
                                length = int(length_match.group(1))
                                i += 1

                                # Extract property data from the next line(s)
                                if i < len(lines):
                                    data_line = lines[i].strip()
                                    if data_line.endswith(','):
                                        data_line = data_line[:-1]

                                    properties.append({
                                        'signature': 'MIB8',
                                        'type': prop_type,
                                        'length': length,
                                        'data_line': data_line
                                    })

                    elif type_line.startswith('0x') and 'L' in type_line:
                        # Handle hex property types like 0x65564552L
                        hex_value = self._parse_long_value(type_line.split(',')[0])
                        try:
                            prop_type = struct.pack('>I', hex_value).decode('ascii', errors='ignore')
                        except:
                            prop_type = f'0x{hex_value:08x}'

                        # Look for following lines
                        i += 1
                        if i < len(lines) and lines[i].strip() == '0L,':
                            i += 1
                        if i < len(lines) and lines[i].strip().endswith('L'):
                            length_line = lines[i].strip()
                            if length_line.endswith(','):
                                length_line = length_line[:-1]
                            if length_line.endswith('L'):
                                length_line = length_line[:-1]
                            try:
                                length = int(length_line)
                            except:
                                length = 4
                            i += 1
                            if i < len(lines):
                                data_line = lines[i].strip()
                                if data_line.endswith(','):
                                    data_line = data_line[:-1]
                                properties.append({
                                    'signature': 'MIB8',
                                    'type': prop_type,
                                    'length': length,
                                    'data_line': data_line
                                })

            i += 1

        return properties

    def parse_pipl_properties(self) -> List[PiplProperty]:
        """Parse PIPL properties from the RCP file."""
        pipl_content = self._extract_pipl_block()
        if not pipl_content:
            return []

        raw_properties = self._parse_pipl_properties(pipl_content)
        properties = []

        for prop in raw_properties:
            # Convert property type to 4-character code
            prop_type = prop['type']
            if len(prop_type) > 4:
                prop_type = prop_type[:4]

            # Parse property data
            data_line = prop['data_line'].strip()
            if data_line.endswith(','):
                data_line = data_line[:-1]

            # Handle different data formats
            if data_line.startswith('"') and data_line.endswith('"'):
                # String literal
                string_content = data_line[1:-1]
                data = self._parse_string_literal(string_content)
            elif ',' in data_line and not data_line.startswith('"'):
                # Multiple numeric values
                values = [self._parse_long_value(v.strip()) for v in data_line.split(',') if v.strip()]
                if len(values) == 1:
                    data = struct.pack('>I', values[0])
                elif len(values) == 2:
                    data = struct.pack('>HH', values[0], values[1])
                else:
                    # Pack as array of 32-bit values
                    data = b''.join(struct.pack('>I', v) for v in values)
            elif data_line.endswith('L'):
                # Single long value
                value = self._parse_long_value(data_line)
                data = struct.pack('>I', value)
            else:
                # Try to parse as integer
                try:
                    value = int(data_line)
                    data = struct.pack('>I', value)
                except ValueError:
                    # Fallback to raw string
                    data = data_line.encode('utf-8', errors='ignore')

            properties.append(PiplProperty(
                property_type=prop_type,
                data=data,
                length=len(data)
            ))

        return properties

    def get_file_info(self) -> Dict:
        """Get basic information about the RCP file."""
        has_pipl = 'PiPL' in self.content
        pipl_content = self._extract_pipl_block()

        return {
            'file_path': self.file_path,
            'file_size': len(self.content),
            'has_pipl_block': has_pipl,
            'pipl_content_length': len(pipl_content) if pipl_content else 0,
            'num_mib8_signatures': self.content.count('"MIB8"')
        }