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
