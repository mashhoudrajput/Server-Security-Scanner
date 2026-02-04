"""SSH executor for running commands on remote servers."""

import io
from typing import Optional

import paramiko


class SSHExecutor:
    """Execute commands on remote servers via SSH."""

    def __init__(
        self,
        host: str,
        user: str,
        key_data: bytes,
        port: int = 22,
        timeout: int = 30,
    ):
        self.host = host
        self.user = user
        self.key_data = key_data
        self.port = port
        self.timeout = timeout
        self._client: Optional[paramiko.SSHClient] = None

    def _load_pkey(self):
        """Load private key, trying RSA, Ed25519, ECDSA."""
        # Paramiko expects text (PEM is ASCII), not bytes
        key_str = self.key_data.decode("utf-8") if isinstance(self.key_data, bytes) else self.key_data
        key_file = io.StringIO(key_str)
        for key_class in (
            paramiko.RSAKey,
            paramiko.Ed25519Key,
            paramiko.ECDSAKey,
        ):
            try:
                key_file.seek(0)
                return key_class.from_private_key(key_file)
            except (paramiko.ssh_exception.SSHException, ValueError):
                continue
        raise ValueError("Could not load key: not RSA, Ed25519, or ECDSA")

    def connect(self) -> tuple[bool, str | None]:
        """Establish SSH connection. Returns (success, error_message)."""
        last_error = None
        try:
            pkey = self._load_pkey()
        except Exception as e:
            return False, f"Invalid key format: {e}"

        for _ in range(1):
            try:
                self._client = paramiko.SSHClient()
                self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._client.connect(
                    hostname=self.host,
                    username=self.user,
                    pkey=pkey,
                    port=self.port,
                    timeout=self.timeout,
                    allow_agent=False,
                    look_for_keys=False,
                )
                return True, None
            except Exception as e:
                last_error = str(e)
                break

        return False, last_error or "Connection failed"

    def run(self, command: str, timeout: int = 60) -> dict:
        """
        Run command on remote server.
        Returns dict with: success, stdout, stderr, exit_code, error
        """
        if self._client is None:
            ok, err = self.connect()
            if not ok:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "",
                    "exit_code": -1,
                    "error": err or "Failed to connect",
                }

        try:
            stdin, stdout, stderr = self._client.exec_command(
                command, timeout=timeout
            )
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            return {
                "success": exit_code == 0,
                "stdout": out,
                "stderr": err,
                "exit_code": exit_code,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "error": str(e),
            }

    def close(self):
        """Close SSH connection."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
