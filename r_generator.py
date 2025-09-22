"""Generator for .r resource files from parsed PIPL properties."""

import struct
from typing import List, Dict
from pipl_types import (
    PiplProperty, PLUGIN_KINDS, AE_OUT_FLAGS, AE_OUT_FLAGS_2,
    decode_flags, decode_version, decode_string, decode_entry_point,
    decode_effect_version
)

class RGenerator:
    """Generate .r resource files from PIPL properties."""

    def __init__(self, properties: List[PiplProperty]):
        self.properties = properties
        self.plugin_name = "UnknownPlugin"
        self.category = "Utility"
        self.unique_id = "UNKN"
        self.entry_point = "EffectMain"

    def _normalize_property_type(self, prop_type: str) -> str:
        """Normalize property types from different sources (direct, reversed, Windows)."""
        # Mapping for reversed property types (from RCP/AEX)
        type_mappings = {
            'dnik': 'kind',
            'eman': 'name',
            'gtac': 'catg',
            '4668': '8664',
            'ANMe': 'eMNA',
            'RVPe': 'ePVR',
            'RVSe': 'eSVR',
            'REVe': 'eVER',
            'FNIe': 'eINF',
            'OLGe': 'eGLO',
            '2LGe': 'eGL2',
            'LFea': 'aeFL'
        }

        return type_mappings.get(prop_type, prop_type)

    def _extract_basic_info(self) -> None:
        """Extract basic plugin information from properties."""
        for prop in self.properties:
            normalized_type = self._normalize_property_type(prop.property_type)

            if normalized_type == 'name':
                self.plugin_name = decode_string(prop.data)
            elif normalized_type == 'catg':
                self.category = decode_string(prop.data)
            elif normalized_type == 'eMNA':
                self.unique_id = decode_string(prop.data)
            elif normalized_type in ['8664', 'mi64', 'ma64']:
                self.entry_point = decode_entry_point(prop.data)

    def _generate_property(self, prop: PiplProperty, index: int) -> str:
        """Generate a single property for the PIPL resource."""
        comment = f"/* [{index}] */"
        normalized_type = self._normalize_property_type(prop.property_type)

        if normalized_type == 'kind':
            # Plugin kind
            value = "AEEffect"  # Default
            if len(prop.data) >= 4:
                kind_bytes = prop.data[:4]
                if kind_bytes in PLUGIN_KINDS:
                    value = PLUGIN_KINDS[kind_bytes]
            return f"[{index}] Kind [{normalized_type}]: {value}"

        elif normalized_type == 'name':
            # Plugin name
            value = decode_string(prop.data)
            return f"[{index}] Name [{normalized_type}]: {value}"

        elif normalized_type == 'catg':
            # Category
            value = decode_string(prop.data)
            return f"[{index}] Category [{normalized_type}]: {value}"

        elif normalized_type == '8664':
            # Windows 64-bit code
            value = decode_entry_point(prop.data)
            return f"[{index}] Entry Point (Windows 64) [{normalized_type}]: {value}"

        elif normalized_type == 'mi64':
            # Mac Intel 64-bit code
            value = decode_entry_point(prop.data)
            return f"[{index}] Entry Point (Mac Intel 64) [{normalized_type}]: {value}"

        elif normalized_type == 'ma64':
            # Mac ARM 64-bit code
            value = decode_entry_point(prop.data)
            return f"[{index}] Entry Point (Mac ARM 64) [{normalized_type}]: {value}"

        elif normalized_type == 'ePVR':
            # AE PiPL Version
            major, minor = decode_version(prop.data)
            return f"[{index}] AE_PiPL_Version [{normalized_type}]: {major}, {minor}"

        elif normalized_type == 'eSVR':
            # AE Effect Spec Version
            major, minor = decode_version(prop.data)
            return f"[{index}] AE_Effect_Spec_Version [{normalized_type}]: {major}, {minor}"

        elif normalized_type == 'eVER':
            # Effect Version
            if len(prop.data) >= 4:
                version_raw = struct.unpack('>I', prop.data[:4])[0]
                version_info = decode_effect_version(prop.data)
                if version_info:
                    # VersionInfo implements __str__ for human-readable output
                    return f"[{index}] AE_Effect_Version [{normalized_type}]: {version_raw:#x} // {str(version_info)}"
                return f"[{index}] AE_Effect_Version [{normalized_type}]: {version_raw:#x} // Unrecognized Version Value"

        elif normalized_type == 'eINF':
            # Effect Info Flags
            if len(prop.data) >= 4:
                flags = struct.unpack('>I', prop.data[:4])[0]
            else:
                flags = 0
            return f"[{index}] AE_Effect_Info_Flags [{normalized_type}]: {flags}"

        elif normalized_type == 'eGLO':
            # Global Out Flags
            if len(prop.data) >= 4:
                flags_value = struct.unpack('>I', prop.data[:4])[0]
                flags_str = decode_flags(flags_value, AE_OUT_FLAGS)
                return f"[{index}] AE_Effect_Global_OutFlags [{normalized_type}]: {flags_str}"
            else:
                return f"[{index}] AE_Effect_Global_OutFlags [{normalized_type}]: <Error while parsing...>"

        elif normalized_type == 'eGL2':
            # Global Out Flags 2
            if len(prop.data) >= 4:
                flags_value = struct.unpack('>I', prop.data[:4])[0]
                flags_str = decode_flags(flags_value, AE_OUT_FLAGS_2)
                
                return f"[{index}] AE_Effect_Global_OutFlags_2 [{normalized_type}]: {flags_str}"

        elif normalized_type == 'eMNA':
            # Match Name
            match_name = decode_string(prop.data)
            return f"[{index}] AE_Effect_Match_Name [{normalized_type}]: {match_name}"

        elif normalized_type == 'aeFL':
            # Reserved Info
            if len(prop.data) >= 4:
                reserved = struct.unpack('>I', prop.data[:4])[0]
            else:
                reserved = 8
            return f"[{index}] AE_Reserved_Info [{normalized_type}]: {reserved}"

        else:
            # Unknown property
            data_hex = prop.data[:16].hex() if prop.data else "00"
            return f"[{index}] Unknown [{normalized_type}]: {data_hex}..."

    def print_info(self):
        self._extract_basic_info()
        
        # Generate each property
        for i, prop in enumerate(self.properties, 1):
            print(self._generate_property(prop, i))

    def get_summary(self) -> Dict:
        """Get a summary of the extracted plugin information."""
        self._extract_basic_info()

        property_summary = {}
        version_info = None
        ae_pipl_version = None
        ae_spec_version = None

        for prop in self.properties:
            if prop.property_type in property_summary:
                property_summary[prop.property_type] += 1
            else:
                property_summary[prop.property_type] = 1

            # Extract version information
            normalized_type = self._normalize_property_type(prop.property_type)
            if normalized_type == 'eVER':
                if len(prop.data) >= 4:
                    version_raw = struct.unpack('>I', prop.data[:4])[0]
                    version_info = decode_effect_version(version_raw)
            elif normalized_type == 'ePVR':
                ae_pipl_version = decode_version(prop.data)
            elif normalized_type == 'eSVR':
                ae_spec_version = decode_version(prop.data)

        summary = {
            'plugin_name': self.plugin_name,
            'category': self.category,
            'unique_id': self.unique_id,
            'entry_point': self.entry_point,
            'total_properties': len(self.properties),
            'property_types': property_summary
        }

        if version_info:
            summary['effect_version'] = str(version_info)
            summary['effect_version_raw'] = version_info

        if ae_pipl_version:
            summary['pipl_version'] = f"{ae_pipl_version[0]}.{ae_pipl_version[1]}"

        if ae_spec_version:
            summary['spec_version'] = f"{ae_spec_version[0]}.{ae_spec_version[1]}"

        return summary