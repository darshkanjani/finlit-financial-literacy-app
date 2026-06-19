from app.db.base import Base
from sqlalchemy import Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql.sqltypes import JSON
import random
import datetime
import string
import uuid

""" can be used by creating an instance of DataCreation(number of rows wanted) and calling run()
    currently prints to console but can be modified to insert into database or write to file if needed
    Note: for foreign keys, it just generates a placeholder reference value, since we are not
    actually inserting into the database. The focus is on generating realistic dummy data for each column type.
    USERGUIDE:
    1. Ensure your database models are defined in app.db.models and that Base.metadata is properly set up.
    2. Run this script to see the generated dummy data for each table in your schema
    3. Get data using getter function

    TODO:
    - Generate JSON data that matches expected structure for our app
    - intergrate with database creation
"""
class DataCreation:

    def __init__(self, rows_per_table=5, output_to_console=True):
        self.rows_per_table = rows_per_table
        self.output_to_console = output_to_console
        self.schema = self.create_schema(output_to_console=output_to_console)
        self.data = self.run(output_to_console=output_to_console)
    # ---------------------------
    # Getter for Schema and Data
    # ---------------------------
    def get_schema(self):
        return self.schema
    def get_data(self):
        return self.data
    # ---------------------------
    # Public Runner
    # ---------------------------
    def create_schema(self,output_to_console=True):
        """gets the current database schema and prints out the structure of each table, along with a few example rows of dummy data"""
        schema = {}
        tablesInfo = Base.metadata.tables
        num_Tables = len(tablesInfo)
        for table_name, table in tablesInfo.items():
            schema[table_name] = []
            for column in table.columns:
                schema[table_name].append((column.name, column.type))
        if output_to_console:
            print ("Schema created successfully.")
        return schema
            
    def run(self,output_to_console=True):
        """
        Iterate through all tables in metadata and
        generate printable dummy rows.
        """
        data = {}
        for table_name, columns in self.schema.items():
            if output_to_console:
                print(f"Table: {table_name}")
            data[table_name] = []
            for i in range(self.rows_per_table):
                row = self.generate_row(Base.metadata.tables[table_name])
                if output_to_console:
                    print(row)
                data[table_name].append(row)
            if  output_to_console:    
                print("\n")
        return data

    # ---------------------------
    # Core Row Generator
    # ---------------------------

    def generate_row(self, table, row_index=0):
        row = {}

        for column in table.columns:

            # Skip autoincrement PKs
            if column.primary_key and column.autoincrement:
                continue

            # Foreign Keys (print placeholder reference)
            if column.foreign_keys:
                row[column.name] = self.generate_foreign_key_value(column)
                continue

            # Generate based on type
            col_type = column.type

            if isinstance(col_type, Integer):
                row[column.name] = random.randint(1, 100)

            elif isinstance(col_type, Float):
                row[column.name] = round(random.uniform(1, 100), 2)

            elif isinstance(col_type, Boolean):
                row[column.name] = random.choice([True, False])

            elif isinstance(col_type, DateTime):
                row[column.name] = self.random_datetime()

            elif isinstance(col_type, String) or isinstance(col_type, Text):
                row[column.name] = self.random_string(column)

            elif isinstance(col_type, JSON):
                row[column.name] = self.generate_json_stub()

            else:
                row[column.name] = None

        return row

    # ---------------------------
    # Type Generators
    # ---------------------------

    def random_string(self, column):
        length = getattr(column.type, "length", None)
        length = min(length if length else 20, 20)

        return ''.join(random.choices(string.ascii_letters, k=length))

    def random_datetime(self):
        start = datetime.datetime.now() - datetime.timedelta(days=365 * 2)
        end = datetime.datetime.now()
        return start + (end - start) * random.random()

    def generate_foreign_key_value(self, column):
        """
        Just generate a placeholder reference value.
        We are NOT inserting into DB, so this is symbolic.
        """
        fk = list(column.foreign_keys)[0]
        referenced_table = fk.column.table.name
        return f"{referenced_table}_id_{random.randint(1, 10)}"

    def generate_json_stub(self):
        """
        Minimal stub for JSON columns.
        Can expand later.
        """
        return {
            "sample_key": random.randint(1, 100),
            "generated": True
        }