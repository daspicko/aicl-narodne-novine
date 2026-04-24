from dotenv import load_dotenv
load_dotenv()

import re
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from transformers import logging as transformers_logging
transformers_logging.set_verbosity_error()

class Summarizer:
    def __init__(self, model_name: str = None):
        self.MODEL_NAME = model_name

    def split_sentences(self, text: str):
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def mean_pooling(self, last_hidden_state, attention_mask):
        mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        masked = last_hidden_state * mask
        summed = masked.sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1e-9)
        return summed / counts

    def embed_texts(self, texts, tokenizer, model, device="cpu"):
        encoded = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        encoded = {k: v.to(device) for k, v in encoded.items()}
        model = model.to(device)

        with torch.no_grad():
            outputs = model(**encoded)
            embeddings = self.mean_pooling(outputs.last_hidden_state, encoded["attention_mask"])
            embeddings = F.normalize(embeddings, p=2, dim=1)

        return embeddings

    def mmr_select(self, sentence_embeddings, doc_embedding, num_sentences=3, lambda_param=0.7):
        """
        MMR = lambda * cosine_similarity(sentence, document)
                - (1 - lambda) * max cosine_similarity(sentence, selected)
        """
        # cosine similarity of each sentence against the whole document
        doc_scores = F.cosine_similarity(
            sentence_embeddings,                          # (N, hidden)
            doc_embedding.expand(len(sentence_embeddings), -1),  # (N, hidden)
        )  # → (N,)

        selected = []
        candidates = list(range(len(doc_scores)))

        while candidates and len(selected) < num_sentences:
            if not selected:
                best_idx = max(candidates, key=lambda i: doc_scores[i].item())
                selected.append(best_idx)
                candidates.remove(best_idx)
                continue

            mmr_scores = []
            for i in candidates:
                relevance = doc_scores[i].item()

                # cosine similarity against each already-selected sentence
                redundancy = max(
                    F.cosine_similarity(
                        sentence_embeddings[i].unsqueeze(0),
                        sentence_embeddings[j].unsqueeze(0),
                    ).item()
                    for j in selected
                )

                mmr_score = lambda_param * relevance - (1 - lambda_param) * redundancy
                mmr_scores.append((i, mmr_score))

            best_idx = max(mmr_scores, key=lambda x: x[1])[0]
            selected.append(best_idx)
            candidates.remove(best_idx)

        return sorted(selected)

    def extractive_summary(self, text, num_sentences=3, lambda_param=0.7, device="cpu"):
        sentences = self.split_sentences(text)

        if len(sentences) <= num_sentences:
            return text

        tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME, local_files_only=True)
        model = AutoModel.from_pretrained(self.MODEL_NAME, local_files_only=True)

        sentence_embeddings = self.embed_texts(sentences, tokenizer, model, device=device)
        doc_embedding = self.embed_texts([text], tokenizer, model, device=device)

        selected_indices = self.mmr_select(
            sentence_embeddings,
            doc_embedding,
            num_sentences=num_sentences,
            lambda_param=lambda_param,
        )

        summary_sentences = [sentences[i] for i in selected_indices]
        return " ".join(summary_sentences)

    def extractive_summary_with_scores(self, text, num_sentences=3, lambda_param=0.7, device="cpu"):
        sentences = self.split_sentences(text)

        tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME, local_files_only=True)
        model = AutoModel.from_pretrained(self.MODEL_NAME, local_files_only=True)

        sentence_embeddings = self.embed_texts(sentences, tokenizer, model, device=device)
        doc_embedding = self.embed_texts([text], tokenizer, model, device=device)

        # cosine similarity scores for ranking display
        doc_scores = F.cosine_similarity(
            sentence_embeddings,
            doc_embedding.expand(len(sentence_embeddings), -1),
        )

        selected_indices = self.mmr_select(
            sentence_embeddings,
            doc_embedding,
            num_sentences=num_sentences,
            lambda_param=lambda_param,
        )

        ranked = [(i, sentences[i], float(doc_scores[i])) for i in range(len(sentences))]
        ranked.sort(key=lambda x: x[2], reverse=True)

        summary = " ".join(sentences[i] for i in sorted(selected_indices))
        return summary, ranked

    def sumarize(self, text, num_sentences=3, lambda_param=0.75, device="cuda" if torch.cuda.is_available() else "cpu"): # lambda higher = more relevant, lower = more diverse
        return self.extractive_summary(text, num_sentences=num_sentences, lambda_param=lambda_param, device=device)
