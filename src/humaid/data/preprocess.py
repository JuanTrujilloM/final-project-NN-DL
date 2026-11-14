# Tweet cleaning (decisions justified in docs/protocolo-experimental.md).

import html
import re

# UTF-8 text wrongly decoded as Latin-1 (mojibake).
MOJIBAKE_RE = re.compile(
    "[Â-ô]"
    "[\u0080-¿ŒœŠšŸŽžƒˆ˜"
    "–—‘-„†-•…‰‹›€™]{1,3}"
)
URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
RETWEET_RE = re.compile(r"^(?:RT\s+@\w+:?\s*)+", re.IGNORECASE)
HASHTAG_RE = re.compile(r"#(\w+)")
CAMEL_RE = re.compile(r"(?<=[a-záéíóúñ0-9])(?=[A-ZÁÉÍÓÚÑ])")
REPEATED_TOKEN_RE = re.compile(r"(?<!\S)(HTTPURL|@USER)(?:\s+\1)+(?!\S)")
SPACE_RE = re.compile(r"\s+")


def _split_hashtag(tag):
    return CAMEL_RE.sub(" ", tag.replace("_", " "))


def _to_bytes(chars):
    out = bytearray()
    for ch in chars:
        try:
            out += ch.encode("cp1252")
        except UnicodeEncodeError:
            if ord(ch) >= 256:
                raise
            out.append(ord(ch))
    return bytes(out)


def _repair_run(match):
    try:
        return _to_bytes(match.group()).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return match.group()


def fix_mojibake(text):
    return MOJIBAKE_RE.sub(_repair_run, text)


def clean_tweet(text):
    if not isinstance(text, str):
        return ""
    text = html.unescape(fix_mojibake(text.strip()))
    text = RETWEET_RE.sub("", text)
    text = URL_RE.sub("HTTPURL", text)
    text = MENTION_RE.sub("@USER", text)
    text = HASHTAG_RE.sub(lambda m: _split_hashtag(m.group(1)), text)
    text = REPEATED_TOKEN_RE.sub(r"\1", text)
    return SPACE_RE.sub(" ", text).strip()


# Stage 3: each Spanish Twitter model was pretrained with its own placeholders. These functions start from the
# output of clean_tweet (@USER, HTTPURL) because the Spanish HumAID only exists already cleaned.
LAUGHTER_RE = re.compile(r"[ja][ja]+aj[ja]+")
EMOJI_NAME_RE = re.compile(r"\|([^|]+)\|")


# BERTuit: its tokenizer has the special tokens <usr> and <url> (model card of AIDA-UPM/BERTuit-base).
def _for_bertuit(text):
    return text.replace("@USER", "<usr>").replace("HTTPURL", "<url>")


# RoBERTuito: same steps as pysentimiento.preprocess_tweet for Spanish (@usuario, url, characters repeated at most
# 3 times, laughter as "jaja", emojis as "emoji <name> emoji"). Hashtags were already split by clean_tweet.
def _for_robertuito(text):
    import emoji

    text = text.replace("@USER", "@usuario").replace("HTTPURL", "url")
    text = re.sub(r"(.)\1{3,}", r"\1\1\1", text)
    text = LAUGHTER_RE.sub("jaja", text)
    text = emoji.demojize(text, language="es", delimiters=("|", "|"))
    text = EMOJI_NAME_RE.sub(lambda m: " emoji " + m.group(1).replace("_", " ") + " emoji ", text)
    return SPACE_RE.sub(" ", text).strip()


# BERT colombiano does not document a format; BETO has no emojis and splits @USER/HTTPURL into pieces, so it gets
# the Spanish placeholders of RoBERTuito (@usuario, url, emojis as text).
MODEL_TEXT_STYLES = {"bertuit": _for_bertuit, "robertuito": _for_robertuito, "bert_colombiano": _for_robertuito}


# Adapts a text already cleaned with clean_tweet to the model; None (XLM-R) leaves it as is.
def adapt_text(text, style=None):
    if style is None:
        return text
    return MODEL_TEXT_STYLES[style](text)
