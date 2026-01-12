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

"""Unit tests for ping_wrapper."""

import io
import unittest
from unittest.mock import patch

import ping_wrapper


class TestPingWrapper(unittest.TestCase):
    """Tests for ping_wrapper behaviors."""

    def test_ping_with_helper_rejects_non_positive_timeout(self):
        """Ensure ping_with_helper rejects non-positive timeouts."""
        with self.assertRaises(ValueError):
            ping_wrapper.ping_with_helper("example.com", timeout_ms=0)

    def test_main_rejects_non_positive_timeout(self):
        """Ensure CLI rejects non-positive timeout."""
        stderr = io.StringIO()
        with patch("sys.argv", ["ping_wrapper.py", "example.com", "0"]):
            with patch("sys.stderr", stderr):
                with self.assertRaises(SystemExit) as exc:
                    ping_wrapper.main()
        self.assertEqual(exc.exception.code, 1)
        self.assertIn("timeout_ms must be a positive integer", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
