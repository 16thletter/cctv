"""
PostgreSQL Database Manager for Face Recognition System
Supports multi-camera setup with face recognition and tracking
"""
import logging
import numpy as np
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


# ============================================================================
# DATABASE MODELS
# ============================================================================

class Organization(Base):
    """Organization model"""
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(50), unique=True)
    address = Column(Text)
    contact_person = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    cameras = relationship("Camera", back_populates="organization")
    persons = relationship("Person", back_populates="organization")


class Camera(Base):
    """Camera model"""
    __tablename__ = 'cameras'

    id = Column(Integer, primary_key=True)
    camera_id = Column(String(50), unique=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='SET NULL'))
    location = Column(String(255))
    description = Column(Text)
    rtsp_url = Column(String(500))  # RTSP URL directly stored in database
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Counting line configuration (NULL = use defaults from config.yaml)
    outside_line_x1 = Column(Float, nullable=True)
    outside_line_y1 = Column(Float, nullable=True)
    outside_line_x2 = Column(Float, nullable=True)
    outside_line_y2 = Column(Float, nullable=True)
    inside_line_x1 = Column(Float, nullable=True)
    inside_line_y1 = Column(Float, nullable=True)
    inside_line_x2 = Column(Float, nullable=True)
    inside_line_y2 = Column(Float, nullable=True)
    in_direction = Column(String(10), default='down')
    line_color_r = Column(Integer, default=0)
    line_color_g = Column(Integer, default=255)
    line_color_b = Column(Integer, default=0)
    line_thickness = Column(Integer, default=3)
    cooldown_frames = Column(Integer, default=75)
    min_track_length = Column(Integer, default=5)

    # Relationship
    organization = relationship("Organization", back_populates="cameras")


class Person(Base):
    """Person model (known people)"""
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    employee_id = Column(String(100), unique=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='SET NULL'))
    department = Column(String(100))
    designation = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    photo_path = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    organization = relationship("Organization", back_populates="persons")


class FaceEmbedding(Base):
    """Face embedding model (ArcFace 512-dim vectors)"""
    __tablename__ = 'face_embeddings'
    
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id', ondelete='CASCADE'), unique=True)
    embedding = Column(Vector(512), nullable=False)  # ArcFace embeddings
    quality_score = Column(Float)
    source_image_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)


class FaceDetection(Base):
    """Face detection model"""
    __tablename__ = 'face_detections'
    
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'))
    person_id = Column(Integer, ForeignKey('persons.id'))  # NULL if unknown
    track_id = Column(Integer)
    confidence = Column(Float, nullable=False)
    detection_score = Column(Float)
    bbox_x1 = Column(Integer)
    bbox_y1 = Column(Integer)
    bbox_x2 = Column(Integer)
    bbox_y2 = Column(Integer)
    frame_number = Column(Integer)
    snapshot_path = Column(String(500))
    timestamp = Column(DateTime, default=datetime.now)


class EntryExitLog(Base):
    """Entry/Exit log model"""
    __tablename__ = 'entry_exit_logs'
    
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'))
    person_id = Column(Integer, ForeignKey('persons.id'))  # NULL if unknown
    track_id = Column(Integer)
    event_type = Column(String(10), nullable=False)  # 'IN' or 'OUT'
    confidence = Column(Float)
    position_x = Column(Integer)
    position_y = Column(Integer)
    snapshot_path = Column(String(500))
    timestamp = Column(DateTime, default=datetime.now)


class PersonJourney(Base):
    """Person journey model (cross-camera tracking)"""
    __tablename__ = 'person_journey'
    
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))
    from_camera_id = Column(Integer, ForeignKey('cameras.id'))
    to_camera_id = Column(Integer, ForeignKey('cameras.id'))
    from_timestamp = Column(DateTime)
    to_timestamp = Column(DateTime)
    duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)


class CountingEvent(Base):
    """Counting event model (legacy compatibility)"""
    __tablename__ = 'counting_events'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'))
    track_id = Column(Integer)
    event_type = Column(String(10), nullable=False)
    position_x = Column(Integer)
    position_y = Column(Integer)
    count_in = Column(Integer)
    count_out = Column(Integer)
    occupancy = Column(Integer)
    frame_number = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now)


