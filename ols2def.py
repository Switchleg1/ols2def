import csv
import re
import uuid

from xdfwrite import XDFWrite
from xmlwrite import XMLWrite
from os import path
from sys import argv

#globals

try:
    DEF_BASE_OFFSET = int(argv[3].lstrip("0x"), base=16)
except:
    DEF_BASE_OFFSET = 0
try:
    DEF_BIN_OFFSET = int(argv[4].lstrip("0x"), base=16)
except:
    DEF_BIN_OFFSET = 0
DEF_CATEGORY_OFFSET = 0x0
DEF_TITLE = argv[5]

data_sizes = {
    "eByte": 1,
    "eBitHiLo": 2,
    "eBitLoHi": 2,
    "eFloatHiLo": 4,
    "eFloatLoHi": 4,
    "eHiLo": 2,
    "eLoHi": 2,
    "eHiLoHiLo": 4,
    "eLoHiLoHi": 4,
    "eDataOrgNone": 1,
}

data_endian = {
    "eByte": 0,
    "eBitHiLo": 0,
    "eBitLoHi": 2,
    "eFloatHiLo": 0,
    "eFloatLoHi": 2,
    "eHiLo": 0,
    "eLoHi": 2,
    "eHiLoHiLo": 0,
    "eLoHiLoHi": 2,
    "eDataOrgNone": 0,
}

# Begin

xdfOut = XDFWrite(DEF_BASE_OFFSET, DEF_BIN_OFFSET, DEF_CATEGORY_OFFSET, DEF_TITLE)
xmlOut = XMLWrite(DEF_BASE_OFFSET, DEF_BIN_OFFSET, DEF_CATEGORY_OFFSET, DEF_TITLE)
xdfOut.add_category("OLS")
#parse ols csv
with open(argv[1], encoding="utf-8-sig", errors='ignore') as olsFile:
    csvReader = csv.DictReader(olsFile, delimiter=';')
    for csv in csvReader:
        #build table
        category = csv["FolderName"][:csv["FolderName"].find(":")]
        xdfOut.add_category(category)

        print("  Table Name: " + csv["IdName"])
        print("    Offset: " + hex(int(csv["Fieldvalues.StartAddr"].lstrip("$"), base=16)))
        print("    Datasize: " + str(data_sizes[csv["DataOrg"]]))
        print("    Category: " + category)

        #build table data
        offset = float(csv["Fieldvalues.Offset"])
        negative = False if offset >= 0.0 else True
        offset = abs(offset)
        table_def = {
            "title": csv["IdName"],
            "description": csv["Name"],
            "category": ["OLS", category],
            "z": {
                "min": "",
                "max": "",
                "address": hex(int(csv["Fieldvalues.StartAddr"].lstrip("$"), base=16)),
                "dataSize": data_sizes[csv["DataOrg"]],
                "signed": False if csv["bSigned"] == "0" else True,
                "units": xdfOut.fix_degree(csv["Fieldvalues.Unit"]),
                "math": "X * " + str(float(csv["Fieldvalues.Factor"])) + str(" - " if negative else " + ") + str(offset),
                "order": "cr",
                "flags": hex(data_endian[csv["DataOrg"]] + (0 if csv["bSigned"] == "0" else 1)),
                "columns": csv["Columns"]
            },
        }

        if csv["AxisX.DataAddr"].lstrip("$") != "0" or int(csv["Columns"]) > 1:
            offset = float(csv["AxisX.Offset"])
            negative = False if offset >= 0.0 else True
            offset = abs(offset)
            table_def["x"] = {
                "name": "x",
                "units": xdfOut.fix_degree(csv["AxisX.Unit"]),
                "min": "",
                "max": "",
                "address": hex(int(csv["AxisX.DataAddr"].lstrip("$"), base=16)),
                "length": csv["Columns"],
                "dataSize": data_sizes[csv["AxisX.DataOrg"]],
                "signed": False if csv["AxisX.bSigned"] == "0" else True,
                "math": "X * " + str(float(csv["AxisX.Factor"])) + str(" - " if negative else " + ") + str(offset),
                "flags": hex(data_endian[csv["AxisX.DataOrg"]] + (0 if csv["AxisX.bSigned"] == "0" else 1))
            }
            table_def["z"]["length"] = table_def["x"]["length"]
            print("    Axis X: " + str(table_def["x"]["length"]))
                
        if csv["AxisY.DataAddr"].lstrip("$") != "0" or int(csv["Rows"]) > 1:
            offset = float(csv["AxisY.Offset"])
            negative = False if offset >= 0.0 else True
            offset = abs(offset)
            table_def["y"] = {
                "name": "y",
                "units": xdfOut.fix_degree(csv["AxisY.Unit"]),
                "min": "",
                "max": "",
                "address": hex(int(csv["AxisY.DataAddr"].lstrip("$"), base=16)),
                "length": csv["Rows"],
                "dataSize": data_sizes[csv["AxisY.DataOrg"]],
                "signed": False if csv["AxisY.bSigned"] == "0" else True,
                "math": "X * " + str(float(csv["AxisX.Factor"])) + str(" - " if negative else " + ") + str(offset),
                "flags": hex(data_endian[csv["AxisY.DataOrg"]] + (0 if csv["AxisY.bSigned"] == "0" else 1))
            }
            table_def["z"]["rows"] = table_def["y"]["length"]
            print("    Axis Y: " + str(table_def["y"]["length"]))

        xdfOut.table_with_root(table_def)
        xmlOut.table_with_root(table_def)

xdfOut.write(f"{argv[2]}.xdf")
xmlOut.write(f"{argv[2]}.xml")
