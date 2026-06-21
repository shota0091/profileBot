"""ProfileService のユニットテスト（UserRepo をモック）"""
import pytest
from unittest.mock import MagicMock, patch
from models.user import User
from services.profile_service import ProfileService


def _make_service(mock_repo):
    """UserRepo をモックに差し替えた ProfileService を返す"""
    with patch("services.profile_service.UserRepo", return_value=mock_repo):
        return ProfileService()


# ── can_register ─────────────────────────────────────────────────────────
class TestCanRegister:
    def test_new_user_can_register(self):
        repo = MagicMock()
        repo.get.return_value = None
        svc = _make_service(repo)
        assert svc.can_register(123) is True

    def test_active_user_cannot_register(self):
        # delete_flag=1 → 登録済みなので再登録不可
        repo = MagicMock()
        repo.get.return_value = User(id=123, name="Alice", delete_flag=1)
        svc = _make_service(repo)
        assert svc.can_register(123) is False

    def test_deleted_user_can_register(self):
        # delete_flag=0 → 削除済みなので再登録可
        repo = MagicMock()
        repo.get.return_value = User(id=123, name="Alice", delete_flag=0)
        svc = _make_service(repo)
        assert svc.can_register(123) is True


# ── register ─────────────────────────────────────────────────────────────
class TestRegister:
    def test_new_user_creates_record_with_active_flag(self):
        repo = MagicMock()
        repo.get.return_value = None
        svc = _make_service(repo)
        svc.register(user_id=1, name="Bob", age=25, birth_year=None, birth_month=7, birth_day=11)

        repo.upsert.assert_called_once()
        saved: User = repo.upsert.call_args[0][0]
        assert saved.id == 1
        assert saved.name == "Bob"
        assert saved.age == 25
        assert saved.birth_month == 7
        assert saved.birth_day == 11
        assert saved.delete_flag == 1  # 登録済みフラグ

    def test_existing_user_updates_fields(self):
        existing = User(id=2, name="Carol", age=20, delete_flag=0)
        repo = MagicMock()
        repo.get.return_value = existing
        svc = _make_service(repo)
        svc.register(user_id=2, name="Carol-Updated", age=21, birth_year=None, birth_month=3, birth_day=15)

        saved: User = repo.upsert.call_args[0][0]
        assert saved.name == "Carol-Updated"
        assert saved.age == 21
        assert saved.birth_month == 3
        assert saved.birth_day == 15
        assert saved.delete_flag == 1


# ── soft_delete_profile ──────────────────────────────────────────────────
class TestSoftDeleteProfile:
    def test_calls_clear_profile(self):
        repo = MagicMock()
        svc = _make_service(repo)
        svc.soft_delete_profile(99)
        repo.clear_profile.assert_called_once_with(99)


# ── get_user ─────────────────────────────────────────────────────────────
class TestGetUser:
    def test_returns_user_from_repo(self):
        user = User(id=5, name="Dave")
        repo = MagicMock()
        repo.get.return_value = user
        svc = _make_service(repo)
        assert svc.get_user(5) is user

    def test_returns_none_when_not_found(self):
        repo = MagicMock()
        repo.get.return_value = None
        svc = _make_service(repo)
        assert svc.get_user(999) is None
