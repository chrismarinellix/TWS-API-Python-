# A0 Connect Module - IB TWS API Connection & Trading Module

## IMPORTANT: CODE MODIFICATION POLICY
**⚠️ CRITICAL: When modifying this code, ONLY make the specific changes requested. Do not add, remove, or modify ANY other code, comments, features, or functionality unless explicitly instructed. This ensures stability and prevents unintended side effects.**

## Overview
The A0 Connect Module is a comprehensive Python module for connecting to Interactive Brokers TWS/IB Gateway API. It provides core functionality for establishing connections, retrieving market data, managing orders, and accessing account information. This module serves as a foundation that can be imported and used by other trading modules.

## Key Features
- **Safe connection management** with automatic client ID generation to prevent conflicts
- **Automatic connection cleanup** to prevent IB Gateway crashes
- Connection management for both live and paper trading accounts
- Market data retrieval (delayed 15-minute data by default, no subscription required)
- Order placement and management (market & limit orders)
- Account information and position tracking
- Pending order monitoring across multiple accounts
- Error handling with categorized message types
- **Built-in protection against multiple connection issues**

## Module Structure

### Connection Safety Features

#### Global Connection Management
- **`active_connections`**: List tracking all active connections
- **`cleanup_all_connections()`**: Ensures all connections are closed on exit
- **`get_unique_client_id()`**: Generates random client IDs (1000-9999) to prevent conflicts
- **Automatic cleanup**: Registered with `atexit` to close connections on script termination

### Core Classes

#### 1. `TradingApp(EWrapper, EClient)`
Basic connection class with safe connection methods.
- **Key Methods**:
  - `connect_safely()`: Safe connection with unique client ID
  - `disconnect_safely()`: Proper disconnection with cleanup delay

#### 2. `TradingBot(EClient, EWrapper)`
Full-featured trading class with comprehensive callback handlers.
- **Enhanced with safe connection methods**
- **Key Attributes**:
  - `nextOrderId`: Tracks the next valid order ID from IB
  - `accounts`: List of available trading accounts
  - `market_data`: Dictionary storing real-time market data
  - `positions`: Current positions by symbol
  - `account_values`: Account summary values
  - `open_orders`: List of open orders

### Important Callback Methods

#### Connection & Order Management
- `nextValidId(orderId)`: Receives next valid order ID from IB (line 28)
- `error(reqId, errorCode, errorString)`: Handles all error messages with categorization (lines 32-46)
- `orderStatus()`: Tracks order execution status (line 48)
- `openOrder()`: Receives open order details (line 51)
- `execDetails()`: Execution confirmation details (line 65)

#### Market Data
- `tickPrice()`: Price updates (delayed 15-min by default) (line 68)
- `tickSize()`: Volume/size updates (line 77)
- `contractDetails()`: Contract specifications (line 114)

#### Account Information
- `managedAccounts()`: Available accounts list (line 89)
- `accountSummary()`: Account values (line 93)
- `position()`: Current positions (line 102)

### Helper Functions

#### `create_clean_order(action, quantity, order_type, limit_price=None)`
**Location**: Lines 127-142
**Purpose**: Creates properly formatted orders avoiding problematic IB API attributes
**Parameters**:
- `action`: "BUY" or "SELL"
- `quantity`: Number of shares (integer)
- `order_type`: "MKT" or "LMT"
- `limit_price`: Required for limit orders (float)

**Returns**: Configured Order object ready for submission

## Port Configuration
- **Port 4001**: Live trading account
- **Port 4002**: Paper trading account (default in module)
- Current default: `port = 4002` (line 15)

## How to Import and Use in Other Modules

### Basic Import (UPDATED for Safe Connections)
```python
# Import the module
from A0_Connect_Module import TradingBot, create_clean_order, get_unique_client_id
import threading
import time

# Create instance
app = TradingBot()

# SAFE CONNECTION METHOD (Recommended)
if app.connect_safely("127.0.0.1", 4002):  # Auto-generates unique client ID
    print("Connected successfully!")
    
    # Start the API thread
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    
    # Wait for connection
    time.sleep(2)
    
    # Your code here...
    
    # Always disconnect safely
    app.disconnect_safely()

# Alternative with manual client ID
client_id = get_unique_client_id()
if app.connect_safely("127.0.0.1", 4002, client_id):
    # ... your code ...
    app.disconnect_safely()
```

