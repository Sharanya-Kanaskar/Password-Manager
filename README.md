# Password-Manager
Terminal Password Manager
This is a lightweight password manager designed for use within a terminal environment. Users are required to remember only a single master password, which secures access to all other stored credentials.
Initially developed as an introductory Python project, the codebase remains concise and accessible. The application employs established encryption standards; however, it has not undergone professional security auditing. It is suitable for educational purposes and accounts with minimal security requirements. For critical accounts, it is advisable to use a professionally maintained password manager such as Bitwarden or KeePass.

What is this?
Most of us have dozens of accounts, and nobody can remember a different strong password for every one of them. A password manager fixes that by keeping everything in one place, locked behind a single master password.
This is a tiny version of that idea:
The first time you run it, you pick a master password.
Your saved logins go into one encrypted file called vault.json.
Without the master password, that file is unreadable.
You use it through a simple text menu: find, add or delete a password.
Everything happens on your own computer. There’s no account to create and nothing gets sent over the internet.

What it can do
Lock everything behind one password. Type your master password once and you’re in.
Encrypt properly. Your vault is encrypted with AES-256-GCM, which also notices if the file has been tampered with.
Make guessing expensive. Your master password is stretched with scrypt, a deliberately slow method that makes brute-force guessing much harder.
Hide more than just the passwords. The whole vault is encrypted as one piece, so the names of your apps and the number of entries stay private too.
Find things easily. Search by part of a name, in any capitalisation. Typing git will find GitHub.
Keep typing private. Passwords you type are hidden on screen, and the program asks before it overwrites or deletes anything.
Set itself up. On the first run it walks you through creating your vault.
Save safely. Changes are written to a temporary file first and then swapped in, so a crash halfway through saving can’t wreck your existing data.
Fail politely. A damaged vault file, a full disk or a missing package gives you a readable message instead of a wall of red text.
Limit access to the file. On Linux and macOS the vault is set so only you can read it.
Run anywhere. Windows, macOS and Linux all work.

What it’s built with
Python 3.8 or newer
PyCryptodome for the AES-256-GCM encryption. This is the only thing you need to install.
Python’s built-in tools for everything else: hashlib (scrypt key derivation), getpass (hidden typing), json and base64 (storing the vault), and os and sys (files, clearing the screen, exit codes).
What’s in the folder
The code is split into three small files, each with one job:
main.py is the part you actually interact with: the login, the menu and the vault itself.
encrypt.py does all the cryptography and knows nothing about files or menus.
save.py handles reading and writing the vault file and knows nothing about encryption.
Alongside them, requirements.txt lists the one package you need, and vault.json appears the first time you run the program. That’s your encrypted data.

What you’ll need
Python 3.8 or newer. To check, open a terminal and run one of these:

   python --version
   python3 --version      # macOS / Linux
   py --version           # Windows

If you don’t have Python, grab it from python.org.
pip, Python’s package installer. It comes with Python on Windows and macOS. On Debian or Ubuntu you may need to install it yourself:

   sudo apt install python3-pip python3-venv

A real terminal. Command Prompt, PowerShell, Terminal, iTerm or GNOME Terminal are all fine. Some editor consoles (IDLE, or PyCharm’s default Run window) can’t hide what you type, so your password would show on screen. If you use PyCharm, turn on “Emulate terminal in output console” in the run configuration.
A folder you can write to. The program creates vault.json right next to main.py.

Getting it set up
Put the files together. Save main.py, encrypt.py, save.py and requirements.txt in one folder, for example password-manager.
Open a terminal in that folder.

   cd path/to/password-manager

Create a virtual environment (recommended). This keeps the project’s package separate from the rest of your system:

   python -m venv venv

Then switch it on:

    venv\Scripts\activate           # Windows
    source venv/bin/activate        # macOS / Linux
  
  When it’s active, you’ll see (venv) at the start of your prompt.
Install the dependency.

   pip install -r requirements.txt

That installs pycryptodome.

Heads up: make sure it’s pycryptodome, not pycrypto or crypto. They share the same import name (Crypto) and will clash. If you have either of those installed, remove it first:

pip uninstall pycrypto crypto

---

Running it
From the project folder:

python main.py

If python isn’t recognised, try python3 main.py on macOS/Linux or py main.py on Windows.
You can launch it from any folder you like, because the vault is always stored next to main.py.

Using it
The first time: creating your vault
If there’s no vault.json yet, the program sets one up with you:

No vault found - let's create one.
Choose a master password:
Repeat it:
Creating vault...

Nothing appears on screen while you type, which is normal. Pick something long that you’ll remember, like a phrase made of several words.

