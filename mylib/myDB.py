#!/usr/bin/python3
import sqlite3


class DB:
    def __init__(self, args):
        ...

    def store_file(self, file_name, size):
        # print("записываем файл %s размером %s" % (File,Size))
        pass

    def get_file_sz(self, file_name):
        return 0

    def read_db(self):
        pass
    
    def write_db(self):
        pass


class IniDb(DB):

    def __init__(self, args):
        super().__init__(args)
        self.args = args

    def store_file(self, file_name, size):

        self.args.config.set("DB", file_name, "S_" + str(size))

    def get_file_sz(self, file_name):
        try:
            return int(self.args.files[file_name].split('_')[1])
        except Exception:
            return -2
        
    def read_db(self):
        pass

    def write_db(self):
        with open(self.args.config_file, 'w') as configfile:
            self.args.config.write(configfile)
            
    
class SQLiteDB(DB):
    def __init__(self, args):
        super().__init__(args)
        self.database = args.name
        # print(self.database)
        self.conn = sqlite3.connect(self.database+".db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS "+self.database+"(file text, size int) ")
        self.conn.commit()

    def get_file_sz(self, file_name):
        pass

    def store_file(self, file_name, size):
        self.cursor.execute(f"INSERT INTO {self.database} VALUES (\'{file_name}\', \'{size}\'")
        self.conn.commit()

    def read_db(self):
        pass

    def write_db(self):
        pass

    
