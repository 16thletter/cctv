"""
Web Dashboard for CCTV People Counter
Provides real-time statistics and historical data visualization
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cctv.database.database import Database
from cctv.utils.utils import load_config

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Load config and initialize database
config = load_config()
db = Database(config)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/current')
def get_current_stats():
    """Get current statistics"""
    try:
        # Get latest event
        events = db.get_events(limit=1)
        
        if events:
            latest = events[0]
            return jsonify({
                'count_in': latest.count_in,
                'count_out': latest.count_out,
                'occupancy': latest.occupancy,
                'last_update': latest.timestamp.isoformat()
            })
        else:
            return jsonify({
                'count_in': 0,
                'count_out': 0,
                'occupancy': 0,
                'last_update': None
            })
    except Exception as e:
        logger.error(f"Error getting current stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/events')
def get_events():
    """Get recent events"""
    try:
        limit = int(request.args.get('limit', 50))
        events = db.get_events(limit=limit)
        
        return jsonify([{
            'id': e.id,
            'timestamp': e.timestamp.isoformat(),
            'type': e.event_type,
            'track_id': e.track_id,
            'count_in': e.count_in,
            'count_out': e.count_out,
            'occupancy': e.occupancy
        } for e in events])
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics')
def get_statistics():
    """Get statistics for a time period"""
    try:
        # Get time range from query params
        hours = int(request.args.get('hours', 24))
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        stats = db.get_statistics(start_time, end_time)
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/hourly')
def get_hourly_data():
    """Get hourly breakdown"""
    try:
        hours = int(request.args.get('hours', 24))
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        events = db.get_events(start_time, end_time, limit=10000)
        
        # Group by hour
        hourly_data = {}
        for event in events:
            hour_key = event.timestamp.strftime('%Y-%m-%d %H:00')
            if hour_key not in hourly_data:
                hourly_data[hour_key] = {'in': 0, 'out': 0}
            
            if event.event_type == 'IN':
                hourly_data[hour_key]['in'] += 1
            else:
                hourly_data[hour_key]['out'] += 1
        
        # Convert to list
        result = [
            {
                'hour': hour,
                'in': data['in'],
                'out': data['out']
            }
            for hour, data in sorted(hourly_data.items())
        ]
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting hourly data: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting dashboard server...")
    app.run(host='0.0.0.0', port=5000, debug=True)

