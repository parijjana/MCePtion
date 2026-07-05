import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from example_memory_server.__main__ import MemoryRecord, append_record, read_records


class StorageTests(unittest.TestCase):
    def test_appends_and_reads_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("example_memory_server.__main__.data_dir", return_value=Path(temp_dir)):
                append_record(
                    MemoryRecord(
                        id="one",
                        text="Remember local stdio first.",
                        tags=["mcp"],
                        project="hub",
                        created_at="2026-07-04T00:00:00+00:00",
                    )
                )

                records = read_records()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].text, "Remember local stdio first.")


if __name__ == "__main__":
    unittest.main()
