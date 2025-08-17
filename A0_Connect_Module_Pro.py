#!/usr/bin/env python3
"""
A0 Connect Module Pro - Professional Momentum Trading System
Enhanced IB TWS API with Smart Order Management
"""

from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.scanner import ScannerSubscription
from ibapi.tag_value import TagValue
import threading
import time
import random
import atexit
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys

# Port Configuration
PAPER_PORT = 4002  # Paper trading
LIVE_PORT = 4001   # Live trading

# Global connection management
active_connections = []

def cleanup_all_connections():
    """Cleanup all active connections on exit"""
    for app in active_connections:
        try:
            if app.isConnected():
                app.disconnect()
        except:
            pass

atexit.register(cleanup_all_connections)

def get_unique_client_id():
    """Generate unique client ID to prevent conflicts"""
    return random.randint(1000, 9999)

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    @staticmethod
    def green(text): return f"{Colors.GREEN}{text}{Colors.END}"
    
    @staticmethod
    def red(text): return f"{Colors.RED}{text}{Colors.END}"
    
    @staticmethod
    def yellow(text): return f"{Colors.YELLOW}{text}{Colors.END}"
    
    @staticmethod
    def blue(text): return f"{Colors.BLUE}{text}{Colors.END}"
    
    @staticmethod
    def cyan(text): return f"{Colors.CYAN}{text}{Colors.END}"
    
    @staticmethod
    def bold(text): return f"{Colors.BOLD}{text}{Colors.END}"

class TradingBot(EClient, EWrapper):
    """Enhanced Trading Bot with Professional Features"""
    
    def __init__(self):
        EClient.__init__(self, self)
        EWrapper.__init__(self)
        
        # Core attributes
        self.nextOrderId = None
        self.accounts = []
        self.market_data = {}
        self.positions = {}
        self.account_values = {}
        self.open_orders = []
        self.historical_data = {}
        self.scanner_data = []
        self.contract_details = {}
        
        # Enhanced attributes for Pro features
        self.latest_prices = {}  # Symbol -> {bid, ask, last, high, low, close}
        self.volatility_data = {}  # Symbol -> {atr, std_dev, range}
        self.order_statuses = {}  # OrderId -> status info
        
    def nextValidId(self, orderId: int):
        self.nextOrderId = orderId
        
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        info_codes = [2104, 2106, 2107, 2108, 2119, 2158]
        warning_codes = [10268, 2102, 2103, 2110, 399]
        
        if errorCode in info_codes:
            print(f"ℹ️  {errorString}")
        elif errorCode in warning_codes:
            print(f"⚠️  Warning {errorCode}: {errorString}")
        else:
            print(f"❌ Error {errorCode}: {errorString}")
            
    def tickPrice(self, reqId, tickType, price, attrib):
        """Enhanced price handling with latest price tracking"""
        symbol = self.market_data.get(reqId, {}).get("symbol", "Unknown")
        
        if symbol not in self.latest_prices:
            self.latest_prices[symbol] = {}
            
        # Map tick types to price fields
        if tickType == 1:  # BID
            self.market_data[reqId]["bid"] = price
            self.latest_prices[symbol]["bid"] = price
        elif tickType == 2:  # ASK
            self.market_data[reqId]["ask"] = price
            self.latest_prices[symbol]["ask"] = price
        elif tickType == 4:  # LAST
            self.market_data[reqId]["last"] = price
            self.latest_prices[symbol]["last"] = price
        elif tickType == 6:  # HIGH
            self.market_data[reqId]["high"] = price
            self.latest_prices[symbol]["high"] = price
        elif tickType == 7:  # LOW
            self.market_data[reqId]["low"] = price
            self.latest_prices[symbol]["low"] = price
        elif tickType == 9:  # CLOSE
            self.market_data[reqId]["close"] = price
            self.latest_prices[symbol]["close"] = price
            
    def tickSize(self, reqId, tickType, size):
        if tickType == 5:  # Last Size
            self.market_data[reqId]["volume"] = size
        elif tickType == 8:  # Total Volume
            self.market_data[reqId]["total_volume"] = size
            
    def historicalData(self, reqId, bar):
        """Store historical data for analysis"""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        self.historical_data[reqId].append({
            "date": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        })
        
    def historicalDataEnd(self, reqId, start, end):
        """Calculate volatility metrics when historical data is complete"""
        if reqId in self.historical_data and len(self.historical_data[reqId]) > 0:
            data = self.historical_data[reqId]
            symbol = self.market_data.get(reqId, {}).get("symbol", "Unknown")
            
            # Calculate ATR (Average True Range)
            if len(data) >= 14:
                atr = self.calculate_atr(data)
                self.volatility_data[symbol] = {"atr": atr}
                
    def calculate_atr(self, bars, period=14):
        """Calculate Average True Range for volatility"""
        true_ranges = []
        for i in range(1, len(bars)):
            high = bars[i]["high"]
            low = bars[i]["low"]
            prev_close = bars[i-1]["close"]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
            
        if len(true_ranges) >= period:
            return sum(true_ranges[-period:]) / period
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0
        
    def managedAccounts(self, accountsList):
        self.accounts = accountsList.split(",")
        
    def accountSummary(self, reqId, account, tag, value, currency):
        self.account_values[tag] = {
            "value": value,
            "currency": currency,
            "account": account
        }
        
    def position(self, account, contract, position, avgCost):
        symbol = contract.symbol
        self.positions[symbol] = {
            "contract": contract,
            "position": position,
            "avgCost": avgCost,
            "account": account
        }
        
    def openOrder(self, orderId, contract, order, orderState):
        self.open_orders.append({
            "orderId": orderId,
            "symbol": contract.symbol,
            "action": order.action,
            "quantity": order.totalQuantity,
            "orderType": order.orderType,
            "limitPrice": order.lmtPrice if order.orderType == "LMT" else None,
            "status": orderState.status
        })
        
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId,
                   parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        self.order_statuses[orderId] = {
            "status": status,
            "filled": filled,
            "remaining": remaining,
            "avgFillPrice": avgFillPrice
        }
        
    def connect_safely(self, host="127.0.0.1", port=4002, clientId=None):
        """Safe connection with automatic client ID"""
        if clientId is None:
            clientId = get_unique_client_id()
        
        try:
            self.connect(host, port, clientId)
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
                time.sleep(1)
            if self in active_connections:
                active_connections.remove(self)
        except:
            pass

