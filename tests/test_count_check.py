"""FinalModal.count_check のユニットテスト"""
import pytest
from ui.flows import FinalModal


class TestCountCheck:
    def test_none_value_returns_none(self):
        assert FinalModal.count_check("趣味", None) is None

    def test_empty_string_returns_none(self):
        assert FinalModal.count_check("趣味", "") is None

    def test_single_item_ok(self):
        assert FinalModal.count_check("趣味", "筋トレ") is None

    def test_five_items_ok(self):
        assert FinalModal.count_check("趣味", "筋トレ ゲーム 料理 読書 映画") is None

    def test_six_items_error(self):
        result = FinalModal.count_check("趣味", "筋トレ ゲーム 料理 読書 映画 旅行")
        assert result is not None
        assert "趣味" in result
        assert "6" in result

    def test_seven_items_error(self):
        result = FinalModal.count_check("特技", "a b c d e f g")
        assert result is not None
        assert "特技" in result
        assert "7" in result

    def test_whitespace_only_returns_none(self):
        # 空白のみ → split() で空リスト → None
        assert FinalModal.count_check("趣味", "   ") is None

    def test_newline_separated_counts_correctly(self):
        # 改行区切りも split() で正しくカウント
        assert FinalModal.count_check("趣味", "筋トレ\nゲーム\n料理\n読書\n映画\n旅行") is not None
