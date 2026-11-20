"""A string-keyed hash table using linear probing."""

from typing import Any

from src.hash_table import _HornerHash


class _Entry:
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value


class _Deleted:
    pass


_DELETED = _Deleted()


class LinearProbingHashTable(_HornerHash):
    strategy = "linear probing"

    def __init__(
        self, initial_capacity: int = 8, max_load_factor: float | None = 0.75
    ):
        if type(initial_capacity) is not int or initial_capacity < 1:
            raise ValueError("initial_capacity must be a positive integer")
        if max_load_factor is not None and max_load_factor <= 0:
            raise ValueError("max_load_factor must be positive or None")
        self.capacity = initial_capacity
        self.max_load_factor = max_load_factor
        self._slots: list[_Entry | _Deleted | None] = [None] * initial_capacity
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def _find_slot(
        self, key: str
    ) -> tuple[int | None, int | None, list[int]]:
        start = self._index(key)
        first_deleted = None
        trace = []
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            trace.append(index)
            entry = self._slots[index]
            if entry is None:
                return None, first_deleted if first_deleted is not None else index, trace
            if isinstance(entry, _Deleted):
                if first_deleted is None:
                    first_deleted = index
            elif entry.key == key:
                return index, index, trace
        return None, first_deleted, trace

    def get(self, key: str) -> Any:
        found_index, _, _ = self._find_slot(key)
        if found_index is None:
            return None
        entry = self._slots[found_index]
        return entry.value if isinstance(entry, _Entry) else None

    def contains(self, key: str) -> bool:
        return self._find_slot(key)[0] is not None

    def put(self, key: str, value: Any) -> None:
        found_index, insert_index, _ = self._find_slot(key)
        if found_index is not None:
            entry = self._slots[found_index]
            if isinstance(entry, _Entry):
                entry.value = value
            return

        over_limit = (
            self.max_load_factor is not None
            and (self._size + 1) / self.capacity > self.max_load_factor
        )
        if insert_index is None or over_limit:
            if self.max_load_factor is None:
                raise OverflowError("hash table is full")
            self._resize(self.capacity * 2)
            _, insert_index, _ = self._find_slot(key)

        if insert_index is None:
            raise OverflowError("hash table is full")
        self._slots[insert_index] = _Entry(key, value)
        self._size += 1

    def remove(self, key: str) -> Any:
        found_index, _, _ = self._find_slot(key)
        if found_index is None:
            return None
        entry = self._slots[found_index]
        if not isinstance(entry, _Entry):
            return None
        self._slots[found_index] = _DELETED
        self._size -= 1
        return entry.value

    def _resize(self, new_capacity: int) -> None:
        old_slots = self._slots
        self.capacity = new_capacity
        self._slots = [None] * new_capacity
        for entry in old_slots:
            if not isinstance(entry, _Entry):
                continue
            index = self._index(entry.key)
            while self._slots[index] is not None:
                index = (index + 1) % self.capacity
            self._slots[index] = entry

    def bucket_items(self) -> list[list[tuple[str, Any]]]:
        """Return each occupied slot as a one-entry bucket snapshot."""
        buckets = []
        for entry in self._slots:
            if isinstance(entry, _Entry):
                buckets.append([(entry.key, entry.value)])
            else:
                buckets.append([])
        return buckets

    def probe_trace(self, key: str) -> list[int]:
        """Return every slot inspected while searching for key."""
        return self._find_slot(key)[2]
