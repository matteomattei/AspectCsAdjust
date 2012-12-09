from distutils.core import setup
import py2exe
import os

Mydata_files = []
for dirname, dirnames, filenames in os.walk('.\\resources'):
    for subdirname in dirnames:
        print('skip folder: '+os.path.join(dirname, subdirname))
    for filename in filenames:
        f = os.path.join(dirname, filename)
        data = 'resources', [f]
        Mydata_files.append(data)
		
setup(
    windows = [
		{
		"script": 'aspectcsadjust.py',
		"icon_resources": [(0,'resources\icon.ico')],
		}
	],
    options = {
        "py2exe" : {
            "includes" : ['sys', 'os', 'time', 'csv'],
			"optimize": 2,
        }
    },
    data_files = Mydata_files
)