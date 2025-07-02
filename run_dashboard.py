#!/usr/bin/env python3
"""
Launcher script for the Tour de France Simulator Dashboard
"""

import subprocess
import sys
import os
import warnings

def main():
    """Launch the Streamlit dashboard"""
    try:
        # Check if streamlit is installed
        import streamlit
        print("🚀 Starting Tour de France Simulator Dashboard...")
        print("📊 Dashboard will open in your default web browser")
        print("🔄 To stop the dashboard, press Ctrl+C in this terminal")
        print("-" * 50)
        
        # Suppress specific Streamlit warnings
        warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
        warnings.filterwarnings("ignore", category=UserWarning)
        
        # Set environment variables to suppress warnings
        env = os.environ.copy()
        env['STREAMLIT_SERVER_HEADLESS'] = 'true'
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        env['PYTHONWARNINGS'] = 'ignore'
        
        # Run the dashboard with comprehensive warning suppression
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false",
            "--logger.level", "error",  # Only show errors, not warnings
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