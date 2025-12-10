# Quick Command Reference
**Important:** Always activate virtual environment first!```bashsource venv/bin/activate```
---
## Organization Management
### Add Organization```bashpython3 manage_organizations.py add \ --name "Company Name" \ --description "Description" \ --contact-email "admin@company.com" \ --contact-phone "+1234567890"```
### List Organizations```bash# List active organizationspython3 manage_organizations.py list
# List all organizations (including inactive)python3 manage_organizations.py list --all```
### View Organization Statistics```bashpython3 manage_organizations.py stats --id 1```
---
## Camera Management
### Add Camera (Default Settings)```bash# Camera will use default counting lines from config.yamlpython3 manage_cameras.py add \ --camera-id entrance \ --rtsp-url-env CAMERA_ENTRANCE_URL \ --location "Main Entrance" \ --organization-id 1 \ --description "Front door camera"```
### Add Camera (Custom Counting Lines)```bash# Camera with custom horizontal counting linespython3 manage_cameras.py add \ --camera-id exit \ --rtsp-url-env CAMERA_EXIT_URL \ --location "Main Exit" \ --organization-id 1 \ --outside-line 0.30,0.50,0.70,0.50 \ --inside-line 0.30,0.56,0.70,0.56 \ --in-direction up
# Camera with vertical counting lines (side entrance)python3 manage_cameras.py add \ --camera-id side_entrance \ --rtsp-url-env CAMERA_SIDE_URL \ --location "Side Entrance" \ --organization-id 1 \ --outside-line 0.45,0.30,0.45,0.70 \ --inside-line 0.52,0.30,0.52,0.70 \ --in-direction right```
### Update Camera Counting Lines```bash# Update counting lines for existing camerapython3 manage_cameras.py update-lines \ --camera-id entrance \ --outside-line 0.35,0.48,0.65,0.48 \ --inside-line 0.35,0.54,0.65,0.54 \ --in-direction down```
### List Cameras```bash# List all cameraspython3 manage_cameras.py list
# List cameras for specific organizationpython3 manage_cameras.py list --organization-id 1
# List all cameras (including inactive)python3 manage_cameras.py list --all```
### View Camera Details```bashpython3 manage_cameras.py view --camera-id entrance```
---
## Employee Management
### Enroll Employee (with webcam)```bashpython3 enroll_face.py \ --name "John Doe" \ --employee-id "EMP001" \ --organization-id 1 \ --designation "Manager" \ --email "john.doe@company.com" \ --phone "+1234567890"
# Follow on-screen instructions:# - Press SPACE to capture face# - Press 'q' to quit```
### Enroll Employee (from image file)```bashpython3 enroll_face.py \ --name "Jane Smith" \ --employee-id "EMP002" \ --organization-id 1 \ --designation "Developer" \ --image /path/to/photo.jpg```
---
## Check IN/OUT Events
### Quick Check (Recent Events)```bashbash quick_check.sh```
### Detailed Report (All Statistics)```bashbash check_entries.sh```
### Direct Database Query (Last 20 Events)```bashpsql -h localhost -U postgres -d face_recognition -c \ "SELECT * FROM counting_events ORDER BY timestamp DESC LIMIT 20;"```
### Check Current Occupancy```bashpsql -h localhost -U postgres -d face_recognition -c \ "SELECT camera_id, location, (SELECT occupancy FROM counting_events WHERE camera_id = c.id ORDER BY timestamp DESC LIMIT 1) as occupancy, (SELECT count_in FROM counting_events WHERE camera_id = c.id ORDER BY timestamp DESC LIMIT 1) as total_in, (SELECT count_out FROM counting_events WHERE camera_id = c.id ORDER BY timestamp DESC LIMIT 1) as total_out FROM cameras c WHERE is_active = true;"```
---
## Running the System
### List Available Cameras```bashpython3 run_cameras.py --list```
### Run Single Camera```bashpython3 run_cameras.py --camera-id entrance```
### Run All Cameras```bashpython3 run_cameras.py```
### Run Cameras for Specific Organization```bashpython3 run_cameras.py --organization-id 1```
---
## Attendance Reports
### View Today's Attendance```bash# All organizationspython3 view_attendance.py
# Specific organizationpython3 view_attendance.py --organization-id 1```
### View Specific Date```bashpython3 view_attendance.py --date 2024-01-15```
### View Date Range```bashpython3 view_attendance.py \ --start-date 2024-01-01 \ --end-date 2024-01-31```
### Export to CSV```bashpython3 view_attendance.py --export attendance_report.csv```
---
## Calibration & Testing
### Calibrate Counting Lines```bashpython3 calibrate_two_lines.py```
### Test Camera Connection```bashpython3 -c "import cv2import osfrom dotenv import load_dotenvload_dotenv()url = os.getenv('CAMERA_ENTRANCE_URL')cap = cv2.VideoCapture(url)print(' Connected!' if cap.isOpened() else ' Failed!')cap.release()"```
### Verify Installation```bashpython3 verify_installation.py```
---
## Database Management
### Setup Database```bashpython3 setup_database.py --password your_password```
### Backup Database```bashpg_dump -U postgres face_recognition > backup_$(date +%Y%m%d).sql```
### Restore Database```bashpsql -U postgres face_recognition < backup_20240115.sql```
---
## REST API (Optional)
### Start API Server```bashpython3 camera_api.py```
### API Endpoints```bash# Get all camerascurl http://localhost:5000/api/cameras
# Get cameras for organizationcurl http://localhost:5000/api/cameras?organization_id=1
# Add cameracurl -X POST http://localhost:5000/api/cameras \ -H "Content-Type: application/json" \ -d '{ "camera_id": "new_camera", "rtsp_url_env": "CAMERA_NEW_URL", "location": "New Location", "organization_id": 1 }'
# Test cameracurl http://localhost:5000/api/test-camera/entrance
# Get organizationscurl http://localhost:5000/api/organizations```
---
## Common Workflows
### Complete Setup Workflow```bash# 1. Activate virtual environmentsource venv/bin/activate
# 2. Add organizationpython3 manage_organizations.py add --name "Company A"
# 3. Add camerapython3 manage_cameras.py add \ --camera-id entrance \ --rtsp-url-env CAMERA_ENTRANCE_URL \ --organization-id 1
# 4. Enroll employeespython3 enroll_face.py --name "John Doe" --employee-id "EMP001" --organization-id 1
# 5. Calibratepython3 calibrate_two_lines.py
# 6. Run systempython3 run_cameras.py```
### Daily Operations```bash# Start systemsource venv/bin/activatepython3 run_cameras.py
# View attendance (in another terminal)source venv/bin/activatepython3 view_attendance.py```
### Adding New Camera```bash# 1. Add RTSP URL to .envecho "CAMERA_NEW_URL=rtsp://admin:pass@192.168.1.104:554/stream1" >> .env
# 2. Add to databasepython3 manage_cameras.py add \ --camera-id new_camera \ --rtsp-url-env CAMERA_NEW_URL \ --organization-id 1
# 3. Run (no restart needed!)python3 run_cameras.py```
---
## Troubleshooting Commands
### Check System Status```bash# Check PostgreSQLsudo systemctl status postgresql
# Check virtual environmentwhich python3 # Should show venv path
# Check installed packagespip list | grep -E "numpy|opencv|insightface"```
### View Logs```bash# Application logstail -f logs/app.log
# PostgreSQL logssudo tail -f /var/log/postgresql/postgresql-14-main.log```
### Database Queries```bash# Connect to databasepsql -h localhost -U postgres -d face_recognition
# Useful queries:SELECT * FROM organizations;SELECT * FROM cameras WHERE is_active = true;SELECT * FROM persons WHERE organization_id = 1;SELECT COUNT(*) FROM entry_exit_events WHERE DATE(timestamp) = CURRENT_DATE;```
---
** Tip:** Bookmark this file for quick reference!
