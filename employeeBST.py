from bisect import insort, bisect_left  # Import bisect functions for BST operations

class EmployeeBST:  # Define EmployeeBST class for name searches
    def __init__(self):  # Initialize BST
        self.names = []  # Create empty list for (name, empId) tuples

    def insert(self, empId, name):  # Insert employee into BST
        insort(self.names, (name, empId))  # Insert tuple in sorted order

    def search(self, name):  # Search for employees by name prefix
        idx = bisect_left(self.names, (name,))  # Find insertion point
        return [self.names[i][1] for i in range(idx, len(self.names)) if self.names[i][0].startswith(name)]  # Return matching empIds