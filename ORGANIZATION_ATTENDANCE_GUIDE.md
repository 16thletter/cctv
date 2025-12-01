# 📊 Organization & Attendance Tracking Guide

Complete guide for managing organizations and tracking employee attendance with automatic IN/OUT counting.

---

## 🎯 **Overview**

The system now supports:
- ✅ **Multiple Organizations**: Track employees from different companies/departments
- ✅ **Automatic Attendance**: IN/OUT counts updated automatically on face recognition
- ✅ **Daily Summaries**: Employee and organization-level reports
- ✅ **Real-time Status**: Know who's currently present
- ✅ **Duration Tracking**: Total time spent inside per day
- ✅ **Peak Occupancy**: Maximum simultaneous presence tracking

---

## 📋 **Database Structure**

### **Organizations Table**
Stores organization/company information:
- Name, Code, Address
- Contact person, email, phone
- Active status

### **Persons Table (Enhanced)**
Employee information now includes:
- Name, Employee ID
- **Organization ID** (links to organization)
- Department, **Designation**
- Email, Phone
- Face embedding reference

### **Employee Attendance Table**
Daily attendance summary per employee:
- **Date**: Attendance date
- **Total IN**: Number of IN events
- **Total OUT**: Number of OUT events
- **First IN Time**: When they first entered
- **Last OUT Time**: When they last exited
- **Total Duration**: Time spent inside (seconds)
- **Is Present**: Currently inside or not

### **Organization Attendance Table**
Daily summary per organization:
- **Date**: Attendance date
- **Total Employees**: Total employees in organization
- **Present Count**: Currently present employees
- **Total IN Count**: Sum of all IN events
- **Total OUT Count**: Sum of all OUT events
- **Peak Occupancy**: Maximum simultaneous presence
- **Peak Time**: When peak occurred

---

## 🚀 **Quick Start**

### **1. Add Organizations**

```bash
# Add first organization
python3 manage_organizations.py add \
  --name "Acme Corporation" \
  --code "ACME" \
  --address "123 Main Street, New York" \
  --contact-person "John Manager" \
  --contact-email "john@acme.com" \
  --contact-phone "+1-555-0100"

# Add second organization
python3 manage_organizations.py add \
  --name "Tech Solutions Inc" \
  --code "TECH" \
  --address "456 Tech Park, San Francisco" \
  --contact-person "Jane Director" \
  --contact-email "jane@techsolutions.com"
```

### **2. List Organizations**

```bash
# List all active organizations
python3 manage_organizations.py list

# List all organizations (including inactive)
python3 manage_organizations.py list --all
```

**Output Example**:
```
+----+---------------------+------+----------------+--------------------+--------+
| ID | Name                | Code | Contact Person | Email              | Active |
+====+=====================+======+================+====================+========+
|  1 | Acme Corporation    | ACME | John Manager   | john@acme.com      | ✓      |
|  2 | Tech Solutions Inc  | TECH | Jane Director  | jane@techsol.com   | ✓      |
+----+---------------------+------+----------------+--------------------+--------+
```

### **3. Enroll Employees with Organization**

```bash
# Enroll employee from Acme Corporation (org_id=1)
python3 enroll_face.py \
  --name "Alice Johnson" \
  --image photos/alice.jpg \
  --employee-id "ACME001" \
  --organization-id 1 \
  --department "Engineering" \
  --designation "Senior Software Engineer" \
  --email "alice@acme.com" \
  --phone "+1-555-0101"

# Enroll employee from Tech Solutions (org_id=2)
python3 enroll_face.py \
  --name "Bob Smith" \
  --webcam \
  --employee-id "TECH001" \
  --organization-id 2 \
  --department "Sales" \
  --designation "Sales Manager"
```

### **4. Run the System**

```bash
# Start the CCTV system
python3 main.py
```

**What happens automatically**:
1. ✅ Person detected and tracked
2. ✅ Face recognized → Person identified
3. ✅ IN/OUT event logged
4. ✅ **Employee attendance updated automatically**
5. ✅ **Organization attendance updated automatically**

---

## 📊 **Viewing Reports**

### **Employee Attendance Report**

```bash
# View last 7 days for employee ID 1
python3 view_attendance.py --employee 1

# View last 30 days
python3 view_attendance.py --employee 1 --days 30
```

**Output Example**:
```
Employee: Alice Johnson
Employee ID: ACME001
Organization: Acme Corporation

+------------+----+-----+----------+----------+----------+-----------+
| Date       | IN | OUT | First IN | Last OUT | Duration | Status    |
+============+====+=====+==========+==========+==========+===========+
| 2024-12-01 |  1 |  1  | 09:15:23 | 18:30:45 | 9h 15m   | ✗ Left    |
| 2024-12-02 |  2 |  1  | 08:45:12 | 17:20:33 | 8h 35m   | ✗ Left    |
| 2024-12-03 |  1 |  0  | 09:00:00 | -        | 0h 0m    | ✓ Present |
+------------+----+-----+----------+----------+----------+-----------+

Summary:
Total IN events: 4
Total OUT events: 2
Total time: 17h 50m
Average per day: 5h 56m
```

