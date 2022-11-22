
import os
import Ws_Fix
import sys
 
from Strategy4 import Strategy4
from Helper import Helper
from Proxy import Proxy
from datetime import datetime, date

from service import MyService

if __name__ == '__main__':
    service = MyService()
    service.start()

sys.exit(0)
 


