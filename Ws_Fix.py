import json
from fyers_api.Websocket import ws
  

def new_on_message(self, ws, msg):
    self_data_type = self._FyersSocket__data_type

    if self_data_type == "symbolData":
        self.response = self.parse_symbol_data(msg)
        if type(msg)== str:
            if "error" in msg:
                msg = json.loads(msg)
                self.response_out["s"]=msg["s"]
                self.response_out["code"]=msg["code"]
                self.response_out["message"]=msg["message"]
                self.response = self.response_out
                self.logger.error("Response:{self.response}")
            
            #self.logger.debug(f"Response:{self.response}")

        if self.background_flag:
            self.logger.debug(f"Response:{self.response}")
        else:
            print(f"Response:{self.response}")	

        self.websocket_data(self.response)

    else:
        self.response = msg
        if self.background_flag:
            if type(msg)== str:
                if "error" in msg:
                    msg = json.loads(msg)
                    self.response_out["s"]=msg["s"]
                    self.response_out["code"]=msg["code"]
                    self.response_out["message"]=msg["message"]
                    self.response = self.response_out
                    self.logger.error(self.response)
            self.logger.debug(f"Response:{self.response}")
        else:
            if type(msg)== str:
                if "error" in msg:
                    msg = json.loads(msg)
                    self.response_out["s"]=msg["s"]
                    self.response_out["code"]=msg["code"]
                    self.response_out["message"]=msg["message"]
                    self.response = self.response_out
                    self.logger.error(self.response)
                    if self.websocket_data is not None:
                        self.websocket_data(self.response)
                    else:
                        print(f"Response:{self.response}")
                else:
                    if self.websocket_data is not None:
                        self.websocket_data(self.response)
                    else:
                        print(f"Response:{self.response}")
            else:
                if self.websocket_data is not None:
                    self.websocket_data(self.response)
                else:
                    print(f"Response:{self.response}")
        # self.websocket_data()
    return 
    # if self.__ws_message is not None:
    #     self.__ws_message(msg)


ws.FyersSocket._FyersSocket__on_message = new_on_message
 