class EmployeeAttendance(Base):
    """Employee attendance summary model"""
    __tablename__ = 'employee_attendance'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id', ondelete='CASCADE'))
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='SET NULL'))
    date = Column(Date, nullable=False)
    total_in = Column(Integer, default=0)
    total_out = Column(Integer, default=0)
    first_in_time = Column(DateTime)
    last_out_time = Column(DateTime)
    total_duration_seconds = Column(Integer, default=0)
    is_present = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class OrganizationAttendance(Base):
    """Organization attendance summary model"""
    __tablename__ = 'organization_attendance'

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'))
    date = Column(Date, nullable=False)
    total_employees = Column(Integer, default=0)
    present_count = Column(Integer, default=0)
    total_in_count = Column(Integer, default=0)
    total_out_count = Column(Integer, default=0)
    peak_occupancy = Column(Integer, default=0)
    peak_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class PostgreSQLDatabase:
    """PostgreSQL database manager with face recognition support"""
    
    def __init__(self, config: Dict):
        """Initialize PostgreSQL connection"""
        self.logger = logging.getLogger(__name__)
        self.config = config.get('database', {})
        
        if not self.config.get('enabled', True):
            self.logger.info("Database disabled")
            self.session = None
            self.engine = None
            return
        
        # Build connection string
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 5432)
        database = self.config.get('database', 'face_recognition')
        user = self.config.get('user', 'postgres')
        password = self.config.get('password', '')
        
        connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'
        
        try:
            # Create engine
            self.engine = create_engine(connection_string, echo=False, pool_size=10, max_overflow=20)

            # Create tables
            Base.metadata.create_all(self.engine)

            # Create session
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

            self.logger.info(f"PostgreSQL database connected: {host}:{port}/{database}")

        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.session = None
            self.engine = None
            raise

    # ========================================================================
    # CAMERA MANAGEMENT
    # ========================================================================

    def add_camera(self, camera_id: str, rtsp_url: str, location: str = None,
                   organization_id: int = None, description: str = None,
                   outside_line: list = None, inside_line: list = None,
                   in_direction: str = None, line_color: list = None,
                   line_thickness: int = None, cooldown_frames: int = None,
                   min_track_length: int = None) -> Optional[int]:
        """
        Add a new camera

        Args:
            camera_id: Unique camera identifier
            rtsp_url: RTSP URL directly (e.g., 'rtsp://user:pass@ip:port/stream')
            location: Camera location description
            organization_id: Organization ID this camera belongs to
            description: Camera description
            outside_line: Outside counting line [x1, y1, x2, y2] (normalized 0.0-1.0)
            inside_line: Inside counting line [x1, y1, x2, y2] (normalized 0.0-1.0)
            in_direction: Direction that counts as IN ('up', 'down', 'left', 'right')
            line_color: Line color [r, g, b] (0-255)
            line_thickness: Line thickness in pixels
            cooldown_frames: Frames to wait before counting same person again
            min_track_length: Minimum track length before counting

        Returns:
            Camera ID if successful, None otherwise
        """
        if not self.session:
            return None

        try:
            camera = Camera(
                camera_id=camera_id,
                organization_id=organization_id,
                location=location,
                description=description,
                rtsp_url=rtsp_url,
                is_active=True
            )

            # Set counting line configuration if provided
            if outside_line and len(outside_line) == 4:
                camera.outside_line_x1 = outside_line[0]
                camera.outside_line_y1 = outside_line[1]
                camera.outside_line_x2 = outside_line[2]
                camera.outside_line_y2 = outside_line[3]

            if inside_line and len(inside_line) == 4:
                camera.inside_line_x1 = inside_line[0]
                camera.inside_line_y1 = inside_line[1]
                camera.inside_line_x2 = inside_line[2]
                camera.inside_line_y2 = inside_line[3]

            if in_direction:
                camera.in_direction = in_direction

            if line_color and len(line_color) == 3:
                camera.line_color_r = line_color[0]
                camera.line_color_g = line_color[1]
                camera.line_color_b = line_color[2]

            if line_thickness is not None:
                camera.line_thickness = line_thickness

            if cooldown_frames is not None:
                camera.cooldown_frames = cooldown_frames

            if min_track_length is not None:
                camera.min_track_length = min_track_length

            self.session.add(camera)
            self.session.commit()

            self.logger.info(f"Camera added: {camera_id} (ID: {camera.id})")
            return camera.id

        except Exception as e:
            self.logger.error(f"Error adding camera: {e}")
            self.session.rollback()
            return None

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Get camera by camera_id"""
        if not self.session:
            return None

        try:
            return self.session.query(Camera).filter_by(camera_id=camera_id).first()
        except Exception as e:
            self.logger.error(f"Error getting camera: {e}")
            return None

    def get_cameras_by_organization(self, org_id: int, active_only: bool = True) -> List[Camera]:
        """Get all cameras for an organization"""
        if not self.session:
            return []

        try:
            query = self.session.query(Camera).filter_by(organization_id=org_id)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting cameras for organization: {e}")
            return []

    def get_all_cameras(self, active_only: bool = True) -> List[Camera]:
        """Get all cameras"""
        if not self.session:
            return []

        try:
            query = self.session.query(Camera)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting cameras: {e}")
            return []

    def update_camera_counting_lines(self, camera_id: str, outside_line: list = None,
                                     inside_line: list = None, in_direction: str = None,
                                     line_color: list = None, line_thickness: int = None,
                                     cooldown_frames: int = None, min_track_length: int = None) -> bool:
        """
        Update counting line configuration for a camera

        Args:
            camera_id: Camera identifier
            outside_line: Outside counting line [x1, y1, x2, y2] (normalized 0.0-1.0)
            inside_line: Inside counting line [x1, y1, x2, y2] (normalized 0.0-1.0)
            in_direction: Direction that counts as IN ('up', 'down', 'left', 'right')
            line_color: Line color [r, g, b] (0-255)
            line_thickness: Line thickness in pixels
            cooldown_frames: Frames to wait before counting same person again
            min_track_length: Minimum track length before counting

        Returns:
            True if successful, False otherwise
        """
        if not self.session:
            return False

        try:
            camera = self.get_camera(camera_id)
            if not camera:
                self.logger.error(f"Camera not found: {camera_id}")
                return False

            # Update counting line configuration
            if outside_line and len(outside_line) == 4:
                camera.outside_line_x1 = outside_line[0]
                camera.outside_line_y1 = outside_line[1]
                camera.outside_line_x2 = outside_line[2]
                camera.outside_line_y2 = outside_line[3]

            if inside_line and len(inside_line) == 4:
                camera.inside_line_x1 = inside_line[0]
                camera.inside_line_y1 = inside_line[1]
                camera.inside_line_x2 = inside_line[2]
                camera.inside_line_y2 = inside_line[3]

            if in_direction:
                camera.in_direction = in_direction

            if line_color and len(line_color) == 3:
                camera.line_color_r = line_color[0]
                camera.line_color_g = line_color[1]
                camera.line_color_b = line_color[2]

            if line_thickness is not None:
                camera.line_thickness = line_thickness

            if cooldown_frames is not None:
                camera.cooldown_frames = cooldown_frames

            if min_track_length is not None:
                camera.min_track_length = min_track_length

            camera.updated_at = datetime.now()
            self.session.commit()

            self.logger.info(f"Updated counting lines for camera: {camera_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating camera counting lines: {e}")
            self.session.rollback()
            return False

    def update_camera(self, camera_id: str, **kwargs) -> bool:
        """Update camera details"""
        if not self.session:
            return False

        try:
            camera = self.get_camera(camera_id)
            if not camera:
                return False

            for key, value in kwargs.items():
                if hasattr(camera, key):
                    setattr(camera, key, value)
            
            camera.updated_at = datetime.now()
            self.session.commit()
            self.logger.info(f"Updated camera: {camera_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating camera: {e}")
            self.session.rollback()
            return False

    # ========================================================================
    # ORGANIZATION MANAGEMENT
    # ========================================================================

    def add_organization(self, name: str, code: str = None, address: str = None,
                        contact_person: str = None, contact_email: str = None,
                        contact_phone: str = None) -> Optional[int]:
        """Add a new organization"""
        if not self.session:
            return None

        try:
            org = Organization(
                name=name,
                code=code,
                address=address,
                contact_person=contact_person,
                contact_email=contact_email,
                contact_phone=contact_phone,
                is_active=True
            )

            self.session.add(org)
            self.session.commit()

            self.logger.info(f"Organization added: {name} (ID: {org.id})")
            return org.id

        except Exception as e:
            self.logger.error(f"Error adding organization: {e}")
            self.session.rollback()
            return None

    def get_organization(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID"""
        if not self.session:
            return None

        return self.session.query(Organization).filter_by(id=org_id).first()

    def get_organization_by_code(self, code: str) -> Optional[Organization]:
        """Get organization by code"""
        if not self.session:
            return None

        return self.session.query(Organization).filter_by(code=code).first()

    def get_all_organizations(self, active_only: bool = True) -> List[Organization]:
        """Get all organizations"""
        if not self.session:
            return []

        query = self.session.query(Organization)
        if active_only:
            query = query.filter_by(is_active=True)

        return query.all()

    def create_organization(self, *args, **kwargs) -> Optional[int]:
        """Alias for add_organization"""
        return self.add_organization(*args, **kwargs)

    def update_organization(self, org_id: int, **kwargs) -> bool:
        """Update organization details"""
        if not self.session:
            return False
            
        try:
            org = self.get_organization(org_id)
            if not org:
                return False
                
            for key, value in kwargs.items():
                if hasattr(org, key):
                    setattr(org, key, value)
            
            org.updated_at = datetime.now()
            self.session.commit()
            self.logger.info(f"Updated organization: {org_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating organization: {e}")
            self.session.rollback()
            return False

    def delete_organization(self, org_id: int) -> bool:
        """Soft delete an organization"""
        return self.update_organization(org_id, is_active=False)

    # ========================================================================
    # CAMERA MANAGEMENT
    # ========================================================================

    def register_camera(self, camera_id: str, location: str = None,
                       description: str = None, rtsp_url: str = None) -> int:
        """Register or update a camera"""
        if not self.session:
            return None

        try:
            camera = self.session.query(Camera).filter_by(camera_id=camera_id).first()

            if camera:
                # Update existing camera
                if location:
                    camera.location = location
                if description:
                    camera.description = description
                if rtsp_url:
                    camera.rtsp_url = rtsp_url
                camera.is_active = True
                camera.updated_at = datetime.now()
            else:
                # Create new camera
                camera = Camera(
                    camera_id=camera_id,
                    location=location,
                    description=description,
                    rtsp_url=rtsp_url,
                    is_active=True
                )
                self.session.add(camera)

            self.session.commit()
            self.logger.info(f"Camera registered: {camera_id} (ID: {camera.id})")
            return camera.id

        except Exception as e:
            self.logger.error(f"Error registering camera: {e}")
            self.session.rollback()
            return None

    def get_camera_id(self, camera_id: str) -> Optional[int]:
        """Get database ID for camera"""
        if not self.session:
            return None

        camera = self.session.query(Camera).filter_by(camera_id=camera_id).first()
        return camera.id if camera else None

    # ========================================================================
    # PERSON MANAGEMENT
    # ========================================================================

    def add_person(self, name: str, employee_id: str = None, organization_id: int = None,
                   department: str = None, designation: str = None, email: str = None,
                   phone: str = None, photo_path: str = None) -> Optional[int]:
        """Add a new person to the database"""
        if not self.session:
            return None

        try:
            person = Person(
                name=name,
                employee_id=employee_id,
                organization_id=organization_id,
                department=department,
                designation=designation,
                email=email,
                phone=phone,
                photo_path=photo_path,
                is_active=True
            )

            self.session.add(person)
            self.session.commit()

            self.logger.info(f"Person added: {name} (ID: {person.id})")
            return person.id

        except Exception as e:
            self.logger.error(f"Error adding person: {e}")
            self.session.rollback()
            return None

    def get_person(self, person_id: int) -> Optional[Person]:
        """Get person by ID"""
        if not self.session:
            return None

        return self.session.query(Person).filter_by(id=person_id).first()

    def get_all_persons(self, active_only: bool = True) -> List[Person]:
        """Get all persons"""
        if not self.session:
            return []

        query = self.session.query(Person)
        if active_only:
            query = query.filter_by(is_active=True)

        return query.all()

    def create_person(self, *args, **kwargs) -> Optional[int]:
        """Alias for add_person"""
        return self.add_person(*args, **kwargs)

    def get_persons_by_organization(self, org_id: int, active_only: bool = True) -> List[Person]:
        """Get all persons for an organization"""
        if not self.session:
            return []
            
        try:
            query = self.session.query(Person).filter_by(organization_id=org_id)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting persons for organization: {e}")
            return []

    def update_person(self, person_id: int, **kwargs) -> bool:
        """Update person details"""
        if not self.session:
            return False
            
        try:
            person = self.get_person(person_id)
            if not person:
                return False
                
            for key, value in kwargs.items():
                if hasattr(person, key):
                    setattr(person, key, value)
            
            person.updated_at = datetime.now()
            self.session.commit()
            self.logger.info(f"Updated person: {person_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating person: {e}")
            self.session.rollback()
            return False

    def delete_person(self, person_id: int) -> bool:
        """Soft delete a person"""
        return self.update_person(person_id, is_active=False)

    # ========================================================================
    # FACE EMBEDDING MANAGEMENT
    # ========================================================================

    def store_face_embedding(self, person_id: int, embedding: np.ndarray,
                            quality_score: float = None, source_image_path: str = None) -> bool:
        """Store face embedding for a person"""
        if not self.session:
            return False

        try:
            # Check if embedding already exists
            existing = self.session.query(FaceEmbedding).filter_by(person_id=person_id).first()

            if existing:
                # Update existing embedding
                existing.embedding = embedding.tolist()
                existing.quality_score = quality_score
                existing.source_image_path = source_image_path
            else:
                # Create new embedding
                face_emb = FaceEmbedding(
                    person_id=person_id,
                    embedding=embedding.tolist(),
                    quality_score=quality_score,
                    source_image_path=source_image_path
                )
                self.session.add(face_emb)

            self.session.commit()
            self.logger.info(f"Face embedding stored for person {person_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error storing face embedding: {e}")
            self.session.rollback()
            return False

    def add_face_embedding(self, person_id: int, embedding: np.ndarray, quality_score: float = None) -> bool:
        """Add a face embedding (alias for store_face_embedding)"""
        return self.store_face_embedding(person_id, embedding, quality_score)

    def delete_face_embeddings(self, person_id: int) -> bool:
        """Delete all face embeddings for a person"""
        if not self.session:
            return False
            
        try:
            self.session.query(FaceEmbedding).filter_by(person_id=person_id).delete()
            self.session.commit()
            self.logger.info(f"Deleted face embeddings for person {person_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting face embeddings: {e}")
            self.session.rollback()
            return False

    def get_all_face_embeddings(self) -> List[Tuple[int, np.ndarray]]:
        """Get all face embeddings for matching"""
        if not self.session:
            return []

        try:
            embeddings = self.session.query(FaceEmbedding).join(Person).filter(Person.is_active == True).all()
            return [(emb.person_id, np.array(emb.embedding)) for emb in embeddings]
        except Exception as e:
            self.logger.error(f"Error getting face embeddings: {e}")
            return []

    def match_face(self, embedding: np.ndarray, threshold: float = 0.6) -> Optional[Tuple[int, float]]:
        """
        Match a face embedding against database
        Returns (person_id, similarity_score) or None
        Uses cosine similarity
        """
        if not self.session:
            return None

        try:
            # Get all embeddings
            all_embeddings = self.get_all_face_embeddings()

            if not all_embeddings:
                return None

            # Calculate cosine similarities
            best_match = None
            best_similarity = -1

            for person_id, stored_embedding in all_embeddings:
                # Cosine similarity
                similarity = np.dot(embedding, stored_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(stored_embedding)
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = person_id

            # Check if best match exceeds threshold
            if best_similarity >= threshold:
                return (best_match, float(best_similarity))

            return None

        except Exception as e:
            self.logger.error(f"Error matching face: {e}")
            return None

    # ========================================================================
    # FACE DETECTION LOGGING
    # ========================================================================

    def log_face_detection(self, camera_id: int, person_id: Optional[int], track_id: int,
                          confidence: float, detection_score: float, bbox: Tuple[int, int, int, int],
                          frame_number: int, snapshot_path: str = None) -> bool:
        """Log a face detection event"""
        if not self.session:
            return False

        try:
            detection = FaceDetection(
                camera_id=camera_id,
                person_id=person_id,
                track_id=track_id,
                confidence=confidence,
                detection_score=detection_score,
                bbox_x1=bbox[0],
                bbox_y1=bbox[1],
                bbox_x2=bbox[2],
                bbox_y2=bbox[3],
                frame_number=frame_number,
                snapshot_path=snapshot_path
            )

            self.session.add(detection)
            self.session.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error logging face detection: {e}")
            self.session.rollback()
            return False

    # ========================================================================
    # ENTRY/EXIT LOGGING
    # ========================================================================

    def log_entry_exit(self, camera_id: int, event_type: str, track_id: int,
                      person_id: Optional[int] = None, confidence: float = None,
                      position: Tuple[int, int] = None, snapshot_path: str = None) -> bool:
        """Log an entry/exit event with optional face recognition"""
        if not self.session:
            return False

        try:
            timestamp = datetime.now()

            log = EntryExitLog(
                camera_id=camera_id,
                person_id=person_id,
                track_id=track_id,
                event_type=event_type,
                confidence=confidence,
                position_x=position[0] if position else None,
                position_y=position[1] if position else None,
                snapshot_path=snapshot_path,
                timestamp=timestamp
            )

            self.session.add(log)
            self.session.commit()

            # Log with person name if identified
            if person_id:
                person = self.get_person(person_id)
                name = person.name if person else "Unknown"
                org_name = ""
                if person and person.organization_id:
                    org = self.get_organization(person.organization_id)
                    org_name = f" ({org.name})" if org else ""

                self.logger.info(f"{event_type} event logged: {name}{org_name} (confidence: {confidence:.2f})")

                # Update employee attendance
                self.update_employee_attendance(person_id, event_type, timestamp)
            else:
                self.logger.info(f"{event_type} event logged: Unknown person")

            return True

        except Exception as e:
            self.logger.error(f"Error logging entry/exit: {e}")
            self.session.rollback()
            return False

    # ========================================================================
    # ATTENDANCE TRACKING
    # ========================================================================

    def update_employee_attendance(self, person_id: int, event_type: str,
                                   timestamp: datetime = None) -> bool:
        """
        Update employee attendance record when IN/OUT event occurs

        Args:
            person_id: Person ID
            event_type: 'IN' or 'OUT'
            timestamp: Event timestamp (default: now)
        """
        if not self.session:
            return False

        try:
            if timestamp is None:
                timestamp = datetime.now()

            date = timestamp.date()

            # Get person to get organization_id
            person = self.get_person(person_id)
            if not person:
                return False

            # Get or create attendance record for today
            attendance = self.session.query(EmployeeAttendance).filter_by(
                person_id=person_id,
                date=date
            ).first()

            if not attendance:
                attendance = EmployeeAttendance(
                    person_id=person_id,
                    organization_id=person.organization_id,
                    date=date,
                    total_in=0,
                    total_out=0,
                    is_present=False
                )
                self.session.add(attendance)

            # Update based on event type
            if event_type == 'IN':
                attendance.total_in += 1
                attendance.is_present = True

                # Set first_in_time if this is the first IN
                if attendance.first_in_time is None:
                    attendance.first_in_time = timestamp

            elif event_type == 'OUT':
                attendance.total_out += 1
                attendance.is_present = False
                attendance.last_out_time = timestamp

                # Calculate duration if we have first_in_time
                if attendance.first_in_time:
                    duration = (timestamp - attendance.first_in_time).total_seconds()
                    attendance.total_duration_seconds = int(duration)

            self.session.commit()

            # Update organization attendance
            if person.organization_id:
                self._update_organization_attendance(person.organization_id, date)

            return True

        except Exception as e:
            self.logger.error(f"Error updating employee attendance: {e}")
            self.session.rollback()
            return False

    def _update_organization_attendance(self, org_id: int, date: date) -> bool:
        """Update organization attendance summary"""
        if not self.session:
            return False

        try:
            # Get or create organization attendance record
            org_attendance = self.session.query(OrganizationAttendance).filter_by(
                organization_id=org_id,
                date=date
            ).first()

            if not org_attendance:
                org_attendance = OrganizationAttendance(
                    organization_id=org_id,
                    date=date
                )
                self.session.add(org_attendance)

            # Count total employees in organization
            total_employees = self.session.query(Person).filter_by(
                organization_id=org_id,
                is_active=True
            ).count()

            # Count currently present employees
            present_count = self.session.query(EmployeeAttendance).filter_by(
                organization_id=org_id,
                date=date,
                is_present=True
            ).count()

            # Sum total IN and OUT counts
            attendance_records = self.session.query(EmployeeAttendance).filter_by(
                organization_id=org_id,
                date=date
            ).all()

            total_in = sum(r.total_in for r in attendance_records)
            total_out = sum(r.total_out for r in attendance_records)

            # Update organization attendance
            org_attendance.total_employees = total_employees
            org_attendance.present_count = present_count
            org_attendance.total_in_count = total_in
            org_attendance.total_out_count = total_out

            # Update peak occupancy
            if present_count > org_attendance.peak_occupancy:
                org_attendance.peak_occupancy = present_count
                org_attendance.peak_time = datetime.now()

            self.session.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error updating organization attendance: {e}")
            self.session.rollback()
            return False

    def get_employee_attendance(self, person_id: int, start_date: date = None,
                               end_date: date = None) -> List[EmployeeAttendance]:
        """Get employee attendance records"""
        if not self.session:
            return []

        try:
            query = self.session.query(EmployeeAttendance).filter_by(person_id=person_id)

            if start_date:
                query = query.filter(EmployeeAttendance.date >= start_date)
            if end_date:
                query = query.filter(EmployeeAttendance.date <= end_date)

            return query.order_by(EmployeeAttendance.date.desc()).all()

        except Exception as e:
            self.logger.error(f"Error getting employee attendance: {e}")
            return []

    def get_organization_attendance(self, org_id: int, start_date: date = None,
                                   end_date: date = None) -> List[OrganizationAttendance]:
        """Get organization attendance records"""
        if not self.session:
            return []

        try:
            query = self.session.query(OrganizationAttendance).filter_by(organization_id=org_id)

            if start_date:
                query = query.filter(OrganizationAttendance.date >= start_date)
            if end_date:
                query = query.filter(OrganizationAttendance.date <= end_date)

            return query.order_by(OrganizationAttendance.date.desc()).all()

        except Exception as e:
            self.logger.error(f"Error getting organization attendance: {e}")
            return []

    # ========================================================================
    # COUNTING EVENT LOGGING (Legacy compatibility)
    # ========================================================================

    def log_counting_event(self, camera_id: int, event: Dict) -> bool:
        """Log a counting event (legacy compatibility)"""
        if not self.session:
            return False

        try:
            counting_event = CountingEvent(
                camera_id=camera_id,
                track_id=event.get('track_id'),
                event_type=event.get('type'),
                position_x=event.get('position', [None, None])[0],
                position_y=event.get('position', [None, None])[1],
                count_in=event.get('count_in'),
                count_out=event.get('count_out'),
                occupancy=event.get('occupancy'),
                frame_number=event.get('frame')
            )

            self.session.add(counting_event)
            self.session.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error logging counting event: {e}")
            self.session.rollback()
            return False

    # ========================================================================
    # JOURNEY TRACKING
    # ========================================================================

    def log_person_journey(self, person_id: int, from_camera_id: int, to_camera_id: int,
                          from_timestamp: datetime, to_timestamp: datetime) -> bool:
        """Log person movement between cameras"""
        if not self.session:
            return False

        try:
            duration = int((to_timestamp - from_timestamp).total_seconds())

            journey = PersonJourney(
                person_id=person_id,
                from_camera_id=from_camera_id,
                to_camera_id=to_camera_id,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                duration_seconds=duration
            )

            self.session.add(journey)
            self.session.commit()

            self.logger.info(f"Journey logged: Person {person_id} from camera {from_camera_id} "
                           f"to {to_camera_id} ({duration}s)")
            return True

        except Exception as e:
            self.logger.error(f"Error logging journey: {e}")
            self.session.rollback()
            return False

    # ========================================================================
    # STATISTICS AND QUERIES
    # ========================================================================

    def get_recent_events(self, limit: int = 100, camera_id: str = None) -> List:
        """Get recent entry/exit events"""
        if not self.session:
            return []
            
        try:
            query = self.session.query(EntryExitLog)
            
            if camera_id:
                # Resolve camera_id string to DB ID
                # If camera_id is numeric, it might be the DB ID, but API param says 'camera_id' which is string usually
                if isinstance(camera_id, str) and not camera_id.isdigit():
                    cam_db_id = self.get_camera_id(camera_id)
                    if cam_db_id:
                        query = query.filter_by(camera_id=cam_db_id)
                    else:
                        # Camera likely not found by string ID, if it's digit treat as ID? 
                        # Or return empty? Let's assume input is correct.
                        return []
                else:
                    query = query.filter_by(camera_id=int(camera_id))
            
            return query.order_by(EntryExitLog.timestamp.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Error getting recent events: {e}")
            return []

    def get_entry_exit_stats(self, camera_id: int = None,
                            start_time: datetime = None,
                            end_time: datetime = None) -> Dict:
        """Get entry/exit statistics"""
        if not self.session:
            return {}

        try:
            query = self.session.query(EntryExitLog)

            if camera_id:
                query = query.filter_by(camera_id=camera_id)
            if start_time:
                query = query.filter(EntryExitLog.timestamp >= start_time)
            if end_time:
                query = query.filter(EntryExitLog.timestamp <= end_time)

            events = query.all()

            total_in = sum(1 for e in events if e.event_type == 'IN')
            total_out = sum(1 for e in events if e.event_type == 'OUT')
            identified = sum(1 for e in events if e.person_id is not None)

            return {
                'total_in': total_in,
                'total_out': total_out,
                'occupancy': total_in - total_out,
                'total_events': len(events),
                'identified_count': identified,
                'unknown_count': len(events) - identified,
                'identification_rate': (identified / len(events) * 100) if events else 0
            }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

    def get_person_activity(self, person_id: int, start_time: datetime = None,
                           end_time: datetime = None) -> List[EntryExitLog]:
        """Get activity log for a specific person"""
        if not self.session:
            return []

        try:
            query = self.session.query(EntryExitLog).filter_by(person_id=person_id)

            if start_time:
                query = query.filter(EntryExitLog.timestamp >= start_time)
            if end_time:
                query = query.filter(EntryExitLog.timestamp <= end_time)

            return query.order_by(EntryExitLog.timestamp.desc()).all()

        except Exception as e:
            self.logger.error(f"Error getting person activity: {e}")
            return []

    def get_last_detection(self, person_id: int, camera_id: int) -> Optional[FaceDetection]:
        """Get last detection of a person on a specific camera"""
        if not self.session:
            return None

        try:
            return self.session.query(FaceDetection)\
                .filter_by(person_id=person_id, camera_id=camera_id)\
                .order_by(FaceDetection.timestamp.desc())\
                .first()
        except Exception as e:
            self.logger.error(f"Error getting last detection: {e}")
            return None

    # ========================================================================
    # CLEANUP
    # ========================================================================

    def close(self):
        """Close database connection"""
        if self.session:
            self.session.close()
            self.logger.info("PostgreSQL database connection closed")

