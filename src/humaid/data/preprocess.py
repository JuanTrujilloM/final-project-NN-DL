# Tweet cleaning (decisions justified in docs/protocolo-experimental.md).

import html
import re

import emoji

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

# Stage 3 text styles.
REPEATED_CHAR_RE = re.compile(r"(.)\1{3,}")
LAUGHTER_RE = re.compile(r"[ja][ja]+aj[ja]+")
EMOJI_NAME_RE = re.compile(r"\|([^|]+)\|")


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


# For BERTuit, its tokenizer has <usr> and <url> as special tokens.
def _bertuit_style(text):
    return text.replace("@USER", "<usr>").replace("HTTPURL", "<url>")


# For RoBERTuito, the Spanish preprocessing of pysentimiento.
def _robertuito_style(text):
    text = text.replace("@USER", "@usuario").replace("HTTPURL", "url")
    text = REPEATED_CHAR_RE.sub(r"\1\1\1", text)
    text = LAUGHTER_RE.sub("jaja", text)
    text = emoji.demojize(text, language="es", delimiters=("|", "|"))
    text = EMOJI_NAME_RE.sub(lambda m: f" emoji {m.group(1).replace('_', ' ')} emoji ", text)
    return SPACE_RE.sub(" ", text).strip()


# For BERT colombiano, since it has no specific format, it reuses the RoBERTuito style.
TEXT_STYLES = {"bertuit": _bertuit_style, "robertuito": _robertuito_style, "bert_colombiano": _robertuito_style}


# Adapts the output of clean_tweet to the text style of a stage 3 model; None leaves it unchanged.
def adapt_text(text, style=None):
    if style is None:
        return text
    return TEXT_STYLES[style](text)
