"""Limpieza de tweets.

Decisiones (justificación en docs/protocolo-experimental.md):
- URLs -> `HTTPURL` y menciones -> `@USER`: la convención de BERTweet, que además funciona
  igual para XLM-R y para el BiLSTM. El contenido de una URL o de un usuario no aporta a la
  categoría humanitaria y solo agrega vocabulario raro.
- Hashtags -> se conserva la palabra y se separa el CamelCase (#HurricaneIrma -> Hurricane
  Irma), porque suelen cargar el tema del tweet.
- Emojis y mayúsculas se conservan; cada modelo decide si pasa a minúsculas (el BiLSTM sí,
  los Transformers según su tokenizador).
- Se quita el prefijo "RT @usuario:" y las entidades HTML (&amp;).
- Se repara el texto con doble codificación ("AtenciÃ³n" -> "Atención"): el 39 % de los
  tweets de Chile 2014 en CrisisBench lo traen así y el modelo vería palabras inexistentes.
"""

import html
import re

# Un byte inicial UTF-8 leído como Latin-1/cp1252 (Â, Ã, ð...) seguido de sus bytes de continuación.
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
WORD_RE = re.compile(r"@?\w+|[^\w\s]")


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


def tokenize_words(text):
    """Tokenización simple por palabras y signos, en minúsculas, para el BiLSTM.

    Los Transformers usan su propio tokenizador sobre `clean_tweet`.
    """
    return WORD_RE.findall(text.lower())
