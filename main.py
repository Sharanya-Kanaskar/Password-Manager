import json
import os
import sys
from getpass import getpass

try:
    from encrypt import (
        CryptoError,
        DecryptionError,
        decrypt,
        derive_key,
        encrypt,
        new_salt,
    )
except ImportError as e:
    sys.exit(
        f"Missing dependency: {e}\n"
        "Install it with:  pip install pycryptodome"
    )

from save import Saver, StorageError

# Stored next to this script, so the vault is found no matter which folder
# you launch the program from.
VAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.json")
MAX_ATTEMPTS = 3


class Vault:
    """Holds the decrypted entries in memory and knows how to save them."""

    def __init__(self, saver):
        self.saver = saver
        self.salt = None
        self.key = None
        self.entries = {}  # {application name: password}

    def _write(self, entries):
        """Encrypt and save `entries`. Doesn't touch self.entries."""
        try:
            plaintext = json.dumps(entries).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise StorageError(f"Could not prepare vault data for saving: {e}") from e
        self.saver.write(self.salt, encrypt(self.key, plaintext))

    def create(self, master_password):
        """Set up a brand-new empty vault. Errors propagate to the caller."""
        self.salt = new_salt()
        self.key = derive_key(master_password, self.salt)
        self._write({})
        self.entries = {}

    def unlock(self, master_password):
        """Returns True on success, False if the password is wrong.

        Raises StorageError / CryptoError for problems that retrying with a
        different password can't fix (unreadable or invalid vault file).
        """
        salt, blob = self.saver.read()
        key = derive_key(master_password, salt)
        try:
            data = decrypt(key, blob)
        except DecryptionError:
            return False

        try:
            entries = json.loads(data.decode("utf-8"))
        except ValueError as e:  # bad JSON or bad text encoding
            raise StorageError("Vault decrypted, but its contents are invalid.") from e
        if not isinstance(entries, dict):
            raise StorageError("Vault decrypted, but its contents are invalid.")

        self.salt, self.key, self.entries = salt, key, entries
        return True

    # Add/remove save to disk FIRST and only update the in-memory copy once
    # that worked, so a failed save never leaves memory and disk out of sync.
    def set_entry(self, app, password):
        new_entries = {**self.entries, app: password}
        self._write(new_entries)
        self.entries = new_entries

    def remove_entry(self, app):
        new_entries = {a: p for a, p in self.entries.items() if a != app}
        self._write(new_entries)
        self.entries = new_entries


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def login(vault):
    """Create a new vault on first run, otherwise ask for the password."""
    if not vault.saver.exists():
        print("No vault found - let's create one.")
        while True:
            password = getpass("Choose a master password: ")
            if not password:
                print("Master password can't be empty.")
                continue
            if getpass("Repeat it: ") != password:
                print("Passwords didn't match. Try again.")
                continue
            print("Creating vault...")
            vault.create(password)
            return True

    for attempt in range(1, MAX_ATTEMPTS + 1):
        password = getpass("Master password: ")
        if password and vault.unlock(password):
            return True
        print(f"Incorrect password ({attempt}/{MAX_ATTEMPTS}).")
    return False


def find_password(vault):
    query = input("Application name: ").strip().lower()
    matches = {a: p for a, p in vault.entries.items() if query in a.lower()}
    if not matches:
        print("Nothing found.")
        return
    for app, password in matches.items():
        print("\n" + "-" * 40)
        print(f"Application: {app}")
        print(f"Password:    {password}")


def add_password(vault):
    app = input("Application name: ").strip()
    if not app:
        print("Name can't be empty.")
        return
    if app in vault.entries:
        if input(f"'{app}' already exists. Overwrite? [y/n]: ").strip().lower() != "y":
            print("Cancelled.")
            return
    password = getpass("Password (hidden): ")
    if not password:
        print("Password can't be empty.")
        return
    vault.set_entry(app, password)
    print("Saved.")


def delete_password(vault):
    app = input("Application name: ").strip()
    if app not in vault.entries:
        print(f"'{app}' not found.")
        return
    if input(f"Are you sure you want to delete '{app}'? [y/n]: ").strip().lower() == "y":
        vault.remove_entry(app)
        print("Deleted.")
    else:
        print("Cancelled.")


ACTIONS = {
    "1": find_password,
    "2": add_password,
    "3": delete_password,
}


def main():
    vault = Vault(Saver(VAULT_FILE))
    if not login(vault):
        print("Too many failed attempts.")
        return 1

    while True:
        clear_screen()
        print("1. Find Password")
        print("2. Add Password")
        print("3. Delete Password")
        print("4. Quit")

        choice = input("\nChoice: ").strip()
        if choice == "4":
            return 0

        action = ACTIONS.get(choice)
        if action is None:
            print("Please enter a number from 1-4.")
        else:
            try:
                action(vault)
            except (StorageError, CryptoError) as e:
                # A failed save shouldn't kill the session - the vault in
                # memory is unchanged, so the user can just try again.
                print(f"\nError: {e}")
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):  # Ctrl+C / Ctrl+D / closed input
        print("\nGoodbye.")
        sys.exit(0)
    except (StorageError, CryptoError) as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
