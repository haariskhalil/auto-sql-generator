import sqlite3
from faker import Faker
import random
from datetime import datetime, timedelta

sqlite3.register_adapter(datetime.date, lambda val: val.isoformat())
sqlite3.register_converter("DATE", lambda val: datetime.date.fromisoformat(val.decode()))

# Initialize Faker
fake = Faker()

def create_connection():
    conn = sqlite3.connect('company.db')
    return conn

def create_tables(conn):
    c = conn.cursor()
    
    # 1. Departments Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY,
        name TEXT,
        manager_name TEXT
    )
    ''')
    
    # 2. Employees Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        salary INTEGER,
        department_id INTEGER,
        hire_date DATE,
        FOREIGN KEY(department_id) REFERENCES departments(id)
    )
    ''')
    
    # 3. Projects Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        name TEXT,
        budget INTEGER,
        deadline DATE,
        department_id INTEGER,
        status TEXT,
        FOREIGN KEY(department_id) REFERENCES departments(id)
    )
    ''')
    conn.commit()

def generate_data(conn):
    c = conn.cursor()
    
    # --- Clear existing data (idempotent) ---
    c.execute("DELETE FROM projects")
    c.execute("DELETE FROM employees")
    c.execute("DELETE FROM departments")
    
    # --- Generate Departments ---
    departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Legal', 'Product']
    dept_ids = []
    
    print("🌱 Seeding Departments...")
    for i, dept_name in enumerate(departments, 1):
        c.execute("INSERT INTO departments VALUES (?, ?, ?)", 
                  (i, dept_name, fake.name()))
        dept_ids.append(i)

    # --- Generate Employees (50 rows) ---
    print("🌱 Seeding Employees...")
    for _ in range(50):
        name = fake.name()
        email = fake.email()
        salary = random.randint(45000, 150000)
        dept_id = random.choice(dept_ids)
        hire_date = fake.date_between(start_date='-5y', end_date='today')
        
        c.execute("INSERT INTO employees (name, email, salary, department_id, hire_date) VALUES (?, ?, ?, ?, ?)",
                  (name, email, salary, dept_id, hire_date))

    # --- Generate Projects (20 rows) ---
    print("🌱 Seeding Projects...")
    project_statuses = ['Not Started', 'In Progress', 'Completed', 'On Hold']
    
    for _ in range(20):
        name = fake.bs().title()  # Generates fake business phrases
        budget = random.randint(10000, 500000)
        deadline = fake.date_between(start_date='today', end_date='+1y')
        dept_id = random.choice(dept_ids)
        status = random.choice(project_statuses)
        
        c.execute("INSERT INTO projects (name, budget, deadline, department_id, status) VALUES (?, ?, ?, ?, ?)",
                  (name, budget, deadline, dept_id, status))

    conn.commit()
    print("✅ Database populated successfully!")

if __name__ == "__main__":
    conn = create_connection()
    create_tables(conn)
    generate_data(conn)
    conn.close()