Please don’t forget it. There is no password recovery. If the master password is lost, the vault can’t be opened by anyone, including you. That’s how the encryption is supposed to work.
After that: logging in

Master password:

You get 3 tries, and then the program exits.
The menu

1. Find Password
2. Add Password
3. Delete Password
4. Quit

Choice:

Type a number and press Enter.

1. Find Password. Type all or part of an app’s name. Case doesn’t matter, and every match is shown:

Application name: git

----------------------------------------
Application: GitHub
Password:    my-secret-password

Passwords appear on screen as plain text, so check that nobody is looking over your shoulder. The screen clears when you return to the menu.
2. Add Password. Type the app’s name, then the password, which stays hidden as you type. If that name already exists, the program asks before replacing it. Names are matched exactly, so GitHub and github end up as two separate entries.
3. Delete Password. Type the exact name, with the same capitalisation you used when you added it, then confirm with y.
4. Quit. Exits the program. Every change is saved the moment you make it, so there’s no separate “save” step. You can also leave at any time with Ctrl+C.
Back it up
Your whole vault is that one file, vault.json. Copy it somewhere safe now and then. A backup is no use without the master password, and the master password is no use without the file, so look after both.

A peek under the hood
Here’s what happens behind the scenes, in case you’re curious.
When you create a vault:
A random 16-byte salt is generated.
Your master password and the salt go through scrypt, which produces a 32-byte encryption key. Scrypt is slow and memory-hungry on purpose, so trying millions of guesses becomes expensive for an attacker.
Your entries (a simple list of app name and password pairs) are turned into JSON and encrypted with AES-256-GCM, using a fresh random nonce every time.
When you unlock it:
The program reads the salt from vault.json and rebuilds the key from the password you typed.
It tries to decrypt. GCM includes an authentication tag, so a wrong password or a modified file makes decryption fail instead of producing nonsense. That failure is how the program knows the password was wrong. No password or hash is stored anywhere to compare against.
What’s in vault.json: just two base64-encoded fields.

{
    "salt": "...",
    "data": "..."
}

The data field holds the nonce, the authentication tag and the encrypted contents, joined together. The salt isn’t a secret. Its job is to make sure the same password gives a different key in every vault.
How saving works: the program writes to vault.json.tmp first, then swaps it in for vault.json in one step. If saving fails, what’s in memory stays as it was, so what you see always matches what’s on disk.

Things it can’t do (yet)
It’s better to be upfront about the gaps:
Passwords sit in memory while it runs. Python can’t reliably wipe them afterwards.
Found passwords show up as plain text. There’s no clipboard support and no timer to clear the screen.
It can’t protect you from malware. A keylogger or screen recorder on your computer can still see everything you do.
The 3-try limit only applies while the program is running. If someone copies vault.json, they can guess offline. Scrypt slows them down, but a weak master password can still fall, so make yours a long one.
You can’t change your master password, or export and import your vault.
There’s no password generator.
No professional has audited it.
On Windows, the owner-only file permission doesn’t do much.

When something goes wrong
Missing dependency: No module named 'Crypto': PyCryptodome isn’t installed for the Python you’re using. Run pip install pycryptodome, and if you’re using a virtual environment, make sure it’s switched on.
An ImportError about Crypto even after installing: the old pycrypto package is probably in the way. Run pip uninstall pycrypto crypto, then pip install --force-reinstall pycryptodome.
This Python build doesn't support scrypt: your Python was built without scrypt, which happens with some macOS system Pythons. Installing Python from python.org or Homebrew fixes it.
... is not a valid vault file (damaged or wrong format): vault.json has been edited, cut short or corrupted. Restore it from a backup.
Incorrect password when you’re sure it’s right: check Caps Lock and your keyboard layout. A file damaged in transit can give the same message, so try a backup copy too.
No permission to read/write ...: the folder or file is read-only or belongs to another user. Move the project to a folder you own, or fix the permissions.
Could not save the vault: ...: usually a full disk, an unplugged drive or a read-only folder. Your existing vault is untouched, so fix the cause and try again.
You can see your password as you type: you’re probably in an editor console that can’t hide input. Use a real terminal instead (see “What you’ll need” above).
You forgot your master password: sadly it can’t be recovered. You can delete vault.json to start over with a fresh, empty vault, but that permanently throws away the old data.

Where it could go next
A password generator (Python’s secrets module would do the job)
Changing the master password (re-encrypting with a new salt)
Copy to clipboard, with a timer that clears it
Auto-lock after a period of inactivity
Export, import and automatic backups
Extra fields such as usernames, URLs and notes
Unit tests for the encryption and storage code
A graphical interface
