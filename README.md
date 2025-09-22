# AE PiPL Extractor

A minimal Python tool to extract and print PiPL properties from existing Adobe After Effects plug-ins/resources. The PiPL concept and required properties are described in Adobe’s After Effects SDK docs; see PiPL Resources. This tool was built with the [after-effects PiPL library](https://github.com/virtualritz/after-effects/tree/master/pipl/src) in mind as a reference, but it does not require or depend on it.

- Adobe SDK docs on PiPL: [PiPL Resources](https://ae-plugins.docsforadobe.dev/intro/pipl-resources/)
- Reference library: [`virtualritz/after-effects` PiPL](https://github.com/virtualritz/after-effects/tree/master/pipl/src)

## Features

- Extracts PiPL properties from ready-built AE plug-ins and resources
- Supports macOS `.plugin` bundles (finds internal `.rsrc`)
- Supports Windows `.aex` (extracts resource section and parses PiPL-like data)
- Supports raw `.rcp` and raw `.rsrc` files
- Decodes versions, flags, entry points, match name, etc.
- Outputs a concise, human-readable list of properties

## Supported inputs

1. macOS plug-in bundle: directory ending with `.plugin` (searches for `.rsrc` inside)
2. Windows `.aex` file: parses compiled resource for PiPL data
3. Raw `.rcp` text resource
4. Raw `.rsrc` binary resource

## Requirements

- Python 3.8+ (standard library only)

## Usage

Run one of the following commands:

```bash
# 1) macOS plugin bundle: search for internal .rsrc
python3 ae_pipl_extractor.py "/path/to/Example.plugin"

# 2) Windows .aex: extract RCP-like data from resource section
python3 ae_pipl_extractor.py "/path/to/Plugin.aex"

# 3) Raw .rcp file
python3 ae_pipl_extractor.py "/path/to/Plugin.rcp"

# 4) Raw .rsrc file
python3 ae_pipl_extractor.py "/path/to/Example.plugin/Contents/Resources/Plugin.rsrc"
```

The output lists decoded PiPL properties, for example:

```text
Detected file type: aex
Parsing /path/to/Plugin.aex...
Analyzing 1574 bytes of PIPL data...
Found 12 PIPL properties:
[1] Kind [kind]: AEEffect
[2] Name [name]: Example Plugin
[3] Category [catg]: Example Category
[4] Entry Point (Windows 64) [8664]: EffectMain
[5] AE_PiPL_Version [ePVR]: 2, 0
[6] AE_Effect_Spec_Version [eSVR]: 13, 28
[7] AE_Effect_Version [eVER]: 0xb9801 // 1.7.3 PF_Stage_DEVELOP (Build 1)
... (etc)
```

## Notes on PiPL format

- Per Adobe docs, PiPL properties are defined in macOS byte order even on Windows; Windows builds use tools to compile `.r` into `.rc`. This extractor normalizes and decodes accordingly.
- See Adobe docs for property definitions and expectations: [PiPL Resources](https://ae-plugins.docsforadobe.dev/intro/pipl-resources/)

## License

This project is open source and available under the MIT License.
