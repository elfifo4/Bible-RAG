import re
import unicodedata
import json
from pathlib import Path

class HebrewProcessor:
    @staticmethod
    def normalize_spaces(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def remove_cantillation(text: str) -> str:
        result = []
        for char in unicodedata.normalize("NFD", text):
            code = ord(char)
            if 0x0591 <= code <= 0x05AF: continue
            if code == 0x05BD: continue  # METEG
            result.append(char)
        return unicodedata.normalize("NFC", "".join(result))

    @staticmethod
    def remove_niqqud(text: str) -> str:
        result = []
        for char in unicodedata.normalize("NFD", text):
            code = ord(char)
            if 0x05B0 <= code <= 0x05BC: continue
            if code in (0x05C1, 0x05C2, 0x05C7): continue
            result.append(char)
        return unicodedata.normalize("NFC", "".join(result))

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r"[׃:]", "", text)
        text = text.replace("־", " ")
        text = text.replace("׀", " ")
        return HebrewProcessor.normalize_spaces(text)

class Gematria:
    @staticmethod
    def to_otiot(num: int) -> str:
        def ahadot(n): return {1:"א",2:"ב",3:"ג",4:"ד",5:"ה",6:"ו",7:"ז",8:"ח",9:"ט"}.get(n % 10, "")
        def asarot(n): return {1:"י",2:"כ",3:"ל",4:"מ",5:"נ",6:"ס",7:"ע",8:"פ",9:"צ"}.get((n % 100) // 10, "")
        def meot(n): return {1:"ק",2:"ר",3:"ש",4:"ת"}.get(n // 100, "")

        if num % 100 == 15: return meot(num) + "טו"
        if num % 100 == 16: return meot(num) + "טז"
        return meot(num) + asarot(num) + ahadot(num)

    @staticmethod
    def otiot_to_number(value: str) -> int:
        for number in range(1, 1000):
            if Gematria.to_otiot(number) == value:
                return number
        raise ValueError(f"Unsupported Hebrew number: {value}")

def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_jsonl(path: Path, item: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
