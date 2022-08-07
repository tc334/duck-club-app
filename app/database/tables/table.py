class Table:
    def __init__(self, table_cols):
        self.table_cols = table_cols

    def get_names_list(self):
        # returns the list of the column names sorted in alphabetical order
        names = [a_dict["name"] for a_dict in self.table_cols]
        names.sort()
        return names

    def get_schema_string(self):
        # this function returns the string representation of the variable names used in SQL table creation
        s = ""
        f = ""  # foreign key constraints get added at the end
        i = ""  # secondary indices get added at the end
        for item in self.table_cols:
            s = s + item['name'] + ' ' + item['type'] + ' '
            if 'foreign' in item:
                f = f + 'FOREIGN KEY (' + item['name'] + ') REFERENCES ' + item['foreign'] + ', '
            if 'secondary_index' in item:
                i = i + 'INDEX '
            s = s + item['extra'] + ', '
        full_str = s + f
        # print(f"get_schema_string:{full_str[:-2]}")
        return full_str[:-2]

    def get_add_row(self, dict_in):
        names_all = [a_dict["name"] for a_dict in self.table_cols]
        names_in = [key for key in dict_in]
        # This takes only the intersection of the full list and the input list
        names = list(set(names_all) & set(names_in))
        insert_string = ",".join(names)
        insert_list = [dict_in[key] for key in names]
        # insert_list.insert(0, None)
        insert_tuple = tuple(insert_list)
        return insert_string, insert_tuple
