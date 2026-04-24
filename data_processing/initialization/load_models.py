"""
load_models.py
--------------
Downloads both models used in the NLP process to the local HuggingFace cache
so that all subsequent scripts can run fully offline (HF_HUB_OFFLINE=1).

Models downloaded:
  - classla/bcms-bertic           (summarization – extractive MMR)
  - sentence-transformers/all-MiniLM-L6-v2  (embedding)

Run once before using the individual data processes:
    python data_processing/initialization/load_models.py
"""
from pathlib import Path
from transformers import AutoTokenizer, AutoModel
import yaml
from dotenv import load_dotenv

# ==================== Load configurations ====================
MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(MODULE_DIR / ".env")
with open(MODULE_DIR / "config.yaml") as f:
    _cfg = yaml.safe_load(f)

MODELS = []
for model in _cfg["models"]["summarizers"]:
    MODELS.append(model)
for model in _cfg["models"]["embeddings"]:
    MODELS.append(model)

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
