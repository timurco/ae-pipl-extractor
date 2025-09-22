# AE PIPL Extractor

A Python application for extracting and decompiling Adobe After Effects Plugin Information Property List (PIPL) resources from binary files back to readable .r format.

## Features

- ✅ Parse macOS .rsrc resource fork files
- ✅ Parse Windows .rcp resource files
- ✅ Extract all PIPL properties and settings
- ✅ Generate readable .r source files with correct syntax
- ✅ Support for all standard After Effects PIPL properties
- ✅ Automatic file type detection
- ✅ CLI interface with debugging options

## Usage

```bash
# Extract from macOS .rsrc file
python3 ae_pipl_extractor.py plugin.rsrc -o plugin.r

# Extract from Windows .rcp file
python3 ae_pipl_extractor.py plugin.rcp -o plugin.r

# Show plugin information only
python3 ae_pipl_extractor.py plugin.rsrc --info

# Debug mode
python3 ae_pipl_extractor.py plugin.rsrc --debug
```

## Supported File Formats

- **`.rsrc`** - macOS resource fork binary format (big-endian)
- **`.rcp`** - Windows resource compiler text format

## Supported PIPL Properties

| Property | Description |
|----------|-------------|
| `kind` | Plugin type (AEEffect) |
| `name` | Plugin display name |
| `catg` | Effect category for menu |
| `8664` | Windows 64-bit entry point |
| `mi64` | macOS Intel 64-bit entry point |
| `ma64` | macOS ARM 64-bit entry point |
| `ePVR` | AE PiPL Version |
| `eSVR` | AE Effect Spec Version |
| `eVER` | Effect Version |
| `eINF` | Effect Info Flags |
| `eGLO` | Global Output Flags |
| `eGL2` | Global Output Flags 2 |
| `eMNA` | Effect Match Name |
| `aeFL` | Reserved Info |

## Example Output

The tool generates properly formatted .r files with:

- All necessary includes and defines
- Complete flag definitions
- Readable property structure
- Platform-specific code blocks
- Proper constant mapping

```c
#include "AEConfig.h"
#include "AE_EffectVers.h"

// ... flag definitions ...

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

## Testing

Run the test suite:

```bash
python3 test_parsers.py
```

## Requirements

- Python 3.7+
- No external dependencies (uses only built-in modules)

## Architecture

- `pipl_types.py` - PIPL property types and constants
- `resource_fork_parser.py` - macOS .rsrc binary parser
- `rcp_parser.py` - Windows .rcp text parser
- `r_generator.py` - .r file generator
- `ae_pipl_extractor.py` - Main CLI application

## Successfully Tested With

- ✅ PSS License Plugin (.rsrc and .rcp formats)
- ✅ Extracted 13 properties from .rsrc
- ✅ Extracted 10 properties from .rcp
- ✅ Generated valid .r files for both formats