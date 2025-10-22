from db.database import Database

db_info = {"user": "root", "port": "3306", "host": "localhost", "database": "bankDb"}
db = Database(db_info)

db.insert_users("ruvais", "ruvais@host.com", "12345")
db.insert_users("pavan", "pavan@host.com", "12345")
db.insert_users("adharsh", "adharsh@host.com", "12345")

db.insert_accounts(1, "savings", 1500)
db.insert_accounts(2, "savings", 2500)
db.insert_accounts(3, "current", 500)

db.insert_branch("uduma", "kasragod,kerala", "12345")

db.insert_employee("dusk", "dusk@some.com", "12345", 1)
