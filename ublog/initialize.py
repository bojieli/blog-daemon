
from ublog.params import get_param

import os

def initialize():
    try:
        os.mkdir(get_param('path.tmp'))
    except:
        pass
    try:
        os.mkdir(get_param('path.base'))
    except:
        pass
    
