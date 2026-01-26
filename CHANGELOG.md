# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Always-on ESC sequence buffering for robust arrow key input** (Issue #174)
  - Implemented automatic buffering of escape sequences to handle split byte arrivals in environments like VSCode→WSL2, SSH with delays, etc.
  - New module `paraping/escape_buffering.py` with hardcoded timing parameters:
    - Inter-byte gap timeout: 30ms (T_GAP)
    - Maximum accumulation timeout: 500ms (T_TOTAL)
  - Added JSONL diagnostic logging for escape sequence aggregation with per-byte timing information
  - Comprehensive unit tests for buffering logic covering various delay scenarios
  - Backward-compatible integration with existing arrow key handling

### Changed
- Modified `paraping/input_keys.py` to use the new escape sequence buffering mechanism
- Updated existing unit tests to work with the new buffering implementation

### Technical Details
- Early exit optimization when complete sequences are detected
- Fallback to legacy behavior for unmatched/incomplete escape sequences
- Support for CSI (Control Sequence Introducer), SS3 (Single Shift 3), and function key sequences
- Zero configuration required - buffering is always enabled with hardcoded timing

## [1.0.0] - Previous Release

Initial release with basic functionality.
