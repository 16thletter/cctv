#!/usr/bin/env python3
"""
CCTV Management REST API with Swagger UI
Complete CRUD operations for all database entities
"""
import sys
import os

from flask import Flask, request
from flask_restx import Api, Resource, fields, Namespace
from flask_cors import CORS
import logging
from datetime import datetime, date
from dotenv import load_dotenv
import cv2

from cctv.utils.utils import load_config
from cctv.database.database_pg import PostgreSQLDatabase
from cctv.features.face_recognition import FaceRecognizer
import base64
import numpy as np

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize API with Swagger documentation
api = Api(
    app,
    version='1.0',
    title='CCTV Management API',
    description='Complete REST API for CCTV People Counter with Face Recognition',
    doc='/api/docs',  # Swagger UI endpoint
    prefix='/api'
)

# Load configuration
config = load_config()
db = PostgreSQLDatabase(config)
face_recognizer = FaceRecognizer(config)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# API NAMESPACES
# ============================================================================
ns_organizations = Namespace('organizations', description='Organization operations')
ns_persons = Namespace('persons', description='Person/Employee operations')
ns_cameras = Namespace('cameras', description='Camera operations')
ns_attendance = Namespace('attendance', description='Attendance operations')
ns_events = Namespace('events', description='Entry/Exit event operations')

api.add_namespace(ns_organizations)
api.add_namespace(ns_persons)
api.add_namespace(ns_cameras)
api.add_namespace(ns_attendance)
api.add_namespace(ns_events)

# ============================================================================
# API MODELS (for Swagger documentation)
# ============================================================================

# Organization models
organization_model = api.model('Organization', {
    'id': fields.Integer(description='Organization ID'),
    'name': fields.String(required=True, description='Organization name'),
    'code': fields.String(description='Organization code'),
    'contact_email': fields.String(description='Contact email'),
    'contact_phone': fields.String(description='Contact phone'),
    'address': fields.String(description='Address'),
    'is_active': fields.Boolean(description='Active status'),
    'created_at': fields.DateTime(description='Creation timestamp')
})

organization_input = api.model('OrganizationInput', {
    'name': fields.String(required=True, description='Organization name'),
    'code': fields.String(description='Organization code'),
    'contact_email': fields.String(description='Contact email'),
    'contact_phone': fields.String(description='Contact phone'),
    'address': fields.String(description='Address')
})

# Person models
person_model = api.model('Person', {
    'id': fields.Integer(description='Person ID'),
    'name': fields.String(required=True, description='Person name'),
    'employee_id': fields.String(description='Employee ID'),
    'organization_id': fields.Integer(description='Organization ID'),
    'department': fields.String(description='Department'),
    'designation': fields.String(description='Job designation'),
    'email': fields.String(description='Email'),
    'phone': fields.String(description='Phone'),
    'is_active': fields.Boolean(description='Active status'),
    'created_at': fields.DateTime(description='Creation timestamp')
})

person_input = api.model('PersonInput', {
    'name': fields.String(required=True, description='Person name'),
    'employee_id': fields.String(description='Employee ID'),
    'organization_id': fields.Integer(description='Organization ID'),
    'department': fields.String(description='Department'),
    'designation': fields.String(description='Job designation'),
    'email': fields.String(description='Email'),
    'phone': fields.String(description='Phone'),
    'face_image_base64': fields.String(description='Base64 encoded face image for enrollment')
})

# Camera models
camera_model = api.model('Camera', {
    'id': fields.Integer(description='Camera ID'),
    'camera_id': fields.String(required=True, description='Camera identifier'),
    'organization_id': fields.Integer(description='Organization ID'),
    'location': fields.String(description='Camera location'),
    'description': fields.String(description='Camera description'),
    'rtsp_url_env': fields.String(description='Environment variable name for RTSP URL'),
    'is_active': fields.Boolean(description='Active status'),
    'created_at': fields.DateTime(description='Creation timestamp')
})

camera_input = api.model('CameraInput', {
    'camera_id': fields.String(required=True, description='Camera identifier'),
    'organization_id': fields.Integer(description='Organization ID'),
    'location': fields.String(description='Camera location'),
    'description': fields.String(description='Camera description'),
    'rtsp_url_env': fields.String(required=True, description='Environment variable name for RTSP URL')
})

