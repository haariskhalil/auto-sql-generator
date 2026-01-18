import sqlite3

def create_db():
    conn = sqlite3.connect('company.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS departments 
                 (id INTEGER PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS employees 
                 (id INTEGER PRIMARY KEY, name TEXT, salary INTEGER, 
                  department_id INTEGER, hire_date DATE)''')
    
    # Insert data
    c.execute("INSERT OR IGNORE INTO departments VALUES (1, 'Sales'), (2, 'Engineering')")
    c.execute("INSERT OR IGNORE INTO employees VALUES (1, 'Alice', 80000, 2, '2021-01-15')")
    c.execute("INSERT OR IGNORE INTO employees VALUES (2, 'Bob', 60000, 1, '2020-05-20')")
    
    conn.commit()
    conn.close()
    print("Database ready!")

if __name__ == "__main__":
    create_db()