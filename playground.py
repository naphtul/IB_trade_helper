from ibapi.client import *
from ibapi.wrapper import *
import time
import threading

class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.positions = []
        self.positions_map = {}

    def nextValidId(self, orderId):
        self.orderId = orderId

    def nextId(self):
        self.orderId += 1
        return self.orderId

    def currentTime(self, time):
        print(time)

    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        print(f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderReject}")

    def position(self, account, contract, position, avgCost):
        print(f"Account: {account}, Symbol: {contract.symbol}, Position: {position}, AvgCost: {avgCost}")
        self.positions.append((account, contract.symbol, position, avgCost))
        self.positions_map[contract.symbol] = int(position)

    def positionEnd(self):
        print("All positions received.")

    def get_my_positions(self):
        self.reqPositions()



app = TestApp()
app.connect("127.0.0.1", 7496, 0)
threading.Thread(target=app.run).start()
time.sleep(1)

# for i in range(0,5):
#   print(app.nextId())
app.reqCurrentTime()
app.get_my_positions()
