"""
backend/dsa/sorting.py
Custom Sorting Algorithms (Merge Sort & Quick Sort) with performance metrics.

Time Complexity:
- Merge Sort: O(N log N) Best, Average, Worst (Stable)
- Quick Sort: O(N log N) Best/Average, O(N^2) Worst (with 3-way/random pivot)
Space Complexity:
- Merge Sort: O(N) auxiliary space
- Quick Sort: O(log N) recursion stack space
"""

from typing import List, Dict, Any, Callable, Tuple
import time


def get_field_accessor(field: str) -> Callable[[Any], Any]:
    """Returns accessor function for sorting by specific file/transfer property."""
    field_lower = field.lower()

    def accessor(item: Any) -> Any:
        if isinstance(item, dict):
            val = item.get(field_lower)
            if val is None:
                # Alternate mappings
                if field_lower in ("name", "file_name"):
                    val = item.get("file_name") or item.get("name") or ""
                elif field_lower in ("size", "file_size"):
                    val = item.get("size") or 0
                elif field_lower in ("date", "modified", "modified_time"):
                    val = item.get("modified_time") or 0.0
                elif field_lower in ("type", "file_type", "extension"):
                    val = item.get("file_type") or item.get("extension") or ""
                elif field_lower in ("speed", "transfer_speed"):
                    val = item.get("speed") or 0.0
                else:
                    val = ""
            if isinstance(val, str):
                return val.lower()
            return val or 0

        # Object attribute lookup
        val = getattr(item, field_lower, None)
        if isinstance(val, str):
            return val.lower()
        return val or 0

    return accessor


class Sorter:
    """
    Sorting engine providing Merge Sort and Quick Sort with benchmark metrics.
    """

    @staticmethod
    def merge_sort(
        items: List[Any],
        key_fn: Optional[Callable[[Any], Any]] = None,
        reverse: bool = False
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Pure divide-and-conquer Merge Sort implementation.
        Stable sorting algorithm with O(N log N) guaranteed performance.
        """
        key = key_fn or (lambda x: x)
        comparisons = 0
        start_time = time.perf_counter()

        def _merge(left: List[Any], right: List[Any]) -> List[Any]:
            nonlocal comparisons
            merged = []
            i = j = 0
            while i < len(left) and j < len(right):
                comparisons += 1
                val_l = key(left[i])
                val_r = key(right[j])

                if (val_l <= val_r) if not reverse else (val_l >= val_r):
                    merged.append(left[i])
                    i += 1
                else:
                    merged.append(right[j])
                    j += 1

            merged.extend(left[i:])
            merged.extend(right[j:])
            return merged

        def _sort(arr: List[Any]) -> List[Any]:
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left_half = _sort(arr[:mid])
            right_half = _sort(arr[mid:])
            return _merge(left_half, right_half)

        sorted_list = _sort(list(items))
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        metrics = {
            "algorithm": "Merge Sort",
            "comparisons": comparisons,
            "elapsed_ms": round(elapsed_ms, 3),
            "time_complexity": "O(N log N)",
            "space_complexity": "O(N)",
            "stable": True
        }
        return sorted_list, metrics

    @staticmethod
    def quick_sort(
        items: List[Any],
        key_fn: Optional[Callable[[Any], Any]] = None,
        reverse: bool = False
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        In-place Hoare/Lomuto partitioning Quick Sort implementation.
        """
        arr = list(items)
        key = key_fn or (lambda x: x)
        comparisons = 0
        start_time = time.perf_counter()

        def _qsort(low: int, high: int) -> None:
            nonlocal comparisons
            if low < high:
                # Choose median-of-three or middle element as pivot
                mid = (low + high) // 2
                pivot_val = key(arr[mid])

                i = low
                j = high
                while i <= j:
                    if not reverse:
                        while i <= high and key(arr[i]) < pivot_val:
                            comparisons += 1
                            i += 1
                        while j >= low and key(arr[j]) > pivot_val:
                            comparisons += 1
                            j -= 1
                    else:
                        while i <= high and key(arr[i]) > pivot_val:
                            comparisons += 1
                            i += 1
                        while j >= low and key(arr[j]) < pivot_val:
                            comparisons += 1
                            j -= 1

                    if i <= j:
                        arr[i], arr[j] = arr[j], arr[i]
                        i += 1
                        j -= 1

                if low < j:
                    _qsort(low, j)
                if i < high:
                    _qsort(i, high)

        if arr:
            _qsort(0, len(arr) - 1)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        metrics = {
            "algorithm": "Quick Sort",
            "comparisons": comparisons,
            "elapsed_ms": round(elapsed_ms, 3),
            "time_complexity": "O(N log N) avg, O(N^2) worst",
            "space_complexity": "O(log N)",
            "stable": False
        }
        return arr, metrics

    @classmethod
    def sort(
        cls,
        items: List[Any],
        by: str = "name",
        algorithm: str = "merge_sort",
        reverse: bool = False
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Unified sorting interface.
        Supports by="name" | "size" | "modified" | "type" | "speed".
        """
        key_func = get_field_accessor(by)
        if algorithm.lower() in ("quicksort", "quick_sort", "quick"):
            return cls.quick_sort(items, key_fn=key_func, reverse=reverse)
        return cls.merge_sort(items, key_fn=key_func, reverse=reverse)
