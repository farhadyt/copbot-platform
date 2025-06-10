# Shadow Agent Configuration Guide

## For Maximum Transaction Detection

### 1. **Scan Frequency** ✅
- **Set to:** `Maximum Fast`
- This is the MOST IMPORTANT setting for detecting all transactions
- Maximum Fast = Real-time monitoring with no delays

### 2. **Active Days** ✅
- **Select:** All 7 days (Monday through Sunday)
- This ensures 24/7 monitoring without interruption

### 3. **Active Hours** ✅
- **Start:** `00:00`
- **End:** `23:59`
- This covers the entire day

### 4. **Transaction Limits** (Optional)
- **Max Transactions/Hour:** Leave empty (unlimited)
- **Max Transactions/Day:** Leave empty (unlimited)
- Only set these if you want to limit the number of transactions

### 5. **Value Filters**
- **Min Transaction Value:** `1.00` USD (default)
- **Max Transaction Value:** Leave empty (no maximum)
- **Min Wallet Balance:** Leave empty (no minimum)

### 6. **Token Filters** ✅
- **Filter Type:** Select `All Tokens`
- This will track ALL token transactions
- Only use "Exclude" or "Include" if you want specific tokens

### 7. **Database Retention**
- **Keep for:** `10` days (default)
- Increase if you want longer history

## Quick Setup for Maximum Detection:

1. **Name:** Leave empty (auto-generates as Shadow-1, Shadow-2, etc.)
2. **Scan Frequency:** `Maximum Fast`
3. **Active Days:** Check all boxes ✅
4. **Active Hours:** `00:00` to `23:59`
5. **Token Filter:** `All Tokens`
6. Leave all other fields at default

## After Creating:
- The agent will automatically start monitoring
- Check the green status indicator
- View transactions by clicking the agent name or 📊 icon

## Troubleshooting:
- If no transactions appear, check the connection status
- Make sure the agent shows "Active" status
- The monitoring indicator should be green and pulsing 