# AE PIPL Extractor - Complete Usage Guide

A comprehensive Python tool for extracting and decompiling Adobe After Effects Plugin Information Property List (PIPL) resources from multiple file formats.

## 🚀 Features

- ✅ **macOS .rsrc files** - Resource fork binary format
- ✅ **Windows .rcp files** - Resource compiler text format
- ✅ **Windows .aex files** - Compiled plugin binaries (PE format)
- ✅ **macOS .plugin bundles** - Plugin bundle directories
- ✅ **Config.h analysis** - Extract all constants in Config.h format
- ✅ **Automatic type detection** - Smart file format detection
- ✅ **Cross-platform support** - Works on macOS, Windows, Linux

## 📁 Supported File Types

| Format | Description | Platform | Example |
|--------|-------------|----------|---------|
| `.rsrc` | Resource fork binary | macOS | `plugin.rsrc` |
| `.rcp` | Resource compiler text | Windows | `plugin.rcp` |
| `.aex` | Compiled plugin binary | Windows | `plugin.aex` |
| `.plugin` | Plugin bundle directory | macOS | `Plugin.plugin/` |

## 🛠️ Usage

### Basic Extraction

```bash
# Extract from any supported format
python3 ae_pipl_extractor.py input_file -o output.r

# Examples for each format:
python3 ae_pipl_extractor.py plugin.rsrc -o plugin.r              # macOS resource
python3 ae_pipl_extractor.py plugin.rcp -o plugin.r               # Windows text
python3 ae_pipl_extractor.py plugin.aex -o plugin.r               # Windows binary
python3 ae_pipl_extractor.py Plugin.plugin -o plugin.r            # macOS bundle
```

### Information Analysis

```bash
# Show plugin information without generating files
python3 ae_pipl_extractor.py plugin.aex --info

# Config.h style analysis
python3 config_analyzer.py plugin.rsrc
```

### Advanced Options

```bash
# Force file type detection
python3 ae_pipl_extractor.py unknown_file --force-type aex

# Enable debug output
python3 ae_pipl_extractor.py plugin.aex --debug
```

## 📊 What Gets Extracted

### Plugin Information
- **Plugin Name** → `FX_NAME`
- **Category** → `FX_CATEGORY`
- **Unique ID** → `FX_UNIQUEID`
- **Entry Points** → Platform-specific function names

### Version Information
- **Major/Minor/Bug versions** → `MAJOR_VERSION`, `MINOR_VERSION`, `BUG_VERSION`
- **Stage** → `STAGE_VERSION` (Develop, Alpha, Beta, Release)
- **Build number** → `BUILD_VERSION`
- **Calculated version** → `RESSOURCEVERSION`

### Flags and Settings
- **Output Flags** → `FX_OUT_FLAGS`
- **Output Flags 2** → `FX_OUT_FLAGS2`
- **AE PiPL Version** → Required by After Effects
- **Effect Spec Version** → SDK compatibility

## 📋 Example Output

### Plugin Information Display
```
Plugin Information:
  Name: PSS License Plugin
  Category: Pixel Sorter Studio
  Unique ID: PSSLICPLUGIN
  Entry Point: EffectMain
  Effect Version: 1.7.3 PF_Stage_DEVELOP (Build 1)
  Total Properties: 13
```

### Config.h Style Analysis
```c
#define FX_NAME "PSS License Plugin"
#define FX_CATEGORY "Pixel Sorter Studio"
#define FX_UNIQUEID "PSSLICPLUGIN"

#define MAJOR_VERSION 1
#define MINOR_VERSION 7
#define BUG_VERSION 3
#define STAGE_VERSION 0  // PF_Stage_DEVELOP
#define BUILD_VERSION 1

#define RESSOURCEVERSION 759809

#define FX_OUT_FLAGS    (   PF_OutFlag_NON_PARAM_VARY + \
                            PF_OutFlag_I_DO_DIALOG + \
                            PF_OutFlag_PIX_INDEPENDENT + \
                            PF_OutFlag_DEEP_COLOR_AWARE + \
                            PF_OutFlag_SEND_UPDATE_PARAMS_UI )
```

### Generated .r File
```c
#include "AEConfig.h"
#include "AE_EffectVers.h"

// ... all flag definitions ...

resource 'PiPL' (16000) {
    {    /* array properties: 13 elements */
        /* [1] */
        Kind {
            AEEffect
        },
        /* [2] */
        Name {
            "PSS License Plugin"
        },
        /* [3] */
        Category {
            "Pixel Sorter Studio"
        },
        // ... more properties ...
    }
};
```

## 🔬 Technical Details

### Windows .aex Analysis
- Parses PE (Portable Executable) format
- Extracts resources from `.rsrc` section
- Handles little-endian byte order
- Supports property type mapping from Windows format

### macOS Bundle Support
- Automatically finds `.rsrc` files in `Contents/Resources/`
- Supports standard macOS plugin bundle structure
- Handles resource fork format with big-endian byte order

### Property Type Mapping
The tool automatically handles different property type encodings:

| Source | Property Type | Normalized |
|--------|---------------|------------|
| .rsrc | `name` | `name` |
| .rcp | `eman` | `name` |
| .aex | `eman` | `name` |

## 🧪 Testing

### Verified Compatibility
- ✅ **PSS License Plugin** (.rsrc, .rcp, .aex, .plugin)
- ✅ **Debug builds** (6.4MB) → 12 properties extracted
- ✅ **Release builds** (3.8MB) → 12 properties extracted
- ✅ **Cross-platform** (macOS ↔ Windows)

### Test Suite
```bash
# Run comprehensive tests
python3 test_parsers.py

# Test specific formats
python3 ae_pipl_extractor.py test_file.aex --info
python3 config_analyzer.py test_file.rsrc
```

## 🚨 Troubleshooting

### Common Issues

**No properties found:**
```bash
# Check file format
python3 ae_pipl_extractor.py file --debug

# Try forcing type
python3 ae_pipl_extractor.py file --force-type aex
```

**Wrong version numbers:**
- AEX files may show different versions due to endianness
- Use Config.h analyzer for accurate version extraction

**Missing .rsrc in plugin bundle:**
- Some plugins may not include resource files
- Check Contents/Resources/ directory manually

## 🔧 Development

### Architecture
- `ae_pipl_extractor.py` - Main CLI application
- `resource_fork_parser.py` - macOS .rsrc parser
- `rcp_parser.py` - Windows .rcp parser
- `aex_resource_extractor.py` - Windows .aex parser
- `r_generator.py` - .r file generator
- `config_analyzer.py` - Config.h style analyzer
- `pipl_types.py` - Property type definitions

### Adding New Formats
1. Create parser class in new file
2. Add file type detection to `detect_file_type()`
3. Add parsing logic to `parse_file()`
4. Update help text and examples

## 📚 References

- [Adobe After Effects SDK](https://developer.adobe.com/after-effects/)
- [PIPL Resource Format](https://github.com/virtualritz/after-effects/tree/master/pipl)
- [PE Format Specification](https://docs.microsoft.com/en-us/windows/win32/debug/pe-format)
- [macOS Resource Manager](https://developer.apple.com/library/archive/documentation/Carbon/Conceptual/Carbon_Event_Manager/index.html)

The tool successfully demonstrates the complete reverse engineering pipeline from compiled plugins back to source configuration format.