from collections import deque  # Import deque for efficient processing
from datetime import datetime  # Import datetime for date parsing

class PayrollStrategy:  # Abstract base class for payroll strategies
    def calculate(self, employee, timeEntries):  # Abstract calculate method
        pass  # Placeholder for subclasses

class HourlyPayroll(PayrollStrategy):  # Strategy for hourly employees
    def calculate(self, employee, timeEntries):  # Calculate hourly payroll
        hourlyRate = employee[16]  # Get hourly rate (index 16)
        medicalCost = 100 if employee[17] == "Married" else 50  # Set medical cost
        dependentsStipend = employee[18] * 45  # Calculate stipend
        totalHours = 0  # Initialize regular hours
        overtimeHours = 0  # Initialize overtime hours

        entries = deque(timeEntries)  # Convert to deque
        while entries:  # Process entries
            entry = entries.popleft()  # Get first entry
            date = datetime.strptime(entry[2], '%Y-%m-%d')  # Parse date
            hours = entry[3] or 0  # Get hours, default 0
            if date.weekday() == 5:  # Check for Saturday
                overtimeHours += hours  # Add to overtime
            elif hours > 8:  # Check for overtime
                overtimeHours += hours - 8  # Add excess to overtime
                totalHours += 8  # Add regular hours
            else:  # Regular hours
                totalHours += hours  # Add hours

        grossPay = (totalHours * hourlyRate) + (overtimeHours * hourlyRate * 1.5)  # Calculate gross pay
        deductions = {"medical": medicalCost}  # Initialize deductions
        pretaxGross = grossPay - medicalCost + dependentsStipend  # Calculate pretax gross
        deductions.update({
            "stateTax": pretaxGross * 0.0315,  # State tax
            "federalTax": pretaxGross * 0.0765,  # Federal tax
            "socialSecurity": pretaxGross * 0.062,  # Social security
            "medicare": pretaxGross * 0.0145  # Medicare
        })  # Update deductions
        employerDeductions = {
            "federalTax": pretaxGross * 0.0765,  # Employer federal tax
            "socialSecurity": pretaxGross * 0.062,  # Employer social security
            "medicare": pretaxGross * 0.0145  # Employer medicare
        }  # Employer deductions
        netPay = pretaxGross - sum(deductions.values()) + dependentsStipend  # Calculate net pay
        return grossPay, netPay, deductions, employerDeductions  # Return results

class SalaryPayroll(PayrollStrategy):  # Strategy for salaried employees
    def calculate(self, employee, timeEntries):  # Calculate salaried payroll
        baseSalary = employee[15] / 52  # Weekly base salary
        medicalCost = 100 if employee[17] == "Family" else 50  # Medical cost
        dependentsStipend = employee[18] * 45  # Stipend
        ptoHours = sum(entry[4] or 0 for entry in timeEntries)  # Sum PTO hours
        grossPay = baseSalary + (ptoHours * (baseSalary / 40))  # Gross pay with PTO
        deductions = {"medical": medicalCost}  # Initialize deductions
        pretaxGross = grossPay - medicalCost + dependentsStipend  # Pretax gross
        deductions.update({
            "stateTax": pretaxGross * 0.0315,  # State tax
            "federalTax": pretaxGross * 0.0765,  # Federal tax
            "socialSecurity": pretaxGross * 0.062,  # Social security
            "medicare": pretaxGross * 0.0145  # Medicare
        })  # Update deductions
        employerDeductions = {
            "federalTax": pretaxGross * 0.0765,  # Employer federal tax
            "socialSecurity": pretaxGross * 0.062,  # Employer social security
            "medicare": pretaxGross * 0.0145  # Employer medicare
        }  # Employer deductions
        netPay = pretaxGross - sum(deductions.values()) + dependentsStipend  # Net pay
        return grossPay, netPay, deductions, employerDeductions  # Return results