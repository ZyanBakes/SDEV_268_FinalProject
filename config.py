# Define shared constants for the payroll system
DATABASE_FILE = "payroll.db"  # Name of the SQLite database file

# Fields for the employees table (20 fields, excluding pto_accrual_rate which is set to a default value in the database)
EMPLOYEE_FIELDS = [
    "Emp ID", "First Name", "Last Name", "DOB", "Gender", "Address", "Phone",
    "City", "State", "ZIP", "Email", "Department", "Job Title", "Status",
    "Pay Type", "Base Salary", "Hourly Rate", "Hire Date", "Marital Status", "Dependents"
]
