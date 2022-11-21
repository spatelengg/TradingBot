from Helper import Helper
from datetime import datetime, date, timedelta
from Proxy import Proxy
import time


class Strategy4:
    name = 'Strategy_4'    
    premium = 250
    step = 30  
    cur_date = datetime.now()  
    start_time = datetime(
                        year=cur_date.year
                        ,month=cur_date.month
                        ,day=cur_date.day
                        ,hour=9
                        ,minute=32)
    stop_time = datetime(
                        year=cur_date.year
                        ,month=cur_date.month
                        ,day=cur_date.day
                        ,hour=13
                        ,minute=30)
 
    def __init__(self, _proxy: Proxy, expiry:date, on_message_callback = None):
        self.stop_signal = False
        self._proxy = _proxy
        self._helper = Helper(self._proxy)
        self.expiry = expiry

        # self.fyers = fyers
        # self.fyersWs = fyersWs
        self.on_message_callback = on_message_callback
        self.ce = None
        self.pe = None
        self.selected = None
        self.buy_order = None
        self.sl_order = None
        
        
       

    def order_log(self, msg):
        msg = datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + ': ' + msg + '\n'
        with  open('./' + Strategy4.name + '.log', mode='a') as file:
            file.writelines([msg])
        
        print(msg)

    def order_update_message(msg):
        a = 0

    def deploy(self, underlying, order_qty):
        self.order_qty = order_qty
        print('Deploying ' + Strategy4.name)
        self.op_chain = self._helper.get_option_chain(underlying, self.expiry)

        ws_order = self._proxy.get_web_socket('orderUpdate', True)
        ws_order.websocket_data = self.order_update_message

        while self.ce is None:
            cur_date = datetime.now()
            td = cur_date - self.start_time
            if td.total_seconds() > 0:
                watch_list = self._helper.get_option_with_nearest_premium(self.op_chain['Symbol'].values.tolist(), self.premium)
                print('Watching: ' + str([watch_list['ce'], watch_list['pe'] ]) )
                self.ce = watch_list['ce']
                self.pe = watch_list['pe']

                self.ws_data = self._proxy.get_web_socket('symbolData', False)
                self.ws_data.websocket_data = self.MsgReceived
                self.ws_data.subscribe(symbol=[self.ce['n'], self.pe['n']],data_type='symbolData')
                
            else:
                time.sleep(0.5)
       
    def option_selected_do_order(self, msg):
        if self.buy_order is None:
            m = self.selected
            
            ord_data={
                "symbol":m['n'],
                "qty": self.order_qty  ,
                "type":1, #Limit order
                "side":1,
                "productType":"CO",
                "limitPrice":msg['ltp'] + 1,
                "stopPrice":0,
                "validity":"DAY",
                "disclosedQty":0,
                "offlineOrder":"False",
                "stopLoss":msg['ltp'] - Strategy4.step,
                "takeProfit":0
            }

            self.order_log('BUY {0} {1} @ {2} SL {3}'.format( m['n'],self.order_qty , msg['ltp'], msg['ltp'] - Strategy4.step))
            ord_id = 0
            #ord_id = Helper.place_order(Helper, ord_data)
            
            self.buy_order = {
                'id': ord_id
                ,'type': ord_data['type'] 
                ,'qty' : ord_data['qty'] 
                ,'p' : ord_data['limitPrice']
                ,'lp' : ord_data['limitPrice']
                ,'sl' : ord_data['stopLoss']
            }
             
    
    def trail_stop_loss(self, m):
        buy_o = self.buy_order
        ltp = m['ltp']
        if buy_o is not None:
            if buy_o['sl'] - ltp > 0:
                self.stop_and_exit(m)
                return
            print('Buy:{0} SL:{1} LTP: {2} vs {3}'.format(buy_o['p'], buy_o['sl'], m['ltp'],buy_o['lp'] ))
            if m['ltp'] - buy_o['lp'] >= 10:
                buy_o['lp'] = m['ltp']
                ord_data = {
                    'id': buy_o['id']
                    ,'type' : buy_o['type']
                    ,'qty' : buy_o['qty']
                    ,'stopLoss' : m['ltp'] - Strategy4.step
                }
                
                #new_o_id = Helper.modify_order(Helper, ord_data)
                new_o_id = ord_data['id'] + 1
                new_sl = m['ltp'] - Strategy4.step
                self.order_log('ChangeSL {0} -> {1}'.format(buy_o['sl'], new_sl))
                buy_o['sl'] = new_sl
                buy_o['id'] = new_o_id
                buy_o['lp'] = m['ltp']
            


    def stop_and_exit(self, m):
        self.stop_signal = True
        buy_o = self.buy_order
        self.order_log('SELL {0} @{1}'.format( m['symbol'] , m['ltp']))
        self.ws_data.unsubscribe(symbol=[self.ce['n'], self.pe['n']]) 
        self.ws_data.stop_running()
        self.close_web_socket(self.ws_data)
        self.order_log('End of strategy')
         

    def MsgReceived(self, msg):
        if msg is None:
            return

        if self.on_message_callback is not None:
            try:
                self.on_message_callback(msg)
            except Exception as e:
                print('Something went wrong: {0}'.format(e))
            
        if self.stop_signal == True:
            return
        cur_date = datetime.now()
        td = cur_date - self.stop_time
        if td.total_seconds() > 0:
            self.stop_and_exit()
        

        for m in msg:
            symb = m['symbol']

            if self.selected is not None:
                cur = self.selected
                if symb == cur['n']:
                    self.trail_stop_loss(m)
                return

            cmp = None
            if m['symbol'] == self.ce['n']:
                cmp = self.ce
            elif m['symbol'] == self.pe['n']:
                cmp = self.pe

            p_diff = m['ltp'] - cmp['p'];
            print('Checking price diff: {0} {1} - {2} = {3}'.format(cmp['n'], m['ltp'] , cmp['p'], p_diff) )
            if m['ltp'] - cmp['p'] > Strategy4.step:
                print('Selected: ' + str(cmp) + '| Price=' + str(m['ltp']))
                self.selected = cmp
                self.option_selected_do_order(m)
                return




