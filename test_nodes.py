import unittest

from code_utils import extract_python_code, parse_result


class TestNodeHelpers(unittest.TestCase):
    def test_extract_python_code_accepts_fenced_code_with_prose(self):
        response = """Here is the analysis:
```python
result = df["Age"].mean()
```
"""

        self.assertEqual(extract_python_code(response), 'result = df["Age"].mean()')

    def test_extract_python_code_removes_prose_around_unfenced_code(self):
        response = """I calculated the answer below.
result = df["Age"].mean()
"""

        self.assertEqual(extract_python_code(response), 'result = df["Age"].mean()')

    def test_extract_python_code_rejects_responses_without_code(self):
        with self.assertRaisesRegex(ValueError, "valid Python"):
            extract_python_code("I cannot answer this question.")

    def test_parse_result_handles_repr_values(self):
        self.assertEqual(parse_result("RESULT: 42"), "42")
        self.assertEqual(parse_result("RESULT: {'survived': 0.38}"), "{'survived': 0.38}")

    def test_parse_result_returns_none_when_marker_is_missing(self):
        self.assertIsNone(parse_result("execution completed"))
