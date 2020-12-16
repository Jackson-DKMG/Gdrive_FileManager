# Gdrive_FileManager
A GUI for Google Drive with basic file management capabilities.

Uses Tkinter and the Google Drive API.

The GUI display the Drive tree and the files, much like a (very basic) file explorer really. 
No data is stored locally except for a list of the files in the Drive.

The functionalities at this point are :

- *Move, copy, trash/unstrash, star/unstar files and folders. The trashed files are just moved to the trash, to delete them permanently one must use the normal web interface.
- *Download files and folders
- *Create folders
- *Upload files

The file operations are normally stored in the local file list so that they appear on the application's next start, but it's wise to refresh the data regularly, especially if other people use the Drive.
Normally, all files are picked up including those from external shared areas.

***IMPORTANT***
to make this work, API credentials are required : a client_secret.json file, to be placed in the credentials folder.
The user must allow the application to access its Drive (OAuth authentication flow), which includes a warning because it's in development and not validated by Google (and it won't ever be, probably. Currently the only drawback is that there is a 100 users limitation, which is more than there will ever be.)
