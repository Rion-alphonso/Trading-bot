import MetaTrader5 as mt5

if not mt5.initialize():
    print("MT5 init failed")
    quit()

targets = ["EURUSD", "EURGBP", "EURJPY", "XAG", "XTI", "USOIL", "XAU"]

print("Found matching symbols in Exness:")
for t in targets:
    syms = mt5.symbols_get("*" + t + "*")
    if syms:
        for s in syms:
            print(f"- {s.name} ({s.description})")
    else:
        print(f"- No match for {t}")

mt5.shutdown()
