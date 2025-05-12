import logging
from database import Database
from ui import PayrollUI

logging.basicConfig(filename='payroll.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initializeData():
    db = Database()
    # Check and insert admin account
    try:
        db.cursor.execute("SELECT userId FROM users WHERE userId = ?", ("HR0001",))
        if not db.cursor.fetchone():
            db.insertUser("HR0001", "Admin", "SecurePass123!")
            logging.info("Admin account HR0001 inserted")
        else:
            logging.info("Admin account HR0001 already exists")
    except Exception as e:
        logging.error(f"Failed to insert/check admin account: {e}")
        raise

    # Check if employees table is empty
    if db.is_employees_empty():
        logging.info("Employees table is empty, starting with empty database")
    else:
        logging.info("Employees table already populated, skipping initialization")
    db.close()

if __name__ == "__main__":
    initializeData()
    app = PayrollUI()
    app.run()