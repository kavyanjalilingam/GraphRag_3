import os
import shutil

def main():
    pilot_tickers = ["AMGN", "CAT", "CSCO", "COP", "DIS"]
    for ticker in pilot_tickers:
        src = os.path.join("artifacts", ticker, "auditor.json")
        dst = os.path.join("fixtures", ticker, "auditor.json")
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"Copied {ticker} auditor fixture.")

if __name__ == "__main__":
    main()
