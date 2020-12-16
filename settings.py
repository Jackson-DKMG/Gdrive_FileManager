from os import path, remove, getcwd, name, popen
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools

downloadIsRunning = False
retrievingFiles = False
retrievedFiles = []
loadingData = False
treeview = None
contentview = None
files = []
folders = []
directory = {}

folderIcon = None
imageIcon = None
videoIcon = None
pdfIcon = None
wordIcon = None
excelIcon = None
gappsIcon = None
writerIcon = None
spreadsheetIcon = None
audioIcon = None
documentIcon = None
shortcutIcon = None
compressedIcon = None

rootID = ''
owner = ''

fileDownloading = ""
fileDownloadingSize = ""

copyInProgress = ""
itemCopying = ""
moveInProgress = ""
itemMoving = ""

error = ""
drive = None
widget = None

currentDir = getcwd()

#GET DOWNLOAD FOLDER#
#absolutely no idea of how this works for the Windows part. Copy-pasted from somewhere.
if name == 'nt':
    #import ctypes
    from ctypes import windll, wintypes, Structure, POINTER, c_wchar_p, byref, WinError
    from uuid import UUID

    # ctypes GUID copied from MSDN sample code
    class GUID(Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", wintypes.BYTE * 8)
        ]

        def __init__(self, uuidstr):
            uuid = UUID(uuidstr)
            Structure.__init__(self)
            self.Data1, self.Data2, self.Data3, \
                self.Data4[0], self.Data4[1], rest = uuid.fields
            for i in range(2, 8):
                self.Data4[i] = rest>>(8-i-1)*8 & 0xff

    SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
    SHGetKnownFolderPath.argtypes = [
        POINTER(GUID), wintypes.DWORD,
        wintypes.HANDLE, POINTER(c_wchar_p)
    ]

    def _get_known_folder_path(uuidstr):
        pathptr = c_wchar_p()
        guid = GUID(uuidstr)
        if SHGetKnownFolderPath(byref(guid), 0, 0, byref(pathptr)):
            raise WinError()
        return pathptr.value

    FOLDERID_Download = '{374DE290-123F-4565-9164-39C4925E467B}'

    def get_download_folder():
        return _get_known_folder_path(FOLDERID_Download)
else:
    def get_download_folder():
        return popen("xdg-user-dir DOWNLOAD").read().split('\n')[0]

downloadFolder = get_download_folder()

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


