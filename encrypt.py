#%%
import cryptography.fernet
import hashlib, getpass

class Encryption:
  def __init__(self, passhash):
    def encrypt(data:bytes): return cryptography.fernet.Fernet(passhash).encrypt(data)
    def decrypt(data:bytes): return cryptography.fernet.Fernet(passhash).decrypt(data)
    self.encrypt = encrypt
    self.decrypt = decrypt

encrypt = Encryption(hashlib.sha256((getpass.getpass("Enter password: ")+'hielp_salt').encode()).hexdigest()[:43]+'=')
