
import os
import threading
from Strategy4 import Strategy4
from Helper import Helper
from Proxy import Proxy
from datetime import datetime, date


def write_market_data_to_file(m):
    now = datetime.now()
    file_name = './data/'+ now.strftime('%Y%m%d') 
    if os.path.exists(file_name) == False:
        os.makedirs(file_name)
    file_name += '/' + m['symbol'].replace(':','_') + '.txt'
    msg = '{0}|{1} {2}\n'.format( now.strftime('%H:%M:%S-%f') ,  now.timestamp() , m['ltp'])
    with open(file_name, mode='a') as file:
        file.writelines([msg])
    
    #print(msg)

def message_from_web_socket(msg):
    for m in msg:
        write_market_data_to_file(m)
   
 
def run_strategy_in_thread(s, underlying):
    s.deploy(underlying, 25) 

_proxy = Proxy()
_proxy.do_login()


s4 = Strategy4(_proxy, date(2022, 11, 24), message_from_web_socket)
#s4 = Strategy4(_proxy)
#s4.deploy('BANKNIFTY')
t1 = threading.Thread(target=run_strategy_in_thread, args=(s4,'BANKNIFTY',))
t1.start()

 

command = ''
print ("Type exit to exit...")
while command != 'exit':
    command = input()

t1.join(1.0)



#fyersSocket.keep_running() # {This is used in order to keep your Websocket Thread Open and also do the remaining functionality as expected or other method calls}


 


