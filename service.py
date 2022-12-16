import logging
import os

import threading
import time
from datetime import  datetime, date
from Strategy4 import Strategy4
from Strategy9 import Strategy9
from Proxy import Proxy
from Const import Const

class MyService:
    FIFO = '/tmp/myservice_pipe'
    running_strategies = []
    
    def __init__(self, delay=5):
        self._s4 = None
        self.logger = self._init_logger()
        self.delay = delay
        # if not os.path.exists(MyService.FIFO):
        #     os.mkfifo(MyService.FIFO)
        # self.fifo = os.open(MyService.FIFO, os.O_RDWR | os.O_NONBLOCK)
        self.logger.info('MyService instance created')

    def _init_logger(self):
        logger = logging.getLogger(__name__)
        #logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.INFO)
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(logging.Formatter('%(levelname)8s | %(message)s'))
        logger.addHandler(stdout_handler)
        return logger

    def write_market_data_to_file(self, m):
        now = datetime.now()
        file_name = './data/'+ now.strftime('%Y%m%d') 
        if os.path.exists(file_name) == False:
            os.makedirs(file_name)
        file_name += '/' + m['symbol'].replace(':','_') + '.txt'
        msg = '{0}|{1} {2}\n'.format( now.strftime('%H:%M:%S-%f') ,  now.timestamp() , m['ltp'])
        with open(file_name, mode='a') as file:
            file.writelines([msg])
        
        #print(msg)

    def message_from_web_socket(self, msg):
        for m in msg:
            self.write_market_data_to_file(m)
            for s in self.running_strategies:
                try:
                    s.MsgReceived(m)    
                except Exception  as  e:
                    print (e)
                   
    def order_update_message (self, msg):
        for s in self.running_strategies:
            try:
                s.MsgReceivedOrder(msg)
            except Exception  as  e:
                print (e)
    
    def run_strategy_in_thread(self, s):
        s.deploy() 
        self.running_strategies.append(s)
 

    def start(self):
        _proxy = Proxy()
        _proxy.do_login()
        _proxy.set_callback(self.message_from_web_socket)

        # _ws4 = _proxy.get_web_socket('symbolData', True)
        # _ws9 = _proxy.get_web_socket('symbolData', True)
        # _ws4.websocket_data = self.message_from_web_socket
        # _ws9.websocket_data = self.message_from_web_socket

        ws_order = _proxy.get_web_socket('orderUpdate', True)
        ws_order.websocket_data = self.order_update_message

        exp = Const.get_banknifry_expiry(Const, date.today())

        self._s4 = Strategy4(_proxy, 'BANKNIFTY', 25, exp)
        self._s9 = Strategy9(_proxy, 'BANKNIFTY', 25, exp)
        #self._s4.deploy('BANKNIFTY', 25)
        t4 = threading.Thread(target=self.run_strategy_in_thread, args=(self._s4,))
        t4.daemon = True

        t9 = threading.Thread(target=self.run_strategy_in_thread, args=(self._s9,))
        t9.daemon = True

        #t4.start()
        t9.start()

        try:
            while True:
                time.sleep(self.delay)
                self.logger.debug('Tick')
        except KeyboardInterrupt:
            try:                
                t4.join(1.0)
            except:
                pass

            try:
                t9.join(1.0)
            except:
                pass
            
            self.logger.warning('Keyboard interrupt (SIGINT) received...')
            self.stop()

    def stop(self):
        self.logger.info('Cleaning up...')
        if os.path.exists(MyService.FIFO):
            os.close(self.fifo)
            os.remove(MyService.FIFO)
            self.logger.info('Named pipe removed')
        else:
            self.logger.error('Named pipe not found, nothing to clean up')
        


