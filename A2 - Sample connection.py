"""

Sample TWS API connection via app.connect() - https://ibkrcampus.com/ibkr-api-page/trader-workstation-api/#connectivity
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper

port = 4002


class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self,self)
          
    
app = TradingApp()      
app.connect("127.0.0.1", port, clientId=1)
app.run()
