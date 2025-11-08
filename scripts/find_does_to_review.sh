#!/bin/bash
# Find best doe candidates to review next

echo "==============================================="
echo "Best Doe Candidates for Manual Review"
echo "==============================================="
echo ""
echo "Top 50 unreviewed does (confidence > 0.6):"
echo ""

docker-compose exec -T db psql -U deertrack deer_tracking << 'SQL'
SELECT 
  i.filename,
  l.name as location,
  ROUND(d.confidence::numeric, 3) as conf,
  ROUND(((d.bbox->>'x2')::float - (d.bbox->>'x1')::float)::numeric, 0) as width,
  ROUND(((d.bbox->>'y2')::float - (d.bbox->>'y1')::float)::numeric, 0) as height,
  to_char(i.timestamp, 'MM-DD HH24:MI') as date_time
FROM detections d
JOIN images i ON d.image_id = i.id
JOIN locations l ON i.location_id = l.id
WHERE d.classification = 'doe'
  AND d.is_reviewed = false
  AND d.confidence > 0.6
ORDER BY d.confidence DESC
LIMIT 50;
SQL

echo ""
echo "==============================================="
echo "Summary by Location (confidence > 0.6)"
echo "==============================================="
echo ""

docker-compose exec -T db psql -U deertrack deer_tracking << 'SQL'
SELECT 
  l.name as location,
  COUNT(*) as unreviewed_does,
  ROUND(AVG(d.confidence)::numeric, 3) as avg_confidence
FROM detections d
JOIN images i ON d.image_id = i.id
JOIN locations l ON i.location_id = l.id
WHERE d.classification = 'doe'
  AND d.is_reviewed = false
  AND d.confidence > 0.6
GROUP BY l.name
ORDER BY unreviewed_does DESC;
SQL

echo ""
echo "[INFO] To review these in the UI:"
echo "  1. Go to Images page"
echo "  2. Filter by Location: Sanctuary (has most does)"
echo "  3. Filter by Classification: doe"
echo "  4. Sort by: Highest Confidence"
echo "  5. Review and mark good front/side views as VALID"
echo "  6. Mark rear views/poor quality as INVALID"
echo ""
echo "[TARGET] Get 50+ valid does to match your 49 valid bucks"
echo ""
