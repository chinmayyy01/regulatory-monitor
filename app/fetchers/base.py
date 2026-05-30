from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Circular:
    id: str                   #will use the url as the id
    title: str
    source: str               #rbi or sebi
    url: str
    published_date: datetime
    full_text: str            #summarized content
    raw_html: Optional[str] = None