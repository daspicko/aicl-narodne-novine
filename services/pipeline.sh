cd model_loader
uv run load_models.py

cd ../scraper
uv run fetch_data.py

cd ../normalizer
uv run normalize_data.py

cd ../summarizer
uv run summarize_data.py

cd ../extractor
uv run extract_data.py

cd ../embedder
uv run embed_data.py

cd ../data_persistance
uv run persist_data.py
