from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self,server_key: bytes):
        '''konstrukto do szyfrowania i deszyfrowania na serwerze''' 
        self.server_fernet = Fernet(server_key)
    def encryptserver(self,data:str)->bytes:
        '''czaruj enkrypcje(server side) jak panoramix kociołek'''
        return self.server_fernet.encrypt(data.encode())
    def decryptserver(self,data:bytes)->str:
        '''deszyfruje notki(server side) jak ja czekotubke(lubie czeko tubki)'''
        return self.server_fernet.decrypt(data).decode()
    
    