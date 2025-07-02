#!/usr/bin/env python3
"""
Silent launcher script for Tour de France Simulator Dashboards
This version completely suppresses ScriptRunContext warnings using system-level filtering
"""

import subprocess
import sys
import os
import warnings
import re
import threading
import time

class SilentWarningFilter:
    """Advanced filter to remove ScriptRunContext warnings from all output"""
    
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.warning_patterns = [
            re.compile(r'.*ScriptRunContext.*', re.IGNORECASE),
            re.compile(r'.*missing ScriptRunContext.*', re.IGNORECASE),
            re.compile(r'.*Thread.*MainThread.*missing ScriptRunContext.*', re.IGNORECASE)
        ]
        self.buffer = ""
    
    def write(self, text):
        # Buffer the text to handle multi-line warnings
        self.buffer += text
        
        # Check if we have a complete line
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            self.buffer = lines[-1]  # Keep incomplete line in buffer
            
            for line in lines[:-1]:
                if line.strip():  # Skip empty lines
                    # Check if this line contains any warning patterns
                    is_warning = any(pattern.search(line) for pattern in self.warning_patterns)
                    if not is_warning:
                        self.original_stream.write(line + '\n')
    
    def flush(self):
        # Flush any remaining buffered content
        if self.buffer.strip():
            is_warning = any(pattern.search(self.buffer) for pattern in self.warning_patterns)
            if not is_warning:
                self.original_stream.write(self.buffer)
        self.original_stream.flush()

def suppress_warnings():
    """Suppress warnings at multiple levels"""
    # Python warnings
    warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    
    # Environment variables
    os.environ['PYTHONWARNINGS'] = 'ignore'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    
    # Redirect stderr to filter warnings
    original_stderr = sys.stderr
    warning_filter = SilentWarningFilter(original_stderr)
    sys.stderr = warning_filter
    
    return original_stderr

def main():
    """Launch dashboard with complete warning suppression"""
    
    print("🚴‍♂️ Silent Tour de France Simulator Dashboard")
    print("=" * 50)
    print("This launcher completely suppresses ScriptRunContext warnings")
    print()
    
    # Available dashboards
    dashboards = {
        "1": "dashboard.py",
        "2": "tno_ergame_dashboard.py",
        "3": "streamlit_app.py"
    }
    
    print("Available dashboards:")
    print("1. Main Dashboard (dashboard.py)")
    print("2. TNO Ergame Dashboard (tno_ergame_dashboard.py)")
    print("3. Streamlit Pages App (streamlit_app.py)")
    print()
    
    # Get user selection
    while True:
        choice = input("Select dashboard to launch (1-3): ").strip()
        if choice in dashboards:
            break
        print("Invalid choice. Please select 1-3.")
    
    selected_file = dashboards[choice]
    
    print(f"\n🚀 Starting silent dashboard: {selected_file}")
    print(f"📊 Dashboard will open in your default web browser")
    print(f"🔄 To stop the dashboard, press Ctrl+C in this terminal")
    print("-" * 50)
    
    try:
        # Check if streamlit is installed
        import streamlit
        
        # Suppress warnings
        original_stderr = suppress_warnings()
        
        try:
            # Run the dashboard with comprehensive suppression
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", selected_file,
                "--server.port", "8501",
                "--server.address", "localhost",
                "--browser.gatherUsageStats", "false",
                "--logger.level", "error",
                "--global.developmentMode", "false",
                "--server.enableCORS", "false",
                "--server.enableXsrfProtection", "false"
            ], env=os.environ)
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