from cx_Freeze import setup, Executable

# Define the build options
build_exe_options = {
    "packages": [
        "tkinter", "PIL", "cv2", "face_recognition", "pyttsx3",
        "openpyxl", "pathlib", "re", "queue", "multiprocessing"
    ],
    "excludes": [
        "unittest", "email", "http", "test", "doctest" 
    ],
    "include_files": [],
}

# Use "Win32GUI" if it's a GUI application, or "Console" if it's a console application
base = "Win32GUI"  # Change to "Console" if it is a console application or None if unsure

setup(
    name="Facial",
    version="0.1",
    description="only face",
    options={"build_exe": build_exe_options},
    executables=[Executable("C:\\USERS\\OM ADITYA\\DESKTOP\\OLDOLDOLD\\main.py", base=base)],
)
