"""
CanSat GUI Test Launcher
Run this to test the GUI with simulated flight data
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QStyleFactory

# Import the flight simulator
from flight_simulator import Communication, data_base, FlightSimulator

# Import the main GUI (make sure to copy cansat_gui_enhanced.py to same directory)
try:
    from cansat_gui_enhanced import MainWindow
except ImportError:
    print("Error: cansat_gui_enhanced.py not found!")
    print("Please make sure both files are in the same directory.")
    sys.exit(1)

def show_welcome_dialog():
    """Show welcome message with instructions"""
    msg = QMessageBox()
    msg.setWindowTitle("CanSat GUI Test Mode")
    msg.setIcon(QMessageBox.Information)
    msg.setText("Welcome to CanSat GUI Test Mode!")
    msg.setInformativeText(
        "This will simulate a complete CanSat flight:\n\n"
        "• Pre-Launch (0-5s): On launch pad\n"
        "• Ascent (5-120s): Rising to 1000m\n"
        "• Deployment (120-125s): Parachute opens\n"
        "• Descent (125-240s): Falling with parachute\n"
        "• Landing (240s+): On ground\n\n"
        "The simulation runs at 2x speed.\n"
        "Click 'Start Mission' to begin recording data!"
    )
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()

def main():
    print("=" * 60)
    print("CanSat Ground Station - TEST MODE")
    print("=" * 60)
    print()
    print("🚀 Flight Simulator Active")
    print("📊 Simulating realistic telemetry data")
    print("⏱️  Simulation Speed: 2x real-time")
    print()
    print("Instructions:")
    print("1. Click 'Start Mission' to begin data recording")
    print("2. Watch the mission phases change automatically")
    print("3. Monitor alerts for important events")
    print("4. Click 'Export Data' to save telemetry")
    print("5. Use 'Analysis' tab to review flight data")
    print()
    print("=" * 60)
    print()
    
    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Create dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    
    # Show welcome dialog
    show_welcome_dialog()
    
    # Create and show main window
    window = MainWindow()
    window.setWindowTitle("CanSat Ground Station - TEST MODE (Simulated Data)")
    window.show()
    
    # Add test indicator
    print("✅ GUI launched successfully!")
    print("💡 Tip: Watch the Mission Phase indicator at the top")
    print("📈 Graphs will update in real-time")
    print()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
