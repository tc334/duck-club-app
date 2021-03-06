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
        for item in self.table_cols:
            s = s + item['name'] + ' ' + item['type']
            if item['enum'] is not None:
                s = s + "("
                for e in item['enum']:
                    s = s + "'" + e + "',"
                s = s[:-1] + ") "
            else:
                s = s + ' '
            s = s + item['extra'] + ', '
        return s[:-2]

    def get_add_row(self, dict_in):
        names_all = [a_dict["name"] for a_dict in self.table_cols]
        names_in = [key for key in dict_in]
        # This takes only the intersection of the full list and the input list
        names = list(set(names_all) & set(names_in))
        insert_string = "id," + ",".join(names)
        insert_list = [dict_in[key] for key in names]
        insert_list.insert(0, None)
        insert_tuple = tuple(insert_list)
        return insert_string, insert_tuple
