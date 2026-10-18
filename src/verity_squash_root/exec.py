import logging
import subprocess


class ExecBinaryError(ChildProcessError):
    def __init__(self, cmd: list[str], stdout: bytes, stderr: bytes):
        self.__cmd = cmd
        self.__stderr = stderr
        super().__init__([cmd, (stdout, stderr)])

    def stderr(self):
        return self.__stderr.decode(errors="ignore")

    def __str__(self):
        return "Failed to execute '{}', error: {}".format(" ".join(self.__cmd), self.stderr())


def exec_binary(cmd: list[str], expect_returncode: int = 0) -> tuple[bytes, bytes]:
    if len(cmd) == 0:
        raise ChildProcessError("Cannot execute empty cmd")
    try:
        logging.debug(f"Execute {cmd}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise ChildProcessError(f"Binary not found: {cmd[0]}, is it installed?") from None
    result = proc.communicate()
    if proc.returncode != expect_returncode:
        raise ExecBinaryError(cmd, result[0], result[1])
    return result