# Attendance models
attendance_model = api.model('Attendance', {
    'id': fields.Integer(description='Attendance ID'),
    'person_id': fields.Integer(description='Person ID'),
    'person_name': fields.String(description='Person name'),
    'date': fields.Date(description='Attendance date'),
    'first_in_time': fields.DateTime(description='First IN time'),
    'last_out_time': fields.DateTime(description='Last OUT time'),
    'total_in_count': fields.Integer(description='Total IN count'),
    'total_out_count': fields.Integer(description='Total OUT count'),
    'duration_minutes': fields.Integer(description='Duration in minutes'),
    'is_present': fields.Boolean(description='Present status')
})

# Person update model
person_update_input = api.model('PersonUpdate', {
    'name': fields.String(description='Person name'),
    'employee_id': fields.String(description='Employee ID'),
    'department': fields.String(description='Department'),
    'designation': fields.String(description='Designation'),
    'email': fields.String(description='Email'),
    'phone': fields.String(description='Phone')
})

# Face enrollment model
face_enrollment_input = api.model('FaceEnrollment', {
    'face_image_base64': fields.String(required=True, description='Base64 encoded face image')
})

# Camera update model
camera_update_input = api.model('CameraUpdate', {
    'location': fields.String(description='Camera location'),
    'description': fields.String(description='Camera description'),
    'organization_id': fields.Integer(description='Organization ID')
})

# Camera lines configuration model
camera_lines_input = api.model('CameraLines', {
    'outside_line': fields.String(description='Outside line coordinates (x1,y1,x2,y2)'),
    'inside_line': fields.String(description='Inside line coordinates (x1,y1,x2,y2)'),
    'in_direction': fields.String(description='IN direction (up/down/left/right)')
})

# Camera status model
camera_status_input = api.model('CameraStatus', {
    'is_active': fields.Boolean(required=True, description='Camera active status')
})

# Organization statistics model
organization_stats_model = api.model('OrganizationStats', {
    'organization_id': fields.Integer(description='Organization ID'),
    'organization_name': fields.String(description='Organization name'),
    'total_employees': fields.Integer(description='Total employees'),
    'active_employees': fields.Integer(description='Active employees'),
    'total_cameras': fields.Integer(description='Total cameras'),
    'today_present': fields.Integer(description='Present today'),
    'today_attendance_pct': fields.Float(description='Attendance percentage'),
    'today_total_in': fields.Integer(description='Total IN events today'),
    'today_total_out': fields.Integer(description='Total OUT events today'),
    'today_peak_occupancy': fields.Integer(description='Peak occupancy today')
})

# Detailed attendance model
employee_attendance_detail = api.model('EmployeeAttendanceDetail', {
    'date': fields.Date(description='Date'),
    'total_in': fields.Integer(description='Total IN count'),
    'total_out': fields.Integer(description='Total OUT count'),
    'first_in_time': fields.DateTime(description='First IN time'),
    'last_out_time': fields.DateTime(description='Last OUT time'),
    'total_duration_seconds': fields.Integer(description='Total duration in seconds'),
    'is_present': fields.Boolean(description='Currently present')
})

# ============================================================================
# ORGANIZATION ENDPOINTS
# ============================================================================

