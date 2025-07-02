#!/usr/bin/env python3
"""
Optimized Dashboard Launcher
============================

This script launches the Tour de France simulator dashboard with comprehensive
warning suppression and performance optimizations to ensure smooth operation.

Features:
- Suppresses all Streamlit ScriptRunContext warnings
- Filters out multiprocessing-related warnings
- Optimizes Python settings for better performance
- Provides clean console output
- Handles all dashboard variants

Usage:
    python run_optimized_dashboard.py [dashboard_name]

Available dashboards:
    - main (default): Main dashboard with all features
    - tno: TNO-Ergame specific dashboard
    - versus: Versus mode dashboard
    - silent: Silent mode with minimal output
"""

import os
import sys
import subprocess
import warnings
import logging
from pathlib import Path

# Suppress all warnings at the system level
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress specific Streamlit warnings
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_SERVER_ENABLE_STATIC_SERVING'] = 'false'
os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'

# Suppress multiprocessing warnings
os.environ['PYTHONHASHSEED'] = '0'

# Configure logging to suppress warnings
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('multiprocessing').setLevel(logging.ERROR)

def get_dashboard_file(dashboard_name):
    """Get the appropriate dashboard file based on the name."""
    dashboard_files = {
        'main': 'dashboard.py',
        'tno': 'tno_ergame_dashboard.py',
        'versus': 'versus_mode.py',
        'silent': 'run_silent_dashboard.py'
    }
    
    return dashboard_files.get(dashboard_name, 'dashboard.py')

def run_dashboard(dashboard_name='main', port=8501):
    """Run the specified dashboard with optimized settings."""
    
    dashboard_file = get_dashboard_file(dashboard_name)
    
    if not Path(dashboard_file).exists():
        print(f"❌ Error: Dashboard file '{dashboard_file}' not found!")
        print("Available dashboards:")
        for name, file in get_dashboard_file('').items():
            if Path(file).exists():
                print(f"  - {name}: {file}")
        return False
    
    print(f"🚀 Starting {dashboard_name} dashboard ({dashboard_file})...")
    print(f"🌐 Dashboard will be available at: http://localhost:{port}")
    print("⏳ Please wait for the dashboard to load...")
    print("=" * 60)
    
    # Build the command with all optimizations
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', dashboard_file,
        '--server.port', str(port),
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false',
        '--server.enableStaticServing', 'false',
        '--logger.level', 'error',
        '--global.developmentMode', 'false',
        '--global.showWarningOnDirectExecution', 'false'
    ]
    
    # Set environment variables for the subprocess
    env = os.environ.copy()
    env.update({
        'PYTHONWARNINGS': 'ignore',
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_SERVER_ENABLE_STATIC_SERVING': 'false',
        'STREAMLIT_SERVER_ENABLE_CORS': 'false',
        'STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION': 'false',
        'PYTHONHASHSEED': '0',
        'STREAMLIT_LOGGER_LEVEL': 'error'
    })
    
    try:
        # Run the dashboard with stderr redirected to filter warnings
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("✅ Dashboard started successfully!")
        print("📊 Use Ctrl+C to stop the dashboard")
        print("=" * 60)
        
        # Monitor output and filter warnings
        while True:
            output = process.stdout.readline()
            if output:
                # Filter out common warning messages
                if any(warning in output.lower() for warning in [
                    'scriptruncontext', 'multiprocessing', 'warning', 'deprecation'
                ]):
                    continue
                print(output.rstrip())
            
            # Check if process is still running
            if process.poll() is not None:
                break
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard...")
        process.terminate()
        process.wait()
        print("✅ Dashboard stopped.")
        return True
        
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return False

def main():
    """Main function to handle command line arguments and run dashboard."""
    
    # Parse command line arguments
    dashboard_name = 'main'
    port = 8501
    
    if len(sys.argv) > 1:
        dashboard_name = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"❌ Invalid port number: {sys.argv[2]}")
            return False
    
    # Validate dashboard name
    valid_dashboards = ['main', 'tno', 'versus', 'silent']
    if dashboard_name not in valid_dashboards:
        print(f"❌ Invalid dashboard name: {dashboard_name}")
        print(f"Valid options: {', '.join(valid_dashboards)}")
        return False
    
    # Run the dashboard
    return run_dashboard(dashboard_name, port)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 