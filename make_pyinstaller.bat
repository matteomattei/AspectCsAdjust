del /Q dist
del /Q build

c:\Python27\Scripts\pyinstaller.exe --onefile --clean --noconsole -i resources\icon.ico aspectcsadjust.py

pause
