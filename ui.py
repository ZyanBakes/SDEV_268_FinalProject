import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import hashlib
from database import Database
from payrollLogic import HourlyPayroll, SalaryPayroll
from employeeBST import EmployeeBST
from config import EMPLOYEE_FIELDS
import uuid

class PayrollUI:
    def __init__(self):
        self.db = Database()
        self.employee_bst = EmployeeBST()
        self.hourly_strategy = HourlyPayroll()
        self.salary_strategy = SalaryPayroll()
        self.root = tk.Tk()
        self.root.title("Payroll System")
        self.root.geometry("800x600")
        self.current_user = None
        self.show_login()

    def show_login(self):
        self.clear_window()
        tk.Label(self.root, text="Payroll System Login", font=("Arial", 16)).pack(pady=20)
        
        tk.Label(self.root, text="User ID").pack()
        user_id_entry = tk.Entry(self.root)
        user_id_entry.pack(pady=5)
        
        tk.Label(self.root, text="Password").pack()
        password_entry = tk.Entry(self.root, show="*")
        password_entry.pack(pady=5)
        
        tk.Button(self.root, text="Admin Login", command=lambda: self.verify_login(user_id_entry.get(), password_entry.get(), "Admin")).pack(pady=10)
        tk.Button(self.root, text="Employee Login", command=lambda: self.verify_login(user_id_entry.get(), password_entry.get(), "Employee")).pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.root.destroy).pack(pady=10)

    def verify_login(self, user_id, password, user_type):
        if self.db.verifyLogin(user_id, password, user_type):
            self.current_user = user_id
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_window()
        tk.Label(self.root, text="Payroll System Dashboard", font=("Arial", 16)).pack(pady=20)
        
        tk.Button(self.root, text="Manage Employees", command=self.show_employee_management).pack(pady=10)
        tk.Button(self.root, text="Process Payroll", command=self.show_payroll_processing).pack(pady=10)
        tk.Button(self.root, text="Manage PTO Requests", command=self.show_pto_management).pack(pady=10)
        tk.Button(self.root, text="Manage Time Entries", command=self.show_time_entries).pack(pady=10)
        tk.Button(self.root, text="Logout", command=self.show_login).pack(pady=10)

    def show_employee_management(self):
        self.clear_window()
        tk.Label(self.root, text="Employee Management", font=("Arial", 16)).pack(pady=20)
        
        # Employee List
        tree = ttk.Treeview(self.root, columns=("ID", "Name", "Job Title", "Status"), show="headings")
        tree.heading("ID", text="Emp ID")
        tree.heading("Name", text="Name")
        tree.heading("Job Title", text="Job Title")
        tree.heading("Status", text="Status")
        tree.pack(fill="both", expand=True)
        
        for emp in self.db.employees.get_all():
            name = f"{emp[1] if len(emp) > 1 else ''} {emp[2] if len(emp) > 2 else ''}".strip()
            job_title = emp[12] if len(emp) > 12 else "N/A"
            status = emp[13] if len(emp) > 13 else "N/A"
            tree.insert("", "end", values=(emp[0], name, job_title, status))
            self.employee_bst.insert(emp[0], name.lower())
        
        # Search by Name
        tk.Label(self.root, text="Search by Name").pack()
        search_entry = tk.Entry(self.root)
        search_entry.pack(pady=5)
        tk.Button(self.root, text="Search", command=lambda: self.search_employees(tree, search_entry.get())).pack(pady=5)
        
        # Buttons
        tk.Button(self.root, text="Add Employee", command=self.show_add_employee).pack(pady=5)
        tk.Button(self.root, text="Edit Employee", command=lambda: self.show_edit_employee(tree)).pack(pady=5)
        tk.Button(self.root, text="Delete Employee", command=lambda: self.delete_employee(tree)).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.show_dashboard).pack(pady=5)

    def search_employees(self, tree, name):
        for item in tree.get_children():
            tree.delete(item)
        emp_ids = self.employee_bst.search(name.lower())
        for emp_id in emp_ids:
            emp = self.db.employees.get(emp_id)
            if emp:
                name = f"{emp[1] if len(emp) > 1 else ''} {emp[2] if len(emp) > 2 else ''}".strip()
                job_title = emp[12] if len(emp) > 12 else "N/A"
                status = emp[13] if len(emp) > 13 else "N/A"
                tree.insert("", "end", values=(emp[0], name, job_title, status))

    def show_add_employee(self):
        self.clear_window()
        tk.Label(self.root, text="Add Employee", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)

        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        entries = {}
        fields = EMPLOYEE_FIELDS

        for i, field in enumerate(fields):
            tk.Label(scrollable_frame, text=field).grid(row=i, column=0, sticky="w", pady=2)
            entry = tk.Entry(scrollable_frame)
            entry.grid(row=i, column=1, padx=10, pady=2, sticky="ew")
            entries[field] = entry

        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        tk.Button(button_frame, text="Save", command=lambda: self.save_employee(entries)).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Back", command=self.show_employee_management).grid(row=0, column=1, padx=5)

    def save_employee(self, entries):
        emp_id = f"E{uuid.uuid4().hex[:8]}"
        emp_data = [emp_id]
        for field in EMPLOYEE_FIELDS[1:]:
            value = entries[field].get()
            if field == "Base Salary" or field == "Hourly Rate":
                value = float(value) if value else 0.0
            elif field == "Dependents":
                value = int(value) if value else 0
            emp_data.append(value)
        try:
            self.db.employees.insert(emp_data)
            name = f"{emp_data[1]} {emp_data[2]}"
            self.employee_bst.insert(emp_id, name.lower())
            messagebox.showinfo("Success", "Employee added")
            self.show_employee_management()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add employee: {e}")

    def show_edit_employee(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an employee")
            return
        emp_id = tree.item(selected)["values"][0]
        emp = self.db.employees.get(emp_id)
        if not emp:
            messagebox.showerror("Error", "Employee not found")
            return

        self.clear_window()
        tk.Label(self.root, text="Edit Employee", font=("Arial", 16)).pack(pady=10)

        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        entries = {}
        fields = EMPLOYEE_FIELDS
        for i, field in enumerate(fields):
            tk.Label(scrollable_frame, text=field).pack(pady=2, anchor="w")
            entry = tk.Entry(scrollable_frame)
            entry.insert(0, emp[i] if len(emp) > i else "")
            entry.pack(pady=2, padx=10, fill="x")
            entries[field] = entry

        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Save", command=lambda: self.update_employee(emp_id, entries)).pack(side="left", padx=5)
        tk.Button(button_frame, text="Back", command=self.show_employee_management).pack(side="left", padx=5)

        def on_mouse_wheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
        
        canvas.bind_all("<MouseWheel>", on_mouse_wheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    def update_employee(self, emp_id, entries):
        emp_data = []
        fields = EMPLOYEE_FIELDS
        for field in fields:
            value = entries[field].get()
            if field == "Base Salary" or field == "Hourly Rate":
                value = float(value) if value else 0.0
            elif field == "Dependents":
                value = int(value) if value else 0
            emp_data.append(value)
    
        try:
            self.db.employees.update(emp_id, emp_data)
            messagebox.showinfo("Success", "Employee updated")
            self.show_employee_management()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update employee: {e}")

    def delete_employee(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an employee")
            return
        emp_id = tree.item(selected)["values"][0]
        if messagebox.askyesno("Confirm", "Delete employee?"):
            try:
                self.db.employees.delete(emp_id)
                messagebox.showinfo("Success", "Employee deleted")
                self.show_employee_management()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete employee: {e}")

    def show_payroll_processing(self):
        self.clear_window()
        tk.Label(self.root, text="Payroll Processing", font=("Arial", 16)).pack(pady=20)
        
        tk.Label(self.root, text="Employee ID").pack()
        emp_id_entry = tk.Entry(self.root)
        emp_id_entry.pack(pady=5)
        
        tk.Label(self.root, text="Start Date (YYYY-MM-DD)").pack()
        start_date_entry = tk.Entry(self.root)
        start_date_entry.pack(pady=5)
        
        tk.Label(self.root, text="End Date (YYYY-MM-DD)").pack()
        end_date_entry = tk.Entry(self.root)
        end_date_entry.pack(pady=5)
        
        tk.Button(self.root, text="Calculate Payroll", command=lambda: self.calculate_payroll(emp_id_entry.get(), start_date_entry.get(), end_date_entry.get())).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.show_dashboard).pack(pady=5)

    def calculate_payroll(self, emp_id, start_date, end_date):
        emp = self.db.employees.get(emp_id)
        if not emp:
            messagebox.showerror("Error", "Employee not found")
            return
        try:
            time_entries = self.db.getTimeEntries(emp_id, start_date, end_date)
            strategy = self.salary_strategy if len(emp) > 14 and emp[14] == "Salary" else self.hourly_strategy
            gross_pay, net_pay, deductions, employer_deductions = strategy.calculate(emp, time_entries)
            payroll_id = f"P{uuid.uuid4().hex[:8]}"
            deductions_str = str(deductions)
            payroll_data = (payroll_id, emp_id, start_date, end_date, gross_pay, net_pay, deductions_str, "Processed")
            self.db.insertPayroll(payroll_data)
            messagebox.showinfo("Payroll Result", f"Gross Pay: ${gross_pay:.2f}\nNet Pay: ${net_pay:.2f}\nDeductions: {deductions}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process payroll: {e}")

    def show_pto_management(self):
        self.clear_window()
        tk.Label(self.root, text="PTO Management", font=("Arial", 16)).pack(pady=20)
        
        tree = ttk.Treeview(self.root, columns=("ID", "Emp ID", "Start", "End", "Hours", "Status"), show="headings")
        tree.heading("ID", text="Request ID")
        tree.heading("Emp ID", text="Emp ID")
        tree.heading("Start", text="Start Date")
        tree.heading("End", text="End Date")
        tree.heading("Hours", text="PTO Hours")
        tree.heading("Status", text="Status")
        tree.pack(fill="both", expand=True)
        
        for req in self.db.pto_requests.get_pending():
            tree.insert("", "end", values=(req[0], req[1], req[2], req[3], req[4], req[5]))
        
        tk.Button(self.root, text="Approve", command=lambda: self.update_pto_status(tree, "Approved")).pack(pady=5)
        tk.Button(self.root, text="Reject", command=lambda: self.update_pto_status(tree, "Rejected")).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.show_dashboard).pack(pady=5)

    def update_pto_status(self, tree, status):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a PTO request")
            return
        request_id = tree.item(selected)["values"][0]
        try:
            self.db.pto_requests.update_status(request_id, status)
            messagebox.showinfo("Success", f"PTO request {status}")
            self.show_pto_management()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update PTO status: {e}")

    def show_time_entries(self):
        self.clear_window()
        tk.Label(self.root, text="Time Entries", font=("Arial", 16)).pack(pady=20)
        
        tk.Label(self.root, text="Employee ID").pack()
        emp_id_entry = tk.Entry(self.root)
        emp_id_entry.pack(pady=5)
        
        tk.Label(self.root, text="Date (YYYY-MM-DD)").pack()
        date_entry = tk.Entry(self.root)
        date_entry.pack(pady=5)
        
        tk.Label(self.root, text="Hours Worked").pack()
        hours_entry = tk.Entry(self.root)
        hours_entry.pack(pady=5)
        
        tk.Label(self.root, text="PTO Hours").pack()
        pto_hours_entry = tk.Entry(self.root)
        pto_hours_entry.pack(pady=5)
        
        tk.Button(self.root, text="Add Entry", command=lambda: self.add_time_entry(emp_id_entry.get(), date_entry.get(), hours_entry.get(), pto_hours_entry.get())).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.show_dashboard设施).pack(pady=5)

    def add_time_entry(self, emp_id, date, hours, pto_hours):
        entry_id = f"T{uuid.uuid4().hex[:8]}"
        hours = float(hours) if hours else 0.0
        pto_hours = float(pto_hours) if pto_hours else 0.0
        entry_data = (entry_id, emp_id, date, hours, pto_hours)
        try:
            self.db.insertTimeEntry(entry_data)
            messagebox.showinfo("Success", "Time entry added")
            self.show_time_entries()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add time entry: {e}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PayrollUI()
    app.run()