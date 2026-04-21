cd initialization
uv run load_models.py

cd ../scraping
uv run fetch_data.py

cd ../normalization
uv run normalize_data.py

cd ../summarization
uv run summarize_data.py

cd ../extraction
uv run extract_data.py

cd ../embedding
uv run embed_data.py

cd ../storage
uv run store_data.py
