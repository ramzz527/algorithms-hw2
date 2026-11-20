import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


class LinearProbingTests(unittest.TestCase):
    def test_public_operations_match_chaining_table_contract(self):
        for table_type in (HashTable, LinearProbingHashTable):
            with self.subTest(table_type=table_type.__name__):
                table = table_type(initial_capacity=4, max_load_factor=None)

                self.assertEqual(len(table), 0)
                self.assertFalse(table.contains("key"))
                self.assertIsNone(table.get("key"))
                self.assertIsNone(table.remove("key"))
                self.assertIsNone(table.put("key", "first"))
                self.assertTrue(table.contains("key"))
                self.assertEqual(table.get("key"), "first")
                self.assertIsNone(table.put("key", "updated"))
                self.assertEqual(len(table), 1)
                self.assertEqual(table.remove("key"), "updated")
                self.assertEqual(len(table), 0)

    def keys_for_bucket(self, table, bucket, count):
        keys = []
        candidate = 0
        while len(keys) < count:
            key = f"wrap-{candidate}"
            if table.hash_steps(key)[-1][3] == bucket:
                keys.append(key)
            candidate += 1
        return keys

    def test_probe_wraps_from_last_slot_to_first(self):
        table = LinearProbingHashTable(initial_capacity=8, max_load_factor=None)
        keys = self.keys_for_bucket(table, 7, 3)
        for value, key in enumerate(keys):
            table.put(key, value)

        self.assertEqual(table.probe_trace(keys[2]), [7, 0, 1])
        self.assertEqual(table.get(keys[2]), 2)

    def test_full_table_terminates_missing_search_and_rejects_insert(self):
        table = LinearProbingHashTable(initial_capacity=2, max_load_factor=None)
        table.put("first", 1)
        table.put("second", 2)

        self.assertFalse(table.contains("missing"))
        self.assertIsNone(table.get("missing"))
        with self.assertRaises(OverflowError):
            table.put("third", 3)

    def test_removed_slot_in_full_table_can_be_reused(self):
        table = LinearProbingHashTable(initial_capacity=2, max_load_factor=None)
        keys = self.keys_for_bucket(table, 1, 3)
        table.put(keys[0], 0)
        table.put(keys[1], 1)

        self.assertEqual(table.remove(keys[0]), 0)
        table.put(keys[2], 2)

        self.assertEqual(len(table), 2)
        self.assertEqual(table.get(keys[1]), 1)
        self.assertEqual(table.get(keys[2]), 2)

    def test_tombstone_does_not_break_later_collision_lookup(self):
        table = LinearProbingHashTable(initial_capacity=8, max_load_factor=None)
        keys = self.keys_for_bucket(table, 5, 3)
        for value, key in enumerate(keys):
            table.put(key, value)

        self.assertEqual(table.remove(keys[0]), 0)
        self.assertEqual(table.get(keys[2]), 2)
        table.put(keys[0], 10)
        self.assertEqual(table.get(keys[0]), 10)

    def test_resize_preserves_entries_and_update_does_not_duplicate(self):
        table = LinearProbingHashTable()
        entries = [(f"entry-{index}", index) for index in range(20)]
        for key, value in entries:
            table.put(key, value)
        table.put("entry-0", 100)

        self.assertEqual(len(table), 20)
        self.assertEqual(table.get("entry-0"), 100)
        for key, value in entries[1:]:
            with self.subTest(key=key):
                self.assertEqual(table.get(key), value)


if __name__ == "__main__":
    unittest.main()
