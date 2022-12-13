import os
import Ws_Fix
from fyers_api import fyersModel
from fyers_api import accessToken
from fyers_api.Websocket import ws
import time
 

class Proxy: 
    access_token_file =  "accessToken.txt"
    data_subscription_list = {}


    def __init__(self):
        self.fyers = None
        self.logPath = './log'
        self.client_id = 'SWQ4761I81-100'
        self.access_token = None

    def set_callback(self, callback):        
        self.fyersWs.websocket_data = callback

    def do_login(self, force = False):    
        if self.fyers is None:
            access_token = self.access_token
            if force != True:
                access_token = None
                if os.path.exists(self.access_token_file) == True:
                    with open(self.access_token_file, mode='r') as file:
                        access_token = file.read()

            if access_token is None:
                secret_key = 'WZQWYTVQXM'
                redirect_uri = 'http://localhost:5050' 
                
                print('Login to: ')
                print('https://api.fyers.in/api/v2/generate-authcode?client_id=' 
                    + self.client_id + '&redirect_uri=' + redirect_uri 
                    + '&response_type=code&state=sample_state&scope=openid&nonce=sample_nonce')

                print('Then past auth code and hit enter')
                auth_code = input()
                session=accessToken.SessionModel(client_id=self.client_id,
                    secret_key=secret_key,redirect_uri=redirect_uri, 
                    response_type='code', grant_type='authorization_code',
                    state='sample_state',scope='openid',nonce='sample_nonce')
                session.set_token(auth_code)
                response = session.generate_token()
                print(response)
                

                access_token = response["access_token"]
                print('Access Token: ' + access_token)
                with open(self.access_token_file, mode='w') as file:
                    file.write(access_token)

            self.access_token = access_token
             
            #print(access_token)
            self.fyers = fyersModel.FyersModel(client_id=self.client_id, token=access_token,log_path=self.logPath)
            res = self.fyers.get_profile()
            print(res)
            self.fyersWs = self.get_web_socket('symbolData', True)

            if res['s'] == 'error':
                self.access_token = None
                self.fyers = None
                self.do_login(True)
              
            
    def get_web_socket(self, data_type: str, is_async: bool):
        access_token_websocket = self.client_id + ':' + self.access_token
        return ws.FyersSocket(access_token=access_token_websocket
                                            , run_background=is_async
                                            , log_path=self.logPath)

    def close_web_socket(self, ws):
        pass

    def subscribe_order_update(self):
        self.fyersWs.subscribe(data_type='orderUpdate')

    def subscribe(self, symbols):
        dl = self.data_subscription_list
        for s in symbols:
            if s not in dl:
                dl[s] = 0
            dl[s] = dl[s] + 1
            
        self.fyersWs.subscribe(symbol=list(dl.keys()),data_type='symbolData')

    def unsubscribe(self, symbols):
        dl = self.data_subscription_list
        for s in symbols:
            if dl[s] is not None:
                dl[s] = dl[s] - 1
            
            if dl[s] <= 0:
                del dl[s]

        self.fyersWs.subscribe(symbol=list(dl.keys()),data_type='symbolData')

    def quotes(self, symbols):
        res = self.fyers.quotes({'symbols': symbols})
        if res['s'] == 'ok':
            return res['d']
        else:
            time.sleep(1)
            return self.quotes(symbols)


    
 


