import sys
def weHaveTheHulk():
    pPath = 'x:\production\_misc_data\scripts'
    sysPath = sys.path
    if pPath not in sysPath:
		sys.path.append(pPath)  
	

weHaveTheHulk()

import abcHulk
reload(abcHulk)


