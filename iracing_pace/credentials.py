import keyring
import getpass
import keyring.backends.Windows

keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())

def query(namespace):
    print("Username: ", end='')
    username = input()
    password = getpass.getpass()
    return username, password

def retrieve(namespace):
    username = keyring.get_password(namespace, 'username')
    if username is not None:
        password = keyring.get_password(namespace, username)
        return username, password
    return None

def persist(namespace, username, password):
    keyring.set_password(namespace, 'username', username)
    keyring.set_password(namespace, username, password)

def reset(namespace):
    username = keyring.get_password(namespace, 'username')
    if username is not None:
        keyring.delete_password(namespace, 'username')
        try:
            keyring.delete_password(namespace, username)
        except keyring.errors.PasswordDeleteError:
            print("No password to delete")