### **Organization Attendance Report**

```bash
# View last 7 days for organization ID 1
python3 view_attendance.py --organization 1

# View last 30 days
python3 view_attendance.py --organization 1 --days 30
```

**Output Example**:
```
Organization: Acme Corporation
Code: ACME

+------------+-----------+---------+----------+-----------+------+-----------+
| Date       | Total Emp | Present | Total IN | Total OUT | Peak | Peak Time |
+============+===========+=========+==========+===========+======+===========+
| 2024-12-01 |    25     |    0    |    28    |    28     |  24  | 14:30:15  |
| 2024-12-02 |    25     |    2    |    30    |    28     |  25  | 15:45:22  |
| 2024-12-03 |    25     |    18   |    20    |    2      |  20  | 11:20:10  |
+------------+-----------+---------+----------+-----------+------+-----------+
```

### **Today's Summary (All Organizations)**

```bash
python3 view_attendance.py --today
```

**Output Example**:
```
Today's Attendance Summary - All Organizations

+---------------------+-----------+---------+--------------+----------+-----------+------+
| Organization        | Total Emp | Present | Attendance % | Total IN | Total OUT | Peak |
+=====================+===========+=========+==============+==========+===========+======+
| Acme Corporation    |    25     |   18    |    72.0%     |    20    |     2     |  20  |
| Tech Solutions Inc  |    15     |   12    |    80.0%     |    14    |     2     |  14  |
+---------------------+-----------+---------+--------------+----------+-----------+------+
```

---

## 🔄 **How Automatic Attendance Works**

### **When an IN Event Occurs**:
1. Person crosses counting line (IN direction)
2. Face recognized → Person ID identified
3. Entry/exit log created with person_id
4. **Employee attendance record updated**:
   - `total_in` incremented
   - `is_present` set to `True`
   - `first_in_time` set (if first entry of the day)
5. **Organization attendance updated**:
   - `present_count` incremented
   - `total_in_count` incremented
   - `peak_occupancy` updated if needed

### **When an OUT Event Occurs**:
1. Person crosses counting line (OUT direction)
2. Face recognized → Person ID identified
3. Entry/exit log created with person_id
4. **Employee attendance record updated**:
   - `total_out` incremented
   - `is_present` set to `False`
   - `last_out_time` updated
   - `total_duration_seconds` calculated
5. **Organization attendance updated**:
   - `present_count` decremented
   - `total_out_count` incremented

---

## 💡 **Use Cases**

### **1. Office Building with Multiple Companies**
```bash
# Add each company as an organization
python3 manage_organizations.py add --name "Company A" --code "COMPA"
python3 manage_organizations.py add --name "Company B" --code "COMPB"

# Enroll employees with their respective organizations
python3 enroll_face.py --name "Employee 1" --organization-id 1 ...
python3 enroll_face.py --name "Employee 2" --organization-id 2 ...

# View attendance by organization
python3 view_attendance.py --organization 1
python3 view_attendance.py --organization 2
```

### **2. Single Company with Multiple Departments**
```bash
# Add company as organization
python3 manage_organizations.py add --name "My Company" --code "MYCO"

# Enroll employees with different departments
python3 enroll_face.py --name "Engineer 1" --organization-id 1 --department "Engineering"
python3 enroll_face.py --name "Sales 1" --organization-id 1 --department "Sales"
```

### **3. Track Specific Employee**
```bash
# View detailed attendance for employee
python3 view_attendance.py --employee 5 --days 30

# Check if employee is currently present
# (Look at "Status" column in the latest date)
```

---

## 📈 **Advanced Queries**

You can also query the database directly using Python:

```python
from src.database_pg import PostgreSQLDatabase
from src.utils import load_config
from datetime import date, timedelta

config = load_config()
db = PostgreSQLDatabase(config)

# Get today's attendance for all employees in organization 1
today = date.today()
from src.database_pg import EmployeeAttendance
attendance = db.session.query(EmployeeAttendance).filter_by(
    organization_id=1,
    date=today,
    is_present=True
).all()

print(f"Currently present: {len(attendance)} employees")

# Get employee with most IN events this week
from datetime import timedelta
week_ago = today - timedelta(days=7)
top_employee = db.session.query(EmployeeAttendance).filter(
    EmployeeAttendance.date >= week_ago
).order_by(EmployeeAttendance.total_in.desc()).first()

if top_employee:
    person = db.get_person(top_employee.person_id)
    print(f"Most active: {person.name} ({top_employee.total_in} entries)")
```

---

## 🎯 **Best Practices**

1. **Add Organizations First**: Always create organizations before enrolling employees
2. **Use Unique Employee IDs**: Helps with tracking and reporting
3. **Regular Reports**: Check daily summaries to monitor attendance
4. **Verify Face Recognition**: Ensure high confidence threshold for accurate attendance
5. **Backup Database**: Regular PostgreSQL backups for attendance data

---

**🎉 Your system now tracks employee attendance automatically with organization-level reporting!**

