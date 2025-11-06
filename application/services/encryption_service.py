from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self,server_key: str):
        '''konstrukto do szyfrowania i deszyfrowania na serwerze''' 
        self.fernet=Fernet(server_key)
    def encryptserver(self,data:str)->bytes:
        '''czaruj enkrypcje(server side) jak panoramix kociołek'''
        return self.fernet.encrypt(data.encode())
    def decryptserver(self,data:bytes)->str:
        '''deszyfruje notki(server side) jak ja czekotubke(lubie czeko tubki)'''
        return self.fernet.decrypt(data).decode()
    
    