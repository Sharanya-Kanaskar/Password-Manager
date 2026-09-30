import base64
import json
import os


class StorageError(Exception):
    """The vault file could not be read or written."""


class Saver:
    """Stores the salt and the encrypted vault blob in one JSON file."""

    def __init__(self, path):
        self.path = path

    def exists(self):
        return os.path.isfile(self.path)

    def read(self):
        """Returns (salt, encrypted_blob) as bytes."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            salt = base64.b64decode(data["salt"], validate=True)
            blob = base64.b64decode(data["data"], validate=True)
        except FileNotFoundError:
            raise StorageError(f"Vault file not found: {self.path}") from None
        except PermissionError:
            raise StorageError(f"No permission to read {self.path}.") from None
        except OSError as e:
            raise StorageError(f"Could not read {self.path}: {e}") from e
        except (ValueError, KeyError, TypeError) as e:
            # ValueError covers bad JSON, bad base64 and bad text encoding;
            # KeyError/TypeError cover a missing field or wrong structure.
            raise StorageError(
                f"{self.path} is not a valid vault file (damaged or wrong format)."
            ) from e
        return salt, blob

    def write(self, salt, blob):
        data = {
            "salt": base64.b64encode(salt).decode("ascii"),
            "data": base64.b64encode(blob).decode("ascii"),
        }
        # Write to a temp file first, then swap it in. If anything fails
        # halfway, the existing vault is left untouched.
        tmp_path = self.path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            try:
                os.chmod(tmp_path, 0o600)  # owner-only (limited effect on Windows)
            except OSError:
                pass
            os.replace(tmp_path, self.path)
        except PermissionError:
            raise StorageError(f"No permission to write to {self.path}.") from None
        except OSError as e:  # disk full, folder missing, read-only drive...
            raise StorageError(f"Could not save the vault: {e}") from e
        finally:
            # After a successful os.replace the temp file is gone, so this
            # only cleans up after a failure.
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
