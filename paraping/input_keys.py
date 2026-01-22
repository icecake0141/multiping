#!/usr/bin/env python3
# Copyright 2025 icecake0141
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# This file was created or modified with the assistance of an AI (Large Language Model).
# Review required for correctness, security, and licensing.

"""
Keyboard input handling for ParaPing.

This module provides functions for reading keyboard input and parsing
escape sequences, particularly for arrow key navigation.
"""

import select
import sys
import time

# Constants for robust escape sequence buffering
# Inter-byte wait: time to wait for next byte after receiving a byte
# Hard cap: maximum total time to wait for complete escape sequence
# These values handle fragmented sequences from SSH, WSL2, and similar environments
INTER_BYTE_TIMEOUT = 0.05  # 50ms between bytes
ESCAPE_SEQUENCE_HARD_CAP = 0.5  # 500ms maximum total wait


def parse_escape_sequence(seq):
    """
    Parse ANSI escape sequence to identify arrow keys.

    Args:
        seq: The escape sequence string (without the leading ESC)

    Returns:
        String identifier for arrow keys ('arrow_up', 'arrow_down', etc.)
        or None if sequence is not recognized
    """
    arrow_map = {
        "A": "arrow_up",
        "B": "arrow_down",
        "C": "arrow_right",
        "D": "arrow_left",
    }
    if not seq:
        return None
    if seq in ("[A", "OA"):
        return "arrow_up"
    if seq in ("[B", "OB"):
        return "arrow_down"
    if seq in ("[C", "OC"):
        return "arrow_right"
    if seq in ("[D", "OD"):
        return "arrow_left"
    if seq[0] in ("[", "O") and seq[-1] in arrow_map:
        return arrow_map[seq[-1]]
    return None


def read_key():
    """
    Read a key from stdin, handling multi-byte sequences like arrow keys.

    Implements robust buffering for escape sequences that may arrive fragmented,
    especially in SSH, WSL2, and similar environments. Uses inter-byte timing
    to detect complete sequences while maintaining low latency.

    Returns special strings for arrow keys: 'arrow_left', 'arrow_right',
    'arrow_up', 'arrow_down'. Returns the character for normal keys,
    or None if no input is available.
    """
    if not sys.stdin.isatty():
        return None
    ready, _, _ = select.select([sys.stdin], [], [], 0)
    if not ready:
        return None
    char = sys.stdin.read(1)
    # Check for escape sequence (arrow keys start with ESC)
    if char == "\x1b":
        seq = ""
        start_time = time.monotonic()
        hard_deadline = start_time + ESCAPE_SEQUENCE_HARD_CAP

        # Keep reading bytes while they arrive within inter-byte timeout
        # or until hard cap is reached
        while True:
            now = time.monotonic()
            if now >= hard_deadline:
                # Hard cap reached, stop waiting
                break

            # Calculate timeout: inter-byte wait, but don't exceed hard cap
            timeout = min(INTER_BYTE_TIMEOUT, hard_deadline - now)
            if timeout <= 0:
                break

            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if not ready:
                # No more bytes within inter-byte timeout, sequence complete
                break

            # Read next byte
            next_byte = sys.stdin.read(1)
            seq += next_byte

            # Common optimization: if we see a terminal character for arrow keys,
            # we can return early without waiting for more bytes
            if seq and seq[-1] in ("A", "B", "C", "D"):
                # Check if this looks like a complete arrow key sequence
                if len(seq) >= 2 and seq[0] in ("[", "O"):
                    break

        parsed = parse_escape_sequence(seq)
        return parsed if parsed is not None else char
    return char