### Placing Orders
```python
from ibapi.contract import Contract

# Create contract
contract = Contract()
contract.symbol = "AAPL"
contract.secType = "STK"
contract.exchange = "SMART"
contract.currency = "USD"

# Create order using helper function
order = create_clean_order("BUY", 100, "LMT", 150.00)

# Place order
app.placeOrder(app.nextOrderId, contract, order)
```

### Retrieving Market Data
```python
# Set up contract
contract = Contract()
contract.symbol = "TSLA"
contract.secType = "STK"
contract.exchange = "SMART"
contract.currency = "USD"

# Request delayed market data (15-minute delay, no subscription required)
app.reqMarketDataType(3)  # Type 3 = delayed data

# Request market data
reqId = 1001
app.market_data[reqId] = {"symbol": "TSLA"}
app.reqMktData(reqId, contract, "", False, False, [])

# Data will be received in tickPrice/tickSize callbacks
# Access data from app.market_data dictionary
```

### Checking Account Information
```python
# Request account summary
app.reqAccountSummary(9001, "All", 
    "NetLiquidation,TotalCashValue,BuyingPower")

# Request positions
app.reqPositions()

# Data will be stored in:
# - app.account_values (account summary)
# - app.positions (current positions)
```

### Monitoring Open Orders
```python
# Clear existing orders list
app.open_orders = []

# Request all open orders
app.reqAllOpenOrders()

# Also get orders from other clients
app.reqAutoOpenOrders(True)

# Wait for data
time.sleep(5)

# Access orders
for order in app.open_orders:
    print(f"Order {order['orderId']}: {order['symbol']}")
```

## Integration Examples

### Example 1: Creating a Price Monitor Module
```python
from A0_Connect_Module import TradingBot
import threading
import time

class PriceMonitor:
    def __init__(self, symbols, port=4002):
        self.app = TradingBot()
        self.symbols = symbols
        self.port = port
        
    def start_monitoring(self):
        self.app.connect("127.0.0.1", self.port, clientId=2000)
        
        api_thread = threading.Thread(target=self.app.run, daemon=True)
        api_thread.start()
        
        time.sleep(2)
        
        # Request data for each symbol
        for i, symbol in enumerate(self.symbols):
            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            
            reqId = 1000 + i
            self.app.market_data[reqId] = {"symbol": symbol}
            self.app.reqMktData(reqId, contract, "", False, False, [])
    
    def get_prices(self):
        return self.app.market_data
```

### Example 2: Order Management Module
```python
from A0_Connect_Module import TradingBot, create_clean_order
from ibapi.contract import Contract

class OrderManager:
    def __init__(self, port=4002):
        self.app = TradingBot()
        self.port = port
        self.connected = False
        
    def connect(self):
        self.app.connect("127.0.0.1", self.port, clientId=3000)
        # ... (threading setup)
        self.connected = True
    
    def place_stock_order(self, symbol, action, quantity, order_type, price=None):
        if not self.connected:
            self.connect()
            
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        
        order = create_clean_order(action, quantity, order_type, price)
        
        self.app.placeOrder(self.app.nextOrderId, contract, order)
        return self.app.nextOrderId
```

## Key Functions Available for Integration

### Standalone Functions (can be called directly)
1. `run_connection_test()` - Basic connection verification
2. `get_stock_info()` - Interactive stock data retrieval (delayed 15-min data)
3. `get_account_info()` - Account summary and positions
4. `check_open_orders()` - Check orders on current port
5. `check_pending_orders_all_accounts()` - Check orders across accounts
6. `paper_trade_order()` - Interactive paper order placement
7. `place_live_order()` - Interactive live order placement

