# repositories/user_repo.py
from db.connection import get_conn
from models.user import User
from typing import Optional

class UserRepo:
    def _row_to_user(self, row) -> Optional[User]:
        if not row:
            return None
        return User(
            id=int(row["id"]),
            name=row["name"],
            age=row.get("age"),
            birth_year=row.get("birth_year"),
            birth_month=row.get("birth_month"),
            birth_day=row.get("birth_day"),
            delete_flag=int(row.get("delete_flag", 0)),
            last_message_id=row.get("last_message_id"),
            last_channel_id=row.get("last_channel_id"),
        )

    def get(self, user_id: int) -> Optional[User]:
        with get_conn() as c, c.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, age, birth_year, birth_month, birth_day,
                       delete_flag, last_message_id, last_channel_id
                  FROM users
                 WHERE id=%s
                """,
                (user_id,),
            )
            return self._row_to_user(cur.fetchone())

    def upsert(self, u: User) -> None:
        with get_conn() as c, c.cursor() as cur:
            cur.execute(
                """
                REPLACE INTO users
                (id, name, age, birth_year, birth_month, birth_day, delete_flag,
                 last_message_id, last_channel_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    u.id, u.name, u.age, u.birth_year, u.birth_month, u.birth_day,
                    u.delete_flag, u.last_message_id, u.last_channel_id
                ),
            )
            c.commit()

    def save_message_location(self, user_id: int, message_id: int, channel_id: int):
        with get_conn() as c, c.cursor() as cur:
            cur.execute(
                "UPDATE users SET last_message_id=%s, last_channel_id=%s WHERE id=%s",
                (int(message_id), int(channel_id), int(user_id)),
            )
            c.commit()

    def clear_profile(self, user_id: int):
        with get_conn() as c, c.cursor() as cur:
            cur.execute(
                """
                UPDATE users SET
                    delete_flag=0,
                    age=NULL,
                    birth_year=NULL,
                    birth_month=NULL,
                    birth_day=NULL,
                    last_message_id=NULL,
                    last_channel_id=NULL
                WHERE id=%s
                """,
                (user_id,),
            )
            c.commit()
