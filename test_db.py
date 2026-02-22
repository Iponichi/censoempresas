print("START test_db.py")

from data_access import create_db_engine, test_connection

print("Imported data_access ok")

engine = create_db_engine()
print("Engine created")

result = test_connection(engine)
print(result)

print("END test_db.py")