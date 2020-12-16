# Gdrive_FileManager
A GUI for Google Drive with basic file management capabilities.

Uses Python3/Tkinter and the Google Drive API.

The GUI display the Drive tree and the files, much like a (very basic) file explorer really. 
No data is stored locally except for a list of the files in the Drive.

The functionalities at this point are :

- Move, copy, trash/unstrash, star/unstar files and folders. The trashed files are just moved to the trash, to delete them permanently one must use the normal web interface.
- Search
- Download files and folders
- Create folders
- Upload files

The file operations are normally stored in the local file list so that they appear on the application's next start, but it's wise to refresh the data regularly, especially if other people use the Drive.
Normally, all files are picked up including those from external shared areas.

***IMPORTANT***
To make this work, API credentials are required : a client_secret.json file, to be placed in the 'credentials' folder.
The user must allow the application to access its Drive (OAuth authentication flow), which includes a warning because it's in development and not validated by Google (and it won't ever be, probably. Currently the only drawback is that there is a 100 users limitation, which is more than there will ever be.)

On start, required modules will be imported and the missing ones will be installed, which may take some time without any information being displayed.
If there is an error at this point, the application will exit.

On Windows, application should be executed with python.exe and not pythonw.exe, otherwise a console opens as well as the GUI.

The memory footprint is quite large as all the Drive elements and Tkinter treeviews are stored in lists and dictionaries ; this cannot really be avoided.

Google Drive allows files to have multiple "parents", i.e. be in multiple folders : this is NOT implemented and only the first parent will be picked up. 
