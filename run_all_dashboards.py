#!/usr/bin/env python3
"""
Comprehensive launcher for all Tour de France Simulator Dashboards
This script can launch any of the different Streamlit applications with warning suppression
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
    """Main launcher function"""
    
    # Available dashboards
    dashboards = {
        "1": {
            "name": "Main Dashboard (Multi-page)",
            "file": "dashboard.py",
            "description": "Comprehensive dashboard with all features (single simulation, multi-simulation, team optimization, rider management, stage types, versus mode)"
        },
        "2": {
            "name": "TNO Ergame Dashboard",
            "file": "tno_ergame_dashboard.py", 
            "description": "Specialized dashboard for TNO Ergame fantasy cycling rules with different scoring system"
        },
        "3": {
            "name": "Streamlit Pages App",
            "file": "streamlit_app.py",
            "description": "Multi-page Streamlit app structure (for Streamlit Cloud deployment)"
        },
        "4": {
            "name": "Quiet Main Dashboard",
            "file": "dashboard.py",
            "description": "Main dashboard with aggressive warning suppression using stderr filtering"
        }
    }
    
    print("🚴‍♂️ Tour de France Simulator Dashboard Launcher")
    print("=" * 50)
    print("Available dashboards:")
    print()
    
    for key, dashboard in dashboards.items():
        print(f"{key}. {dashboard['name']}")
        print(f"   {dashboard['description']}")
        print()
    
    # Get user selection
    while True:
        choice = input("Select dashboard to launch (1-4): ").strip()
        if choice in dashboards:
            break
        print("Invalid choice. Please select 1-4.")
    
    selected_dashboard = dashboards[choice]
    
    print(f"\n🚀 Starting {selected_dashboard['name']}...")
    print(f"📊 Dashboard will open in your default web browser")
    print(f"🔄 To stop the dashboard, press Ctrl+C in this terminal")
    print("-" * 50)
    
    try:
        # Check if streamlit is installed
        import streamlit
        
        # Suppress warnings at Python level
        warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
        warnings.filterwarnings("ignore", category=UserWarning)
        
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONWARNINGS'] = 'ignore'
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        
        # Special handling for quiet mode (option 4)
        if choice == "4":
            # Redirect stderr to filter warnings
            original_stderr = sys.stderr
            warning_filter = WarningFilter(original_stderr)
            sys.stderr = warning_filter
            
            try:
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", selected_dashboard['file'],
                    "--server.port", "8501",
                    "--server.address", "localhost",
                    "--browser.gatherUsageStats", "false",
                    "--logger.level", "error",
                    "--global.developmentMode", "false"
                ], env=env)
            finally:
                # Restore original stderr
                sys.stderr = original_stderr
        else:
            # Standard launch with warning suppression
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", selected_dashboard['file'],
                "--server.port", "8501",
                "--server.address", "localhost",
                "--browser.gatherUsageStats", "false",
                "--logger.level", "error",
                "--global.developmentMode", "false"
            ], env=env)
        
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