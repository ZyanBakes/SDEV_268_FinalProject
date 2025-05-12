import sqlite3
import hashlib
import logging
from functools import wraps
from datetime import datetime

logging.basicConfig(filename='payroll.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def db_operation(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            self.conn.commit()
            logging.info(f"{func.__name__} executed: {args}")
            return result
        except sqlite3.Error as e:
            logging.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

class EmployeeRepository:
    def __init__(self, db):
        self.db = db

    @db_operation
    def insert(self, empData):
        query = """
            INSERT INTO employees (
            empId, firstName, lastName, dob, address1, city, state, zip,
            address2, phone, email, department, jobTitle, status, payType,
            baseSalary, hourlyRate, hireDate, single/family, dependents,
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.cursor.execute(query, empData[:21])  # Use all 21 values


    @db_operation
    def update(self, empId, empData):
        query = '''
            UPDATE employees SET 
                firstName = ?, lastName = ?, dob = ?, address1 = ?, city = ?, state = ?, zip = ?,
                address2 = ?, phone = ?, email = ?, department = ?, jobTitle = ?, status = ?, payType = ?,
                baseSalary = ?, hourlyRate = ?, hireDate = ?, single/family = ?, dependents = ?
            WHERE empId = ?
        '''
        self.db.cursor.execute(query, empData + [empId])


    @db_operation
    def delete(self, empId):
        self.db.cursor.execute("DELETE FROM employees WHERE empId = ?", (empId,))
        self.db.cursor.execute("DELETE FROM users WHERE userId = ?", (empId,))
        self.db.cursor.execute("DELETE FROM time_entries WHERE empId = ?", (empId,))
        self.db.cursor.execute("DELETE FROM pto_requests WHERE empId = ?", (empId,))

    def get(self, empId):
        self.db.cursor.execute("SELECT * FROM employees WHERE empId = ?", (empId,))
        return self.db.cursor.fetchone()

    def get_all(self):
        self.db.cursor.execute("SELECT * FROM employees")
        return self.db.cursor.fetchall()

class PtoRequestRepository:
    def __init__(self, db):
        self.db = db

    @db_operation
    def insert(self, requestData):
        self.db.cursor.execute("INSERT INTO pto_requests VALUES (?, ?, ?, ?, ?, ?, ?)", requestData)

    def get_pending(self):
        self.db.cursor.execute("SELECT * FROM pto_requests WHERE status = 'Pending'")
        return self.db.cursor.fetchall()

    @db_operation
    def update_status(self, requestId, status):
        self.db.cursor.execute("UPDATE pto_requests SET status = ? WHERE requestId = ?", (status, requestId))

class Database:
    TABLE_SCHEMAS = {
        "employees": [
            ("empId", "TEXT PRIMARY KEY"),
            ("firstName", "TEXT"),
            ("lastName", "TEXT"),
            ("dob", "TEXT"),
            ("gender", "TEXT"),
            ("email", "TEXT"),
            ("address", "TEXT"),
            ("phone", "TEXT"),
            ("city", "TEXT"),
            ("state", "TEXT"),
            ("zip", "TEXT"),
            ("department", "TEXT"),
            ("jobTitle", "TEXT"),
            ("status", "TEXT"),
            ("payType", "TEXT"),
            ("baseSalary", "REAL"),
            ("hourlyRate", "REAL"),
            ("hireDate", "TEXT"), 
            ("maritalStatus", "TEXT"),
            ("dependents", "INTEGER"),
        ],
        "users": [
            ("userId", "TEXT PRIMARY KEY"),
            ("userType", "TEXT"),
            ("password", "TEXT")
        ],
        "time_entries": [
            ("entryId", "TEXT PRIMARY KEY"),
            ("empId", "TEXT"),
            ("date", "TEXT"),
            ("hours_worked", "REAL"),
            ("pto_hours", "REAL"),
            ("FOREIGN KEY(empId)", "REFERENCES employees(empId)")
        ],
        "payroll": [
            ("payrollId", "TEXT PRIMARY KEY"),
            ("empId", "TEXT"),
            ("periodStart", "TEXT"),
            ("periodEnd", "TEXT"),
            ("grossPay", "REAL"),
            ("netPay", "REAL"),
            ("deductions", "TEXT"),
            ("status", "TEXT"),
            ("FOREIGN KEY(empId)", "REFERENCES employees(empId)")
        ],
        "pto_requests": [
            ("requestId", "TEXT PRIMARY KEY"),
            ("empId", "TEXT"),
            ("startDate", "TEXT"),
            ("endDate", "TEXT"),
            ("totalPtoHours", "REAL"),
            ("status", "TEXT"),
            ("requestDate", "TEXT"),
            ("FOREIGN KEY(empId)", "REFERENCES employees(empId)")
        ]
    }

    def __init__(self):
        self.conn = sqlite3.connect('payroll.db')
        self.cursor = self.conn.cursor()
        self.check_and_fix_users_table()
        self.createTables()
        self.employees = EmployeeRepository(self)
        self.pto_requests = PtoRequestRepository(self)

    def check_and_fix_users_table(self):
        try:
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in self.cursor.fetchall()]
            expected_columns = [field[0] for field in self.TABLE_SCHEMAS["users"]]
            if columns != expected_columns:
                logging.warning("Users table schema mismatch, recreating table")
                self.cursor.execute("DROP TABLE IF EXISTS users")
                self.createTables()
                self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to check/fix users table: {e}")
            raise

    def createTables(self):
        for table, fields in self.TABLE_SCHEMAS.items():
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(f'{f[0]} {f[1]}' for f in fields)})")
        self.conn.commit()

    def is_employees_empty(self):
        self.cursor.execute("SELECT COUNT(*) FROM employees")
        return self.cursor.fetchone()[0] == 0

    @db_operation
    def insertUser(self, userId, userType, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("INSERT INTO users (userId, userType, password) VALUES (?, ?, ?)", (userId, userType, hashed))

    def verifyLogin(self, userId, password, userType):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("SELECT userType FROM users WHERE userId = ? AND password = ?", (userId, hashed))
        result = self.cursor.fetchone()
        return result and result[0] == userType

    @db_operation
    def insertTimeEntry(self, entryData):
        self.cursor.execute("INSERT INTO time_entries VALUES (?, ?, ?, ?, ?)", entryData)

    def getTimeEntries(self, empId, startDate, endDate):
        query = "SELECT * FROM time_entries WHERE empId = ? AND date BETWEEN ? AND ?"
        self.cursor.execute(query, (empId, startDate, endDate))
        return self.cursor.fetchall()

    @db_operation
    def lockTimeEntries(self, startDate, endDate):
        self.cursor.execute("UPDATE time_entries SET hours_worked = hours_worked WHERE date BETWEEN ? AND ?", (startDate, endDate))

    @db_operation
    def insertPayroll(self, payrollData):
        self.cursor.execute("INSERT INTO payroll VALUES (?, ?, ?, ?, ?, ?, ?, ?)", payrollData)

    def getWeeklyHoursBatch(self, startDate, endDate):
        try:
            query = """
                SELECT e.empId, COALESCE(SUM(t.hoursWorked), 0) as totalHours
                FROM employees e
                LEFT JOIN time_entries t ON e.empId = t.empId
                WHERE t.date >= ? AND t.date <= ? AND t.date >= e.hireDate
                GROUP BY e.empId
            """
            self.cursor.execute(query, (startDate, endDate))
            return {row[0]: row[1] or 0.0 for row in self.cursor.fetchall()}
        except Exception as e:
            logging.error(f"Failed to fetch weekly hours batch: {e}")
            return {}

    def getYearlyPtoBatch(self, year):
        query = "SELECT empId, SUM(pto_hours) FROM time_entries WHERE date LIKE ? GROUP BY empId"
        self.cursor.execute(query, (f"{year}%",))
        return {row[0]: row[1] or 0.0 for row in self.cursor.fetchall()}

    def getPtoBalance(self, empId):
        self.cursor.execute("SELECT hireDate, pto_accrual_rate FROM employees WHERE empId = ?", (empId,))
        result = self.cursor.fetchone()
        if not result:
            return 0.0
        hireDate, accrualRate = result
        start = datetime.strptime(hireDate, '%Y-%m-%d')
        today = datetime.now()
        days = (today - start).days
        periods = days // 14  # Biweekly periods
        accrued = periods * accrualRate
        used = self.getYearlyPtoBatch(today.year).get(empId, 0.0)
        return max(0.0, accrued - used)

    def close(self):
        self.conn.close()