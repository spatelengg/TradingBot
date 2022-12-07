import pandas as pd
from datetime import datetime, timedelta, date, time as TT

class Helper:

    def __init__(self, proxy):
        self._proxy = proxy
        self.csv_data = None
     
    def get_option_chain(self, symbol, expiry: date):
        allowedSegment = [14]    
        if self.csv_data is None:
            csv_data = pd.read_csv('http://public.fyers.in/sym_details/NSE_FO.csv', header =None)
                                    
            csv_data.columns =  ['FyersToken', 'Name', 'Instrument', 'lot', 'tick' 
                                #101122111535348,FINNIFTY 22 Nov 15 20850 CE,14,40,0.05
                                , 'ISIN','TradingSession', 'Lastupdatedate', 'Expirydate', 'Symbol'
                                # ,,0915-1530|0915-1915:2,2022-11-11,1668522600,NSE:FINNIFTY22N1520850CE
                                , 'Exchange', 'Segment','ScripCode','UnderlyingScripCode','ABC'
                                # ,10,11,35348,FINNIFTY,26037
                                ,'STRIKE', 'OPT_TYPE','ScripName']
                                # ,20850.0,CE,101000000026037

            csv_data = csv_data[csv_data['Instrument'].isin(allowedSegment)]                       
            csv_data['Expirydate'] = pd.to_datetime(csv_data['Expirydate'],unit='s').apply(lambda x: x.date())
            self.csv_data = csv_data
             
        
        #data = csv_data[(csv_data['UnderlyingScripCode'] ==symbol)]
        data = self.csv_data[(csv_data['Expirydate'] == expiry) & (csv_data['UnderlyingScripCode'] ==symbol)]
        return data

    def get_option_with_nearest_premium(self, symbols, price):
        data = {
            'ce': {'n':'', 'p':0.0, 'd':99999.0 },
            'pe' : {'n':'', 'p':0.0, 'd':99999.0 }
        }
        
        index = 0
        cnt = 50
        symbs = symbols[index:(index + cnt)]
        while len(symbs) > 0:
            res = self._proxy.quotes(','.join(symbs))
            for x in res['d']:
                if x['v']['volume'] > 0:
                    typ = x['n'][-2:].lower()
                    ltp = x['v']['lp']
                    diff = price - ltp
                    if diff < 0: 
                        diff = diff * -1 
                    if  diff < data[typ]['d']:
                        data[typ] = {'n':x['n'], 'p':ltp, 'd':diff}

            index += len(symbs)
            symbs = symbols[index:(index + cnt)]
        return data
        

    def get_ption_with_moneyness(self, op_chain, underlaying, type:int):
        data = {
            'CE': '',
            'PE' : ''
        }
        symbol = None
        step = None
        if underlaying == "BANKNIFTY":
            symbol = "NSE:NIFTYBANK-INDEX"
            step = 100
        elif underlaying == "NIFTY":
            symbol = "NSE:NIFTY-INDEX"
            step = 50

        res = self._proxy.quotes(symbol)
        ltp = res['d'][0]['v']['lp']
        print(symbol + ': ' + str(ltp))
        mod = ltp % step
        if mod == 0:
            atm = ltp
        elif mod > (step / 2):
            atm = step * (int(ltp / step) + 1)
        else:
            atm = step * (int(ltp / step))

        data['CE']  = atm + (step * type * -1)
        data['PE']  = atm + (step * type)
        
        data['CE'] = op_chain[(op_chain['STRIKE'] == data['CE']) & (op_chain['OPT_TYPE'] == 'CE')].to_dict('records')[0]
        data['PE'] = op_chain[(op_chain['STRIKE'] == data['PE']) & (op_chain['OPT_TYPE'] == 'PE')].to_dict('records')[0]

        return data
  

    def place_order(self, data):
        str = 'BUY' if data['side'] == 1 else 'SELL'
        str += ' ' + data['symbol']
        str += ' ' + '@Market' if data['type'] == 2 else data['limitPrice']
        if data['productType'] == 'CO':
            str += ' SL:' + str(data['stopLoss'])
        elif data['productType'] == 'BO':
            str += ' SL:' + str(data['stopLoss']) + ' Profit:' + str(data['takeProfit']) 

        print(str)
        order_id = 0
        return order_id

    def modify_order(self, data):
        str = 'Modify: ' + str(data['id'])
        str += (' SL:' + str(data['stopLoss'])) if 'stopLoss' in data else ''
        str += (' Limit:' + str(data['limitPrice'])) if 'limitPrice' in data else ''
        str += (' qty:' + str(data['qty'])) if 'qty' in data else ''
        str += (' type:' + str(data['type'])) if 'type' in data else ''
        print(str)
        order_id = data['id'] + 1
        return order_id 

        






