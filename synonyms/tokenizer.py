import tiktoken

_ENCODING_MAP = {
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-4": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "claude": "cl100k_base",  # approximation
}

_cache: dict[str, tiktoken.Encoding] = {}


def get_encoding(model: str) -> tiktoken.Encoding:
    enc_name = _ENCODING_MAP.get(model, model)
    if enc_name not in _cache:
        _cache[enc_name] = tiktoken.get_encoding(enc_name)
    return _cache[enc_name]


def count(text: str, model: str = "gpt-4o") -> int:
    return len(get_encoding(model).encode(text))


def token_savings(original: str, replacement: str, model: str = "gpt-4o") -> int:
    # Prefix with space to simulate in-text context: BPE merges leading space
    # with the word, making ' word' often 1 token even when 'word' alone is many.
    enc = get_encoding(model)
    return len(enc.encode(" " + original)) - len(enc.encode(" " + replacement))
