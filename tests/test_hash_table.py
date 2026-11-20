import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_empty_table_returns_none_for_missing_keys(self):
        table = HashTable()
        self.assertIsNone(table.get("missing"))
        self.assertFalse(table.contains("missing"))
        self.assertIsNone(table.remove("missing"))

    def test_collisions_keep_distinct_values(self):
        table = HashTable()
        table.put("a", 1)
        table.put("i", 2)

        self.assertEqual(table.get("a"), 1)
        self.assertEqual(table.get("i"), 2)

    def test_put_updates_existing_key_without_duplicate(self):
        table = HashTable()
        table.put("key", "first")
        table.put("key", "second")

        self.assertTrue(table.contains("key"))
        self.assertEqual(table.get("key"), "second")
        self.assertEqual(len(table), 1)

    def test_resize_preserves_entries(self):
        table = HashTable()
        entries = [(f"key-{index}", index) for index in range(20)]
        for key, value in entries:
            table.put(key, value)

        for key, value in entries:
            with self.subTest(key=key):
                self.assertEqual(table.get(key), value)

    def test_remove_and_reinsert(self):
        table = HashTable()
        table.put("key", 1)

        self.assertEqual(table.remove("key"), 1)
        self.assertFalse(table.contains("key"))
        table.put("key", 2)
        self.assertEqual(table.get("key"), 2)


if __name__ == "__main__":
    unittest.main()
