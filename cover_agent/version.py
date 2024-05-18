import os
import sys


def get_version():
    """
    Get the version of the application.

    Returns:
        str: The version of the application.

    """
    # Check if the application is "frozen" (bundled by PyInstaller)
    if getattr(sys, "frozen", False):
        # If it's bundled, the base path is the folder containing the executable
        base_path = sys._MEIPASS
    else:
        # If it's not bundled, use the directory of this file
        base_path = os.path.dirname(__file__)

    # Construct the path to version.txt
    version_file_path = os.path.join(base_path, "version.txt")

    # Open and read the version file
    with open(version_file_path, "r") as file:
        version = file.read().strip()

    return version


__version__ = get_version()
