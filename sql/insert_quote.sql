INSERT INTO quotes (text, author_id)
VALUES (%s, %s)
ON CONFLICT DO NOTHING;
