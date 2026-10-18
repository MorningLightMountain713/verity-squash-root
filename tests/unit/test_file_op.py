import unittest
from tests.unit.helpers import get_test_files_path, wrap_tempdir
from verity_squash_root.file_op import read_text_from, write_str_to, \
    read_from

TEST_FILES_DIR = get_test_files_path("file_op")
READ_TXT = TEST_FILES_DIR / "read.txt"
READ_TXT_CONTENT = "This is a test str.\n"


class FileOPTest(unittest.TestCase):

    def test__read_from(self):
        result = read_from(READ_TXT)
        self.assertEqual(result, bytes(READ_TXT_CONTENT, "utf-8"))

    def test__read_text_from(self):
        result = read_text_from(READ_TXT)
        self.assertEqual(result, READ_TXT_CONTENT)

    @wrap_tempdir
    def test__write_str_to(self, tempdir):
        path = tempdir / "testfile"
        text = "Some test string\nnext line"
        write_str_to(path, text)
        self.assertEqual(read_text_from(path), text)
