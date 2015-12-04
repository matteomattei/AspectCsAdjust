del /Q Output
del /Q dist
del /Q build

C:\python27\python.exe setup.py py2exe
"C:\Program Files (x86)\Inno Setup 5\iscc.exe" setup.iss
pause
