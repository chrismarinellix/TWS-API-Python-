"""
Updated IB TWS API Trading Bot with Order Checking and Better Error Handling
"""

from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.tag_value import TagValue
import random
import time
import threading
import atexit

port = 4002  # Paper trading account (4001 is live)

# Global connection tracking
active_connections = []

def cleanup_all_connections():
    """Cleanup function to ensure all connections are closed"""
    global active_connections
    for app in active_connections:
        try:
            if app.isConnected():
                app.disconnect()
                print(f"🔌 Cleaned up connection")
        except:
            pass
    active_connections.clear()

# Register cleanup on exit
atexit.register(cleanup_all_connections)

def get_unique_client_id():
    """Generate a unique client ID to avoid conflicts"""
    return random.randint(1000, 9999)

# Connection Classes
class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self,self)
        self.connected = False
    
    def connect_safely(self, host="127.0.0.1", port=4002, clientId=None):
        """Safe connection with unique client ID"""
        if clientId is None:
            clientId = get_unique_client_id()
        try:
            self.connect(host, port, clientId)
            self.connected = True
            global active_connections
            active_connections.append(self)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect_safely(self):
        """Safe disconnection with cleanup"""
        try:
            if self.isConnected():
                self.disconnect()
                time.sleep(1)  # Give gateway time to clean up
            self.connected = False
            global active_connections
            if self in active_connections:
                active_connections.remove(self)
        except:
            pass

class TradingBot(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextOrderId = None
        self.accounts = []
        self.market_data = {}
        self.positions = {}
        self.account_values = {}
        self.open_orders = []
        self.connected = False
        self.historical_data = {}  # Store historical data
        self.scanner_data = []  # Store scanner results
    
    def connect_safely(self, host="127.0.0.1", port=4002, clientId=None):
        """Safe connection with unique client ID"""
        if clientId is None:
            clientId = get_unique_client_id()
        try:
            self.connect(host, port, clientId)
            self.connected = True
            global active_connections
            active_connections.append(self)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect_safely(self):
        """Safe disconnection with cleanup"""
        try:
            if self.isConnected():
                self.disconnect()
                time.sleep(1)  # Give gateway time to clean up
            self.connected = False
            global active_connections
            if self in active_connections:
                active_connections.remove(self)
        except:
            pass

    def nextValidId(self, orderId: OrderId):
        self.nextOrderId = orderId
        print(f"✅ Next valid order ID: {orderId}")

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        # Informational messages (not real errors)
        info_codes = [2104, 2106, 2107, 2108, 2119, 2158]
        # Non-critical warnings
        warning_codes = [10268, 2102, 2103, 2110]
        
        if errorCode in info_codes:
            print(f"ℹ️  {errorString}")
        elif errorCode in warning_codes:
            print(f"⚠️  Note: {errorString} (not critical)")
        elif errorCode == 2158:
            print(f"✅ {errorString}")
        else:
            # Only use red X for actual errors
            print(f"❌ Error {errorCode}: {errorString}")

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"📋 Order {orderId}: {status} | Filled: {filled} | Remaining: {remaining} | Avg Fill Price: ${avgFillPrice}")

    def openOrder(self, orderId, contract, order, orderState):
        print(f"📝 Open Order {orderId}: {order.action} {order.totalQuantity} {contract.symbol} @ {order.orderType}")
        self.open_orders.append({
            "orderId": orderId,
            "symbol": contract.symbol,
            "action": order.action,
            "quantity": order.totalQuantity,
            "orderType": order.orderType,
            "status": orderState.status
        })

    def openOrderEnd(self):
        print(f"✅ Found {len(self.open_orders)} open order(s)")

    def execDetails(self, reqId, contract, execution):
        print(f"💰 Execution: {execution.shares} shares of {contract.symbol} at ${execution.price}")

    def tickPrice(self, reqId, tickType, price, attrib):
        symbol = self.market_data.get(reqId, {}).get('symbol', 'Unknown')
        tick_name = self.get_tick_name(tickType)
        print(f"📈 {symbol} - {tick_name}: ${price}")
        
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        self.market_data[reqId][tick_name] = price

    def tickSize(self, reqId, tickType, size):
        symbol = self.market_data.get(reqId, {}).get('symbol', 'Unknown')
        tick_name = self.get_tick_name(tickType)
        print(f"📊 {symbol} - {tick_name}: {size}")

    def get_tick_name(self, tickType):
        tick_names = {
            1: "Bid", 2: "Ask", 4: "Last", 6: "High", 7: "Low", 9: "Close",
            0: "Bid Size", 3: "Ask Size", 5: "Last Size", 8: "Volume"
        }
        return tick_names.get(tickType, f"Tick_{tickType}")

    def managedAccounts(self, accountsList):
        self.accounts = accountsList.split(",")
        print(f"📊 Available Accounts: {', '.join(self.accounts)}")

    def accountSummary(self, reqId, account, tag, value, currency):
        print(f"💼 Account {account} - {tag}: {value} {currency}")
        if account not in self.account_values:
            self.account_values[account] = {}
        self.account_values[account][tag] = {"value": value, "currency": currency}

    def accountSummaryEnd(self, reqId):
        print("✅ Account summary complete")

    def position(self, account, contract, position, avgCost):
        if position != 0:
            print(f"📍 Position: {position} shares of {contract.symbol} @ avg cost ${avgCost:.2f}")
            self.positions[contract.symbol] = {
                "position": position,
                "avgCost": avgCost,
                "account": account
            }

    def positionEnd(self):
        print("✅ Positions update complete")

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        contract = contractDetails.contract
        print(f"\n📋 Contract Details for {contract.symbol}:")
        print(f"   Exchange: {contract.exchange}")
        print(f"   Currency: {contract.currency}")
        print(f"   Contract ID: {contract.conId}")
        print(f"   Market Name: {contractDetails.marketName}")
        print(f"   Min Tick: {contractDetails.minTick}")

    def contractDetailsEnd(self, reqId: int):
        print("✅ Contract details complete")
    
    def historicalData(self, reqId, bar):
        """Receive historical data"""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })
    
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """Historical data reception complete"""
        print(f"✅ Historical data complete for request {reqId}")
    
    def scannerData(self, reqId: int, rank: int, contractDetails, distance: str, benchmark: str, projection: str, legsStr: str):
        """Receive scanner results"""
        contract = contractDetails.contract
        self.scanner_data.append({
            'rank': rank,
            'symbol': contract.symbol,
            'exchange': contract.exchange,
            'currency': contract.currency,
            'conId': contract.conId
        })
        print(f"   Found: {contract.symbol} (Rank: {rank})")
    
    def scannerDataEnd(self, reqId: int):
        """Scanner data complete"""
        print(f"✅ Scanner complete - Found {len(self.scanner_data)} results")