class MomentumTrader:
    """Professional Momentum Trading System"""
    
    def __init__(self, port=PAPER_PORT):
        self.app = TradingBot()
        self.port = port
        
    def connect(self):
        """Establish connection to IB Gateway"""
        client_id = get_unique_client_id()
        print(f"🔗 Connecting with client ID: {client_id}...")
        
        if self.app.connect_safely("127.0.0.1", self.port, client_id):
            api_thread = threading.Thread(target=self.app.run, daemon=True)
            api_thread.start()
            time.sleep(2)
            
            if self.app.nextOrderId is not None:
                print(f"✅ Connected! Next Order ID: {self.app.nextOrderId}")
                return True
        
        print("❌ Connection failed!")
        return False
        
    def disconnect(self):
        """Safely disconnect from IB Gateway"""
        self.app.disconnect_safely()
        
    def get_live_price(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Dict:
        """Fetch live price data for a symbol"""
        print(f"\n📊 Fetching live data for {Colors.bold(symbol)}...")
        
        # Create contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        
        # Request market data
        req_id = random.randint(10000, 19999)
        self.app.market_data[req_id] = {"symbol": symbol}
        self.app.reqMarketDataType(3)  # Delayed data
        self.app.reqMktData(req_id, contract, "", False, False, [])
        
        # Request historical data for volatility
        self.app.reqHistoricalData(
            req_id, contract,
            "", "5 D", "1 day", "TRADES",
            1, 1, False, []
        )
        
        # Wait for data
        time.sleep(3)
        
        # Cancel market data
        self.app.cancelMktData(req_id)
        
        # Get prices
        prices = self.app.latest_prices.get(symbol, {})
        volatility = self.app.volatility_data.get(symbol, {})
        
        return {
            "symbol": symbol,
            "bid": prices.get("bid", 0),
            "ask": prices.get("ask", 0),
            "last": prices.get("last", 0),
            "high": prices.get("high", 0),
            "low": prices.get("low", 0),
            "close": prices.get("close", 0),
            "spread": prices.get("ask", 0) - prices.get("bid", 0) if prices.get("ask") and prices.get("bid") else 0,
            "atr": volatility.get("atr", 0)
        }
        
    def display_price_info(self, price_data: Dict):
        """Display price information in a formatted way"""
        print("\n" + "="*60)
        print(f"📈 {Colors.bold(price_data['symbol'])} - LIVE MARKET DATA")
        print("="*60)
        
        last = price_data.get('last', 0)
        bid = price_data.get('bid', 0)
        ask = price_data.get('ask', 0)
        spread = price_data.get('spread', 0)
        atr = price_data.get('atr', 0)
        
        # Price display
        print(f"\n{'LAST PRICE:':<15} {Colors.green(f'${last:.2f}') if last > 0 else 'N/A'}")
        print(f"{'BID/ASK:':<15} ${bid:.2f} / ${ask:.2f}")
        print(f"{'SPREAD:':<15} ${spread:.4f}")
        
        # Daily range
        high = price_data.get('high', 0)
        low = price_data.get('low', 0)
        if high > 0 and low > 0:
            daily_range = high - low
            range_pct = (daily_range / low) * 100 if low > 0 else 0
            print(f"\n{'DAILY RANGE:':<15} ${low:.2f} - ${high:.2f}")
            print(f"{'RANGE SIZE:':<15} ${daily_range:.2f} ({range_pct:.1f}%)")
        
        # Volatility
        if atr > 0:
            atr_pct = (atr / last) * 100 if last > 0 else 0
            print(f"\n{'ATR (14-day):':<15} ${atr:.2f} ({atr_pct:.1f}%)")
        
        print("="*60)
        return last if last > 0 else (ask if ask > 0 else 0)
        
    def calculate_stop_loss(self, entry_price: float, stop_type: str = "percentage") -> float:
        """Calculate stop loss based on different methods"""
        print(f"\n🎯 Stop Loss Calculator (Entry: ${entry_price:.2f})")
        print("-"*40)
        print("1. Percentage-based (e.g., 2%, 5%)")
        print("2. ATR-based (1x, 1.5x, 2x ATR)")
        print("3. Fixed dollar amount")
        print("4. Support level (manual)")
        
        choice = input("\nSelect stop loss method (1-4): ").strip()
        
        if choice == "1":
            pct = float(input("Enter stop loss percentage (e.g., 2 for 2%): "))
            stop_price = entry_price * (1 - pct/100)
            print(f"\n📍 Stop Loss: ${stop_price:.2f} ({pct}% below entry)")
            
        elif choice == "2":
            symbol = input("Confirm symbol for ATR calculation: ").upper()
            atr = self.app.volatility_data.get(symbol, {}).get("atr", 0)
            if atr > 0:
                multiplier = float(input(f"ATR multiplier (ATR=${atr:.2f}): "))
                stop_price = entry_price - (atr * multiplier)
                print(f"\n📍 Stop Loss: ${stop_price:.2f} ({multiplier}x ATR)")
            else:
                print("⚠️  ATR not available, using 2% default")
                stop_price = entry_price * 0.98
                
        elif choice == "3":
            dollar_risk = float(input("Enter dollar risk per share: $"))
            stop_price = entry_price - dollar_risk
            pct_risk = (dollar_risk / entry_price) * 100
            print(f"\n📍 Stop Loss: ${stop_price:.2f} ({pct_risk:.1f}% risk)")
            
        else:
            stop_price = float(input("Enter stop loss price: $"))
            risk_pct = ((entry_price - stop_price) / entry_price) * 100
            print(f"\n📍 Stop Loss: ${stop_price:.2f} ({risk_pct:.1f}% below entry)")
            
        return stop_price
        
    def calculate_position_size(self, account_value: float, entry_price: float, stop_price: float) -> int:
        """Calculate position size based on risk management"""
        print(f"\n💰 Position Size Calculator")
        print("-"*40)
        print(f"Account Value: ${account_value:,.2f}")
        print(f"Entry Price: ${entry_price:.2f}")
        print(f"Stop Loss: ${stop_price:.2f}")
        
        risk_per_share = abs(entry_price - stop_price)
        print(f"Risk per Share: ${risk_per_share:.2f}")
        
        # Get risk percentage
        risk_pct = float(input("\nRisk % of account (e.g., 1 for 1%): "))
        dollar_risk = account_value * (risk_pct / 100)
        
        # Calculate shares
        shares = int(dollar_risk / risk_per_share)
        position_value = shares * entry_price
        position_pct = (position_value / account_value) * 100
        
        print(f"\n📊 POSITION SIZING RESULTS:")
        print(f"{'Risk Amount:':<20} ${dollar_risk:.2f}")
        print(f"{'Position Size:':<20} {shares} shares")
        print(f"{'Position Value:':<20} ${position_value:,.2f}")
        print(f"{'% of Account:':<20} {position_pct:.1f}%")
        print(f"{'Max Loss:':<20} ${shares * risk_per_share:.2f}")
        
        # R-Multiple targets
        print(f"\n🎯 R-MULTIPLE TARGETS:")
        for r in [1, 2, 3, 5]:
            target_price = entry_price + (risk_per_share * r)
            profit = shares * (target_price - entry_price)
            print(f"{r}R Target: ${target_price:.2f} (Profit: ${profit:,.2f})")
            
        return shares
        
    def place_smart_order(self):
        """Enhanced order placement with smart features"""
        if not self.connect():
            return
            
        try:
            print("\n" + "="*60)
            print(Colors.bold("📈 SMART ORDER PLACEMENT SYSTEM"))
            print("="*60)
            
            # Market selection
            print("\n📍 SELECT MARKET:")
            print("1. 🇦🇺 ASX (Australian Securities Exchange)")
            print("2. 🇺🇸 US Markets (NYSE/NASDAQ)")
            
            market_choice = input("\nEnter choice (1-2): ").strip()
            
            if market_choice == "1":
                exchange = "ASX"
                currency = "AUD"
                print(f"\n{Colors.cyan('🇦🇺 Trading on ASX')}")
            else:
                exchange = "SMART"
                currency = "USD"
                print(f"\n{Colors.blue('🇺🇸 Trading on US Markets')}")
                
            # Get symbol
            symbol = input("\nEnter stock symbol: ").upper()
            
            # Fetch live price
            price_data = self.get_live_price(symbol, exchange, currency)
            current_price = self.display_price_info(price_data)
            
            if current_price == 0:
                print("⚠️  Unable to fetch price. Enter manually or try again.")
                current_price = float(input("Enter current price manually: $"))
                
            # Order action
            print(f"\n📊 ORDER ACTION:")
            print("1. BUY (Long)")
            print("2. SELL (Short)")
            action_choice = input("\nEnter choice (1-2): ").strip()
            action = "BUY" if action_choice == "1" else "SELL"
            
            # Smart position sizing
            print(f"\n💡 POSITION SIZING:")
            print("1. Manual quantity")
            print("2. Risk-based calculator")
            print("3. Percentage of account")
            
            size_choice = input("\nEnter choice (1-3): ").strip()
            
            if size_choice == "2":
                # Get account value
                account_value = float(input("Enter account value: $"))
                
                # Calculate stop loss first
                stop_price = self.calculate_stop_loss(current_price)
                
                # Calculate position size
                quantity = self.calculate_position_size(account_value, current_price, stop_price)
                
            elif size_choice == "3":
                account_value = float(input("Enter account value: $"))
                pct_to_use = float(input("Percentage of account to use (e.g., 10): "))
                position_value = account_value * (pct_to_use / 100)
                quantity = int(position_value / current_price)
                print(f"\n📊 Position: {quantity} shares (${position_value:,.2f})")
                
            else:
                quantity = int(input("\nEnter quantity: "))
                
            # Order type selection with smart features
            print(f"\n📋 ORDER TYPE:")
            print("1. Market Order (Immediate)")
            print("2. Limit Order (Price Target)")
            print("3. Stop Loss Order (Risk Management)")
            print("4. Stop Limit Order")
            print("5. Trailing Stop (Dynamic)")
            print("6. Bracket Order (Complete Strategy)")
            print("7. One-Cancels-Other (OCO)")
            
            order_type = input("\nEnter choice (1-7): ").strip()
            
            # Create contract
            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"
            contract.exchange = exchange
            contract.currency = currency
            
            # Create order based on type
            if order_type == "1":  # Market Order
                order = self.create_market_order(action, quantity)
                print(f"\n✅ Placing MARKET order: {action} {quantity} {symbol}")
                
            elif order_type == "2":  # Limit Order
                print(f"\n💰 Current Price: ${current_price:.2f}")
                print("Suggested limit prices:")
                if action == "BUY":
                    print(f"  • Aggressive: ${current_price * 1.01:.2f}")
                    print(f"  • Mid: ${current_price * 0.995:.2f}")
                    print(f"  • Conservative: ${current_price * 0.98:.2f}")
                else:
                    print(f"  • Aggressive: ${current_price * 0.99:.2f}")
                    print(f"  • Mid: ${current_price * 1.005:.2f}")
                    print(f"  • Conservative: ${current_price * 1.02:.2f}")
                    
                limit_price = float(input("\nEnter limit price: $"))
                order = self.create_limit_order(action, quantity, limit_price)
                print(f"\n✅ Placing LIMIT order: {action} {quantity} {symbol} @ ${limit_price:.2f}")
                
            elif order_type == "3":  # Stop Loss
                if 'stop_price' not in locals():
                    stop_price = self.calculate_stop_loss(current_price)
                order = self.create_stop_order(action, quantity, stop_price)
                risk = abs(current_price - stop_price) * quantity
                print(f"\n✅ Placing STOP order: {action} {quantity} {symbol} @ ${stop_price:.2f}")
                print(f"   Max Risk: ${risk:.2f}")
                
            elif order_type == "5":  # Trailing Stop
                print(f"\n🎯 TRAILING STOP CONFIGURATION")
                print("1. Percentage trailing")
                print("2. Dollar amount trailing")
                trail_choice = input("\nEnter choice (1-2): ").strip()
                
                if trail_choice == "1":
                    trail_pct = float(input("Trail percentage (e.g., 5): "))
                    order = self.create_trailing_stop_percent(action, quantity, trail_pct)
                    print(f"\n✅ Placing TRAILING STOP: {trail_pct}% trail")
                else:
                    trail_amt = float(input("Trail amount in dollars: $"))
                    order = self.create_trailing_stop_amount(action, quantity, trail_amt)
                    print(f"\n✅ Placing TRAILING STOP: ${trail_amt:.2f} trail")
                    
            elif order_type == "6":  # Bracket Order
                print(f"\n🎯 BRACKET ORDER SETUP")
                print(f"Current Price: ${current_price:.2f}")
                
                # Entry
                entry_price = float(input("Entry limit price (or 0 for market): $") or 0)
                
                # Stop Loss
                stop_price = self.calculate_stop_loss(entry_price if entry_price > 0 else current_price)
                
                # Take Profit
                risk = abs((entry_price if entry_price > 0 else current_price) - stop_price)
                print(f"\n🎯 TAKE PROFIT TARGETS:")
                print(f"  • 1:1 R/R: ${current_price + risk:.2f}")
                print(f"  • 1:2 R/R: ${current_price + (risk * 2):.2f}")
                print(f"  • 1:3 R/R: ${current_price + (risk * 3):.2f}")
                
                profit_price = float(input("\nTake profit price: $"))
                
                parent_order, stop_order, profit_order = self.create_bracket_order(
                    action, quantity, entry_price, stop_price, profit_price
                )
                
                print(f"\n✅ Placing BRACKET ORDER:")
                print(f"   Entry: {'Market' if entry_price == 0 else f'${entry_price:.2f}'}")
                print(f"   Stop: ${stop_price:.2f}")
                print(f"   Target: ${profit_price:.2f}")
                
                # Place bracket order
                self.app.placeOrder(self.app.nextOrderId, contract, parent_order)
                self.app.placeOrder(self.app.nextOrderId + 1, contract, stop_order)
                self.app.placeOrder(self.app.nextOrderId + 2, contract, profit_order)
                
                time.sleep(3)
                print("✅ Bracket order placed successfully!")
                return
                
            else:  # Default to market order
                order = self.create_market_order(action, quantity)
                
            # Place the order
            self.app.placeOrder(self.app.nextOrderId, contract, order)
            
            # Wait for order status
            time.sleep(3)
            
            # Display order status
            if self.app.nextOrderId - 1 in self.app.order_statuses:
                status = self.app.order_statuses[self.app.nextOrderId - 1]
                print(f"\n📊 ORDER STATUS:")
                print(f"   Status: {status['status']}")
                print(f"   Filled: {status['filled']}")
                print(f"   Remaining: {status['remaining']}")
                if status['filled'] > 0:
                    print(f"   Avg Fill: ${status['avgFillPrice']:.2f}")
                    
            print("\n✅ Order placement complete!")
            
        finally:
            self.disconnect()
            
    def create_market_order(self, action: str, quantity: int) -> Order:
        """Create a market order"""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "MKT"
        order.tif = "DAY"
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        return order
        
    def create_limit_order(self, action: str, quantity: int, limit_price: float) -> Order:
        """Create a limit order"""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "LMT"
        order.lmtPrice = limit_price
        order.tif = "DAY"
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        return order
        
    def create_stop_order(self, action: str, quantity: int, stop_price: float) -> Order:
        """Create a stop loss order"""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "STP"
        order.auxPrice = stop_price
        order.tif = "DAY"
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        return order
        
    def create_trailing_stop_percent(self, action: str, quantity: int, trail_percent: float) -> Order:
        """Create a trailing stop order with percentage"""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "TRAIL"
        order.trailingPercent = trail_percent
        order.tif = "DAY"
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        return order
        
    def create_trailing_stop_amount(self, action: str, quantity: int, trail_amount: float) -> Order:
        """Create a trailing stop order with dollar amount"""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "TRAIL"
        order.auxPrice = trail_amount
        order.tif = "DAY"
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        return order
        
    def create_bracket_order(self, action: str, quantity: int, 
                           entry_price: float, stop_price: float, 
                           profit_price: float) -> Tuple[Order, Order, Order]:
        """Create a bracket order (entry + stop + profit)"""
        
        # Parent order (entry)
        parent = Order()
        parent.action = action
        parent.totalQuantity = quantity
        parent.orderType = "LMT" if entry_price > 0 else "MKT"
        if entry_price > 0:
            parent.lmtPrice = entry_price
        parent.tif = "DAY"
        parent.transmit = False
        parent.eTradeOnly = False
        parent.firmQuoteOnly = False
        
        # Stop loss order
        stop = Order()
        stop.action = "SELL" if action == "BUY" else "BUY"
        stop.totalQuantity = quantity
        stop.orderType = "STP"
        stop.auxPrice = stop_price
        stop.parentId = self.app.nextOrderId
        stop.tif = "DAY"
        stop.transmit = False
        stop.eTradeOnly = False
        stop.firmQuoteOnly = False
        
        # Take profit order
        profit = Order()
        profit.action = "SELL" if action == "BUY" else "BUY"
        profit.totalQuantity = quantity
        profit.orderType = "LMT"
        profit.lmtPrice = profit_price
        profit.parentId = self.app.nextOrderId
        profit.tif = "DAY"
        profit.transmit = True
        profit.eTradeOnly = False
        profit.firmQuoteOnly = False
        
        return parent, stop, profit
        
    def scan_momentum_stocks(self):
        """Scan for momentum stocks"""
        if not self.connect():
            return
            
        try:
            print("\n" + "="*60)
            print(Colors.bold("🚀 MOMENTUM STOCK SCANNER"))
            print("="*60)
            
            print("\n📊 SCAN TYPE:")
            print("1. Top Gainers (Day)")
            print("2. Volume Breakouts")
            print("3. New Highs")
            print("4. Gap Ups")
            print("5. Unusual Options Activity")
            
            scan_choice = input("\nEnter choice (1-5): ").strip()
            
            # Predefined momentum stocks for demo
            momentum_stocks = {
                "1": ["NVDA", "AMD", "TSLA", "AAPL", "MSFT"],
                "2": ["GME", "AMC", "BBBY", "SOFI", "PLTR"],
                "3": ["SPY", "QQQ", "META", "GOOGL", "AMZN"],
                "4": ["COIN", "MARA", "RIOT", "SQ", "PYPL"],
                "5": ["NFLX", "DIS", "BA", "UBER", "LYFT"]
            }
            
            stocks = momentum_stocks.get(scan_choice, momentum_stocks["1"])
            
            print(f"\n📈 Scanning {len(stocks)} stocks...")
            results = []
            
            for symbol in stocks:
                price_data = self.get_live_price(symbol)
                if price_data['last'] > 0:
                    # Calculate momentum metrics
                    change = price_data['last'] - price_data.get('close', price_data['last'])
                    change_pct = (change / price_data.get('close', price_data['last'])) * 100 if price_data.get('close') else 0
                    
                    results.append({
                        'symbol': symbol,
                        'price': price_data['last'],
                        'change': change,
                        'change_pct': change_pct,
                        'volume': price_data.get('total_volume', 0),
                        'atr': price_data.get('atr', 0)
                    })
                    
            # Sort by change percentage
            results.sort(key=lambda x: x['change_pct'], reverse=True)
            
            # Display results
            print("\n" + "="*60)
            print(f"{'Symbol':<10} {'Price':<10} {'Change':<10} {'Volume':<15} {'ATR':<10}")
            print("-"*60)
            
            for stock in results[:10]:
                color_func = Colors.green if stock['change_pct'] > 0 else Colors.red
                change_str = color_func(f"{stock['change_pct']:+.2f}%")
                print(f"{stock['symbol']:<10} "
                      f"${stock['price']:<9.2f} "
                      f"{change_str:<20} "
                      f"{stock['volume']:<15,} "
                      f"${stock['atr']:<9.2f}")
                      
        finally:
            self.disconnect()

def main_menu():
    """Enhanced main menu with professional features"""
    while True:
        print("\n" + "="*70)
        print(Colors.bold("🚀 IB TWS PROFESSIONAL MOMENTUM TRADING SYSTEM"))
        print("="*70)
        
        print(f"\n{Colors.cyan('📊 MARKET ANALYSIS:')}")
        print("1. Get Live Price & Volatility Data")
        print("2. Momentum Stock Scanner")
        print("3. Account Info & Positions")
        
        print(f"\n{Colors.green('📈 SMART ORDER PLACEMENT:')}")
        print("4. Smart Order System (with calculators)")
        print("5. Risk-Based Position Calculator")
        
        print(f"\n{Colors.yellow('📋 ORDER MANAGEMENT:')}")
        print("6. View Open Orders")
        print("7. Modify/Cancel Orders")
        
        print(f"\n{Colors.blue('⚙️  UTILITIES:')}")
        print("8. Connection Test")
        print("9. Switch Trading Mode (Paper/Live)")
        
        print("\n0. Exit")
        
        choice = input(f"\n{Colors.bold('Enter choice (0-9):')} ").strip()
        
        if choice == "0":
            print(f"\n{Colors.green('👋 Thank you for using Momentum Trading System!')}")
            break
            
        elif choice == "1":
            trader = MomentumTrader()
            if trader.connect():
                symbol = input("\nEnter symbol: ").upper()
                price_data = trader.get_live_price(symbol)
                trader.display_price_info(price_data)
                trader.disconnect()
                
        elif choice == "2":
            trader = MomentumTrader()
            trader.scan_momentum_stocks()
            
        elif choice == "4":
            trader = MomentumTrader()
            trader.place_smart_order()
            
        elif choice == "8":
            trader = MomentumTrader()
            if trader.connect():
                print("✅ Connection successful!")
                trader.disconnect()
                
        input(f"\n{Colors.cyan('Press Enter to continue...')}")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.yellow('⚠️  Program interrupted by user')}")
    except Exception as e:
        print(f"\n{Colors.red(f'❌ Error: {e}')}")
    finally:
        cleanup_all_connections()