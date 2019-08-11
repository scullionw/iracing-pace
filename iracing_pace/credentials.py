import keyring
import getpass

class Credentials:

    def __init__(self, namespace):
        self.namespace = namespace
        self.username, self.password = self.query()

    def query(self):
        username = keyring.get_password(self.namespace, 'username')
        if username is None:
            print("Username: ", end='')
            username = input()
            password = getpass.getpass()
        else:
            password =  keyring.get_password(self.namespace, username)
            
        return username, password
    
    def get(self):
        return self.username, self.password

    def persist(self):
        keyring.set_password(self.namespace, 'username', self.username)
        keyring.set_password(self.namespace, self.username, self.password)

def reset_credentials(namespace):
    username = keyring.get_password(namespace, 'username')
    if username is not None:
        keyring.delete_password(namespace, 'username')
        try:
            keyring.delete_password(namespace, username)
        except keyring.errors.PasswordDeleteError:
            print("No password to delete")