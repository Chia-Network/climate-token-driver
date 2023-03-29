from pathlib import Path
import sys
import traceback

print(f"{__file__=}", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))


def seh(excType, excValue, tracebackobj):
    traceback.print_exception(excType, excValue, tracebackobj, file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))

sys.excepthook = seh
