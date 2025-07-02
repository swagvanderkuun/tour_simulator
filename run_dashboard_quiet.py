#!/usr/bin/env python3
"""
Quiet launcher script for the Tour de France Simulator Dashboard
This version filters out ScriptRunContext warnings by redirecting stderr
"""

import subprocess
import sys
import os
import warnings
import re

class WarningFilter:
    """Filter to remove ScriptRunContext warnings from stderr"""
    
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.warning_pattern = re.compile(r'.*ScriptRunContext.*', re.IGNORECASE)
    
    def write(self, text):
        if not self.warning_pattern.search(text):
            self.original_stderr.write(text)
    
    def flush(self):
        self.original_stderr.flush()

def main():
    """Launch the Streamlit dashboard with warning filtering"""
    try:
        # Check if streamlit is installed
        import streamlit
        print("🚀 Starting Tour de France Simulator Dashboard...")
        print("📊 Dashboard will open in your default web browser")
        print("🔄 To stop the dashboard, press Ctrl+C in this terminal")
        print("-" * 50)
        
        # Suppress warnings at Python level
        warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
        warnings.filterwarnings("ignore", category=UserWarning)
        
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONWARNINGS'] = 'ignore'
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        
        # Redirect stderr to filter warnings
        original_stderr = sys.stderr
        warning_filter = WarningFilter(original_stderr)
        sys.stderr = warning_filter
        
        try:
            # Run the dashboard
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", "dashboard.py",
                "--server.port", "8501",
                "--server.address", "localhost",
                "--browser.gatherUsageStats", "false",
                "--logger.level", "error",
                "--global.developmentMode", "false"
            ], env=env)
        finally:
            # Restore original stderr
            sys.stderr = original_stderr
        
    except ImportError:
        print("❌ Streamlit is not installed!")
        print("📦 Please install the required dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 