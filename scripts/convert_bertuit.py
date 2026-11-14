# BERTuit (AIDA-UPM/BERTuit-base) only publishes TensorFlow weights, which transformers 5 no longer loads.
# This script reads tf_model.h5 with h5py (no TensorFlow needed), copies the weights into a PyTorch
# RobertaForMaskedLM and checks that the converted model fills in masked Spanish words.

import argparse
import re
import shutil
from pathlib import Path

import h5py
import numpy as np
import torch
from huggingface_hub import hf_hub_download
from transformers import AutoConfig, AutoTokenizer, RobertaForMaskedLM

REPO = "AIDA-UPM/BERTuit-base"
FILES = ["config.json", "vocab.json", "merges.txt", "tokenizer_config.json", "special_tokens_map.json", "tf_model.h5"]
# MLM loss on these sentences; a random model gets about ln(30000) = 10.3.
CHECK_SENTENCES = [
    "El terremoto dejó cientos de casas destruidas y muchas familias sin hogar.",
    "Necesitamos agua, comida y medicinas para las personas evacuadas.",
    "Los bomberos siguen buscando a los desaparecidos entre los escombros.",
    "Mucha fuerza para todas las familias afectadas por las inundaciones.",
]
MAX_CHECK_LOSS = 6.0


# TF name (e.g. roberta/ber_tuit/roberta/encoder/layer_._3/attention/self/query/kernel:0) to PyTorch name.
def torch_name(tf_name):
    name = tf_name.split(":")[0]
    name = name[name.rindex("roberta/"):] if "roberta/" in name else name[name.rindex("lm_head/"):]
    name = re.sub(r"layer_\._(\d+)", r"layer.\1", name)
    name = name.replace("/", ".")
    name = re.sub(r"\.(kernel|gamma)$", ".weight", name)
    name = re.sub(r"\.beta$", ".bias", name)
    name = re.sub(r"(position_embeddings|token_type_embeddings)\.embeddings$", r"\1.weight", name)
    return name


def read_h5(path):
    weights = {}
    with h5py.File(path, "r") as f:
        f.visititems(lambda name, obj: weights.__setitem__(name, np.array(obj)) if isinstance(obj, h5py.Dataset) else None)
    return weights


def convert(source, out_dir):
    config = AutoConfig.from_pretrained(source)
    model = RobertaForMaskedLM(config)
    state = model.state_dict()
    loaded = {}
    for tf_name, array in read_h5(source / "tf_model.h5").items():
        name = torch_name(tf_name)
        if name not in state:
            raise KeyError(f"Peso sin destino: {tf_name} -> {name}")
        tensor = torch.from_numpy(array.T.copy() if tf_name.split(":")[0].endswith("kernel") else array)
        if tensor.shape != state[name].shape:
            raise ValueError(f"{name}: forma {tuple(tensor.shape)} en TF, {tuple(state[name].shape)} en PyTorch")
        # The .h5 stores the embeddings twice (also under lm_head, which shares them); both copies must match.
        if name in loaded and not torch.equal(loaded[name], tensor):
            raise ValueError(f"{name}: dos copias distintas en el .h5")
        loaded[name] = tensor
    # The decoder shares the word embeddings and lm_head.bias; position_ids are buffers, not weights.
    missing = [k for k in state if k not in loaded and not k.startswith("lm_head.decoder.")
               and not k.endswith("position_ids")]
    if missing:
        raise KeyError(f"Pesos sin valor en el .h5: {missing}")
    model.load_state_dict(loaded, strict=False)
    model.tie_weights()
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(source)
    loss = check(model, tokenizer)
    print(f"Pérdida MLM en frases de prueba: {loss:.2f} (modelo aleatorio ≈ 10.3)")
    if loss > MAX_CHECK_LOSS:
        raise RuntimeError("El modelo convertido no predice bien las palabras enmascaradas")

    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)
    print(f"BERTuit en PyTorch guardado en {out_dir}")


# Masks every 4th word token (deterministic) and returns the mean cross-entropy on them.
@torch.no_grad()
def check(model, tokenizer):
    enc = tokenizer(CHECK_SENTENCES, padding=True, return_tensors="pt")
    labels = torch.full_like(enc["input_ids"], -100)
    special = torch.tensor([[t in tokenizer.all_special_ids for t in row] for row in enc["input_ids"].tolist()])
    positions = (~special).nonzero().tolist()
    for row, col in positions[::4]:
        labels[row, col] = enc["input_ids"][row, col]
        enc["input_ids"][row, col] = tokenizer.mask_token_id
    return model(**enc, labels=labels).loss.item()


def main():
    parser = argparse.ArgumentParser(description="Convierte BERTuit de TensorFlow a PyTorch")
    parser.add_argument("--out", default="models/checkpoints/hf/bertuit-base")
    args = parser.parse_args()
    out_dir = Path(args.out)
    source = out_dir.with_name(out_dir.name + "-tf")
    source.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        hf_hub_download(REPO, name, local_dir=source)
    convert(source, out_dir)
    shutil.rmtree(source)


if __name__ == "__main__":
    main()
