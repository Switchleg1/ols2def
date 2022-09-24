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
    "eBitLoHi": 2,
    "eByte": 1,
    "eFloatLoHi": 4,
    "eLoHi": 2,
    "eLoHiLoHi": 4,
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

        #xdf
        table_def = {
            "title": csv["IdName"],
            "description": csv["Name"],
            "category": "OLS",
            "category1": category,
            "z": {
                "min": "",
                "max": "",
                "address": hex(int(csv["Fieldvalues.StartAddr"].lstrip("$"), base=16)),
                "dataSize": data_sizes[csv["DataOrg"]],
                "units": xdfOut.fix_degree(csv["Fieldvalues.Unit"]),
                "math": "(X * " + csv["Fieldvalues.Factor"] + ") + " + csv["Fieldvalues.Offset"],
                "flags": "0x02",
                "columns": csv["Columns"]
            },
        }

        if csv["AxisX.DataAddr"].lstrip("$") != "0":
            table_def["x"] = {
                "name": "x",
                "units": xdfOut.fix_degree(csv["AxisX.Unit"]),
                "min": "",
                "max": "",
                "address": hex(int(csv["AxisX.DataAddr"].lstrip("$"), base=16)),
                "length": csv["Columns"],
                "dataSize": data_sizes[csv["AxisX.DataOrg"]],
                "math": "(X * " + csv["AxisX.Factor"] + ") + " + csv["AxisX.Offset"],
                "flags": "0x02"
            }
            table_def["z"]["length"] = table_def["x"]["length"]
            print("    Axis X: " + str(table_def["x"]["length"]))
                
        if csv["AxisY.DataAddr"].lstrip("$") != "0":
            table_def["y"] = {
                "name": "y",
                "units": xdfOut.fix_degree(csv["AxisY.Unit"]),
                "min": "",
                "max": "",
                "address": hex(int(csv["AxisY.DataAddr"].lstrip("$"), base=16)),
                "length": csv["Rows"],
                "dataSize": data_sizes[csv["AxisY.DataOrg"]],
                "math": "(X * " + csv["AxisY.Factor"] + ") + " + csv["AxisY.Offset"],
                "flags": "0x02"
            }
            table_def["z"]["rows"] = table_def["y"]["length"]
            print("    Axis Y: " + str(table_def["y"]["length"]))

        xdfOut.table_with_root(table_def)

        #xml
        table_def = {
            "title": csv["IdName"],
            "description": csv["Name"],
            "category": ["OLS", category],
            "z": {
                "min": "",
                "max": "",
                "address": hex(int(csv["Fieldvalues.StartAddr"].lstrip("$"), base=16)),
                "dataSize": data_sizes[csv["DataOrg"]],
                "units": xmlOut.fix_degree(csv["Fieldvalues.Unit"]),
                "math": "(X * " + csv["Fieldvalues.Factor"] + ") + " + csv["Fieldvalues.Offset"],
                "math2": "(X / " + csv["Fieldvalues.Factor"] + ") - " + csv["Fieldvalues.Offset"],
                "order": "cr"
            },
        }

        if csv["AxisX.DataAddr"].lstrip("$") != "":
            axis_def = {
                "name": "x",
                "units": xmlOut.fix_degree(csv["AxisX.Unit"]),
                "min": "",
                "max": "",
                "address": hex(int(csv["AxisX.DataAddr"].lstrip("$"), base=16)),
                "length": csv["Columns"],
                "dataSize": data_sizes[csv["AxisX.DataOrg"]],
                "math": "(X * " + csv["AxisX.Factor"] + ") + " + csv["AxisX.Offset"],
                "math2": "(X / " + csv["AxisX.Factor"] + ") - " + csv["AxisX.Offset"]
            }
            table_def["x"] = axis_def
            table_def["z"]["length"] = table_def["x"]["length"]
            table_def["description"] += f'|X: {table_def["x"]["name"]}'

        if csv["AxisY.DataAddr"].lstrip("$") != "":
            axis_def = {
                "name": "y",
                "units": xmlOut.fix_degree(csv["AxisY.Unit"]),
                "min": "",
                "max": "",
                "address":  hex(int(csv["AxisY.DataAddr"].lstrip("$"), base=16)),
                "length": csv["Rows"],
                "dataSize": data_sizes[csv["AxisY.DataOrg"]],
                "math": "(X * " + csv["AxisY.Factor"] + ") + " + csv["AxisY.Offset"],
                "math2": "(X / " + csv["AxisY.Factor"] + ") - " + csv["AxisY.Offset"]
            }
            table_def["y"] = axis_def
            table_def["description"] += f'|Y: {table_def["y"]["name"]}'
            table_def["z"]["rows"] = table_def["y"]["length"]

        xmlOut.table_with_root(table_def)

xdfOut.write(f"{argv[2]}.xdf")
xmlOut.write(f"{argv[2]}.xml")
