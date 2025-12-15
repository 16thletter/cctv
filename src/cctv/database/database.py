"""
Database Module for storing counting events and statistics
"""
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

Base = declarative_base()


class CountingEvent(Base):
    """Model for counting events"""
    __tablename__ = 'counting_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    frame_number = Column(Integer)
    track_id = Column(Integer)
    event_type = Column(String(10))  # 'IN' or 'OUT'
    position_x = Column(Integer)
    position_y = Column(Integer)
    count_in = Column(Integer)
    count_out = Column(Integer)
    occupancy = Column(Integer)
    
    def __repr__(self):
        return f"<CountingEvent(id={self.id}, type={self.event_type}, timestamp={self.timestamp})>"


class HourlySummary(Base):
    """Model for hourly statistics"""
    __tablename__ = 'hourly_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    hour = Column(Integer)
    total_in = Column(Integer)
    total_out = Column(Integer)
    peak_occupancy = Column(Integer)
    avg_occupancy = Column(Float)
    
    def __repr__(self):
        return f"<HourlySummary(hour={self.hour}, in={self.total_in}, out={self.total_out})>"


class Database:
    """Database manager for people counter"""
    
    def __init__(self, config):
        """Initialize database connection"""
        self.logger = logging.getLogger(__name__)
        self.config = config['database']
        
        if not self.config['enabled']:
            self.logger.info("Database disabled")
            self.session = None
            return
        
        # Create database file path
        db_path = self.config['path']
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        self.logger.info(f"Database initialized: {db_path}")
    
    def log_event(self, event):
        """
        Log a counting event to database
        
        Args:
            event: Event dictionary
        """
        if not self.session or not self.config['log_events']:
            return
        
        try:
            db_event = CountingEvent(
                timestamp=event['timestamp'],
                frame_number=event['frame'],
                track_id=event['track_id'],
                event_type=event['type'],
                position_x=event['position'][0],
                position_y=event['position'][1],
                count_in=event['count_in'],
                count_out=event['count_out'],
                occupancy=event['occupancy']
            )
            
            self.session.add(db_event)
            self.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error logging event: {e}")
            self.session.rollback()
    
    def get_events(self, start_time=None, end_time=None, limit=100):
        """Get events from database"""
        if not self.session:
            return []
        
        query = self.session.query(CountingEvent)
        
        if start_time:
            query = query.filter(CountingEvent.timestamp >= start_time)
        if end_time:
            query = query.filter(CountingEvent.timestamp <= end_time)
        
        return query.order_by(CountingEvent.timestamp.desc()).limit(limit).all()
    
    def get_statistics(self, start_time=None, end_time=None):
        """Get statistics from database"""
        if not self.session:
            return {}
        
        query = self.session.query(CountingEvent)
        
        if start_time:
            query = query.filter(CountingEvent.timestamp >= start_time)
        if end_time:
            query = query.filter(CountingEvent.timestamp <= end_time)
        
        events = query.all()
        
        if not events:
            return {}
        
        total_in = sum(1 for e in events if e.event_type == 'IN')
        total_out = sum(1 for e in events if e.event_type == 'OUT')
        
        return {
            'total_in': total_in,
            'total_out': total_out,
            'total_events': len(events),
            'start_time': events[-1].timestamp if events else None,
            'end_time': events[0].timestamp if events else None
        }
    
    def close(self):
        """Close database connection"""
        if self.session:
            self.session.close()
            self.logger.info("Database connection closed")

