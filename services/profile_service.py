# services/profile_service.py
from repositories.user_repo import UserRepo
from models.user import User
from typing import Optional

class ProfileService:
    def __init__(self):
        self.repo = UserRepo()

    def can_register(self, user_id: int) -> bool:
        u = self.repo.get(user_id)
        return (u is None) or (u.delete_flag != 1)

    def register(self, user_id: int, name: str, age, birth_year, birth_month, birth_day):
        u: Optional[User] = self.repo.get(user_id)
        if u is None:
            u = User(id=int(user_id), name=name)
        # 更新
        u.name = name
        u.age = age
        u.birth_year = birth_year
        u.birth_month = birth_month
        u.birth_day = birth_day
        u.delete_flag = 1
        self.repo.upsert(u)

    def save_message_location(self, user_id: int, message_id: int, channel_id: int):
        self.repo.save_message_location(user_id, message_id, channel_id)

    def get_user(self, user_id: int) -> Optional[User]:
        return self.repo.get(user_id)

    def soft_delete_profile(self, user_id: int):
        self.repo.clear_profile(user_id)