# Helper function to create clean orders without problematic attributes
def create_clean_order(action, quantity, order_type, limit_price=None):
    """Create an order with explicitly disabled problematic attributes"""
    order = Order()
    order.action = action
    order.totalQuantity = int(quantity)
    order.orderType = order_type
    order.tif = "DAY"
    
    # Explicitly set these to False to override defaults
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    
    # For limit orders, add the limit price
    if order_type == "LMT" and limit_price:
        order.lmtPrice = float(limit_price)
    
    return order

def create_stop_loss_order(action, quantity, stop_price):
    """Create a stop loss order"""
    order = Order()
    order.action = "SELL" if action == "BUY" else "BUY"  # Opposite of entry
    order.totalQuantity = int(quantity)
    order.orderType = "STP"
    order.auxPrice = float(stop_price)  # Stop trigger price
    order.tif = "GTC"  # Good till cancelled
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    return order

def create_stop_limit_order(action, quantity, stop_price, limit_price):
    """Create a stop limit order"""
    order = Order()
    order.action = "SELL" if action == "BUY" else "BUY"
    order.totalQuantity = int(quantity)
    order.orderType = "STP LMT"
    order.auxPrice = float(stop_price)  # Stop trigger price
    order.lmtPrice = float(limit_price)  # Limit price after trigger
    order.tif = "GTC"
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    return order

def create_trailing_stop_order(action, quantity, trail_amount=None, trail_percent=None):
    """Create a trailing stop order"""
    order = Order()
    order.action = "SELL" if action == "BUY" else "BUY"
    order.totalQuantity = int(quantity)
    order.orderType = "TRAIL"
    order.tif = "GTC"
    
    if trail_amount:
        order.auxPrice = float(trail_amount)  # Dollar amount to trail
    elif trail_percent:
        order.trailingPercent = float(trail_percent)  # Percentage to trail
    
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    return order

def create_bracket_order(parent_order_id, action, quantity, limit_price, stop_loss_price, take_profit_price):
    """Create a bracket order (entry + stop loss + take profit)"""
    # Parent order (entry)
    parent = Order()
    parent.orderId = parent_order_id
    parent.action = action
    parent.totalQuantity = int(quantity)
    parent.orderType = "LMT"
    parent.lmtPrice = float(limit_price)
    parent.tif = "GTC"
    parent.eTradeOnly = False
    parent.firmQuoteOnly = False
    parent.transmit = False  # Don't transmit until children are attached
    
    # Take profit order
    take_profit = Order()
    take_profit.orderId = parent_order_id + 1
    take_profit.parentId = parent_order_id
    take_profit.action = "SELL" if action == "BUY" else "BUY"
    take_profit.totalQuantity = int(quantity)
    take_profit.orderType = "LMT"
    take_profit.lmtPrice = float(take_profit_price)
    take_profit.tif = "GTC"
    take_profit.eTradeOnly = False
    take_profit.firmQuoteOnly = False
    take_profit.transmit = False
    
    # Stop loss order
    stop_loss = Order()
    stop_loss.orderId = parent_order_id + 2
    stop_loss.parentId = parent_order_id
    stop_loss.action = "SELL" if action == "BUY" else "BUY"
    stop_loss.totalQuantity = int(quantity)
    stop_loss.orderType = "STP"
    stop_loss.auxPrice = float(stop_loss_price)
    stop_loss.tif = "GTC"
    stop_loss.eTradeOnly = False
    stop_loss.firmQuoteOnly = False
    stop_loss.transmit = True  # Transmit all orders
    
    return parent, take_profit, stop_loss

# Main execution functions
def run_connection_test():
    """Test basic connection to TWS/Gateway"""
    app = TradingApp()
    try:
        client_id = get_unique_client_id()
        print(f"🔗 Connecting with client ID: {client_id}")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
            
        print("✅ Connection successful!")
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        time.sleep(3)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        app.disconnect_safely()
        print("✅ Disconnected. Test complete!")

