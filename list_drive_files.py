from json import dumps

import settings
from api_connect import apiConnect

class listDriveFiles():

    def __init__(self):
        super().__init__()
        settings.drive = apiConnect().connect()  # connect to the api and get the drive variable
        self.retrieveFiles()

    def retrieveFiles(self):
        api_service = settings.drive
        page_token = None

        while True:
            settings.retrievingFiles = True
            try:
                param = {}
                param['orderBy'] = "name"
                param['pageSize'] = 1000
                param['includeItemsFromAllDrives'] = True
                param['supportsAllDrives'] = True
                param['corpora'] = "allDrives"
                param[
                    'fields'] = "nextPageToken, files(name, id, parents, trashed, size, mimeType, modifiedTime, starred, ownedByMe, shared, owners/displayName, shortcutDetails/targetId,shortcutDetails/targetMimeType)"  # '*'
                # files(name, id, parents, trashed, size, mimeType, modifiedTime,starred,owners/displayName, shortcutDetails(targetId,targetMimeType)
                if page_token:
                    param['pageToken'] = page_token

                files = api_service.files().list(**param).execute()
                # append the files from the current result page to our list
                settings.retrievedFiles.extend(files.get('files'))
                page_token = files.get('nextPageToken')

                if not page_token:
                    break

            except Exception as error:

                print(f'An error has occurred: {error}')
                break

        with open('files', 'w') as f:  # dump the json data to a file
            f.write(dumps(settings.retrievedFiles, sort_keys=True, indent=4, separators=(',', ': ')))

        settings.retrievingFiles = False
        settings.retrievedFiles = []