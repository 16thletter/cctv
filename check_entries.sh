#!/bin/bash
# Script to check IN/OUT entries for all people (recognized and anonymous)

echo "============================================================"
echo "📊 COUNTING EVENTS - ALL PEOPLE (Recognized & Anonymous)"
echo "============================================================"
echo ""

# Show recent counting events (all are currently anonymous since face recognition not integrated)
psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT
    ce.id,
    TO_CHAR(ce.timestamp, 'YYYY-MM-DD HH24:MI:SS') as time,
    c.camera_id as camera,
    c.location,
    ce.event_type,
    ce.track_id,
    'ANONYMOUS' as person_status,
    ce.count_in as "IN",
    ce.count_out as "OUT",
    ce.occupancy,
    CONCAT('(', ce.position_x, ',', ce.position_y, ')') as position
FROM counting_events ce
LEFT JOIN cameras c ON ce.camera_id = c.id
ORDER BY ce.timestamp DESC
LIMIT 30;
EOF

echo ""
echo "============================================================"
echo "📈 SUMMARY BY EVENT TYPE"
echo "============================================================"
echo ""

# Summary by event type
psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT
    event_type,
    COUNT(*) as total_events,
    MIN(timestamp) as first_event,
    MAX(timestamp) as last_event
FROM counting_events
GROUP BY event_type
ORDER BY event_type;
EOF

echo ""
echo "============================================================"
echo "👥 CURRENT OCCUPANCY BY CAMERA"
echo "============================================================"
echo ""

# Current occupancy
psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT 
    c.camera_id,
    c.location,
    COALESCE(
        (SELECT occupancy 
         FROM counting_events 
         WHERE camera_id = c.id 
         ORDER BY timestamp DESC 
         LIMIT 1), 
        0
    ) as current_occupancy,
    COALESCE(
        (SELECT count_in 
         FROM counting_events 
         WHERE camera_id = c.id 
         ORDER BY timestamp DESC 
         LIMIT 1), 
        0
    ) as total_in,
    COALESCE(
        (SELECT count_out 
         FROM counting_events 
         WHERE camera_id = c.id 
         ORDER BY timestamp DESC 
         LIMIT 1), 
        0
    ) as total_out
FROM cameras c
WHERE c.is_active = true;
EOF

echo ""
echo "============================================================"
echo "📅 EVENTS BY DATE"
echo "============================================================"
echo ""

# Events by date
psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_events,
    COUNT(CASE WHEN event_type = 'IN' THEN 1 END) as in_events,
    COUNT(CASE WHEN event_type = 'OUT' THEN 1 END) as out_events
FROM counting_events
GROUP BY DATE(timestamp)
ORDER BY date DESC;
EOF

echo ""
echo "============================================================"
echo "🕐 EVENTS BY HOUR (Today)"
echo "============================================================"
echo ""

# Events by hour today
psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT
    EXTRACT(HOUR FROM timestamp) as hour,
    COUNT(*) as total_events,
    COUNT(CASE WHEN event_type = 'IN' THEN 1 END) as in_events,
    COUNT(CASE WHEN event_type = 'OUT' THEN 1 END) as out_events
FROM counting_events
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY EXTRACT(HOUR FROM timestamp)
ORDER BY hour;
EOF

echo ""
echo "============================================================"
echo "👤 RECOGNIZED PERSONS (From Face Recognition)"
echo "============================================================"
echo ""

# Check if any persons have been recognized
psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT
    p.employee_id,
    p.name,
    p.organization_id,
    COUNT(el.id) as total_logs,
    MAX(el.timestamp) as last_seen
FROM persons p
LEFT JOIN entry_exit_logs el ON p.id = el.person_id
GROUP BY p.id, p.employee_id, p.name, p.organization_id
ORDER BY last_seen DESC NULLS LAST;
EOF

echo ""
echo "============================================================"
echo "📊 EMPLOYEE ATTENDANCE (Recognized Persons Only)"
echo "============================================================"
echo ""

# Employee attendance
psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT
    p.employee_id,
    p.name,
    ea.date,
    ea.first_in_time,
    ea.last_out_time,
    ea.total_in,
    ea.total_out,
    ea.is_present
FROM employee_attendance ea
JOIN persons p ON ea.person_id = p.id
ORDER BY ea.date DESC, ea.first_in_time DESC
LIMIT 20;
EOF

echo ""
echo "============================================================"
echo "ℹ️  NOTE: Face recognition is initialized but not yet"
echo "   integrated with counting. All current events are"
echo "   anonymous. Integration is pending."
echo "============================================================"
echo ""
echo "Done!"

