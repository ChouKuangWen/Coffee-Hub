# tests/core/test_sanitizer.py
import pytest
from app.core.sanitizer import sanitize_user_input, sanitize_number_input

""""Tests for sanitize_user_input"""

# 測試：sanitize_user_input 應該移除所有 HTML 標籤，只保留純文字。
def test_sanitize_removes_html_tags():
    """
    範例：<b>hello</b> <script>alert('xss')</script> → hello alert('xss')
    """
    raw_input = "<b>hello</b> <script>alert('xss')</script>"
    expected = "hello alert('xss')"
    assert sanitize_user_input(raw_input) == expected

# 測試：sanitize_user_input 對純文字輸入不應修改。
def test_sanitize_keeps_plain_text():
    raw_input = "just some text"
    assert sanitize_user_input(raw_input) == "just some text"

# 測試：sanitize_user_input 對 None 輸入應回傳空字串。
def test_sanitize_none_input():
    assert sanitize_user_input(None) == ""

# 測試：sanitize_user_input 對空字串輸入應回傳空字串。
def test_sanitize_empty_string():
    assert sanitize_user_input("") == ""

# 測試：sanitize_user_input 對複雜 HTML 標籤應正確淨化。
def test_sanitize_complex_html():
    """
    範例：<div>Hello <a href='url'>link</a></div> → Hello link
    """
    raw_input = "<div>Hello <a href='url'>link</a></div>"
    expected = "Hello link"
    assert sanitize_user_input(raw_input) == expected


"""Tests for sanitize_number_input"""


# 測試：sanitize_number_input 應保留原始數字輸入，不做修改。
@pytest.mark.parametrize("input_val", [123, 45.6, -10, 0])
def test_sanitize_number_returns_same_value(input_val):
    """
    使用 parametrize 測試多組數字值。
    """
    assert sanitize_number_input(input_val) == input_val
