def normalize_with_map(text: str) -> tuple[str, list[int]]:
    characters: list[str] = []
    index_map: list[int] = []
    previous_space = False
    for index, character in enumerate(text):
        if character.isspace():
            if previous_space:
                continue
            characters.append(" ")
            index_map.append(index)
            previous_space = True
        else:
            characters.append(character.lower())
            index_map.append(index)
            previous_space = False
    return "".join(characters), index_map


def find_span(text: str, quote: str) -> dict | None:
    if not quote or not text:
        return None
    haystack, index_map = normalize_with_map(text)
    needle, _ = normalize_with_map(quote)
    needle = needle.strip()
    if not needle:
        return None
    position = haystack.find(needle)
    if position == -1:
        return None
    start = index_map[position]
    end = index_map[position + len(needle) - 1] + 1
    return {"start": start, "end": end}
