#!/usr/bin/env python3
"""QDVC Countdowns - a small GTK 3 application for tracking countdowns.

This file is a thin entry point. All real code lives in the
``qdvc_countdowns_lib`` package.
"""
import sys

from qdvc_countdowns_lib.app import main

if __name__ == "__main__":
    sys.exit(main())
