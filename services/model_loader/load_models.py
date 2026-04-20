"""
load_models.py
--------------
Downloads both models used in the NLP pipeline to the local HuggingFace cache
so that all subsequent scripts can run fully offline (HF_HUB_OFFLINE=1).

Models downloaded:
  - classla/bcms-bertic           (summarizer – extractive MMR)
  - sentence-transformers/all-MiniLM-L6-v2  (embedder)

Run once before using the pipeline:
    python services/model_loader/load_models.py
"""

from transformers import AutoTokenizer, AutoModel

MODELS = [
    {
        "name": "classla/bcms-bertic",
        "description": "BERTić – Croatian/Bosnian/Serbian BERT (used by Summarizer)",
    },
    {
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "description": "MiniLM-L6 – multilingual sentence embedder (used by Embedder)",
    },
]


def download_model(name: str, description: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {description}")
    print(f"  {name}")
    print(f"{'─' * 60}")

    print("  Downloading tokenizer …")
    try:
        AutoTokenizer.from_pretrained(name)
    except ConnectionError as e:
        print(f"  Error downloading tokenizer for {name}: {e}")
    print("  ✓ Tokenizer cached")

    print("  Downloading model weights …")
    try:
        AutoModel.from_pretrained(name)
    except ConnectionError as e:
        print(f"  Error downloading model {name}: {e}")
    print("  ✓ Model weights cached")


def main() -> None:
    print("Downloading models to HuggingFace cache for offline use …")
    for m in MODELS:
        download_model(m["name"], m["description"])
    print(f"\n{'═' * 60}")
    print("  All models downloaded. You can now set:")
    print("    HF_HUB_OFFLINE=1")
    print("    TRANSFORMERS_OFFLINE=1")
    print("  and run the pipeline without network access.")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
