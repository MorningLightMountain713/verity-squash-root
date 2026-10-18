import unittest

import pytest

from verity_squash_root.exec import ExecBinaryError, exec_binary


class ExecTest(unittest.TestCase):
    def test__exec_binary__exit_code(self):
        exit_3_cmd = ["dash", "-c", "echo err str >&2 ; exit 3"]
        assert exec_binary(exit_3_cmd, 3) == (b"", b"err str\n")
        with pytest.raises(ExecBinaryError) as e_ctx:
            exec_binary(exit_3_cmd)
        exception = ([exit_3_cmd, (b"", b"err str\n")],)
        assert e_ctx.value.args == exception

        with pytest.raises(ExecBinaryError) as e_ctx:
            exec_binary(exit_3_cmd, 1)
        assert e_ctx.value.args == exception
        assert (
            str(e_ctx.value)
            == "Failed to execute 'dash -c echo err str >&2 ; exit 3', error: err str\n"
        )
        assert e_ctx.value.stderr() == "err str\n"

    def test__exec_binary__result(self):
        result = exec_binary(
            ["dash", "-c", "printf StdOutStr\\\\n123;printf StdErrStr\\\\n456 >&2"]
        )
        assert result == (b"StdOutStr\n123", b"StdErrStr\n456")

    def test__exec_binary__empty(self):
        with pytest.raises(ChildProcessError) as e_ctx:
            exec_binary([])
        assert e_ctx.value.args == ("Cannot execute empty cmd",)

    def test__exec_binary__not_found(self):
        with pytest.raises(ChildProcessError) as e_ctx:
            exec_binary(["notexistingbin", "-c", "param"])
        assert e_ctx.value.args == ("Binary not found: notexistingbin, is it installed?",)
