#!/bin/bash
# Quick check of recent IN/OUT events

echo "============================================================"
echo "📊 RECENT IN/OUT EVENTS (Last 20)"
echo "============================================================"
echo ""

psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT 
    TO_CHAR(ce.timestamp, 'HH24:MI:SS') as time,
    ce.event_type,
    ce.track_id,
    'ANONYMOUS' as person,
    CONCAT('IN:', ce.count_in, ' OUT:', ce.count_out, ' OCC:', ce.occupancy) as counts
FROM counting_events ce
ORDER BY ce.timestamp DESC
LIMIT 20;
EOF

echo ""
echo "============================================================"
echo "📈 CURRENT STATUS"
echo "============================================================"
echo ""

psql -h localhost -U postgres -d face_recognition << 'EOF'
SELECT 
    c.camera_id,
    c.location,
    COALESCE(
        (SELECT count_in FROM counting_events WHERE camera_id = c.id ORDER BY timestamp DESC LIMIT 1), 
        0
    ) as total_in,
    COALESCE(
        (SELECT count_out FROM counting_events WHERE camera_id = c.id ORDER BY timestamp DESC LIMIT 1), 
        0
    ) as total_out,
    COALESCE(
        (SELECT occupancy FROM counting_events WHERE camera_id = c.id ORDER BY timestamp DESC LIMIT 1), 
        0
    ) as occupancy
FROM cameras c
WHERE c.is_active = true;
EOF

echo ""

