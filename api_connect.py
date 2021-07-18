#Class to handle the Oauth flow and connect to the Google Drive API.

from os import path, remove
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools

class apiConnect():
    def __init__(self):
        super().__init__()
        #self.connect()

    def connect(self):#, setup=False):
        # define path variables
        credentials_file_path = './credentials/credentials.json'

        # define store
        store = file.Storage(credentials_file_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            return None
        else:
            http = credentials.authorize(Http())
            drive = discovery.build('drive', 'v3', http=http)
            return drive

    def config(self):

        credentials_file_path = './credentials/credentials.json'
        clientsecret_file_path = './credentials/client_secret.json'

        # define scope
        SCOPE = 'https://www.googleapis.com/auth/drive'

        if path.isfile('./credentials/credentials.json'):
            remove('./credentials/credentials.json')   #if the file exist, might be corrupted and not working, or someone just wants to switch accounts. Delete it.

        # define store
        store = file.Storage(credentials_file_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(clientsecret_file_path, SCOPE)
            credentials = tools.run_flow(flow, store)
        # define API service
        http = credentials.authorize(Http())
        drive = discovery.build('drive', 'v3', http=http)

        return drive