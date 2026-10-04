#!/usr/bin/env python3
"""Compatibility alias for the complete project FK/source validation."""
import sys

from validate_project import main

sys.argv = ["validate_project.py", *sys.argv[1:], "--no-report"]
main()
