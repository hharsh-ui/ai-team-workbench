"""Turn command-line words into a dict of tool arguments.

Accepted forms (use whichever your shell quotes most easily):
  JSON:       '{"title": "Ship v1", "due": "+1d"}'
  key=value:  title="Ship v1" due=+1d
  flags:      --title "Ship v1" --due +1d
Words after a key=value or --key that are not themselves keys are joined to that value.
"""

import json


def coerce(value: str):
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    for kind in (int, float):
        try:
            return kind(value)
        except ValueError:
            pass
    if value[:1] in {"[", "{"}:
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value


def parse_arguments(words: list[str]) -> dict:
    if not words:
        return {}
    joined = " ".join(words).strip().strip("'")
    if joined.startswith("{"):
        try:
            value = json.loads(joined)
        except ValueError as error:
            raise ValueError(f"Arguments look like JSON but are not valid JSON: {error}") from error
        if not isinstance(value, dict):
            raise ValueError("JSON arguments must be an object.")
        return value
    pairs: list[tuple[str, list[str]]] = []
    for word in words:
        if word.startswith("--") and len(word) > 2:
            name, separator, value = word[2:].partition("=")
            pairs.append((name.replace("-", "_"), [value] if separator else []))
        elif "=" in word and word.split("=", 1)[0].isidentifier():
            name, _, value = word.partition("=")
            pairs.append((name, [value]))
        elif pairs:
            pairs[-1][1].append(word)
        else:
            raise ValueError(f"Unexpected word '{word}'. Use key=value, --key value or a JSON object.")
    return {name: coerce(" ".join(parts)) if parts else True for name, parts in pairs}
