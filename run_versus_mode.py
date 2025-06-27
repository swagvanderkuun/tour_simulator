#!/usr/bin/env python3
"""
Tour de France Versus Mode Runner

This script runs the Versus Mode functionality, allowing users to:
1. Select a team of 20 riders with a budget of 48 points
2. Run multiple simulations with stage-by-stage optimization
3. Compare their team against the optimal team from team optimization
4. Get detailed stage-by-stage analysis

Usage:
    python run_versus_mode.py
"""

from versus_mode import main

if __name__ == "__main__":
    main() 