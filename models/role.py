# models/user.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    role_name: str
    role_id: Optional[int] = None
    guild_id: Optional[int] = None  