@ns_organizations.route('/')
class OrganizationList(Resource):
    @ns_organizations.doc('list_organizations')
    @ns_organizations.marshal_list_with(organization_model)
    def get(self):
        """List all organizations"""
        orgs = db.get_all_organizations()
        return [{
            'id': org.id,
            'name': org.name,
            'code': org.code,
            'contact_email': org.contact_email if hasattr(org, 'contact_email') else None,
            'contact_phone': org.contact_phone if hasattr(org, 'contact_phone') else None,
            'address': org.address if hasattr(org, 'address') else None,
            'is_active': org.is_active,
            'created_at': org.created_at
        } for org in orgs]
    
    @ns_organizations.doc('create_organization')
    @ns_organizations.expect(organization_input)
    @ns_organizations.marshal_with(organization_model, code=201)
    def post(self):
        """Create a new organization"""
        data = request.json
        org_id = db.create_organization(
            name=data['name'],
            code=data.get('code'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            address=data.get('address')
        )
        
        if org_id:
            org = db.get_organization(org_id)
            return {
                'id': org.id,
                'name': org.name,
                'code': org.code,
                'contact_email': org.contact_email if hasattr(org, 'contact_email') else None,
                'is_active': org.is_active,
                'created_at': org.created_at
            }, 201
        else:
            api.abort(500, "Failed to create organization")

@ns_organizations.route('/<int:id>')
class Organization(Resource):
    @ns_organizations.doc('get_organization')
    @ns_organizations.marshal_with(organization_model)
    def get(self, id):
        """Get organization by ID"""
        org = db.get_organization(id)
        if not org:
            api.abort(404, f"Organization {id} not found")
        
        return {
            'id': org.id,
            'name': org.name,
            'code': org.code,
            'is_active': org.is_active,
            'created_at': org.created_at
        }
    
    @ns_organizations.doc('update_organization')
    @ns_organizations.expect(organization_input)
    @ns_organizations.marshal_with(organization_model)
    def put(self, id):
        """Update an organization"""
        data = request.json
        success = db.update_organization(id, **data)
        
        if success:
            org = db.get_organization(id)
            return {
                'id': org.id,
                'name': org.name,
                'code': org.code,
                'is_active': org.is_active,
                'created_at': org.created_at
            }
        else:
            api.abort(500, "Failed to update organization")
    
    @ns_organizations.doc('delete_organization')
    def delete(self, id):
        """Delete an organization"""
        success = db.delete_organization(id)
        if success:
            return {'message': 'Organization deleted successfully'}
        else:
            api.abort(500, "Failed to delete organization")

@ns_organizations.route('/<int:id>/stats')
class OrganizationStats(Resource):
    @ns_organizations.doc('get_organization_stats')
    @ns_organizations.marshal_with(organization_stats_model)
    def get(self, id):
        """Get organization statistics including today's attendance"""
        org = db.get_organization(id)
        if not org:
            api.abort(404, f"Organization {id} not found")
        
        # Count employees
        from cctv.database.database_pg import Person, Camera
        total_employees = db.session.query(Person).filter_by(organization_id=id).count()
        active_employees = db.session.query(Person).filter_by(organization_id=id, is_active=True).count()
        
        # Count cameras
        total_cameras = db.session.query(Camera).filter_by(organization_id=id, is_active=True).count()
        
        # Get today's attendance
        today = date.today()
        attendance = db.get_organization_attendance(id, start_date=today, end_date=today)
        
        today_present = 0
        today_attendance_pct = 0.0
        today_total_in = 0
        today_total_out = 0
        today_peak_occupancy = 0
        
        if attendance and len(attendance) > 0:
            att = attendance[0]
            today_present = att.present_count if hasattr(att, 'present_count') else 0
            today_total_in = att.total_in_count if hasattr(att, 'total_in_count') else 0
            today_total_out = att.total_out_count if hasattr(att, 'total_out_count') else 0
            today_peak_occupancy = att.peak_occupancy if hasattr(att, 'peak_occupancy') else 0
            
            if att.total_employees and att.total_employees > 0:
                today_attendance_pct = (today_present / att.total_employees) * 100
        
        return {
            'organization_id': id,
            'organization_name': org.name,
            'total_employees': total_employees,
            'active_employees': active_employees,
            'total_cameras': total_cameras,
            'today_present': today_present,
            'today_attendance_pct': round(today_attendance_pct, 2),
            'today_total_in': today_total_in,
            'today_total_out': today_total_out,
            'today_peak_occupancy': today_peak_occupancy
        }

@ns_organizations.route('/<int:id>/attendance')
class OrganizationAttendance(Resource):
    @ns_organizations.doc('get_organization_attendance')
    @ns_organizations.param('start_date', 'Start date (YYYY-MM-DD)')
    @ns_organizations.param('end_date', 'End date (YYYY-MM-DD)')
    @ns_organizations.param('days', 'Number of days to look back (default: 7)')
    def get(self, id):
        """Get attendance history for an organization"""
        org = db.get_organization(id)
        if not org:
            api.abort(404, f"Organization {id} not found")
        
        # Parse date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        days = request.args.get('days', type=int, default=7)
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            from datetime import timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
        
        attendance = db.get_organization_attendance(id, start_date, end_date)
        
        return {
            'success': True,
            'organization_id': id,
            'organization_name': org.name,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'attendance': [{
                'date': att.date.isoformat() if att.date else None,
                'total_employees': att.total_employees if hasattr(att, 'total_employees') else 0,
                'present_count': att.present_count if hasattr(att, 'present_count') else 0,
                'total_in_count': att.total_in_count if hasattr(att, 'total_in_count') else 0,
                'total_out_count': att.total_out_count if hasattr(att, 'total_out_count') else 0,
                'peak_occupancy': att.peak_occupancy if hasattr(att, 'peak_occupancy') else 0,
                'peak_time': att.peak_time.isoformat() if hasattr(att, 'peak_time') and att.peak_time else None
            } for att in attendance]
        }


# ============================================================================
# PERSON ENDPOINTS
# ============================================================================

@ns_persons.route('/')
class PersonList(Resource):
    @ns_persons.doc('list_persons')
    @ns_persons.param('organization_id', 'Filter by organization ID')
    @ns_persons.param('search', 'Search by name or employee ID')
    @ns_persons.marshal_list_with(person_model)
    def get(self):
        """List all persons"""
        org_id = request.args.get('organization_id', type=int)
        search = request.args.get('search')
        
        if org_id:
            persons = db.get_persons_by_organization(org_id)
        elif search:
            # Implement search inline since db.search_persons doesn't exist
            from cctv.database.database_pg import Person
            from sqlalchemy import or_
            
            search_pattern = f"%{search}%"
            persons = db.session.query(Person).filter(
                or_(
                    Person.name.ilike(search_pattern),
                    Person.employee_id.ilike(search_pattern),
                    Person.email.ilike(search_pattern),
                    Person.phone.ilike(search_pattern)
                )
            ).all()
        else:
            persons = db.get_all_persons()
        
        return [{
            'id': p.id,
            'name': p.name,
            'employee_id': p.employee_id if hasattr(p, 'employee_id') else None,
            'organization_id': p.organization_id,
            'department': p.department if hasattr(p, 'department') else None,
            'designation': p.designation if hasattr(p, 'designation') else None,
            'email': p.email if hasattr(p, 'email') else None,
            'phone': p.phone if hasattr(p, 'phone') else None,
            'is_active': p.is_active,
            'created_at': p.created_at
        } for p in persons]
    
    @ns_persons.doc('create_person')
    @ns_persons.expect(person_input)
    @ns_persons.marshal_with(person_model, code=201)
    def post(self):
        """Create a new person and optionally enroll face"""
        data = request.json
        
        # Create person
        person_id = db.create_person(
            name=data['name'],
            employee_id=data.get('employee_id'),
            organization_id=data.get('organization_id'),
            department=data.get('department'),
            designation=data.get('designation'),
            email=data.get('email'),
            phone=data.get('phone')
        )
        
        if not person_id:
            api.abort(500, "Failed to create person")
        
        # Enroll face if image provided
        if data.get('face_image_base64'):
            try:
                # Decode base64 image
                img_data = base64.b64decode(data['face_image_base64'])
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Extract face embedding
                embedding = face_recognizer.extract_embedding(img)
                
                if embedding is not None:
                    db.add_face_embedding(person_id, embedding)
                else:
                    logger.warning(f"No face detected in image for person {person_id}")
            except Exception as e:
                logger.error(f"Failed to enroll face: {e}")
        
        person = db.get_person(person_id)
        return {
            'id': person.id,
            'name': person.name,
            'employee_id': person.employee_id if hasattr(person, 'employee_id') else None,
            'organization_id': person.organization_id,
            'is_active': person.is_active,
            'created_at': person.created_at
        }, 201

@ns_persons.route('/<int:id>')
class Person(Resource):
    @ns_persons.doc('get_person')
    @ns_persons.marshal_with(person_model)
    def get(self, id):
        """Get person by ID"""
        person = db.get_person(id)
        if not person:
            api.abort(404, f"Person {id} not found")
        
        return {
            'id': person.id,
            'name': person.name,
            'employee_id': person.employee_id if hasattr(person, 'employee_id') else None,
            'organization_id': person.organization_id,
            'department': person.department if hasattr(person, 'department') else None,
            'designation': person.designation if hasattr(person, 'designation') else None,
            'email': person.email if hasattr(person, 'email') else None,
            'phone': person.phone if hasattr(person, 'phone') else None,
            'is_active': person.is_active,
            'created_at': person.created_at
        }
    
    @ns_persons.doc('delete_person')
    def delete(self, id):
        """Delete a person"""
        success = db.delete_person(id)
        if success:
            return {'message': 'Person deleted successfully'}
        else:
            api.abort(500, "Failed to delete person")
    
    @ns_persons.doc('update_person')
    @ns_persons.expect(person_update_input)
    @ns_persons.marshal_with(person_model)
    def put(self, id):
        """Update person details"""
        person = db.get_person(id)
        if not person:
            api.abort(404, f"Person {id} not found")
        
        data = request.json
        success = db.update_person(id, **data)
        
        if success:
            person = db.get_person(id)
            return {
                'id': person.id,
                'name': person.name,
                'employee_id': person.employee_id if hasattr(person, 'employee_id') else None,
                'organization_id': person.organization_id,
                'department': person.department if hasattr(person, 'department') else None,
                'designation': person.designation if hasattr(person, 'designation') else None,
                'email': person.email if hasattr(person, 'email') else None,
                'phone': person.phone if hasattr(person, 'phone') else None,
                'is_active': person.is_active,
                'created_at': person.created_at
            }
        else:
            api.abort(500, "Failed to update person")

@ns_persons.route('/search')
class PersonSearch(Resource):
    @ns_persons.doc('search_persons')
    @ns_persons.param('q', 'Search query (name, employee_id, email, phone)')
    @ns_persons.marshal_list_with(person_model)
    def get(self):
        """Search persons by query"""
        query = request.args.get('q', '').strip()
        if not query:
            api.abort(400, "Search query ' q' parameter is required")
        
        # Implement search inline since db.search_persons doesn't exist
        from cctv.database.database_pg import Person
        from sqlalchemy import or_
        
        search_pattern = f"%{query}%"
        persons = db.session.query(Person).filter(
            or_(
                Person.name.ilike(search_pattern),
                Person.employee_id.ilike(search_pattern),
                Person.email.ilike(search_pattern),
                Person.phone.ilike(search_pattern)
            )
        ).all()
        
        return [{
            'id': p.id,
            'name': p.name,
            'employee_id': p.employee_id if hasattr(p, 'employee_id') else None,
            'organization_id': p.organization_id,
            'department': p.department if hasattr(p, 'department') else None,
            'designation': p.designation if hasattr(p, 'designation') else None,
            'email': p.email if hasattr(p, 'email') else None,
            'phone': p.phone if hasattr(p, 'phone') else None,
            'is_active': p.is_active,
            'created_at': p.created_at
        } for p in persons]

@ns_persons.route('/<int:id>/enroll-face')
class PersonFaceEnrollment(Resource):
    @ns_persons.doc('enroll_person_face')
    @ns_persons.expect(face_enrollment_input)
    def post(self, id):
        """Enroll or update face embedding for existing person"""
        person = db.get_person(id)
        if not person:
            api.abort(404, f"Person {id} not found")
        
        data = request.json
        if not data.get('face_image_base64'):
            api.abort(400, "face_image_base64 is required")
        
        try:
            # Decode base64 image
            img_data = base64.b64decode(data['face_image_base64'])
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                api.abort(400, "Invalid image data")
            
            # Extract face embedding
            embedding = face_recognizer.extract_embedding(img)
            
            if embedding is not None:
                # Delete existing embeddings for this person
                db.delete_face_embeddings(id)
                # Add new embedding
                db.add_face_embedding(id, embedding)
                return {
                    'success': True,
                    'message': 'Face enrolled successfully',
                    'person_id': id,
                    'person_name': person.name
                }
            else:
                return {
                    'success': False,
                    'message': 'No face detected in image',
                    'person_id': id
                }, 400
        except Exception as e:
            logger.error(f"Failed to enroll face: {e}")
            api.abort(500, f"Failed to enroll face: {str(e)}")

@ns_persons.route('/<int:id>/attendance')
class PersonAttendance(Resource):
    @ns_persons.doc('get_person_attendance')
    @ns_persons.param('start_date', 'Start date (YYYY-MM-DD)')
    @ns_persons.param('end_date', 'End date (YYYY-MM-DD)')
    @ns_persons.param('days', 'Number of days to look back (default: 7)')
    @ns_persons.marshal_list_with(employee_attendance_detail)
    def get(self, id):
        """Get attendance history for a person"""
        person = db.get_person(id)
        if not person:
            api.abort(404, f"Person {id} not found")
        
        # Parse date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        days = request.args.get('days', type=int, default=7)
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            from datetime import timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
        
        attendance = db.get_employee_attendance(id, start_date, end_date)
        
        return [{
            'date': att.date,
            'total_in': att.total_in,
            'total_out': att.total_out,
            'first_in_time': att.first_in_time,
            'last_out_time': att.last_out_time,
            'total_duration_seconds': att.total_duration_seconds,
            'is_present': att.is_present
        } for att in attendance]


# ============================================================================
# CAMERA ENDPOINTS
# ============================================================================

@ns_cameras.route('/')
class CameraList(Resource):
    @ns_cameras.doc('list_cameras')
    @ns_cameras.param('organization_id', 'Filter by organization ID')
    @ns_cameras.marshal_list_with(camera_model)
    def get(self):
        """List all cameras"""
        org_id = request.args.get('organization_id', type=int)
        
        if org_id:
            cameras = db.get_cameras_by_organization(org_id)
        else:
            cameras = db.get_all_cameras()
        
        return [{
            'id': cam.id,
            'camera_id': cam.camera_id,
            'organization_id': cam.organization_id,
            'location': cam.location,
            'description': cam.description,
            'rtsp_url_env': cam.rtsp_url_env,
            'is_active': cam.is_active,
            'created_at': cam.created_at
        } for cam in cameras]
    
    @ns_cameras.doc('create_camera')
    @ns_cameras.expect(camera_input)
    @ns_cameras.marshal_with(camera_model, code=201)
    def post(self):
        """Create a new camera"""
        data = request.json
        
        # Verify environment variable exists
        rtsp_url = os.getenv(data['rtsp_url_env'])
        if not rtsp_url:
            api.abort(400, f"Environment variable '{data['rtsp_url_env']}' not found in .env file")
        
        camera_id = db.add_camera(
            camera_id=data['camera_id'],
            rtsp_url_env=data['rtsp_url_env'],
            location=data.get('location'),
            organization_id=data.get('organization_id'),
            description=data.get('description')
        )
        
        if camera_id:
            camera = db.get_camera_by_id(camera_id)
            return {
                'id': camera.id,
                'camera_id': camera.camera_id,
                'organization_id': camera.organization_id,
                'location': camera.location,
                'rtsp_url_env': camera.rtsp_url_env,
                'is_active': camera.is_active,
                'created_at': camera.created_at
            }, 201
        else:
            api.abort(500, "Failed to create camera")

@ns_cameras.route('/<string:camera_id>')
class Camera(Resource):
    @ns_cameras.doc('get_camera')
    @ns_cameras.marshal_with(camera_model)
    def get(self, camera_id):
        """Get camera by ID"""
        camera = db.get_camera(camera_id)
        if not camera:
            api.abort(404, f"Camera {camera_id} not found")
        
        return {
            'id': camera.id,
            'camera_id': camera.camera_id,
            'organization_id': camera.organization_id,
            'location': camera.location,
            'description': camera.description,
            'rtsp_url_env': camera.rtsp_url_env,
            'is_active': camera.is_active,
            'created_at': camera.created_at
        }
    
    @ns_cameras.doc('update_camera')
    @ns_cameras.expect(camera_update_input)
    @ns_cameras.marshal_with(camera_model)
    def put(self, camera_id):
        """Update camera details"""
        camera = db.get_camera(camera_id)
        if not camera:
            api.abort(404, f"Camera {camera_id} not found")
        
        data = request.json
        success = db.update_camera(camera_id, **data)
        
        if success:
            camera = db.get_camera(camera_id)
            return {
                'id': camera.id,
                'camera_id': camera.camera_id,
                'organization_id': camera.organization_id,
                'location': camera.location,
                'description': camera.description,
                'rtsp_url_env': camera.rtsp_url_env,
                'is_active': camera.is_active,
                'created_at': camera.created_at
            }
        else:
            api.abort(500, "Failed to update camera")
    
    @ns_cameras.doc('delete_camera')
    def delete(self, camera_id):
        """Delete camera (soft delete - deactivate)"""
        camera = db.get_camera(camera_id)
        if not camera:
            api.abort(404, f"Camera {camera_id} not found")
        
        success = db.update_camera(camera_id, is_active=False)
        if success:
            return {'message': 'Camera deleted successfully', 'camera_id': camera_id}
        else:
            api.abort(500, "Failed to delete camera")

@ns_cameras.route('/<string:camera_id>/lines')
class CameraLines(Resource):
    @ns_cameras.doc('update_camera_lines')
    @ns_cameras.expect(camera_lines_input)
    def put(self, camera_id):
        """Update camera counting lines configuration"""
        camera = db.get_camera(camera_id)
        if not camera:
            api.abort(404, f"Camera {camera_id} not found")
        
        data = request.json
        
        # Parse line coordinates
        update_data = {}
        if 'outside_line' in data and data['outside_line']:
            try:
                coords = [int(x) for x in data['outside_line'].split(',')]
                if len(coords) != 4:
                    api.abort(400, "outside_line must be in format 'x1,y1,x2,y2'")
                update_data['outside_line'] = data['outside_line']
            except ValueError:
                api.abort(400, "Invalid outside_line coordinates")
        
        if 'inside_line' in data and data['inside_line']:
            try:
                coords = [int(x) for x in data['inside_line'].split(',')]
                if len(coords) != 4:
                    api.abort(400, "inside_line must be in format 'x1,y1,x2,y2'")
                update_data['inside_line'] = data['inside_line']
            except ValueError:
                api.abort(400, "Invalid inside_line coordinates")
        
        if 'in_direction' in data and data['in_direction']:
            if data['in_direction'] not in ['up', 'down', 'left', 'right']:
                api.abort(400, "in_direction must be one of: up, down, left, right")
            update_data['in_direction'] = data['in_direction']
        
        success = db.update_camera(camera_id, **update_data)
        
        if success:
            return {
                'success': True,
                'message': 'Camera lines updated successfully',
                'camera_id': camera_id,
                **update_data
            }
        else:
            api.abort(500, "Failed to update camera lines")

@ns_cameras.route('/<string:camera_id>/test')
class CameraTest(Resource):
    @ns_cameras.doc('test_camera')
    def get(self, camera_id):
        """Test camera RTSP connectivity"""
        camera = db.get_camera(camera_id)
        if not camera:
            api.abort(404, f"Camera {camera_id} not found")
        
        # Get RTSP URL from environment
        rtsp_url = os.getenv(camera.rtsp_url_env)
        if not rtsp_url:
            return {
                'success': False,
                'camera_id': camera_id,
                'accessible': False,
                'error': f"Environment variable '{camera.rtsp_url_env}' not found"
            }, 400
        
        # Try to open camera
        try:
            cap = cv2.VideoCapture(rtsp_url)
            is_accessible = cap.isOpened()
            cap.release()
            
            return {
                'success': True,
                'camera_id': camera_id,
                'accessible': is_accessible,
                'rtsp_url_env': camera.rtsp_url_env
            }
        except Exception as e:
            logger.error(f"Error testing camera: {e}")
            return {
                'success': False,
                'camera_id': camera_id,
                'accessible': False,
                'error': str(e)
            }, 500

@ns_cameras.route('/<string:camera_id>/status')
class CameraStatus(Resource):
    @ns_cameras.doc('update_camera_status')
    @ns_cameras.expect(camera_status_input)
    def put(self, camera_id):
        """Activate or deactivate camera"""
        camera = db.get_camera(camera_id)
        if not camera:
            api.abort(404, f"Camera {camera_id} not found")
        
        data = request.json
        if 'is_active' not in data:
            api.abort(400, "is_active field is required")
        
        success = db.update_camera(camera_id, is_active=data['is_active'])
        
        if success:
            status = 'activated' if data['is_active'] else 'deactivated'
            return {
                'success': True,
                'message': f'Camera {status} successfully',
                'camera_id': camera_id,
                'is_active': data['is_active']
            }
        else:
            api.abort(500, "Failed to update camera status")


# ============================================================================
# ATTENDANCE ENDPOINTS
# ============================================================================

@ns_attendance.route('/')
class AttendanceList(Resource):
    @ns_attendance.doc('list_attendance')
    @ns_attendance.param('date', 'Filter by date (YYYY-MM-DD)')
    @ns_attendance.param('organization_id', 'Filter by organization ID')
    @ns_attendance.param('person_id', 'Filter by person ID')
    @ns_attendance.marshal_list_with(attendance_model)
    def get(self):
        """List attendance records"""
        date_str = request.args.get('date')
        org_id = request.args.get('organization_id', type=int)
        person_id = request.args.get('person_id', type=int)
        
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        attendance_records = db.get_attendance(
            date=target_date,
            organization_id=org_id,
            person_id=person_id
        )
        
        return [{
            'id': att.id if hasattr(att, 'id') else None,
            'person_id': att.person_id,
            'person_name': db.get_person(att.person_id).name if att.person_id else 'Unknown',
            'date': att.date,
            'first_in_time': att.first_in_time,
            'last_out_time': att.last_out_time,
            'total_in_count': att.total_in_count,
            'total_out_count': att.total_out_count,
            'duration_minutes': att.duration_minutes,
            'is_present': att.is_present
        } for att in attendance_records]

@ns_attendance.route('/today-summary')
class AttendanceTodaySummary(Resource):
    @ns_attendance.doc('get_today_summary')
    def get(self):
        """Get today's attendance summary for all organizations"""
        today = date.today()
        orgs = db.get_all_organizations(active_only=True)
        
        if not orgs:
            return {
                'success': True,
                'date': today.isoformat(),
                'organizations': []
            }
        
        summary_data = []
        
        for org in orgs:
            attendance = db.get_organization_attendance(org.id, start_date=today, end_date=today)
            
            if attendance and len(attendance) > 0:
                att = attendance[0]
                attendance_pct = 0.0
                if hasattr(att, 'total_employees') and att.total_employees > 0:
                    present = att.present_count if hasattr(att, 'present_count') else 0
                    attendance_pct = (present / att.total_employees) * 100
                
                summary_data.append({
                    'organization_id': org.id,
                    'organization_name': org.name,
                    'total_employees': att.total_employees if hasattr(att, 'total_employees') else 0,
                    'present_count': att.present_count if hasattr(att, 'present_count') else 0,
                    'attendance_pct': round(attendance_pct, 1),
                    'total_in_count': att.total_in_count if hasattr(att, 'total_in_count') else 0,
                    'total_out_count': att.total_out_count if hasattr(att, 'total_out_count') else 0,
                    'peak_occupancy': att.peak_occupancy if hasattr(att, 'peak_occupancy') else 0
                })
            else:
                # Count employees even if no attendance data
                from cctv.database.database_pg import Person
                emp_count = db.session.query(Person).filter_by(
                    organization_id=org.id,
                    is_active=True
                ).count()
                
                summary_data.append({
                    'organization_id': org.id,
                    'organization_name': org.name,
                    'total_employees': emp_count,
                    'present_count': 0,
                    'attendance_pct': 0.0,
                    'total_in_count': 0,
                    'total_out_count': 0,
                    'peak_occupancy': 0
                })
        
        return {
            'success': True,
            'date': today.isoformat(),
            'total_organizations': len(summary_data),
            'organizations': summary_data
        }


# ============================================================================
# EVENT ENDPOINTS
# ============================================================================

@ns_events.route('/')
class EventList(Resource):
    @ns_events.doc('list_events')
    @ns_events.param('limit', 'Limit number of results (default: 100)')
    @ns_events.param('camera_id', 'Filter by camera ID')
    def get(self):
        """List entry/exit events"""
        limit = request.args.get('limit', default=100, type=int)
        camera_id = request.args.get('camera_id')
        
        events = db.get_recent_events(limit=limit, camera_id=camera_id)
        
        return {
            'success': True,
            'count': len(events),
            'events': [{
                'id': evt.id if hasattr(evt, 'id') else None,
                'timestamp': evt.timestamp.isoformat() if evt.timestamp else None,
                'event_type': evt.event_type,
                'person_id': evt.person_id,
                'person_name': db.get_person(evt.person_id).name if evt.person_id else 'Anonymous',
                'camera_id': evt.camera_id if hasattr(evt, 'camera_id') else None,
                'count_in': evt.count_in if hasattr(evt, 'count_in') else 0,
                'count_out': evt.count_out if hasattr(evt, 'count_out') else 0
            } for evt in events]
        }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@api.route('/health')
class Health(Resource):
    def get(self):
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'database': 'connected' if db.session else 'disconnected',
            'face_recognition': 'enabled' if face_recognizer.is_enabled() else 'disabled'
        }

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("CCTV Management API Server")
    logger.info("=" * 60)
    logger.info("Swagger UI: http://localhost:5000/api/docs")
    logger.info("API Base URL: http://localhost:5000/api")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
