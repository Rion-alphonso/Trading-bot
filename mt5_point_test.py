import MetaTrader5 as mt5

mt5.initialize()
symbol_info = mt5.symbol_info("XAUUSDm")
if symbol_info:
    print("Point:", symbol_info.point)
    print("Contract Size:", symbol_info.trade_contract_size)
    print("Digits:", symbol_info.digits)
else:
    print("Symbol not found")
mt5.shutdown()
