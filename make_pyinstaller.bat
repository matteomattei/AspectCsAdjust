del /Q dist
del /Q build

c:\Python34\Scripts\pyinstaller.exe --onefile --clean --noconsole -i resources\icon.ico aspectcsadjust.py

pause
