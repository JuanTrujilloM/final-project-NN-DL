import json
import re
from pathlib import Path

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence, pad_sequence
from transformers import AutoConfig, AutoModel, AutoTokenizer

# Same tokenizer as the BiLSTM in the training notebooks (GloVe Twitter symbols, lowercase).
PAD, UNK = "<pad>", "<unk>"
TOKEN_RE = re.compile(r"<user>|<url>|[a-z0-9áéíóúüñ]+(?:'[a-z]+)?|[^\sa-z0-9áéíóúüñ]")
NUMBER_RE = re.compile(r"^\d+$")


def tokenize(text):
    text = text.replace("@USER", " <user> ").replace("HTTPURL", " <url> ").lower()
    return ["<number>" if NUMBER_RE.match(tok) else tok for tok in TOKEN_RE.findall(text)]


def mlp_head(in_dim, hidden, num_classes, dropout):
    return nn.Sequential(nn.Dropout(dropout), nn.Linear(in_dim, hidden), nn.ReLU(),
                         nn.Dropout(dropout), nn.Linear(hidden, num_classes))


# Same layers and parameter names as BiLSTMClassifier in the notebooks, so the saved state dict loads as is.
class BiLSTMClassifier(nn.Module):
    def __init__(self, hp, vocab_size, emb_dim, pad_id, num_classes):
        super().__init__()
        self.pooling = hp["pooling"]
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=pad_id)
        self.emb_dropout = nn.Dropout(hp["emb_dropout"])
        self.lstm = nn.LSTM(emb_dim, hp["hidden_size"], num_layers=hp["num_layers"], batch_first=True,
                            bidirectional=True, dropout=hp["rnn_dropout"] if hp["num_layers"] > 1 else 0.0)
        out_dim = 2 * hp["hidden_size"]
        if "attention" in self.pooling:
            self.attention = nn.Linear(out_dim, 1)
        rep_dim = out_dim * (2 if self.pooling == "attention_max" else 1)
        self.head = mlp_head(rep_dim, hp["head_hidden"], num_classes, hp["dropout"])

    def forward(self, ids, lengths):
        emb = self.emb_dropout(self.embedding(ids))
        packed = pack_padded_sequence(emb, lengths.cpu(), batch_first=True, enforce_sorted=False)
        out, _ = pad_packed_sequence(self.lstm(packed)[0], batch_first=True, total_length=ids.size(1))
        mask = torch.arange(ids.size(1))[None, :] < lengths[:, None]
        parts = []
        if "attention" in self.pooling:
            scores = self.attention(out).squeeze(-1).masked_fill(~mask, float("-inf"))
            parts.append((torch.softmax(scores, dim=1).unsqueeze(-1) * out).sum(dim=1))
        if "max" in self.pooling:
            parts.append(out.masked_fill(~mask.unsqueeze(-1), float("-inf")).max(dim=1).values)
        return self.head(torch.cat(parts, dim=1))


# Same parameter names as PretrainedClassifier in the notebooks: encoder, mean pooling and a linear layer.
class TransformerClassifier(nn.Module):
    def __init__(self, encoder_dir, dropout, num_classes):
        super().__init__()
        self.encoder = AutoModel.from_config(AutoConfig.from_pretrained(encoder_dir))
        self.drop = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_classes)

    def forward(self, input_ids, attention_mask):
        hidden = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        mask = attention_mask.unsqueeze(-1).to(hidden.dtype)
        return self.classifier(self.drop((hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)))


# A model folder exported by the notebooks, ready to return class probabilities for cleaned texts.
class LoadedModel:
    def __init__(self, model_dir):
        model_dir = Path(model_dir)
        config = json.loads((model_dir / "config.json").read_text())
        self.labels = config["labels"]
        self.hp = config["hiperparametros"]
        self.kind = config["tipo"]
        if self.kind == "bilstm":
            self.vocab = json.loads((model_dir / "vocab.json").read_text())
            self.model = BiLSTMClassifier(self.hp, len(self.vocab), config["glove_dim"], self.vocab[PAD], len(self.labels))
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir / "tokenizer")
            self.model = TransformerClassifier(model_dir / "encoder", self.hp["dropout"], len(self.labels))
        self.model.load_state_dict(torch.load(model_dir / "model.pt", map_location="cpu"))
        self.model.eval()

    @torch.inference_mode()
    def predict(self, texts):
        if self.kind == "bilstm":
            unk = self.vocab[UNK]
            ids = [[self.vocab.get(tok, unk) for tok in tokenize(text)][:self.hp["max_len"]] or [unk] for text in texts]
            padded = pad_sequence([torch.tensor(i) for i in ids], batch_first=True, padding_value=self.vocab[PAD])
            logits = self.model(padded, torch.tensor([len(i) for i in ids]))
        else:
            chunks = []
            for start in range(0, len(texts), 16):
                enc = self.tokenizer(texts[start:start + 16], truncation=True, max_length=self.hp["max_len"],
                                     padding=True, return_tensors="pt")
                chunks.append(self.model(enc["input_ids"], enc["attention_mask"]))
            logits = torch.cat(chunks)
        probs = torch.softmax(logits.float(), dim=1)
        return [dict(zip(self.labels, row.tolist())) for row in probs]
