"""_parse_birthday のユニットテスト"""
import pytest
from ui.flows import _parse_birthday


# ── 正常系 ──────────────────────────────────────────────────────────────
class TestParseBirthdayValid:
    def test_slash_format(self):
        assert _parse_birthday("7-11") == (7, 11)

    def test_4digit_format(self):
        assert _parse_birthday("0711") == (7, 11)

    def test_3digit_format(self):
        assert _parse_birthday("711") == (7, 11)

    def test_kanji_format(self):
        assert _parse_birthday("7月11日") == (7, 11)

    def test_slash_format_alt(self):
        assert _parse_birthday("7/11") == (7, 11)

    def test_december_31(self):
        assert _parse_birthday("12/31") == (12, 31)

    def test_jan_1(self):
        assert _parse_birthday("1/1") == (1, 1)

    def test_feb_28(self):
        assert _parse_birthday("2/28") == (2, 28)

    def test_april_30(self):
        assert _parse_birthday("4/30") == (4, 30)

    def test_spaces_stripped(self):
        assert _parse_birthday("  7/11  ") == (7, 11)


# ── 異常系：無効な日付 ────────────────────────────────────────────────────
class TestParseBirthdayInvalid:
    def test_empty_string(self):
        assert _parse_birthday("") == (None, None)

    def test_none_equivalent(self):
        assert _parse_birthday("   ") == (None, None)

    def test_feb_29_invalid(self):
        # うるう年の考慮なし（2/29は常に無効）
        assert _parse_birthday("2/29") == (None, None)

    def test_june_31_invalid(self):
        # 6月は30日まで
        assert _parse_birthday("6/31") == (None, None)

    def test_april_31_invalid(self):
        # 4月は30日まで
        assert _parse_birthday("4/31") == (None, None)

    def test_month_0_invalid(self):
        assert _parse_birthday("0/15") == (None, None)

    def test_month_13_invalid(self):
        assert _parse_birthday("13/1") == (None, None)

    def test_alphabetic_input(self):
        assert _parse_birthday("abc") == (None, None)

    def test_single_digit_only(self):
        # 1桁のみ → 判定不能
        assert _parse_birthday("7") == (None, None)

    def test_day_0_invalid(self):
        assert _parse_birthday("7/0") == (None, None)
