# 🚀 IB TWS Professional Momentum Trading System

## Overview
The **A0 Connect Module Pro** is an advanced trading system built on top of the Interactive Brokers TWS API, specifically designed for momentum traders who need real-time data, smart order management, and professional risk controls.

## ✨ Key Features

### 📊 Real-Time Market Data
- **Live Price Fetching**: Automatically retrieves current bid/ask/last prices before every order
- **Spread Analysis**: Shows bid-ask spread for better entry decisions
- **Volatility Metrics**: Calculates 14-day ATR (Average True Range) for volatility-based decisions
- **Daily Range**: Displays high/low range with percentage movements

### 🎯 Smart Stop Loss Calculator
Choose from multiple stop loss methods:
- **Percentage-Based**: Set stops at specific percentages (e.g., 2%, 5%)
- **ATR-Based**: Use volatility multiples (1x, 1.5x, 2x ATR)
- **Dollar Amount**: Fixed dollar risk per share
- **Support Level**: Manual entry for technical analysis levels

### 💰 Professional Position Sizing
- **Risk-Based Calculator**: Size positions based on account risk percentage
- **R-Multiple Targets**: Automatically calculates 1R, 2R, 3R, 5R profit targets
- **Position Analytics**: Shows position value as % of account
- **Max Loss Display**: Clear view of maximum potential loss

### 📈 Advanced Order Types
- **Market Orders**: Immediate execution
- **Limit Orders**: With smart price suggestions
- **Stop Loss Orders**: With automatic calculation
- **Trailing Stops**: Percentage or dollar-based
- **Bracket Orders**: Complete entry + stop + profit in one order
- **OCO Orders**: One-Cancels-Other for multiple scenarios

### 🚀 Momentum Trading Features
- **Stock Scanner**: Find top gainers, volume breakouts, new highs
- **Gap Scanner**: Identify gap-up opportunities
- **Volume Analysis**: Track unusual volume activity
- **Color-Coded Display**: Green for gains, red for losses

## 📋 Installation

1. Ensure you have IB Gateway or TWS running
2. Enable API connections in IB Gateway/TWS settings
3. Install required dependencies:
```bash
pip install ibapi
```

## 🎮 Usage

### Basic Usage
```bash
python3 A0_Connect_Module_Pro.py
```

### Main Menu Options

#### 1. Get Live Price & Volatility Data
- Enter any symbol to get real-time pricing
- Shows bid/ask/last/spread
- Displays daily range and ATR
- Color-coded price movements

#### 2. Momentum Stock Scanner
- Scan for top daily gainers
- Find volume breakouts
- Identify new highs
- Track gap-up stocks

#### 4. Smart Order System
Complete order workflow with:
1. **Market Selection**: ASX or US markets
2. **Live Price Fetch**: Automatic current price retrieval
3. **Position Sizing**: Manual, risk-based, or percentage of account
4. **Stop Loss Calculation**: Multiple methods with suggestions
5. **Order Type Selection**: All professional order types
6. **Risk Display**: Shows maximum risk before execution

#### 5. Risk-Based Position Calculator
- Enter account value
- Set risk percentage
- Calculate optimal position size
- View R-multiple profit targets

## 💡 Example Workflow

### Placing a Momentum Trade
1. Select "Smart Order System" (Option 4)
2. Choose your market (ASX or US)
3. Enter symbol (e.g., "TSLA")
4. System fetches live price automatically
5. Choose BUY or SELL
6. Select position sizing method:
   - Risk-based calculator (recommended)
   - Enter account value and risk %
7. System calculates stop loss options
8. Choose order type (bracket order for complete strategy)
9. Review risk metrics
10. Confirm order placement

### Example Output
```
📊 TSLA - LIVE MARKET DATA
============================================================
LAST PRICE:     $245.67
BID/ASK:        $245.65 / $245.69
SPREAD:         $0.04

DAILY RANGE:    $242.30 - $248.90
RANGE SIZE:     $6.60 (2.7%)

ATR (14-day):   $8.45 (3.4%)
============================================================

💰 Position Size Calculator
--------------------------------------------
Account Value: $100,000.00
Entry Price: $245.67
Stop Loss: $240.00
Risk per Share: $5.67

📊 POSITION SIZING RESULTS:
Risk Amount:         $1,000.00
Position Size:       176 shares
Position Value:      $43,237.92
% of Account:        43.2%
Max Loss:           $998.32

🎯 R-MULTIPLE TARGETS:
1R Target: $251.34 (Profit: $998.32)
2R Target: $257.01 (Profit: $1,996.64)
3R Target: $262.68 (Profit: $2,994.96)
5R Target: $274.02 (Profit: $4,991.60)
```

## ⚙️ Configuration

### Port Settings
- **Paper Trading**: Port 4002 (default)
- **Live Trading**: Port 4001

To switch between paper and live:
```python
PAPER_PORT = 4002  # Paper trading
LIVE_PORT = 4001   # Live trading
```

### Market Data Types
The system uses delayed data (15-minute) by default. To use real-time data (requires subscription):
```python
app.reqMarketDataType(1)  # Real-time (requires subscription)
app.reqMarketDataType(3)  # Delayed (default, no subscription)
```

## 🛡️ Risk Management

### Built-in Safety Features
- **Stop Loss Required**: System prompts for stop loss on every trade
- **Position Size Limits**: Based on account risk percentage
- **Max Loss Display**: Always shows maximum potential loss
- **Order Confirmation**: Review all parameters before execution

### Best Practices
1. Always use stop losses
2. Risk only 1-2% per trade
3. Use bracket orders for complete strategy
4. Review R-multiples before entry
5. Check spread before market orders

## 🎨 UI Features

### Color Coding
- 🟢 **Green**: Positive changes, profits
- 🔴 **Red**: Negative changes, losses
- 🔵 **Blue**: US market indicators
- 🟡 **Yellow**: Warnings, important info
- 🔷 **Cyan**: ASX market indicators

### Smart Formatting
- Clear section dividers
- Aligned columns for easy reading
- Bold headers for navigation
- Emoji indicators for quick recognition

## 📊 Technical Indicators

### ATR (Average True Range)
- 14-day period by default
- Used for volatility-based stops
- Displayed as dollar amount and percentage

### Price Spreads
- Real-time bid-ask spread
- Helps identify liquidity
- Important for limit order placement

## 🔧 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure IB Gateway/TWS is running
   - Check API settings are enabled
   - Verify correct port (4002 for paper, 4001 for live)

2. **No Price Data**
   - Symbol may not be available
   - Market may be closed
   - Try different exchange (ASX vs SMART)

3. **Order Rejected**
   - Check account permissions
   - Verify market hours
   - Ensure sufficient buying power

## 📈 Advanced Features

### Bracket Order Example
```
Entry: Market or Limit
Stop: $240.00 (2% below entry)
Target: $255.00 (2:1 risk/reward)
```

### Trailing Stop Configuration
- Percentage: Trails by X% from high
- Dollar: Trails by fixed dollar amount
- Adjusts automatically as price moves

## 🚀 Future Enhancements
- [ ] Options trading support
- [ ] Multi-timeframe analysis
- [ ] Automated scanning alerts
- [ ] Portfolio analytics
- [ ] Trade journal integration
- [ ] Custom indicators
- [ ] Backtesting capabilities

## 📝 License
This software is provided as-is for educational purposes. Trading involves risk. Always do your own research.

## 💬 Support
For issues or questions, please open an issue on GitHub.

---
**Version**: 1.0.0  
**Author**: Momentum Trader Pro  
**Built with**: Interactive Brokers API v9.81+