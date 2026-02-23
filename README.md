# PomeFi v0.3.0 MVP

## Run locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

## Tests

```bash
pytest -q
```

## Notes

- `app.py`: Skill Lab single-page UI
- `skill_engine.py`: real logic entry
- `utils.py`: helper utilities
