# AE Version Extractor

A tool to extract version information from After Effects plugin `.rsrc` files. Available in both Rust and Python implementations.

## Features

- Extracts version information from AE plugin resource files
- Supports both Mac resource fork format and 8BIM (Photoshop plugin) format
- Decodes PF_VERS encoded version data
- Cross-platform support

## Installation

### Rust Version

```bash
cargo build --release
```

### Python Version

No additional dependencies required - uses only Python standard library.

## Usage

### Rust Version

```bash
cargo run -- <path_to_rsrc_file>
```

### Python Version

```bash
python3 ae_version_extractor.py <path_to_rsrc_file>
```

## Example

```bash
$ python3 ae_version_extractor.py AIColorMatch.rsrc
Raw encoded version: 0x00106001
Decoded version information:
  Version: 2
  Subversion: 0
  Bug version: 12
  Stage: DEVELOP
  Build: 1
  Full version: 2.0.12 Develop (Build 1)
```

## Version Format

The tool extracts version information in the following format:
- **Version**: Major version number
- **Subversion**: Minor version number  
- **Bug version**: Bug fix version number
- **Stage**: Development stage (Develop, Alpha, Beta, Release)
- **Build**: Build number

## Supported File Formats

1. **Mac Resource Fork**: Traditional Mac resource files with PiPL resources
2. **8BIM Format**: Photoshop plugin format with 8BIM chunks (eVER chunk)

## License

This project is open source and available under the MIT License.
