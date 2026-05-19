from typing import Optional, Dict, Any
from .constants import BIBLE_CATALOG

class MetadataRetriever:
    def __init__(self):
        self.catalog = BIBLE_CATALOG

    def retrieve(self, query: str) -> Optional[str]:
        query = query.lower()
        
        # Total number of books
        if any(w in query for w in ["כמה ספרים", "מספר הספרים", "number of books"]):
            return f"בתנ\"ך ישנם {len(self.catalog)} ספרים."

        # Longest book (by chapter count)
        if any(w in query for w in ["הספר הארוך ביותר", "longest book"]):
            longest = max(self.catalog, key=lambda x: x["number_of_chapters"])
            return f"הספר הארוך ביותר הוא {longest['hebrew']} עם {longest['number_of_chapters']} פרקים."

        # Shortest book
        if any(w in query for w in ["הספר הקצר ביותר", "shortest book"]):
            shortest = min(self.catalog, key=lambda x: x["number_of_chapters"])
            return f"הספר הקצר ביותר הוא {shortest['hebrew']} עם {shortest['number_of_chapters']} פרקים."

        # Specific book index (e.g. 5th book)
        import re
        match = re.search(r"(חומש|ספר)\s+(הראשון|השני|השלישי|הרביעי|החמישי)", query)
        if match:
            ordinals = {"הראשון": 1, "השני": 2, "השלישי": 3, "הרביעי": 4, "החמישי": 5}
            idx = ordinals.get(match.group(2))
            if idx:
                book = self.catalog[idx-1]
                return f"הספר ה{match.group(2)} הוא {book['hebrew']}."

        return None
