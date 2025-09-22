"""PIPL property types and constants for After Effects plugins."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import struct
from enum import IntEnum

class Stage(IntEnum):
    """Version stage enumeration"""
    DEVELOP = 0
    ALPHA = 1
    BETA = 2
    RELEASE = 3

@dataclass
class VersionInfo:
    """Version information container"""
    version: int
    subversion: int
    bugversion: int
    stage: Stage
    build: int

    def __str__(self):
        stage_names = {Stage.DEVELOP: "Develop", Stage.ALPHA: "Alpha",
                      Stage.BETA: "Beta", Stage.RELEASE: "Release"}
        return f"{self.version}.{self.subversion}.{self.bugversion} {stage_names[self.stage]} (Build {self.build})"

@dataclass
class PiplProperty:
    """Represents a single PIPL property."""
    property_type: str  # 4-character code like 'kind', 'name', etc.
    data: bytes
    length: int

    def __str__(self) -> str:
        return f"Property(type='{self.property_type}', length={self.length})"

# PIPL property type constants
PIPL_PROPERTY_TYPES = {
    b'kind': 'Kind',
    b'name': 'Name',
    b'catg': 'Category',
    b'8664': 'CodeWin64X86',  # Windows 64-bit entry point
    b'mi64': 'CodeMacIntel64',  # Mac Intel 64-bit entry point
    b'ma64': 'CodeMacARM64',    # Mac ARM 64-bit entry point
    b'ePVR': 'AE_PiPL_Version',
    b'eSVR': 'AE_Effect_Spec_Version',
    b'eVER': 'AE_Effect_Version',
    b'eINF': 'AE_Effect_Info_Flags',
    b'eGLO': 'AE_Effect_Global_OutFlags',
    b'eGL2': 'AE_Effect_Global_OutFlags_2',
    b'eMNA': 'AE_Effect_Match_Name',
    b'aeFL': 'AE_Reserved_Info'
}

# Plugin kind constants
PLUGIN_KINDS = {
    b'eFKT': 'AEEffect',
    b'SPEA': 'AdobeSuitePea',
    b'ARPI': 'AdobeIllustrator',
    b'8BFM': 'FilterModule',
    b'8BIF': 'FormatModule'
}

# Standard After Effects flags
AE_OUT_FLAGS = {
    0x00000001: 'PF_OutFlag_KEEP_RESOURCE_OPEN',
    0x00000002: 'PF_OutFlag_WIDE_TIME_INPUT',
    0x00000004: 'PF_OutFlag_NON_PARAM_VARY',
    0x00000010: 'PF_OutFlag_SEQUENCE_DATA_NEEDS_FLATTENING',
    0x00000020: 'PF_OutFlag_I_DO_DIALOG',
    0x00000040: 'PF_OutFlag_USE_OUTPUT_EXTENT',
    0x00000080: 'PF_OutFlag_SEND_DO_DIALOG',
    0x00000100: 'PF_OutFlag_DISPLAY_ERROR_MESSAGE',
    0x00000200: 'PF_OutFlag_I_EXPAND_BUFFER',
    0x00000400: 'PF_OutFlag_PIX_INDEPENDENT',
    0x00000800: 'PF_OutFlag_I_WRITE_INPUT_BUFFER',
    0x00001000: 'PF_OutFlag_I_SHRINK_BUFFER',
    0x00002000: 'PF_OutFlag_WORKS_IN_PLACE',
    0x00008000: 'PF_OutFlag_CUSTOM_UI',
    0x00020000: 'PF_OutFlag_REFRESH_UI',
    0x00040000: 'PF_OutFlag_NOP_RENDER',
    0x00080000: 'PF_OutFlag_I_USE_SHUTTER_ANGLE',
    0x00100000: 'PF_OutFlag_I_USE_AUDIO',
    0x00200000: 'PF_OutFlag_I_AM_OBSOLETE',
    0x00400000: 'PF_OutFlag_FORCE_RERENDER',
    0x00800000: 'PF_OutFlag_PiPL_OVERRIDES_OUTDATA_OUTFLAGS',
    0x01000000: 'PF_OutFlag_I_HAVE_EXTERNAL_DEPENDENCIES',
    0x02000000: 'PF_OutFlag_DEEP_COLOR_AWARE',
    0x04000000: 'PF_OutFlag_SEND_UPDATE_PARAMS_UI',
    0x08000000: 'PF_OutFlag_AUDIO_FLOAT_ONLY',
    0x10000000: 'PF_OutFlag_AUDIO_IIR',
    0x20000000: 'PF_OutFlag_I_SYNTHESIZE_AUDIO',
    0x40000000: 'PF_OutFlag_AUDIO_EFFECT_TOO',
    0x80000000: 'PF_OutFlag_AUDIO_EFFECT_ONLY'
}

AE_OUT_FLAGS_2 = {
    0x00000001: 'PF_OutFlag2_SUPPORTS_QUERY_DYNAMIC_FLAGS',
    0x00000002: 'PF_OutFlag2_I_USE_3D_CAMERA',
    0x00000004: 'PF_OutFlag2_I_USE_3D_LIGHTS',
    0x00000008: 'PF_OutFlag2_PARAM_GROUP_START_COLLAPSED_FLAG',
    0x00000010: 'PF_OutFlag2_I_AM_THREADSAFE',
    0x00000020: 'PF_OutFlag2_CAN_COMBINE_WITH_DESTINATION',
    0x00000040: 'PF_OutFlag2_DOESNT_NEED_EMPTY_PIXELS',
    0x00000080: 'PF_OutFlag2_REVEALS_ZERO_ALPHA',
    0x00000100: 'PF_OutFlag2_PRESERVES_FULLY_OPAQUE_PIXELS',
    0x00000400: 'PF_OutFlag2_SUPPORTS_SMART_RENDER',
    0x00001000: 'PF_OutFlag2_FLOAT_COLOR_AWARE',
    0x00002000: 'PF_OutFlag2_I_USE_COLORSPACE_ENUMERATION',
    0x00004000: 'PF_OutFlag2_I_AM_DEPRECATED',
    0x00008000: 'PF_OutFlag2_PPRO_DO_NOT_CLONE_SEQUENCE_DATA_FOR_RENDER',
    0x00020000: 'PF_OutFlag2_AUTOMATIC_WIDE_TIME_INPUT',
    0x00040000: 'PF_OutFlag2_I_USE_TIMECODE',
    0x00080000: 'PF_OutFlag2_DEPENDS_ON_UNREFERENCED_MASKS',
    0x00100000: 'PF_OutFlag2_OUTPUT_IS_WATERMARKED',
    0x00200000: 'PF_OutFlag2_I_MIX_GUID_DEPENDENCIES',
    0x00400000: 'PF_OutFlag2_AE13_5_THREADSAFE',
    0x00800000: 'PF_OutFlag2_SUPPORTS_GET_FLATTENED_SEQUENCE_DATA',
    0x01000000: 'PF_OutFlag2_CUSTOM_UI_ASYNC_MANAGER',
    0x02000000: 'PF_OutFlag2_SUPPORTS_GPU_RENDER_F32',
    0x08000000: 'PF_OutFlag2_SUPPORTS_THREADED_RENDERING',
    0x10000000: 'PF_OutFlag2_MUTABLE_RENDER_SEQUENCE_DATA_SLOWER'
}

def decode_flags(flags_value: int, flags_dict: Dict[int, str]) -> str:
    """Convert flags integer to readable flag names."""
    active_flags = []
    for flag_bit, flag_name in flags_dict.items():
        if flags_value & flag_bit:
            active_flags.append(flag_name)

    if not active_flags:
        return "0"
    elif len(active_flags) == 1:
        return active_flags[0]
    else:
        return " | ".join(active_flags)

def decode_version(version_bytes: bytes) -> tuple:
    """Decode version bytes to major.minor format."""
    if len(version_bytes) >= 4:
        major, minor = struct.unpack('>HH', version_bytes[:4])
        return major, minor
    return 0, 0

def decode_string(data: bytes) -> str:
    """Decode string data from PIPL property."""
    if not data:
        return ""

    # Check for Pascal string format (length byte + string)
    if len(data) > 0 and data[0] < len(data) and data[0] > 0:
        length = data[0]
        if length + 1 <= len(data):
            return data[1:length+1].decode('utf-8', errors='ignore')

    # Try as null-terminated string
    null_pos = data.find(b'\x00')
    if null_pos >= 0:
        return data[:null_pos].decode('utf-8', errors='ignore')

    # Try as plain string
    return data.decode('utf-8', errors='ignore')

def decode_entry_point(data: bytes) -> str:
    """Decode entry point string from code property."""
    return decode_string(data)

def extract_pf_version(encoded: int) -> VersionInfo:
    """Extract version information from encoded version value using AE format."""
    # PF_VERS constants from After Effects SDK
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

def decode_effect_version(data: bytes) -> Optional[VersionInfo]:
    """Decode effect version from property data."""
    if len(data) >= 4:
        encoded_version = struct.unpack('>I', data[:4])[0]
        return extract_pf_version(encoded_version)
    return None