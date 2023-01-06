#@category Examples.Python

from ghidra.app.plugin.core.colorizer import ColorizingService
from ghidra.app.script import GhidraScript
from ghidra.program.model.address import Address
from ghidra.program.model.address import AddressSet
from ghidra.program.model.symbol import SymbolTable

from java.awt import Color
import json

symbol_table = currentProgram.getSymbolTable()
main_symbol = list(symbol_table.getSymbols("main"))[0]
main_addr = main_symbol.getAddress()


service = state.getTool().getService(ColorizingService)
if service is None:
     print "Can't find ColorizingService service"

location = currentProgram.getExecutablePath()
json_file = location + ".json"
labels = json.load(open(json_file))
base = 0x100000
addresses = AddressSet()
for name, arr in labels.items():
    for addr in arr:
        addresses.add(main_addr.getNewAddress(base + addr))
setBackgroundColor(addresses, Color.YELLOW)

