#!/bin/bash
docker-compose exec -T db psql -U deertrack deer_tracking << 'SQL'
UPDATE detections SET classification='doe' WHERE id='f484345a-d107-4284-9438-9f8512b94cef';
UPDATE detections SET classification='uncertain' WHERE id='69172612-1f59-450d-b27d-0680feaa1956';
UPDATE detections SET classification='uncertain' WHERE id='e1180d92-d110-4693-b62d-e47f7b8e9f0c';
UPDATE detections SET classification='uncertain' WHERE id='5d2b698b-455a-4b9c-8830-7b2a668d9b78';
UPDATE detections SET classification='doe' WHERE id='fd78669a-2fbe-4c56-8828-cc7bb40f71fb';
UPDATE detections SET classification='uncertain' WHERE id='212c7dab-5a9e-496d-b2df-b7d3952ff27a';
UPDATE detections SET classification='uncertain' WHERE id='c4a09910-4fdb-4afb-8665-eba061394ef6';
UPDATE detections SET classification='uncertain' WHERE id='397efff6-3ed5-4403-a6da-0ae8c114fb19';
UPDATE detections SET classification='uncertain' WHERE id='60c307ce-7b95-4d9f-9627-b1da169ef0b4';
UPDATE detections SET classification='uncertain' WHERE id='f32ec575-f705-487f-a15e-9b7faae7c097';
SQL