def get_stock_info():
    """Get real-time stock information"""
    symbol = input("Enter stock symbol (e.g., AAPL): ").upper().strip()
    
    app = TradingBot()
    try:
        client_id = get_unique_client_id()
        print(f"📡 Connecting with client ID: {client_id} to get data for {symbol}...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        time.sleep(2)  # Give more time for connection
        
        if app.nextOrderId is not None:
            # Request delayed market data (type 3)
            app.reqMarketDataType(3)
            
            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            
            reqId = 1001
            app.market_data[reqId] = {"symbol": symbol}
            app.reqMktData(reqId, contract, "", False, False, [])
            
            app.reqContractDetails(reqId + 100, contract)
            
            print(f"📊 Requesting delayed data for {symbol} (15-min delay)...")
            time.sleep(10)
            
            app.cancelMktData(reqId)
        else:
            print("⚠️  Could not get valid order ID from gateway")
        
    except Exception as e:
        print(f"❌ Failed to get stock info: {e}")
    finally:
        app.disconnect_safely()
        print("✅ Stock info request complete!")

def get_account_info():
    """Get account information and positions"""
    app = TradingBot()
    try:
        client_id = get_unique_client_id()
        print(f"📊 Connecting with client ID: {client_id} to get account information...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        time.sleep(2)  # Give more time for connection
        
        if app.nextOrderId is not None:
            app.reqAccountSummary(9001, "All", "AccountType,NetLiquidation,TotalCashValue,SettledCash,AccruedCash,BuyingPower,EquityWithLoanValue,PreviousDayEquityWithLoanValue,GrossPositionValue")
            app.reqPositions()
            
            print("📋 Fetching account data...")
            time.sleep(8)
            
            app.cancelAccountSummary(9001)
            app.cancelPositions()
        else:
            print("⚠️  Could not get valid order ID from gateway")
        
    except Exception as e:
        print(f"❌ Failed to get account info: {e}")
    finally:
        app.disconnect_safely()
        print("✅ Account info request complete!")

def check_open_orders():
    """Check all open orders"""
    app = TradingBot()
    try:
        client_id = get_unique_client_id()
        print(f"🔍 Checking open orders with client ID: {client_id}...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        time.sleep(2)
        
        if app.nextOrderId is not None:
            app.open_orders = []  # Clear the list
            app.reqAllOpenOrders()
            
            time.sleep(5)
            
            if not app.open_orders:
                print("📭 No open orders found")
            else:
                print("\n📋 Open Orders Summary:")
                for order in app.open_orders:
                    print(f"   Order {order['orderId']}: {order['action']} {order['quantity']} {order['symbol']} ({order['orderType']})")
        else:
            print("⚠️  Could not get valid order ID from gateway")
            
    except Exception as e:
        print(f"❌ Failed to check orders: {e}")
    finally:
        app.disconnect_safely()
        print("✅ Order check complete!")

def check_pending_orders_all_accounts():
    """Check pending orders from IB system for both live and paper accounts"""
    print("\n" + "="*60)
    print("🔍 CHECKING PENDING ORDERS IN IB SYSTEM")
    print("="*60)
    
    port_choice = input("Which account to check?\n1. Live Account (port 4001)\n2. Paper Account (port 4002)\n3. Both\nEnter choice (1-3): ").strip()
    
    ports_to_check = []
    if port_choice == "1":
        ports_to_check = [(4001, "LIVE")]
    elif port_choice == "2":
        ports_to_check = [(4002, "PAPER")]
    elif port_choice == "3":
        ports_to_check = [(4001, "LIVE"), (4002, "PAPER")]
    else:
        print("❌ Invalid choice")
        return
    
    for check_port, account_type in ports_to_check:
        print(f"\n📊 Checking {account_type} account (port {check_port})...")
        print("-" * 40)
        
        app = TradingBot()
        try:
            client_id = get_unique_client_id()
            print(f"   Using client ID: {client_id}")
            
            if not app.connect_safely("127.0.0.1", check_port, client_id):
                print(f"   Could not connect to port {check_port}")
                continue
            
            api_thread = threading.Thread(target=app.run, daemon=True)
            api_thread.start()
            
            time.sleep(2)
            
            if app.nextOrderId is not None:
                print(f"✅ Connected to {account_type} account")
                
                # Clear and request all open orders
                app.open_orders = []
                app.reqAllOpenOrders()
                
                # Also request auto open orders (orders placed by other clients)
                app.reqAutoOpenOrders(True)
                
                # Request completed orders for today
                app.reqCompletedOrders(False)
                
                print(f"⏳ Retrieving orders from IB system...")
                time.sleep(5)
                
                if not app.open_orders:
                    print(f"📭 No pending orders in {account_type} account")
                else:
                    print(f"\n✅ Found {len(app.open_orders)} pending order(s) in {account_type} account:")
                    print("-" * 40)
                    for order in app.open_orders:
                        print(f"📋 Order ID: {order['orderId']}")
                        print(f"   Symbol: {order['symbol']}")
                        print(f"   Action: {order['action']}")
                        print(f"   Quantity: {order['quantity']}")
                        print(f"   Type: {order['orderType']}")
                        print(f"   Status: {order.get('status', 'Unknown')}")
                        print("-" * 40)
                
            else:
                print(f"⚠️  Could not connect to {account_type} account on port {check_port}")
                print(f"   Make sure IB Gateway/TWS is running on this port")
                
        except Exception as e:
            print(f"❌ Failed to connect to {account_type} account: {e}")
            print(f"   Make sure IB Gateway/TWS is running on port {check_port}")
        finally:
            app.disconnect_safely()
            time.sleep(2)  # Wait between account checks
    
    print("\n✅ Pending orders check complete!")

def enhanced_order_placement():
    """Enhanced order placement with multiple order types and better UI"""
    print("\n" + "="*60)
    print("📈 ENHANCED ORDER PLACEMENT")
    print("="*60)
    
    # Market selection
    print("\n📍 Select Market:")
    print("1. 🇦🇺 ASX (Australian Securities Exchange)")
    print("2. 🇺🇸 US Markets (NYSE/NASDAQ)")
    market_choice = input("Enter choice (1-2): ").strip()
    
    if market_choice == "1":
        exchange = "ASX"
        currency = "AUD"
        print("\n🇦🇺 Trading on ASX")
    else:
        exchange = "SMART"
        currency = "USD"
        print("\n🇺🇸 Trading on US Markets")
    
    # Stock selection
    symbol = input("\nEnter stock symbol: ").upper().strip()
    
    # Action selection with numbers
    print("\n📊 Select Action:")
    print("1. BUY")
    print("2. SELL")
    action_choice = input("Enter choice (1-2): ").strip()
    action = "BUY" if action_choice == "1" else "SELL"
    
    # Quantity
    quantity = input("\nEnter quantity: ").strip()
    
    # Order type selection
    print("\n📋 Select Order Type:")
    print("1. Market Order (MKT)")
    print("2. Limit Order (LMT)")
    print("3. Stop Loss Order (STP)")
    print("4. Stop Limit Order (STP LMT)")
    print("5. Trailing Stop Order")
    print("6. Bracket Order (Entry + Stop Loss + Take Profit)")
    order_type_choice = input("Enter choice (1-6): ").strip()
    
    app = TradingBot()
    try:
        client_id = get_unique_client_id()
        print(f"\n🔗 Connecting with client ID: {client_id}...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        time.sleep(2)
        
        if app.nextOrderId is None:
            print("⚠️  Could not get valid order ID from gateway")
            return
        
        # Create contract with selected market
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        
        # Handle different order types
        if order_type_choice == "1":  # Market Order
            order = create_clean_order(action, quantity, "MKT")
            print(f"\n📄 Placing Market Order: {action} {quantity} shares of {symbol}")
            app.placeOrder(app.nextOrderId, contract, order)
            
        elif order_type_choice == "2":  # Limit Order
            limit_price = input("Enter limit price: $").strip()
            order = create_clean_order(action, quantity, "LMT", limit_price)
            print(f"\n📄 Placing Limit Order: {action} {quantity} shares of {symbol} @ ${limit_price}")
            app.placeOrder(app.nextOrderId, contract, order)
            
        elif order_type_choice == "3":  # Stop Loss Order
            stop_price = input("Enter stop price: $").strip()
            order = create_stop_loss_order(action, quantity, stop_price)
            print(f"\n📄 Placing Stop Loss Order: {quantity} shares @ stop ${stop_price}")
            app.placeOrder(app.nextOrderId, contract, order)
            
        elif order_type_choice == "4":  # Stop Limit Order
            stop_price = input("Enter stop trigger price: $").strip()
            limit_price = input("Enter limit price after trigger: $").strip()
            order = create_stop_limit_order(action, quantity, stop_price, limit_price)
            print(f"\n📄 Placing Stop Limit Order: {quantity} shares @ stop ${stop_price}, limit ${limit_price}")
            app.placeOrder(app.nextOrderId, contract, order)
            
        elif order_type_choice == "5":  # Trailing Stop
            print("\n📊 Trailing Stop Type:")
            print("1. Trail by dollar amount")
            print("2. Trail by percentage")
            trail_choice = input("Enter choice (1-2): ").strip()
            
            if trail_choice == "1":
                trail_amount = input("Enter trail amount: $").strip()
                order = create_trailing_stop_order(action, quantity, trail_amount=trail_amount)
                print(f"\n📄 Placing Trailing Stop Order: {quantity} shares, trail by ${trail_amount}")
            else:
                trail_percent = input("Enter trail percentage: ").strip()
                order = create_trailing_stop_order(action, quantity, trail_percent=trail_percent)
                print(f"\n📄 Placing Trailing Stop Order: {quantity} shares, trail by {trail_percent}%")
            
            app.placeOrder(app.nextOrderId, contract, order)
            
        elif order_type_choice == "6":  # Bracket Order
            entry_price = input("Enter entry limit price: $").strip()
            stop_loss_price = input("Enter stop loss price: $").strip()
            take_profit_price = input("Enter take profit price: $").strip()
            
            parent, take_profit, stop_loss = create_bracket_order(
                app.nextOrderId, action, quantity, entry_price, stop_loss_price, take_profit_price
            )
            
            print(f"\n📄 Placing Bracket Order:")
            print(f"   Entry: {action} {quantity} shares @ ${entry_price}")
            print(f"   Stop Loss: @ ${stop_loss_price}")
            print(f"   Take Profit: @ ${take_profit_price}")
            
            # Place all three orders
            app.placeOrder(parent.orderId, contract, parent)
            app.placeOrder(take_profit.orderId, contract, take_profit)
            app.placeOrder(stop_loss.orderId, contract, stop_loss)
        
        else:
            print("⚠️  Invalid order type selection")
            return
        
        # Wait for order status
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Failed to place order: {e}")
    finally:
        app.disconnect_safely()
        print("✅ Order placement complete!")

def quick_order_templates():
    """Quick order templates for common strategies"""
    print("\n" + "="*60)
    print("🚀 QUICK ORDER TEMPLATES")
    print("="*60)
    
    print("1. Buy with 2% Stop Loss")
    print("2. Buy with Bracket (1% Stop, 3% Profit)")
    print("3. Sell with Trailing Stop (2%)")
    print("4. Dollar Cost Average (DCA) Entry")
    
    template_choice = input("\nSelect template (1-4): ").strip()
    
    if template_choice == "1":
        symbol = input("Enter stock symbol: ").upper().strip()
        quantity = input("Enter quantity: ").strip()
        entry_price = float(input("Enter entry price (or current price): $").strip())
        stop_price = entry_price * 0.98  # 2% below entry
        
        print(f"\n📋 Order Preview:")
        print(f"   BUY {quantity} shares of {symbol} @ Market")
        print(f"   Stop Loss @ ${stop_price:.2f} (2% below ${entry_price:.2f})")
        
        if input("\nConfirm order? (yes/no): ").lower() == "yes":
            place_template_order(symbol, "BUY", quantity, stop_loss=stop_price)
    
    # Add more templates as needed

def place_template_order(symbol, action, quantity, stop_loss=None, take_profit=None):
    """Helper to place template orders"""
    app = TradingBot()
    try:
        client_id = get_unique_client_id()
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        time.sleep(2)
        
        if app.nextOrderId is None:
            print("⚠️  Could not get valid order ID")
            return
        
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        
        # Place market order
        order = create_clean_order(action, quantity, "MKT")
        app.placeOrder(app.nextOrderId, contract, order)
        
        # Place stop loss if provided
        if stop_loss:
            stop_order = create_stop_loss_order(action, quantity, stop_loss)
            app.placeOrder(app.nextOrderId + 1, contract, stop_order)
        
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        app.disconnect_safely()

def scan_all_asx_gainers():
    """Use IB Scanner to find ALL ASX stocks with 5%+ weekly gains"""
    print("\n" + "="*60)
    print("🇦🇺 SCANNING ALL ASX STOCKS - WEEKLY GAINERS")
    print("="*60)
    print("Using IB Scanner to search entire ASX market...")
    print("This will find ALL stocks, not just a predefined list\n")
    
    from ibapi.scanner import ScannerSubscription
    
    app = TradingBot()
    
    try:
        client_id = get_unique_client_id()
        print(f"🔗 Connecting with client ID: {client_id}...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        time.sleep(2)
        
        if app.nextOrderId is None:
            print("⚠️  Could not get valid order ID from gateway")
            return
        
        # Clear scanner data
        app.scanner_data = []
        
        # Create scanner subscription for ASX
        scanner = ScannerSubscription()
        scanner.instrument = "STK"
        scanner.locationCode = "STK.ASX"  # ASX stocks only
        scanner.scanCode = "TOP_PERC_GAIN"  # Top percentage gainers
        
        # Optional filters
        scanner.abovePrice = 0.50  # Minimum price $0.50
        scanner.belowPrice = 10000  # Maximum price $10,000
        scanner.aboveVolume = 10000  # Minimum volume
        scanner.marketCapAbove = 1000000  # Minimum market cap $1M
        
        print("📡 Requesting top gainers from ASX...")
        print("⏳ Scanning entire exchange...\n")
        
        # Request scanner data
        app.reqScannerSubscription(7001, scanner, [], [])
        
        # Wait for results
        time.sleep(10)
        
        # Cancel scanner
        app.cancelScannerSubscription(7001)
        
        if app.scanner_data:
            print(f"\n📊 Found {len(app.scanner_data)} top gaining stocks on ASX")
            
            # Now get historical data for each to calculate exact weekly change
            print("\n⏳ Fetching weekly performance data...")
            results = []
            
            for i, stock_data in enumerate(app.scanner_data[:30]):  # Limit to top 30
                try:
                    contract = Contract()
                    contract.symbol = stock_data['symbol']
                    contract.secType = "STK"
                    contract.exchange = "ASX"
                    contract.currency = "AUD"
                    
                    reqId = 8000 + i
                    app.historical_data[reqId] = []
                    
                    app.reqHistoricalData(
                        reqId, contract, "", "1 W", "1 day",
                        "MIDPOINT", 1, 1, False, []
                    )
                    
                    time.sleep(0.5)
                    
                    if reqId in app.historical_data and len(app.historical_data[reqId]) >= 2:
                        data = app.historical_data[reqId]
                        first_close = data[0]['close']
                        last_close = data[-1]['close']
                        
                        if first_close > 0:
                            change_pct = ((last_close - first_close) / first_close) * 100
                            
                            if change_pct >= 5:  # Only keep 5%+ gainers
                                results.append({
                                    'symbol': stock_data['symbol'],
                                    'rank': stock_data['rank'],
                                    'start_price': first_close,
                                    'end_price': last_close,
                                    'change_pct': change_pct
                                })
                                print(f"✅ {stock_data['symbol']}: +{change_pct:.2f}%")
                
                except Exception as e:
                    continue
            
            # Display results
            if results:
                results.sort(key=lambda x: x['change_pct'], reverse=True)
                
                print("\n" + "="*60)
                print("🚀 ASX WEEKLY GAINERS (5%+ from ENTIRE MARKET)")
                print("="*60)
                print(f"\n{'Rank':<6} {'Symbol':<8} {'Start (AUD)':<12} {'Current (AUD)':<12} {'Change %'}")
                print("-" * 60)
                
                for stock in results:
                    print(f"{stock['rank']:<6} {stock['symbol']:<8} A${stock['start_price']:<10.2f} "
                          f"A${stock['end_price']:<10.2f} {stock['change_pct']:>+7.2f}%")
            else:
                print("\n📉 No stocks found with 5%+ weekly gains")
        else:
            print("📭 No scanner results received")
            print("Note: Scanner requires market data subscriptions")
            
    except Exception as e:
        print(f"❌ Scanner failed: {e}")
        print("\nNote: IB Scanner requires:")
        print("- Active market data subscription for ASX")
        print("- Scanner permissions on your account")
    finally:
        app.disconnect_safely()
        print("\n✅ Scan complete!")

def scan_weekly_gainers():
    """Scan for ASX stocks that have moved up 5% or more in the last week"""
    print("\n" + "="*60)
    print("🇦🇺 SCANNING ASX WEEKLY GAINERS (5%+)")
    print("="*60)
    
    # List of popular ASX stocks (ASX 50 components)
    # Note: Some tickers have changed or been delisted
    symbols = [
        "BHP", "CBA", "CSL", "NAB", "WBC", "ANZ", "WES", "MQG", 
        "GMG", "WDS", "TLS", "WOW", "FMG", "TCL", "RIO", "ALL",
        "REA", "SHL", "NCM", "COL", "BXB", "QBE", "IAG",
        "SUN", "AMC", "APA", "SCG", "GPT", "MGR", "DXS",
        "SGP", "JHX", "ASX", "CPU", "CTX", "BSL",
        "AGL", "MPL", "TWE", "QAN", "STO", "RHC", "NST", "EVN",
        "S32", "SOL", "XRO", "PME", "MIN", "LLC", "NXT"
    ]
    
    print(f"📊 Scanning {len(symbols)} ASX stocks for weekly performance...")
    print("⏳ This may take a moment...\n")
    
    app = TradingBot()
    results = []
    
    try:
        client_id = get_unique_client_id()
        print(f"🔗 Connecting with client ID: {client_id}...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        time.sleep(2)
        
        if app.nextOrderId is None:
            print("⚠️  Could not get valid order ID from gateway")
            return
        
        # Process each symbol
        for i, symbol in enumerate(symbols):
            try:
                # Create contract for ASX stocks
                contract = Contract()
                contract.symbol = symbol
                contract.secType = "STK"
                contract.exchange = "ASX"  # Australian Securities Exchange
                contract.currency = "AUD"  # Australian Dollar
                
                # Request historical data for the last week
                reqId = 5000 + i
                app.historical_data[reqId] = []
                
                # Request 1 week of daily bars
                app.reqHistoricalData(
                    reqId,
                    contract,
                    "",  # End date (blank = current)
                    "1 W",  # Duration (1 week)
                    "1 day",  # Bar size
                    "MIDPOINT",  # Data type
                    1,  # Use RTH (regular trading hours)
                    1,  # Format date as yyyyMMdd
                    False,  # Keep up to date
                    []
                )
                
                # Wait for data
                time.sleep(1)
                
                # Calculate performance if we have data
                if reqId in app.historical_data and len(app.historical_data[reqId]) >= 2:
                    data = app.historical_data[reqId]
                    first_close = data[0]['close']
                    last_close = data[-1]['close']
                    
                    if first_close > 0:
                        change_pct = ((last_close - first_close) / first_close) * 100
                        
                        results.append({
                            'symbol': symbol,
                            'start_price': first_close,
                            'end_price': last_close,
                            'change_pct': change_pct
                        })
                        
                        # Show progress
                        if change_pct >= 5:
                            print(f"✅ {symbol}: +{change_pct:.2f}% 🚀")
                        elif change_pct >= 0:
                            print(f"   {symbol}: +{change_pct:.2f}%")
                        else:
                            print(f"   {symbol}: {change_pct:.2f}%")
                
            except Exception as e:
                print(f"   ⚠️  Error scanning {symbol}: {e}")
                continue
        
        # Sort results by performance
        results.sort(key=lambda x: x['change_pct'], reverse=True)
        
        # Display summary
        print("\n" + "="*60)
        print("🇦🇺 ASX WEEKLY GAINERS SUMMARY (5%+ Movers)")
        print("="*60)
        
        gainers = [r for r in results if r['change_pct'] >= 5]
        
        if gainers:
            print(f"\n🚀 Found {len(gainers)} ASX stocks up 5% or more this week:\n")
            print(f"{'Symbol':<8} {'Start (AUD)':<12} {'Current (AUD)':<12} {'Change %':<12} {'Status'}")
            print("-" * 60)
            
            for stock in gainers:
                status = "🔥 HOT" if stock['change_pct'] >= 10 else "📈 Rising"
                print(f"{stock['symbol']:<8} A${stock['start_price']:<10.2f} A${stock['end_price']:<10.2f} "
                      f"{stock['change_pct']:>+7.2f}%     {status}")
        else:
            print("\n📉 No stocks found with 5%+ gains this week")
        
        # Also show top losers for context
        losers = [r for r in results if r['change_pct'] <= -5]
        if losers:
            print(f"\n📉 Biggest ASX losers this week:\n")
            print(f"{'Symbol':<8} {'Start (AUD)':<12} {'Current (AUD)':<12} {'Change %'}")
            print("-" * 50)
            for stock in losers[:5]:  # Show top 5 losers
                print(f"{stock['symbol']:<8} A${stock['start_price']:<10.2f} A${stock['end_price']:<10.2f} "
                      f"{stock['change_pct']:>+7.2f}%")
        
        # Market overview
        if results:
            avg_change = sum(r['change_pct'] for r in results) / len(results)
            positive = len([r for r in results if r['change_pct'] > 0])
            negative = len([r for r in results if r['change_pct'] < 0])
            
            print(f"\n📊 ASX MARKET OVERVIEW:")
            print(f"   Average Change: {avg_change:+.2f}%")
            print(f"   Gainers: {positive} | Losers: {negative}")
            print(f"   Best ASX Performer: {results[0]['symbol']} ({results[0]['change_pct']:+.2f}%)")
            print(f"   Worst ASX Performer: {results[-1]['symbol']} ({results[-1]['change_pct']:+.2f}%)")
        
    except Exception as e:
        print(f"❌ Scanner failed: {e}")
    finally:
        app.disconnect_safely()
        print("\n✅ Scan complete!")

def scan_custom_list():
    """Scan a custom list of stocks for weekly performance"""
    print("\n" + "="*60)
    print("📈 CUSTOM STOCK SCANNER")
    print("="*60)
    
    # Ask for market
    print("Select Market:")
    print("1. 🇦🇺 ASX (Australian Securities Exchange)")
    print("2. 🇺🇸 US Markets (NYSE/NASDAQ)")
    market_choice = input("Enter choice (1-2): ").strip()
    
    if market_choice == "1":
        exchange = "ASX"
        currency = "AUD"
        example = "BHP,CBA,CSL"
        market_name = "ASX"
    else:
        exchange = "SMART"
        currency = "USD"
        example = "AAPL,MSFT,GOOGL"
        market_name = "US"
    
    # Get custom symbols from user
    symbols_input = input(f"\nEnter stock symbols separated by commas (e.g., {example}): ").upper().strip()
    symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
    
    if not symbols:
        print("❌ No symbols entered")
        return
    
    print(f"\n📊 Scanning {len(symbols)} stocks for weekly performance...")
    
    app = TradingBot()
    results = []
    
    try:
        client_id = get_unique_client_id()
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        time.sleep(2)
        
        if app.nextOrderId is None:
            print("⚠️  Could not connect to gateway")
            return
        
        for i, symbol in enumerate(symbols):
            try:
                contract = Contract()
                contract.symbol = symbol
                contract.secType = "STK"
                contract.exchange = exchange
                contract.currency = currency
                
                reqId = 6000 + i
                app.historical_data[reqId] = []
                
                app.reqHistoricalData(
                    reqId, contract, "", "1 W", "1 day", 
                    "MIDPOINT", 1, 1, False, []
                )
                
                time.sleep(1.5)
                
                if reqId in app.historical_data and len(app.historical_data[reqId]) >= 2:
                    data = app.historical_data[reqId]
                    first_close = data[0]['close']
                    last_close = data[-1]['close']
                    
                    if first_close > 0:
                        change_pct = ((last_close - first_close) / first_close) * 100
                        results.append({
                            'symbol': symbol,
                            'start_price': first_close,
                            'end_price': last_close,
                            'change_pct': change_pct
                        })
                
            except Exception as e:
                print(f"⚠️  Error scanning {symbol}")
                continue
        
        # Display results
        if results:
            results.sort(key=lambda x: x['change_pct'], reverse=True)
            
            print("\n" + "="*60)
            print(f"📊 {market_name} WEEKLY PERFORMANCE RESULTS")
            print("="*60)
            
            curr_symbol = "A$" if currency == "AUD" else "$"
            print(f"\n{'Symbol':<8} {'Start':<10} {'Current':<10} {'Change %':<12} {'Trend'}")
            print("-" * 55)
            
            for stock in results:
                if stock['change_pct'] >= 5:
                    trend = "🚀 Strong Up"
                elif stock['change_pct'] >= 0:
                    trend = "📈 Up"
                elif stock['change_pct'] >= -5:
                    trend = "📉 Down"
                else:
                    trend = "💥 Strong Down"
                    
                print(f"{stock['symbol']:<8} {curr_symbol}{stock['start_price']:<9.2f} {curr_symbol}{stock['end_price']:<9.2f} "
                      f"{stock['change_pct']:>+7.2f}%     {trend}")
        
    except Exception as e:
        print(f"❌ Scanner failed: {e}")
    finally:
        app.disconnect_safely()

def position_size_calculator():
    """Calculate position size based on risk management"""
    print("\n" + "="*60)
    print("💰 POSITION SIZE CALCULATOR")
    print("="*60)
    
    account_size = float(input("Enter account size: $").strip())
    risk_percent = float(input("Enter risk per trade (%): ").strip())
    entry_price = float(input("Enter entry price: $").strip())
    stop_loss_price = float(input("Enter stop loss price: $").strip())
    
    # Calculate risk amount
    risk_amount = account_size * (risk_percent / 100)
    
    # Calculate price difference
    price_diff = abs(entry_price - stop_loss_price)
    
    # Calculate position size
    if price_diff > 0:
        position_size = int(risk_amount / price_diff)
        total_cost = position_size * entry_price
        
        print("\n📊 POSITION SIZE CALCULATION:")
        print(f"   Account Size: ${account_size:,.2f}")
        print(f"   Risk Per Trade: {risk_percent}% (${risk_amount:,.2f})")
        print(f"   Entry Price: ${entry_price:.2f}")
        print(f"   Stop Loss: ${stop_loss_price:.2f}")
        print(f"   Price Risk per Share: ${price_diff:.2f}")
        print("-" * 40)
        print(f"✅ RECOMMENDED POSITION SIZE: {position_size} shares")
        print(f"   Total Position Value: ${total_cost:,.2f}")
        print(f"   Max Loss if Stopped: ${risk_amount:,.2f}")
        print(f"   % of Account: {(total_cost/account_size*100):.1f}%")
        
        if total_cost > account_size:
            print("\n⚠️  WARNING: Position size exceeds account size!")
            print("   Consider using margin or reducing position size.")
    else:
        print("❌ Invalid prices - stop loss must be different from entry")

def cancel_or_modify_order():
    """Cancel or modify existing orders"""
    app = TradingBot()
    try:
        client_id = get_unique_client_id()
        print(f"🔍 Checking orders...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        time.sleep(2)
        
        if app.nextOrderId is None:
            return
        
        # Get open orders
        app.open_orders = []
        app.reqAllOpenOrders()
        time.sleep(3)
        
        if not app.open_orders:
            print("📭 No open orders to modify/cancel")
            return
        
        print("\n📋 Open Orders:")
        for i, order in enumerate(app.open_orders, 1):
            print(f"{i}. Order {order['orderId']}: {order['action']} {order['quantity']} {order['symbol']}")
        
        print(f"{len(app.open_orders) + 1}. Cancel All Orders")
        
        choice = input("\nSelect order to modify/cancel: ").strip()
        
        if choice.isdigit():
            choice_idx = int(choice) - 1
            if choice_idx == len(app.open_orders):
                # Cancel all orders
                app.reqGlobalCancel()
                print("❌ Cancelling all orders...")
            elif 0 <= choice_idx < len(app.open_orders):
                selected_order = app.open_orders[choice_idx]
                print(f"\nSelected: Order {selected_order['orderId']}")
                print("1. Cancel Order")
                print("2. Modify Order (not implemented yet)")
                
                action = input("Select action (1-2): ").strip()
                if action == "1":
                    app.cancelOrder(selected_order['orderId'])
                    print(f"❌ Cancelling order {selected_order['orderId']}...")
        
        time.sleep(3)
        
    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        app.disconnect_safely()

def paper_trade_order():
    """Place a paper trading order (safe testing)"""
    print("\n📝 Paper Trading Order (Safe Testing)")
    
    # Market selection
    print("\n📍 Select Market:")
    print("1. 🇦🇺 ASX")
    print("2. 🇺🇸 US Markets")
    market_choice = input("Enter choice (1-2): ").strip()
    
    if market_choice == "1":
        exchange = "ASX"
        currency = "AUD"
    else:
        exchange = "SMART"
        currency = "USD"
    
    symbol = input("\nEnter stock symbol: ").upper().strip()
    action = input("Enter action (BUY/SELL): ").upper().strip()
    quantity = input("Enter quantity: ").strip()
    order_type = input("Enter order type (MKT/LMT): ").upper().strip()
    
    limit_price = None
    if order_type == "LMT":
        limit_price = input("Enter limit price: $").strip()
    
    app = TradingBot()
    try:
        client_id = get_unique_client_id()
        print(f"🔗 Connecting for paper trade with client ID: {client_id}...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        time.sleep(2)
        
        if app.nextOrderId is not None:
            contract_obj = Contract()
            contract_obj.symbol = symbol
            contract_obj.secType = "STK"
            contract_obj.exchange = exchange
            contract_obj.currency = currency
            
            # Use helper function for clean order
            order = create_clean_order(action, quantity, order_type, limit_price)
            
            print(f"📄 Placing paper {order_type} order...")
            print(f"   {action} {quantity} shares of {symbol}")
            if order_type == "LMT" and limit_price:
                print(f"   Limit price: ${limit_price}")
            
            app.placeOrder(app.nextOrderId, contract_obj, order)
            
            time.sleep(8)
        else:
            print("⚠️  Could not get valid order ID from gateway")
        
    except Exception as e:
        print(f"❌ Failed to place paper order: {e}")
    finally:
        app.disconnect_safely()
        print("✅ Paper trade complete!")

def place_live_order():
    """Place a live order - BE CAREFUL!"""
    print("\n" + "="*60)
    print("⚠️  LIVE ORDER PLACEMENT - REAL MONEY AT RISK! ⚠️")
    print("="*60)
    
    confirm = input("Are you sure you want to place a LIVE order? (type 'YES' to continue): ")
    if confirm != "YES":
        print("❌ Order cancelled for safety")
        return
    
    symbol = input("Enter stock symbol: ").upper().strip()
    action = input("Enter action (BUY/SELL): ").upper().strip()
    quantity = input("Enter quantity: ").strip()
    order_type = input("Enter order type (MKT/LMT): ").upper().strip()
    
    limit_price = None
    if order_type == "LMT":
        limit_price = input("Enter limit price: $").strip()
    
    print(f"\n📋 Order Summary:")
    print(f"   Symbol: {symbol}")
    print(f"   Action: {action}")
    print(f"   Quantity: {quantity}")
    print(f"   Type: {order_type}")
    if order_type == "LMT":
        print(f"   Limit Price: ${limit_price}")
    
    final_confirm = input("\n⚠️  FINAL CONFIRMATION - Place this LIVE order? (type 'PLACE ORDER'): ")
    if final_confirm != "PLACE ORDER":
        print("❌ Order cancelled")
        return
    
    app = TradingBot()
    try:
        client_id = get_unique_client_id()
        print(f"🔗 Connecting to place order with client ID: {client_id}...")
        
        if not app.connect_safely("127.0.0.1", port, client_id):
            return
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        time.sleep(2)
        
        if app.nextOrderId is not None:
            contract_obj = Contract()
            contract_obj.symbol = symbol
            contract_obj.secType = "STK"
            contract_obj.exchange = exchange
            contract_obj.currency = currency
            
            # Use helper function for clean order
            order = create_clean_order(action, quantity, order_type, limit_price)
            
            print(f"🚀 Placing {order_type} order...")
            print(f"   {action} {quantity} shares of {symbol}")
            if order_type == "LMT":
                print(f"   Limit price: ${limit_price}")
            
            app.placeOrder(app.nextOrderId, contract_obj, order)
            
            time.sleep(5)
        else:
            print("⚠️  Could not get valid order ID from gateway")
        
    except Exception as e:
        print(f"❌ Failed to place order: {e}")
    finally:
        app.disconnect_safely()
        print("✅ Order placement complete!")

# Main execution
if __name__ == "__main__":
    while True:
        print("\n" + "="*60)
        print("🚀 IB TWS API Advanced Trading System")
        print("Make sure TWS/Gateway is running on port", port)
        print("="*60)
        
        print("📊 MARKET DATA & SCANNERS:")
        print("1. Get stock/ticker info (delayed)")
        print("2. Get account info & positions")
        print("3. 🇦🇺 Scan ASX Top 50 Gainers (Predefined List)")
        print("4. 🔥 Scan ALL ASX Stocks (IB Scanner - Requires Subscription)")
        print("5. Custom Stock Scanner")
        
        print("\n📈 ORDER PLACEMENT:")
        print("6. Enhanced Order Placement (All Types)")
        print("7. Quick Order Templates")
        print("8. Simple Order (Original)")
        
        print("\n📋 ORDER MANAGEMENT:")
        print("9. Check open orders")
        print("10. Cancel/Modify orders")
        print("11. Check pending orders (all accounts)")
        
        print("\n⚙️  UTILITIES:")
        print("12. Position size calculator")
        print("13. Basic connection test")
        
        print("\n0. Exit")
        
        choice = input("\nEnter choice (0-13): ").strip()
        
        if choice == "1":
            get_stock_info()
        elif choice == "2":
            get_account_info()
        elif choice == "3":
            scan_weekly_gainers()
        elif choice == "4":
            scan_all_asx_gainers()
        elif choice == "5":
            scan_custom_list()
        elif choice == "6":
            enhanced_order_placement()
        elif choice == "7":
            quick_order_templates()
        elif choice == "8":
            paper_trade_order()
        elif choice == "9":
            check_open_orders()
        elif choice == "10":
            cancel_or_modify_order()
        elif choice == "11":
            check_pending_orders_all_accounts()
        elif choice == "12":
            position_size_calculator()
        elif choice == "13":
            run_connection_test()
        elif choice == "0":
            print("👋 Goodbye!")
            break
        else:
            print("⚠️  Invalid choice, please try again")
            
        input("\nPress Enter to continue...")