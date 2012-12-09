del /Q Output
del /Q dist
del /Q build
del /Q MSVCP90.DLL

copy C:\Windows\System32\MSVCP90.DLL .
python setup.py py2exe
"C:\Program Files (x86)\Inno Setup 5\iscc.exe" setup.iss
pause