import re
import uuid
import xml.etree.ElementTree as ET

class XDFWrite:
    def __init__(self, baseOffset, binOffset, categoryOffset, title):
        self.categories = []
        self.baseOffset = baseOffset
        self.categoryOffset = categoryOffset
        self.binOffset = binOffset
    
        self.root = ET.Element("XDFFORMAT")
        self.root.set("version", "1.60")

        self.xdfheader = ET.SubElement(self.root, "XDFHEADER")
        flags = ET.SubElement(self.xdfheader, "flags")
        flags.text = "0x1"
        deftitle = ET.SubElement(self.xdfheader, "deftitle")
        deftitle.text = title
        description = ET.SubElement(self.xdfheader, "description")
        description.text = "Switch Patch"
        baseoffset = ET.SubElement(self.xdfheader, "BASEOFFSET")
        baseoffset.set("offset", hex(self.binOffset))
        baseoffset.set("subtract", "0")
        defaults = ET.SubElement(self.xdfheader, "DEFAULTS")
        defaults.set("datasizeinbits", "8")
        defaults.set("sigdigits", "4")
        defaults.set("outputtype", "1")
        defaults.set("signed", "0")
        defaults.set("lsbfirst", "1")
        defaults.set("float", "0")
        region = ET.SubElement(self.xdfheader, "REGION")
        region.set("type", "0xFFFFFFFF")
        region.set("startaddress", "0x0")
        region.set("size", "0x7D000")
        region.set("regionflags", "0x0")
        region.set("name", "Binary")
        region.set("desc", "BIN for the XDF")
        self.add_category("Axis")

    def write(self, filename):
        tree = ET.ElementTree(self.root)
        ET.indent(tree, space="  ", level=0)
        tree.write(filename)

    def add_category(self, category):
        if category not in self.categories:
            self.categories.append(category)
            index = self.categories.index(category) + self.categoryOffset
            self.set_category(category, index)

    def embeddeddata(self, element: ET.Element, id, axis_def):
        embed = ET.SubElement(element, "EMBEDDEDDATA")
        embed.set("mmedtypeflags", axis_def["flags"])
        embed.set("mmedaddress", str(axis_def["address"]))
        embed.set("mmedelementsizebits", str(axis_def["dataSize"] * 8))
        embed.set("mmedcolcount", str(axis_def["length"]) if "length" in axis_def else "1")
        if id == "z":
            embed.set("mmedrowcount", str(axis_def["rows"]) if "rows" in axis_def else "1")
        embed.set("mmedmajorstridebits", str(axis_def["dataSize"] * 8))
        embed.set("mmedminorstridebits", "0")
        return embed


    def fake_axis_with_size(self, table: ET.Element, id, size):
        axis = ET.SubElement(table, "XDFAXIS")
        axis.set("uniqueid", "0x0")
        axis.set("id", id)
        indexcount = ET.SubElement(axis, "indexcount")
        indexcount.text = str(size)
        outputtype = ET.SubElement(axis, "outputtype")
        outputtype.text = "4"
        dalink = ET.SubElement(axis, "DALINK")
        dalink.set("index", "0")
        math = ET.SubElement(axis, "MATH")
        math.set("equation", "X")
        var = ET.SubElement(math, "VAR")
        var.set("id", "X")
        for label_index in range(size):
            label = ET.SubElement(axis, "LABEL")
            label.set("index", str(label_index))
            label.set("value", "-")
        return axis


    def axis_with_table(self, table: ET.Element, id, axis_def):
        axis = ET.SubElement(table, "XDFAXIS")
        axis.set("uniqueid", "0x0")
        axis.set("id", id)

        self.embeddeddata(axis, id, axis_def)

        indexcount = ET.SubElement(axis, "indexcount")
        indexcount.text = str(axis_def["length"]) if "length" in axis_def else "1"
        min = ET.SubElement(axis, "min")
        min.text = str(axis_def["min"])
        max = ET.SubElement(axis, "max")
        max.text = str(axis_def["max"])
        units = ET.SubElement(axis, "units")
        units.text = axis_def["units"]
        embedinfo = ET.SubElement(axis, "embedinfo")
        embedinfo.set("type", "1")  # "Pure, Internal"
        dalink = ET.SubElement(axis, "DALINK")
        dalink.set("index", "0")
        math = ET.SubElement(axis, "MATH")
        math.set("equation", axis_def["math"])
        var = ET.SubElement(math, "VAR")
        var.set("id", "X")
        return axis


    def table_with_root(self, table_def):
        table = ET.SubElement(self.root, "XDFTABLE")
        table.set("uniqueid", table_def["z"]["address"])
        table.set("flags", "0x30")
        title = ET.SubElement(table, "title")
        title.text = table_def["title"]
        description = ET.SubElement(table, "description")
        description.text = table_def["description"]
        table_categories = [table_def["category"]]
        if "category1" in table_def:
            table_categories.append(table_def["category1"])
        if "category2" in table_def:
            table_categories.append(table_def["category2"])
        self.add_table_categories(table, table_categories)

        if "x" in table_def:
            self.axis_with_table(table, "x", table_def["x"])
        else:
            columns = int(table_def["z"]["columns"])
            table_def["z"]["length"] = columns
            self.fake_axis_with_size(table, "x", columns)

        if "y" in table_def:
            self.axis_with_table(table, "y", table_def["y"])
        else:
            self.fake_axis_with_size(table, "y", 1)

        self.axis_with_table(table, "z", table_def["z"])
            
        return table


    def add_table_categories(self, table, table_categories):
        index = 0
        for category in table_categories:
            categorymem = ET.SubElement(table, "CATEGORYMEM")
            categorymem.set("index", str(index))
            categorymem.set("category", str(self.categories.index(category) + 1 + self.categoryOffset))
            index += 1


    def constant_with_root(self, table_def):
        table = ET.SubElement(self.root, "XDFCONSTANT")
        table.set("uniqueid", table_def["z"]["address"])
        title = ET.SubElement(table, "title")
        title.text = table_def["title"]
        description = ET.SubElement(table, "description")
        description.text = table_def["description"]
        table_categories = [table_def["category"]]
        if "sub_category" in table_def:
            table_categories.append(table_def["sub_category"])
        add_table_categories(table, table_categories)

        self.embeddeddata(table, "z", table_def["z"])

        math = ET.SubElement(table, "MATH")
        math.set("equation", table_def["z"]["math"])
        var = ET.SubElement(math, "VAR")
        var.set("id", "X")

        return table


    def table_from_axis(self, table_def, axis_name):
        table = ET.SubElement(self.root, "XDFTABLE")
        table.set("uniqueid", table_def[axis_name]["address"])
        table.set("flags", "0x30")
        title = ET.SubElement(table, "title")
        title.text = (f'{table_def["title"]} : {axis_name} axis : {table_def[axis_name]["name"]}')
        description = ET.SubElement(table, "description")
        description.text = table_def[axis_name]["name"]
        table_categories = [table_def["category"]]
        if "sub_category" in table_def:
            table_categories.append(table_def["sub_category"])
        table_categories.append("Axis")
        add_table_categories(table, table_categories)
        fake_axis_with_size(table, "x", table_def[axis_name]["length"])
        fake_axis_with_size(table, "y", 1)
        axis_with_table(table, "z", table_def[axis_name])
        return table


    def set_category(self, category_name, category_index):
        category = ET.SubElement(self.xdfheader, "CATEGORY")
        category.set("index", hex(category_index))
        category.set("name", category_name)
        return category


    # Helpers

    def adjust_address(self, address):
        return address - self.baseOffset


    # A2L to "normal" conversion methods

    def fix_degree(self, bad_string):
        return re.sub("\uFFFD", "\u00B0", bad_string)  # Replace Unicode "unknown" with degree sign


    def coefficients_to_equation(self, coefficients):
        a, b, c, d, e, f = (
            str(coefficients["a"]),
            str(coefficients["b"]),
            str(coefficients["c"]),
            str(coefficients["d"]),
            str(coefficients["e"]),
            str(coefficients["f"]),
        )
        if a == "0.0" and d == "0.0":  # Polynomial is of order 1, ie linear
            return f"(({f} * X) - {c} ) / ({b} - ({e} * X))"
        else:
            return "Cannot handle polynomial ratfunc because we do not know how to invert!"
