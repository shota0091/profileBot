# models/user.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    name: str
    age: Optional[int] = None
    birth_year: Optional[int] = None  
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    delete_flag: int = 0
    last_message_id: Optional[int] = None
    last_channel_id: Optional[int] = None