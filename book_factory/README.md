# KDP Book Factory (Autowriter)

Local implementation of the Book Factory from `AUTOWRITER PDR/`.

## Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt

# Optional: set env vars in book_factory/.env
uvicorn app.main:app --reload --port 8002
```

## API

- `POST /api/v1/topics` create topic
- `GET /api/v1/topics` list topics
- `GET /api/v1/topics/{slug}` get topic
- `GET /api/v1/topics/{slug}/suggest-feeds` topic-based RSS suggestions
- `POST /api/v1/topics/{slug}/sources` add URLs
- `GET /api/v1/topics/{slug}/silos` list silos
- `POST /api/v1/topics/{slug}/silos/{n}/write` write chapter
- `GET /api/v1/topics/{slug}/silos/{n}/review-pack` get summary + prompts
- `POST /api/v1/topics/{slug}/silos/{n}/draft-audio` generate TTS
- `POST /api/v1/topics/{slug}/silos/{n}/author-notes` store voice notes
- `POST /api/v1/topics/{slug}/silos/{n}/rewrite` rewrite with notes
- `POST /api/v1/topics/{slug}/compile` compile manuscript + image manifest
- `POST /api/v1/topics/{slug}/apply-images` replace placeholders with images
- `POST /api/v1/trends/refresh` fetch RSS trend candidates
- `GET /api/v1/trends` list candidates

## Dashboard

- `GET /dashboard` select topic, view silos, add URLs
