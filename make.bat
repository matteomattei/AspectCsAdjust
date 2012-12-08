del /Q Output
del /Q dist
del /Q build

python setup.py py2exe
"C:\Program Files (x86)\Inno Setup 5\iscc.exe" setup.iss 
system pause