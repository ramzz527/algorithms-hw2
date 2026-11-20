import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_round_trips_values_across_digit_boundaries(self):
        for number in (0, 1, 61, 62, 63, 3843, 3844, 2**128):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_zero_has_one_digit(self):
        self.assertEqual(encode(0), "0")

    def test_rejects_negative_and_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        with self.assertRaises(TypeError):
            encode(True)

    def test_rejects_empty_and_invalid_codes(self):
        for code in ("", "abc!"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)

    def test_rejects_non_string_codes(self):
        with self.assertRaises(TypeError):
            decode(62)


if __name__ == "__main__":
    unittest.main()