### Using Standalone Functions
```python
# Import and use directly
from A0_Connect_Module import get_account_info, check_pending_orders_all_accounts

# These functions handle their own connection management
get_account_info()  # Will connect, retrieve, and disconnect
check_pending_orders_all_accounts()  # Interactive account selection
```

## Error Handling
The module categorizes errors into:
- **Info codes** (2104, 2106, 2107, 2108, 2119, 2158): Informational messages
- **Warning codes** (10268, 2102, 2103, 2110): Non-critical warnings
- **Errors**: All other codes are treated as actual errors

Access error handling through the `error()` callback method.

## Thread Safety
- All IB API callbacks run on a separate thread
- Use threading locks when accessing shared data from multiple threads
- The module uses daemon threads for API communication

## Connection Requirements
1. IB Gateway or TWS must be running
2. API connections must be enabled in IB Gateway/TWS settings
3. Correct port must be configured (4001 for live, 4002 for paper)
4. ~~Client ID must be unique for each connection~~ **Module handles this automatically!**

## Preventing IB Gateway Crashes

The module now includes several features to prevent IB Gateway from closing:

### 1. Automatic Client ID Management
- Uses `get_unique_client_id()` to generate random IDs (1000-9999)
- Prevents client ID conflicts that can crash the gateway
- No need to manually track client IDs

### 2. Safe Connection/Disconnection
- `connect_safely()`: Manages connection with error handling
- `disconnect_safely()`: Ensures proper cleanup with 1-second delay
- Prevents rapid connect/disconnect cycles

### 3. Global Connection Tracking
- All connections are tracked in `active_connections` list
- Automatic cleanup on script exit via `atexit`
- Prevents orphaned connections

### 4. Connection Delays
- Built-in delays between operations
- 2-second wait between different account checks
- Prevents overwhelming the gateway

### Example of Safe Usage:
```python
from A0_Connect_Module import TradingBot

# Multiple sequential connections (safe)
for i in range(3):
    app = TradingBot()
    if app.connect_safely():  # Auto client ID
        # Do work...
        app.disconnect_safely()  # Includes delay
    # Module ensures cleanup between iterations
```

## Common Integration Patterns

### Pattern 1: Singleton Connection
```python
class IBConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.app = TradingBot()
            # Initialize connection
        return cls._instance
```

### Pattern 2: Context Manager
```python
class ManagedIBConnection:
    def __enter__(self):
        self.app = TradingBot()
        self.app.connect("127.0.0.1", 4002, clientId=5000)
        # Setup thread
        return self.app
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.app.isConnected():
            self.app.disconnect()
```

## Best Practices for Integration
1. **Always use `connect_safely()` and `disconnect_safely()`** instead of direct connect/disconnect
2. Always check `app.nextOrderId` is not None before placing orders
3. ~~Use unique client IDs~~ Let the module generate client IDs automatically
4. Implement proper cleanup with `disconnect_safely()` when done
5. Allow sufficient sleep time after requests for data to arrive (2+ seconds recommended)
6. Store and reuse connection instances when possible
7. Handle connection errors gracefully with try/finally blocks
8. Use the `create_clean_order()` helper to avoid order attribute issues
9. **Avoid rapid sequential connections** - add delays if needed
10. **Use try/finally blocks** to ensure disconnection:
```python
app = TradingBot()
try:
    if app.connect_safely():
        # Your code here
        pass
finally:
    app.disconnect_safely()
```

## Module Dependencies
```python
from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.tag_value import TagValue
import threading
import time
```

Ensure these are installed via:
```bash
pip install ibapi
```

## Market Data Types
- **Type 1**: Real-time streaming data (requires subscription)
- **Type 2**: Frozen data (last data recorded at market close)
- **Type 3**: Delayed data (15-minute delay, no subscription required) - **DEFAULT**
- **Type 4**: Delayed-frozen data

The module now uses Type 3 (delayed data) by default in `get_stock_info()` to avoid subscription requirements.

## Version & Compatibility
- Compatible with IB API 9.81+
- Python 3.6+
- Tested with IB Gateway and TWS