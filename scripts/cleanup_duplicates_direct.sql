-- Clean up duplicate sightings (same deer_id + image_id)
-- Keeps only the highest confidence detection for each deer+image pair

BEGIN;

-- Show duplicates before cleanup
SELECT COUNT(*) as duplicate_pairs_before
FROM (
  SELECT deer_id, image_id
  FROM detections
  WHERE deer_id IS NOT NULL
  GROUP BY deer_id, image_id
  HAVING COUNT(*) > 1
) as dupes_before;

-- Delete duplicates, keeping highest confidence one
WITH ranked_detections AS (
  SELECT
    id,
    ROW_NUMBER() OVER (
      PARTITION BY deer_id, image_id
      ORDER BY confidence DESC, created_at ASC
    ) as rn
  FROM detections
  WHERE deer_id IS NOT NULL
)
DELETE FROM detections
WHERE id IN (
  SELECT id
  FROM ranked_detections
  WHERE rn > 1
);

-- Show results after cleanup
SELECT COUNT(*) as duplicate_pairs_after
FROM (
  SELECT deer_id, image_id
  FROM detections
  WHERE deer_id IS NOT NULL
  GROUP BY deer_id, image_id
  HAVING COUNT(*) > 1
) as dupes_after;

SELECT COUNT(*) as total_sightings_remaining
FROM detections
WHERE deer_id IS NOT NULL;

COMMIT;
