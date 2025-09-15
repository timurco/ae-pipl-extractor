# AE Version Extractor Makefile

.PHONY: build test clean help

# Default target
all: build

# Build Rust version
build:
	cargo build --release

# Test Rust version
test: build
	cargo run -- $(FILE)

# Run Rust version
run-rust: build
	cargo run -- $(FILE)

# Run Python version
run-python:
	python3 ae_version_extractor.py $(FILE)

# Clean build artifacts
clean:
	cargo clean

# Show help
help:
	@echo "Available targets:"
	@echo "  build      - Build Rust version"
	@echo "  test       - Test Rust version (set FILE=path/to/file)"
	@echo "  run-rust   - Run Rust version (set FILE=path/to/file)"
	@echo "  run-python - Run Python version (set FILE=path/to/file)"
	@echo "  clean      - Clean build artifacts"
	@echo "  help       - Show this help"
	@echo ""
	@echo "Examples:"
	@echo "  make run-rust FILE=plugin.rsrc"
	@echo "  make run-python FILE=plugin.rsrc"
