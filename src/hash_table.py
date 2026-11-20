"""A string-keyed hash table using separate chaining."""

from typing import Any


class _Node:
    def __init__(self, key: str, value: Any, next_node: "_Node | None" = None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    def __init__(
        self, initial_capacity: int = 8, max_load_factor: float | None = 0.75
    ):
        if type(initial_capacity) is not int or initial_capacity < 1:
            raise ValueError("initial_capacity must be a positive integer")
        if max_load_factor is not None and max_load_factor <= 0:
            raise ValueError("max_load_factor must be positive or None")
        self.capacity = initial_capacity
        self.max_load_factor = max_load_factor
        self._buckets: list[_Node | None] = [None] * initial_capacity
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def hash_steps(
        self, key: str, capacity: int | None = None
    ) -> list[tuple[str, int, int, int]]:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        modulus = self.capacity if capacity is None else capacity
        if modulus < 1:
            raise ValueError("capacity must be positive")

        accumulator = 0
        steps = []
        for character in key:
            before = accumulator
            accumulator = (accumulator * 31 + ord(character)) % modulus
            steps.append((character, ord(character), before, accumulator))
        return steps

    def _index(self, key: str) -> int:
        steps = self.hash_steps(key)
        return steps[-1][3] if steps else 0

    def _find(self, key: str) -> tuple[int, _Node | None, _Node | None]:
        index = self._index(key)
        previous = None
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                return index, previous, node
            previous, node = node, node.next
        return index, previous, None

    def get(self, key: str) -> Any:
        _, _, node = self._find(key)
        return None if node is None else node.value

    def contains(self, key: str) -> bool:
        return self._find(key)[2] is not None

    def put(self, key: str, value: Any) -> None:
        index, _, node = self._find(key)
        if node is not None:
            node.value = value
            return

        if (
            self.max_load_factor is not None
            and (self._size + 1) / self.capacity > self.max_load_factor
        ):
            self._resize(self.capacity * 2)
            index = self._index(key)
        self._buckets[index] = _Node(key, value, self._buckets[index])
        self._size += 1

    def remove(self, key: str) -> Any:
        index, previous, node = self._find(key)
        if node is None:
            return None

        if previous is None:
            self._buckets[index] = node.next
        else:
            previous.next = node.next
        self._size -= 1
        return node.value

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self.capacity = new_capacity
        self._buckets = [None] * new_capacity
        for head in old_buckets:
            node = head
            while node is not None:
                index = self._index(node.key)
                self._buckets[index] = _Node(
                    node.key, node.value, self._buckets[index]
                )
                node = node.next

    def bucket_items(self) -> list[list[tuple[str, Any]]]:
        """Return a snapshot of buckets for the inspection page."""
        buckets = []
        for head in self._buckets:
            bucket = []
            node = head
            while node is not None:
                bucket.append((node.key, node.value))
                node = node.next
            buckets.append(bucket)
        return buckets
