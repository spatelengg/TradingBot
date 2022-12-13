from Helper import Helper
from datetime import datetime, date, timedelta
from Proxy import Proxy
from os.path import exists
import time
import asyncio
import csv


class Strategy9:
    name = 'Strategy_9'    
     
    cur_date = datetime.now()  
    start_time = datetime(
                        year=cur_date.year
                        ,month=cur_date.month
                        ,day=cur_date.day
                        ,hour=9
                        ,minute=17)
    stop_time = datetime(
                        year=cur_date.year
                        ,month=cur_date.month
                        ,day=cur_date.day
                        ,hour=15
                        ,minute=15)
    underlying_price = -1.0
     
 
    def __init__(self, _proxy: Proxy, underlying: str, order_qty: int, expiry:date):
        self.stop_signal = False
        self._proxy = _proxy
        self._helper = Helper(self._proxy)
        self.expiry = expiry
        
        self.stop_event = asyncio.Event()
        self.order_qty = order_qty
        self.underlying = underlying
         
        # self.fyers = fyers
        # self.fyersWs = fyersWs
        self.started = False


        self.ce = None
        self.pe = None
        self.selected = None
        self.buy_order = None
        self.sl_order = None
         
    def order_log(self, msg):
        fileName = './' + self.name + '.csv'
        edit = exists(fileName)
        with open(fileName, mode='a',encoding='UTF8', newline='') as file:
            writer = csv.writer(file)
            if edit == False:
                #Date, Time, Price, Qty, Opt_Type (CE/PE),  Strike Price, Position (Buy/Sell), Remark
                header = ['Date', 'Time', 'price', 'qty', 'opt_type' ,  'strike', 'pos' , 'remark']
                writer.writerow(header)
            now = datetime.now()
            data = [now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), msg['price'], msg['qty'], msg['opt_type'], msg['strike'], msg['pos'], msg['remark'] ]
            writer.writerow(data)

            print(data)
 
    
    def deploy(self):
        print('Deploying ' + self.name)
        self.op_chain = self._helper.get_option_chain(self.underlying, self.expiry)
        
        
        while self.ce is None:
            cur_date = datetime.now()
            td = cur_date - self.start_time
            if td.total_seconds() > 0:
                watch_list = self._helper.get_ption_with_moneyness(self.op_chain, self.underlying, -1)
 
                self.place_first_order (watch_list)
               
            else:
                print('Strategy execution will start at: ' +  str(self.start_time) ) 
                time.sleep((self.start_time - datetime.now()).total_seconds())
   

    def stop_and_exit(self, m):
        self.stop_signal = True
        symbols = []
        if self.ce is not None:
            symbols.append(self.ce['Symbol'])
        if self.pe is not None:
            symbols.append(self.pe['Symbol'])

        res = self._proxy.quotes(','.join(symbols))
        for r in res:
            w = None
            if self.ce['Symbol'] == r['n']:
                w = self.ce
            if self.pe['Symbol'] == r['n']:
                w = self.pe
            self.place_order(r['v']['ask'], w, 'BUY', 'Timeout')
        
        self._proxy.unsubscribe(symbols) 
        self.order_log('End of ' + self.name)
         

    def place_first_order(self, watches):
        ce = watches['CE']
        pe = watches['PE']
        res = self._proxy.quotes(ce['Symbol'] + ',' + pe['Symbol'])
        for r in res:
            o = None
            if ce['Symbol'] == r['n']:
                o = ce
            else: 
                o = pe
            
            price = r['v']['bid']
            o['ord'] = {
                'price': price,
                'ltp': price,
                'sl': price  + ( price * 0.3)
                ,'retry': 0
            }
            self.place_order(price, o, 'SELL', 'First orders: SL' + str(o['ord']['sl']))
             
        
        self.ce = ce
        self.pe = pe
       
        self._proxy.subscribe([ce['Symbol'], pe['Symbol']])


    def place_order(self, price, w, pos, remark):
        self.order_log({
                          'price': price
                        , 'qty': self.order_qty
                        , 'opt_type': w['OPT_TYPE'] 
                        , 'strike' : w['STRIKE']
                        , 'pos': pos
                        , 'remark' : remark
                    })

    def place_sl_order(self, ord, m):
        ltp = m['ltp']
        ord['ord']['ltp'] = ltp
        retry = ord['ord']['retry']
        if retry < 3 and ord['ord']['sl'] <= ltp:  #SL Hit
            print('SL hit')
            watch_list = self._helper.get_ption_with_moneyness(self.op_chain, self.underlying, -1)
            w = watch_list[ord['OPT_TYPE']]
            if w['Symbol'] != ord['Symbol']: # new strike found to enter upon SL hit
                self.place_order(m['ltp'], ord, 'BUY', 'SL Hit')
                 
                r = self._proxy.quotes(w['Symbol'])
                r = r[0]
                price = r['v']['bid']
                w['ord'] = {
                    'price': price,
                    'ltp': price,
                    'sl': price  + ( price * 0.3)
                    ,'retry' : retry + 1
                }
                self.place_order(price, w, 'SELL', 'After SL orders: SL' + str(w['ord']['sl']))
                
                self._proxy.unsubscribe([ord['Symbol']]) 
                self._proxy.subscribe([w['Symbol']])

                if w['OPT_TYPE'] == 'CE':
                    self.ce = w
                else:
                    self.pe = w

        self.print_profit_loss()
        

    def print_profit_loss(self):
        ce_price = self.ce['ord']['price']
        ce_ltp = self.ce['ord']['ltp']
        pe_price = self.pe['ord']['price']
        pe_ltp = self.pe['ord']['ltp']

        pl = self.order_qty * ((ce_price - ce_ltp) + (pe_price - pe_ltp))
        print('Current P/L: ' + str(pl))


    def MsgReceivedOrder(self, msg):
        pass

    def MsgReceived(self, m):
        if m is None:
            return
        if self.stop_signal == True:
            return
        
        cur_date = datetime.now()
        td = cur_date - self.stop_time
        if td.total_seconds() > 0:
            self.stop_and_exit()

        if m['symbol'] == self.ce['Symbol']:
            self.place_sl_order(self.ce, m)    
        elif m['symbol'] == self.pe['Symbol']:
            self.place_sl_order(self.pe, m)    
        

 


