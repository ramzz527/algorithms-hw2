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

        self.assertEqual(table.capacity, 32)
        for key, value in entries:
            with self.subTest(key=key):
                self.assertEqual(table.get(key), value)

    def test_resize_occurs_only_after_load_factor_exceeds_three_quarters(self):
        table = HashTable()
        for index in range(6):
            table.put(f"key-{index}", index)
        self.assertEqual(table.capacity, 8)

        table.put("key-6", 6)

        self.assertEqual(table.capacity, 16)
        for index in range(7):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_resize_can_be_disabled_for_fixed_capacity_measurements(self):
        table = HashTable(initial_capacity=4, max_load_factor=None)
        for index in range(12):
            table.put(f"key-{index}", index)

        self.assertEqual(table.capacity, 4)
        self.assertEqual(len(table), 12)

    def test_remove_and_reinsert(self):
        table = HashTable()
        table.put("key", 1)

        self.assertEqual(table.remove("key"), 1)
        self.assertFalse(table.contains("key"))
        table.put("key", 2)
        self.assertEqual(table.get("key"), 2)

    def test_removing_one_colliding_key_preserves_the_other(self):
        table = HashTable()
        table.put("a", 1)
        table.put("i", 2)

        self.assertEqual(table.remove("a"), 1)

        self.assertFalse(table.contains("a"))
        self.assertEqual(table.get("i"), 2)


if __name__ == "__main__":
    unittest.main()
