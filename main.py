# start with importing all necessary  modules.
# some may not be installed (not part of default Python modules), so if any errors, install them all.
# If some are already installed, pip will just move on to the next one.

#TODO: this takes too long. Need to package with all the dependencies.

try:
    from sys import argv
    from json import load
    from os import path, remove, system
    import tkinter as tk
    from threading import Thread, active_count
    from time import sleep
    from tkinter import ttk, messagebox, filedialog
    from apiclient import discovery
    from httplib2 import Http
    from oauth2client import client, file, tools
    from unidecode import unidecode  #to ignore accents / special characters when searching
    from screeninfo import get_monitors #spawn the main window in the middle of the primary screen
    from datetime import datetime
    import turtle

except:
    try:
        system(
            "python3 -m pip install apiclient oauth2client unidecode screeninfo turtle")  #Even with Python2.7 out of the common linux distros, there is a python3 executable
        system("python3 -m pip install --upgrade google-api-python-client")               #in addition to just python. Should work in all cases?
        #this takes really too long.
        from apiclient import discovery
        from httplib2 import Http
        from oauth2client import client, file, tools
        from unidecode import unidecode  # to ignore accents / special characters when searching
        from screeninfo import get_monitors  # in case of multiple monitors.
    except Exception as e:
        print(e)
        exit(1)

search_window_is_open = None

# import all global variables from settings.py, functions from py, and classes from the other files.
import settings
from context_functions import contextFunctions
from search_window import searchWindow
from list_drive_files import listDriveFiles
from api_connect import apiConnect


class appMainWindow():
    def __init__(self):
        super().__init__()
        self.data = []  # list to store the files/folders to copy or move

        if path.isfile('./credentials/client_secret.json'):
            if path.isfile('./credentials/credentials.json'):
                try:
                    settings.drive = apiConnect().connect()  # connect to the api and get the drive variable
                except:
                    pass
            else:
                settings.error = ' No account configured. Please click on "Configuration".'
        else:
            settings.error = ' System file is missing. Please contact the developer.'
        self.runUI()

    def config(self):
        if path.isfile('./credentials/credentials.json'):
            message = tk.messagebox.askokcancel(None,
                                                'Warning: existing configuration will be deleted.\nYou will need to allow access '
                                                'to your Google account again.\nProceed?')
            if message == True:
                if path.isfile('files'):
                    remove('files')
                self.mainWindow.destroy()
                settings.drive = apiConnect().config()
                appMainWindow()
        else:
            message = tk.messagebox.askokcancel(None,
                                                'Your browser will now open and you will be asked to select a Google account'
                                                ' and allow access to Drive.\nOnce done, please click on "Update"')
            if message == True:
                if path.isfile('files'):
                    remove('files')
                self.mainWindow.destroy()
                settings.drive = apiConnect().config()
                appMainWindow()

    def exit(self):
        message = tk.messagebox.askokcancel(None, 'Exit application?')
        if message == True:
            self.mainWindow.destroy()

    def showContextMenu(self,
                        event):  # show a contextual menu. If nothing is selected already, or if another single item is selected,
        try:
            if self.contextMenu:
                self.contextMenu.destroy()
        except:
            pass

        self.contextMenu = tk.Menu(self.mainWindow, tearoff=0)
        self.contextMenu.add_command(label="Create Folder", command=lambda: self.createPopup(event))
        self.contextMenu.add_command(label="Download", command=lambda: self.downloadSelected())
        self.contextMenu.add_command(label="Copy/Move", command=lambda: self.copyMoveSelected())
        self.contextMenu.add_command(label="Rename", command=lambda: self.renamePopup(event))
        self.contextMenu.add_command(label="Remove", command=lambda: self.removeRestore(flag=True))
        self.contextMenu.add_command(label="Star/Unstar", command=lambda: self.starUnstar())

        self.contextMenu.bind("<FocusOut>", lambda event: self.contextMenu.destroy())

        try:
            if 'treeview2' in str(event.widget):
                settings.widget = settings.contentview
                self.contextMenu.delete(0)  # delete the 'create folder' option in contentview

                # automatically select the item below the mouse. Otherwise multiple items are selected, keep it that way.
                if len(settings.widget.selection()) > 1:
                    self.contextMenu.delete(2)  # rename option only present if just one item is selected
                    if settings.widget.item(settings.widget.selection()[0])['values'][-1:][0] == (
                            'True' or True):  # the value item for trashed is the last element of [values]
                        self.contextMenu.delete(1)  # delete the "copy/move" option
                        self.contextMenu.delete(1)  # delete the 'Remove' option and replace with a 'Restore' one
                        self.contextMenu.add_command(label="Restore", command=lambda: self.removeRestore(flag=False))
                    for i in settings.widget.selection():
                        print(settings.widget.item(i))
                        if not settings.widget.item(i)['values'][3] == settings.owner: #if I don't own the files or folders, can't delete/rename
                            self.contextMenu.delete(2)  # remove 'rename' option
                            self.contextMenu.delete(2)
                            break  #if just one file is not owned by me, remove the options for the whole selection.

                else:
                    item = settings.widget.identify_row(event.y)
                    settings.widget.selection_set(item)
                    if settings.widget.item(settings.widget.selection()[0])['values'][-1:][0] == (
                            'True' or True):  # the value item for trashed is the last element of [values]
                        self.contextMenu.delete(1)  # delete the "copy/move" option
                        self.contextMenu.delete(1)  # remove 'rename' option
                        self.contextMenu.delete(1)  # delete the 'Remove' option and replace with a 'Restore' one
                        self.contextMenu.add_command(label="Restore", command=lambda: self.removeRestore(flag=False))

                    if settings.treeview.selection()[0] == settings.directory['theirShares']: #I don't own these files, can't do much on them.
                        self.contextMenu.delete(2)  # remove 'rename' option
                        self.contextMenu.delete(2)  # delete the 'Remove' option

                    if not settings.widget.item(settings.widget.selection()[0])['values'][3] == settings.owner:  # if I don't own the files or folders, can't delete/rename
                        self.contextMenu.delete(2)  # remove 'rename' option
                        self.contextMenu.delete(2)

            else:  # treeview
                settings.widget = settings.treeview
                self.contextMenu.add_command(label="Upload Files", command=lambda: self.uploadPopup(event))

                item = settings.widget.identify_row(event.y)  # this treeview allows only one selected item.
                settings.widget.selection_set(item)

                # do not display the context menu if a top level folder is selected, except "create folder" and "upload files" at root
                for key in settings.directory:
                    if key in {'starred', 'trash', 'theirShares', 'myShares', 'orphans'}:
                        if settings.widget.selection()[0] == settings.directory[key]:
                            raise BaseException
                    elif key == 'root':
                        if settings.widget.selection()[0] == settings.directory[key]:
                            raise NotImplementedError

                if settings.widget.item(settings.widget.selection()[0])['values'][-1:][0] == (
                        'True' or True):  # the value item for trashed is the last element of [values]
                    self.contextMenu.delete(0)  # delete 'create folder' option
                    self.contextMenu.delete(1)  # delete the "copy/move" option
                    self.contextMenu.delete(1)  # delete the 'Rename' option
                    self.contextMenu.delete(1)  # delete the 'Upload' option
                    self.contextMenu.delete(1)  # delete the 'Remove' option and replace with a 'Restore' one
                    self.contextMenu.add_command(label="Restore", command=lambda: self.removeRestore(flag=False))

                if not settings.widget.item(settings.widget.selection()[0])['values'][3] == settings.owner:  # if I don't own the files or folders, can't delete/rename
                    self.contextMenu.delete(0) # remove 'create folder'
                    self.contextMenu.delete(2)  # remove 'rename' option
                    self.contextMenu.delete(2)

            self.contextMenu.tk_popup(event.x_root, event.y_root)

        except NotImplementedError:
            self.contextMenu2 = tk.Menu(self.mainWindow, tearoff=0)
            self.contextMenu2.add_command(label="Create Folder", command=lambda: self.createPopup(event))
            self.contextMenu2.add_command(label="Upload Files", command=lambda: self.uploadPopup(event))
            self.contextMenu2.bind("<FocusOut>", lambda event: self.contextMenu.destroy())
            self.contextMenu2.tk_popup(event.x_root, event.y_root)

        except BaseException as e:
            # print({e})
            try:
                self.contextMenu.destroy()
                self.contextMenu2.destroy()
            except:
                pass
            pass

        finally:
            try:
                self.contextMenu.grab_release()
                self.contextMenu2.grab_release()
            except:
                pass

    def uploadPopup(self, event):
        if not (
                settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
            selectFiles = filedialog.askopenfilenames(initialdir=settings.downloadFolder, title="Select files")
            self.data = []
            target = settings.widget.item(settings.widget.selection())
            for i in selectFiles:
                size = path.getsize(i)
                self.data.append((i, size))
            Thread(target=contextFunctions().upload, args=(self.data, target)).start()
        tk.messagebox.showinfo(None, "Please wait for the current operation to complete.")

    def starUnstar(self):
        if not (
                settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
            self.data = []
            items = settings.widget.selection()
            for i in items:
                self.data.append(settings.widget.item(i))
            Thread(target=contextFunctions().starUnstar, args=[self.data]).start()
        else:
            tk.messagebox.showinfo(None, "Please wait for the current operation to complete.")

    def createPopup(self, event):
        if not (
                settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
            self.popup = tk.Toplevel()
            self.popup.geometry("+%d+%d" % (event.x_root, event.y_root))
            self.popup.title("New folder name")
            entry = ttk.Entry(self.popup)
            okButton = tk.Button(self.popup, text='Ok',
                                 command=lambda: self.createFolder(settings.widget.selection()[0],
                                                                   settings.widget.item(settings.widget.selection()[0]),
                                                                   entry.get()))
            cancelButton = tk.Button(self.popup, text='Cancel', command=self.popup.destroy)
            cancelButton.pack(side=tk.RIGHT, padx=2, pady=2)
            okButton.pack(side=tk.RIGHT, padx=2, pady=2)
            entry.pack(padx=2, pady=2)
            entry.focus_set()
            self.popup.bind('<Escape>', lambda e: self.popup.destroy())
            self.popup.bind('<Return>', lambda e: self.createFolder(settings.widget.selection()[0],
                                                                    settings.widget.item(
                                                                        settings.widget.selection()[0]), entry.get()))
        else:
            tk.messagebox.showinfo(None, "Please wait for the current operation to complete.")

    def createFolder(self, treeRef, item, newName):
        self.popup.destroy()
        try:
            parentId = item['tags'][1]
        except:
            parentId = item['tags'][0]
        Thread(target=contextFunctions().createFolder, args=(newName, parentId, treeRef)).start()

    def renamePopup(self, event):
        if not (
                settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
            self.popup = tk.Toplevel()
            self.popup.geometry("+%d+%d" % (event.x_root, event.y_root))
            self.popup.title("Enter new name")
            entry = ttk.Entry(self.popup)
            okButton = tk.Button(self.popup, text='Ok', command=lambda: self.rename(settings.widget.selection()[0],
                                                                                    settings.widget.item(
                                                                                        settings.widget.selection()[0]),
                                                                                    entry.get()))
            cancelButton = tk.Button(self.popup, text='Cancel', command=self.popup.destroy)
            cancelButton.pack(side=tk.RIGHT, padx=2, pady=2)
            okButton.pack(side=tk.RIGHT, padx=2, pady=2)
            entry.pack(padx=2, pady=2)
            entry.focus_set()
            self.popup.bind('<Escape>', lambda e: self.popup.destroy())
            self.popup.bind('<Return>', lambda e: self.rename(settings.widget.selection()[0],
                                                              settings.widget.item(settings.widget.selection()[0]),
                                                              entry.get()))
        else:
            tk.messagebox.showinfo(None, "Please wait for the current operation to complete.")

    def rename(self, treeRef, item, newName):
        self.popup.destroy()
        Thread(target=contextFunctions().rename, args=(treeRef, item, newName)).start()

    def removeRestore(self, flag):
        if not (
                settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
            self.data = []
            items = settings.widget.selection()
            for i in items:
                self.data.append(settings.widget.item(i))
            Thread(target=contextFunctions().removeRestore, args=(self.data, flag)).start()
        else:
            tk.messagebox.showinfo(None, "Please wait for the current operation to complete.")

    def downloadSelected(self):
        # should be no problem downloading elements while the data is loading ?
        # if not (settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
        self.data = []
        items = settings.widget.selection()
        for i in items:
            self.data.append(settings.widget.item(i))
        Thread(target=contextFunctions().download, args=[self.data]).start()

    # else:
    #    tk.messagebox.showinfo(None, "Please wait for the current operation to complete.")

    def copyMoveSelected(self):
        if not (
                settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
            self.data = []
            items = settings.widget.selection()
            for i in items:
                self.data.append(settings.widget.item(i))
            # need to get the target folder. Open another window showing the folder tree and select there.
            # Just test the first entry, if there are multiple.
            w = self.mainWindow.winfo_width()
            h = self.mainWindow.winfo_height()
            x = self.mainWindow.winfo_x()
            y = self.mainWindow.winfo_y()  # pass main window position and dimensions to place window appropriately.
            self.spawnCopyMoveWindow(2 * w / 6, h - h / 6, x + w / 6, y + h / 12)

        else:
            tk.messagebox.showinfo(None, "Please wait for the current operation to complete.")

    def copySelected(self):
        destination = self.selectview.item(self.selectview.selection())
        self.selectWindow.destroy()
        Thread(target=contextFunctions().copy, args=(self.data, destination)).start()

    def moveSelected(self):
        destination = self.selectview.item(self.selectview.selection())
        self.selectWindow.destroy()
        Thread(target=contextFunctions().move, args=(self.data, destination)).start()

    def spawnCopyMoveWindow(self, w, h, x, y):

        self.selectWindow = tk.Toplevel()
        self.selectWindow.geometry("%dx%d+%d+%d" % (w, h, x, y))
        self.selectWindow.title("Select destination folder")

        self.selectWindow.rowconfigure(0, weight=0)
        self.selectWindow.rowconfigure(1, weight=1)
        self.selectWindow.columnconfigure(0, weight=1)

        self.selectview = ttk.Treeview(self.selectWindow, style="Treeview", selectmode='browse')
        self.selectview.columnconfigure(0, weight=1)
        self.selectview.rowconfigure(0, weight=1)
        self.selectview.heading('#0', text="Folder Structure")  # , anchor=tk.W)  # shame
        self.selectview.column('#0#', stretch=True, minwidth=400)
        self.selectview.grid(column=0, row=0, rowspan=2, sticky="nsew", padx=2)

        self.selectWindow.bind('<Escape>', lambda e: self.selectWindow.destroy())

        self.toolbar = ttk.Frame(self.selectWindow)
        self.copyButton = ttk.Button(self.toolbar, text='Copy', command=self.copySelected)
        self.moveButton = ttk.Button(self.toolbar, text='Move', command=self.moveSelected)
        self.cancelButton = ttk.Button(self.toolbar, text='Cancel', command=self.selectWindow.destroy)
        self.cancelButton.pack(side=tk.RIGHT, padx=2, pady=2)
        self.moveButton.pack(side=tk.RIGHT, padx=2, pady=2)
        self.copyButton.pack(side=tk.RIGHT, padx=2, pady=2)
        self.toolbar.grid(column=0, row=2, sticky="swe", padx=2, pady=2)

        try:
            for child in settings.treeview.get_children():  # duplicate folder tree in the new window
                # remove Starred, Orphaned and Trash from the selectview. Can't copy or move there
                if not (settings.treeview.item(child)['text'] == ' Starred' or settings.treeview.item(child)[
                    'text'] == ' Orphaned Data' or settings.treeview.item(child)['text'] == ' Trash'):
                    item = self.selectview.insert('', 'end', image=settings.treeview.item(child)['image'],
                                                  text=settings.treeview.item(child)['text'],
                                                  values=settings.treeview.item(child)['values'],
                                                  tags=settings.treeview.item(child)['tags'])
                    self.getsubchildren(item, child)
        except:
            pass

        self.selectWindow.update()

    def getsubchildren(self, item, child):

        self.selectWindow.update()
        try:
            for child in settings.treeview.get_children(child):
                i = self.selectview.insert(item, 'end', image=settings.folderIcon,
                                           text=settings.treeview.item(child)['text'],
                                           values=settings.treeview.item(child)['values'],
                                           tags=settings.treeview.item(child)['tags'])
                if settings.treeview.get_children(child):
                    self.getsubchildren(i, child)
        except Exception as e:
            # print({e})
            pass

    def forest(self):

        import forest
        Thread(target=forest.forest).run()
        # del forest

    def runUI(self):

        ###SETUP GUI###
        self.mainWindow = tk.Tk()
        w = get_monitors()[0].width
        h = get_monitors()[0].height
        # w = self.mainWindow.winfo_screenwidth()
        # h = self.mainWindow.winfo_screenheight()
        self.mainWindow.geometry("%dx%d+%d+%d" % (w - w / 4, h - h / 4, w / 8, h / 8))
        self.mainWindow.title("Google Drive File Manager")
        self.mainWindow.configure(background='black')

        self.mainWindow.rowconfigure(0, weight=0)
        self.mainWindow.rowconfigure(1, weight=1)
        self.mainWindow.rowconfigure(2, weight=1)
        self.mainWindow.columnconfigure(0, weight=1)
        self.mainWindow.columnconfigure(1, weight=4)

        # set application icon
        global appIcon
        appIcon = tk.PhotoImage(file="./resources/GoogleDrive.png")

        self.mainWindow.iconphoto(False, appIcon)

        # Add a menu with a few commands
        self.toolbar = ttk.Frame(self.mainWindow)
        self.configButton = ttk.Button(self.toolbar, text='Configuration', command=self.config)
        self.updateButton = ttk.Button(self.toolbar, text='Update', command=self.updateData)
        self.exitButton = ttk.Button(self.toolbar, text='Exit', command=self.exit)
        self.searchButton = ttk.Button(self.toolbar, text='Search', command=self.spawnSearchWindow)
        self.configButton.pack(side=tk.LEFT, padx=2, pady=2)
        self.updateButton.pack(side=tk.LEFT, padx=2, pady=2)
        self.exitButton.pack(side=tk.LEFT, padx=2, pady=2)
        self.searchButton.pack(side=tk.LEFT, padx=2, pady=2)
        self.forestButton = ttk.Button(self.toolbar, text='Forest', command=self.forest)
        self.forestButton.pack(side=tk.RIGHT, padx=2, pady=2)
        self.toolbar.grid(row=0, columnspan=2, sticky="nwe", padx=2, pady=2)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", highlightthickness=0, bd=0, font=('Calibri', 11), background="#e0e0e0",
                        foreground="black", rowheight=25)  # Modify the font of the body
        style.configure("Treeview.Heading", font=('Calibri', 11, 'bold'))  # Modify the font of the headings

        style.layout("Treeview", [('Treeview', {'sticky': 'nswe'})], )  # Remove the borders
        # not sure what this does, but if absent the background color remains white.
        style.map("Treeview", foreground=[('selected', '#000000')],
                  background=[('selected', '#ffcc00'), (['invalid', '!disabled'], '#e0e0e0'),
                              (['invalid', 'disabled'], '#e0e0e0')])

        # Add some kind of status bar at the bottom of the window
        self.statusbar = ttk.Label(self.mainWindow, text="", anchor=tk.W)
        # self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbar.grid(row=3, columnspan=2, sticky="swe", padx=2, pady=2)

        # add folder view
        settings.treeview = ttk.Treeview(self.mainWindow, style="Treeview", selectmode='browse')
        settings.treeview.grid(column=0, row=1, rowspan=2, sticky="nsew", padx=2)
        settings.treeview.columnconfigure(0, weight=1)
        settings.treeview.rowconfigure(0, weight=1)
        settings.treeview.heading('#0', text="Folder Structure", anchor=tk.W)  # shame
        settings.treeview.column('#0#', stretch=True, minwidth=400)
        # add an horizontal scrollbar
        self.scrollbarX = ttk.Scrollbar(self.mainWindow, orient="horizontal", command=settings.treeview.xview)
        settings.treeview.configure(xscrollcommand=self.scrollbarX.set)
        self.scrollbarX.grid(column=0, row=2, sticky="sew", padx=2)

        settings.contentview = ttk.Treeview(self.mainWindow, style="Treeview", columns=("#1", "#2", "#3", "#4", "#5"),
                                            selectmode='extended')
        settings.contentview.grid(column=1, row=1, rowspan=2, sticky="nsew", padx=2)
        settings.contentview.heading('#0', text="Content")
        settings.contentview.heading('#1', text="Type")
        settings.contentview.heading('#2', text="Size")
        settings.contentview.heading('#3', text="Modified (UTC)")
        settings.contentview.heading('#4', text="Owner")
        settings.contentview.heading('#5', text="Shared")
        settings.contentview.column('#0#', stretch=True)
        settings.contentview.column('#1#', width=int(w / 12), stretch=False)
        settings.contentview.column('#2#', width=int(w / 20), stretch=False)
        settings.contentview.column('#3#', width=int(w / 12), stretch=False)
        settings.contentview.column('#4#', width=int(w / 10), stretch=False)
        settings.contentview.column('#5#', width=int(w / 20), stretch=False)

        settings.contentview.columnconfigure(0, weight=3)
        settings.contentview.rowconfigure(0, weight=1)

        # add a scrollbar
        self.scrollbar = ttk.Scrollbar(self.mainWindow, orient="vertical", command=settings.contentview.yview)
        # self.scrollbar.place(relx=0.978, rely=0.175, relheight=0.713, relwidth=0.020)
        settings.contentview.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(column=1, row=1, rowspan=3, sticky="sne", padx=2, pady=50)

        # make a contextual menu on item selection  --> delegated to the showContextMenu function,

        self.mainWindow.bind("<Button-3>", lambda event: self.showContextMenu(event))
        self.mainWindow.bind('<Escape>', lambda event: self.exit())

        settings.treeview.bind('<<TreeviewSelect>>', self.selectTreeItem)  # enable item selection in tree
        # settings.contentview.bind('<<TreeviewSelect>>', self.selectContentItem)

        for i in range(1, 6):
            settings.contentview.columnconfigure(i, weight=1)
            settings.contentview.rowconfigure(i, weight=1)

        self.mainWindow.after(50, self.getData)  # load data on startup
        self.mainWindow.after(100, self.updateStatusBar)  # routine to constantly update the status bar

        self.mainWindow.protocol("WM_DELETE_WINDOW", self.exit)
        self.mainWindow.mainloop()

        ###END SETUP GUI####

    def updateStatusBar(self):

        if settings.error:
            if 'Warning' in settings.error:
                self.statusbar.configure(text=settings.error, background='yellow', foreground='black')
            else:
                self.statusbar.configure(text=settings.error, background='red', foreground='white')
        elif settings.moveInProgress:
            self.statusbar.configure(text='Processing: "{0}"'.format(settings.itemMoving), background='orange',
                                     foreground='blue')
        elif settings.copyInProgress:
            self.statusbar.configure(text='Copy in progress: "{0}"'.format(settings.itemCopying), background='orange',
                                     foreground='blue')
        elif settings.downloadIsRunning:
            self.statusbar.configure(
                text='Download in progress: "{0}", {1}'.format(settings.fileDownloading, settings.fileDownloadingSize),
                background='orange', foreground='blue')
        elif settings.retrievingFiles == True:
            self.statusbar.configure(
                text=" Retrieving file list from GDrive. This may take some time. {0} files listed.".format(
                    len(settings.retrievedFiles)), background='blue', foreground='orange')
        elif settings.loadingData:  # len(self.folders) > 0:
            self.statusbar.configure(text=" Loading data: {0} entries remaining".format(len(self.folders)),
                                     background='blue', foreground='orange')
        else:
            self.statusbar.configure(text=" Ready", background='green', foreground='black')
        self.statusbar.update()
        self.mainWindow.after(500, self.updateStatusBar)

    def getData(self):

        settings.treeview.delete(*settings.treeview.get_children())  # clear the left panel and populate again.

        global starredIcon
        global rootIcon
        global trashIcon
        global sharedWithIcon
        global sharedByIcon
        global orphanIcon

        self.rootIcon = tk.PhotoImage(file='./resources/root.png')
        self.trashIcon = tk.PhotoImage(file='./resources/trash.png')
        self.sharedWithIcon = tk.PhotoImage(file='./resources/sharedWith.png')
        self.sharedByIcon = tk.PhotoImage(file='./resources/sharedBy.png')
        self.orphanIcon = tk.PhotoImage(file='./resources/orphaned.png')
        self.starredIcon = tk.PhotoImage(file='./resources/starred.png')
        settings.folderIcon = tk.PhotoImage(file='./resources/folder.png')
        settings.audioIcon = tk.PhotoImage(file='./resources/audio.png')
        settings.documentIcon = tk.PhotoImage(file='./resources/document.png')
        settings.excelIcon = tk.PhotoImage(file='./resources/excel.png')
        settings.gappsIcon = tk.PhotoImage(file='./resources/GApps.png')
        settings.imageIcon = tk.PhotoImage(file='./resources/image.png')
        settings.pdfIcon = tk.PhotoImage(file='./resources/pdf.png')
        settings.spreadsheetIcon = tk.PhotoImage(file='./resources/spreadsheet.png')
        settings.wordIcon = tk.PhotoImage(file='./resources/word.png')
        settings.writerIcon = tk.PhotoImage(file='./resources/writer.png')
        settings.videoIcon = tk.PhotoImage(file='./resources/video.png')
        settings.shortcutIcon = tk.PhotoImage(file='./resources/shortcut.png')
        settings.compressedIcon = tk.PhotoImage(file='./resources/compressed.png')

        if settings.drive:

            if path.isfile('files'):

                settings.loadingData = True

                settings.error = ''  # all good, remove any errors

                settings.rootID = self.getRootId()
                # create Starred folders on top
                self.starred = settings.treeview.insert('', 0, image=self.starredIcon, text=' Starred',
                                                        tags=settings.rootID)
                # create the root directory
                self.root = settings.treeview.insert('', 1, image=self.rootIcon, text=' Root', tags=settings.rootID)
                # create a folder where all the external shared data will appear
                self.theirShares = settings.treeview.insert('', 2, image=self.sharedWithIcon, text=' Shared With Me',
                                                            tags=settings.rootID)
                # create a folder where all the data I'm sharing will appear
                self.myShares = settings.treeview.insert('', 3, image=self.sharedByIcon, text=' Shared By Me',
                                                         tags=settings.rootID)
                # create a folder where my data without a parent will be stored
                self.orphans = settings.treeview.insert('', 4, image=self.orphanIcon, text=' Orphaned Data',
                                                        tags=settings.rootID)
                # create the trash folder with arbitrary Id
                self.trash = settings.treeview.insert('', 5, image=self.trashIcon, text=' Trash', tags=settings.rootID)

                settings.directory['root'] = self.root
                settings.directory['trash'] = self.trash
                settings.directory['theirShares'] = self.theirShares
                settings.directory['myShares'] = self.myShares
                settings.directory['orphans'] = self.orphans
                settings.directory['starred'] = self.starred

                try:
                    with open("files") as f:
                        data = load(f)

                    for i in range(len(data)):
                        if 'folder' in data[i]['mimeType']:
                            settings.folders.append(data[i])
                        else:
                            if not data[i]['name'] == '.DS_Store':  # system file with folder metadata, ignore
                                settings.files.append(data[i])

                    self.folders = []  # save to a temporary list that will be gradually emptied next, and keep the settings.folders untouched. Needed for other functions.
                    for i in settings.folders:
                        self.folders.append(i)

                    del data  # saving some memory.

                    ### NOW GET FULL LIST OF FILES AND SUBFOLDERS ###
                    # don't execute if we're updating the data from GDrive

                    while len(self.folders) > 0:
                        if not settings.retrievingFiles:

                            length = len(self.folders)

                            try:
                                for i in self.folders:
                                    # get the last modification timestamp - in UTC
                                    modified = datetime.strftime(
                                        datetime.strptime(i['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'), '%d/%m/%y %H:%M')
                                    self.mainWindow.update()

                                    try:
                                        parent = i['parents'][0]
                                    except KeyError:  # there might be no parent (or multiple parents, but nevermind)
                                        parent = None

                                    # start with identifying toplevel folders
                                    if parent == settings.rootID:  # if parent is root, folder can be either in the root or in the trash. Shared or starred, too, but owned by me anyway.
                                        # IMPORTANT NOTE: folders can be in multiple locations if they are starred, shared, etc.
                                        # if the dict keys are the ids, then only the last entry is stored as the dict is updated. To prevent this, a suffix is added to the key.
                                        if not i['trashed']:
                                            settings.directory[i['id']] = settings.treeview.insert(self.root, 'end',
                                                                                                   image=settings.folderIcon,
                                                                                                   text=' ' + i['name'],
                                                                                                   values=(
                                                                                                   'Folder', modified,
                                                                                                   i['owners'][0][
                                                                                                       'displayName'],
                                                                                                   i['shared'],
                                                                                                   i['trashed']), tags=(
                                                parent, i['id']))
                                        else:
                                            settings.directory[i['id']] = settings.treeview.insert(self.trash, 'end',
                                                                                                   image=settings.folderIcon,
                                                                                                   text=' ' + i['name'],
                                                                                                   values=(
                                                                                                   'Folder', modified,
                                                                                                   i['owners'][0][
                                                                                                       'displayName'],
                                                                                                   i['shared'],
                                                                                                   i['trashed']), tags=(
                                                parent, i['id']))
                                        if i['starred']:
                                            settings.directory[i['id'] + '-starred'] = settings.treeview.insert(
                                                self.starred, 'end', image=settings.folderIcon, text=' ' + i['name'],
                                                values=('Folder', modified, i['owners'][0]['displayName'], i['shared'],
                                                        i['trashed']), tags=(parent, i['id']))
                                        if i['shared']:
                                            settings.directory[i['id'] + '-shared'] = settings.treeview.insert(
                                                self.myShares, 'end', image=settings.folderIcon, text=' ' + i['name'],
                                                values=('Folder', modified, i['owners'][0]['displayName'], i['shared'],
                                                        i['trashed']), tags=(parent, i['id']))
                                        self.folders.remove(i)
                                        break

                                    elif parent == None:  # if parent is None, folder can be shared with me or orphaned (and shared by me), or trashed.

                                        if i['trashed']:  # if trashed, don't care if shared
                                            settings.directory[i['id']] = settings.treeview.insert(self.trash, 'end',
                                                                                                   image=settings.folderIcon,
                                                                                                   text=' ' + i['name'],
                                                                                                   values=(
                                                                                                   'Folder', modified,
                                                                                                   i['owners'][0][
                                                                                                       'displayName'],
                                                                                                   i['shared'],
                                                                                                   i['trashed']), tags=(
                                                parent, i['id']))
                                        elif not i['ownedByMe']:
                                            settings.directory[i['id']] = settings.treeview.insert(self.theirShares,
                                                                                                   'end',
                                                                                                   image=settings.folderIcon,
                                                                                                   text=' ' + i['name'],
                                                                                                   values=(
                                                                                                   'Folder', modified,
                                                                                                   i['owners'][0][
                                                                                                       'displayName'],
                                                                                                   i['shared'],
                                                                                                   i['trashed']), tags=(
                                                parent, i['id']))
                                        else:  # only other option is it's an orphan
                                            settings.directory[i['id']] = settings.treeview.insert(self.orphans, 'end',
                                                                                                   image=settings.folderIcon,
                                                                                                   text=' ' + i['name'],
                                                                                                   values=(
                                                                                                   'Folder', modified,
                                                                                                   i['owners'][0][
                                                                                                       'displayName'],
                                                                                                   i['shared'],
                                                                                                   i['trashed']), tags=(
                                                parent, i['id']))
                                            if i['shared']:
                                                settings.directory[i['id'] + '-shared'] = settings.treeview.insert(
                                                    self.myShares, 'end', image=settings.folderIcon,
                                                    text=' ' + i['name'],
                                                    values=(
                                                    'Folder', modified, i['owners'][0]['displayName'], i['shared'],
                                                    i['trashed']), tags=(parent, i['id']))
                                        if i['starred']:
                                            settings.directory[i['id'] + '-starred'] = settings.treeview.insert(
                                                self.starred, 'end', image=settings.folderIcon, text=' ' + i['name'],
                                                values=('Folder', modified, i['owners'][0]['displayName'], i['shared'],
                                                        i['trashed']), tags=(parent, i['id']))
                                        self.folders.remove(i)
                                        break

                                    else:

                                        for key in settings.directory:
                                            if i['parents'][0] in key and not i['trashed']:
                                                settings.directory[i['id']] = settings.treeview.insert(
                                                    settings.directory[key], 'end', image=settings.folderIcon,
                                                    text=' ' + i['name'],
                                                    values=(
                                                    'Folder', modified, i['owners'][0]['displayName'], i['shared'],
                                                    i['trashed']), tags=(parent, i['id']))
                                                # should be added everywhere, including in shared/trash/starred parent folders
                                                # but if this one is trashed, starred or shared and not its parent ?
                                                # and if it is starred and also its parent ?
                                                # shit.
                                                if i['starred']:
                                                    try:
                                                        if [j['starred'] for j in settings.folders if j['id']] == \
                                                                i['parents'][0] == i[
                                                            'starred']:  # if the parent of the starred folder isn't starred itself
                                                            settings.directory[
                                                                i['id'] + '-starred'] = settings.treeview.insert(
                                                                settings.directory[key], 'end',
                                                                image=settings.folderIcon, text=' '
                                                                                                + i['name'], values=(
                                                                'Folder', modified, i['owners'][0]['displayName'],
                                                                i['shared'], i['trashed']), tags=(parent, i['id']))
                                                        else:
                                                            settings.directory[
                                                                i['id'] + '-starred'] = settings.treeview.insert(
                                                                self.starred, 'end', image=settings.folderIcon, text=' '
                                                                                                                     +
                                                                                                                     i[
                                                                                                                         'name'],
                                                                values=(
                                                                'Folder', modified, i['owners'][0]['displayName'],
                                                                i['shared'], i['trashed']), tags=(parent, i['id']))
                                                    except:  # no parent key
                                                        settings.directory[
                                                            i['id'] + '-starred'] = settings.treeview.insert(
                                                            self.starred, 'end', image=settings.folderIcon,
                                                            text=' ' + i['name'],
                                                            values=('Folder', modified, i['owners'][0]['displayName'],
                                                                    i['shared'], i['trashed']), tags=(parent, i['id']))

                                                if (i['ownedByMe'] and i['shared']):
                                                    for key2 in settings.directory:
                                                        if i['parents'][0] + '-shared' in key2:
                                                            settings.directory[
                                                                i['id'] + '-shared'] = settings.treeview.insert(
                                                                settings.directory[key2], 'end',
                                                                image=settings.folderIcon, text=' '
                                                                                                + i['name'], values=(
                                                                'Folder', modified, i['owners'][0]['displayName'],
                                                                i['shared'], i['trashed']), tags=(parent, i['id']))
                                                            break
                                                self.folders.remove(i)
                                                break

                                            elif i['parents'][0] in key and i['trashed']:
                                                # if parent is not trashed, insert in trash, otherwise, insert under the parent.
                                                if settings.treeview.item(settings.directory[key])['values'][
                                                    4] == 'False':
                                                    settings.directory[i['id']] = settings.treeview.insert(self.trash,
                                                                                                           'end',
                                                                                                           image=settings.folderIcon,
                                                                                                           text=' ' + i[
                                                                                                               'name'],
                                                                                                           values=(
                                                                                                           'Folder',
                                                                                                           modified,
                                                                                                           i['owners'][
                                                                                                               0][
                                                                                                               'displayName'],
                                                                                                           i['shared'],
                                                                                                           i[
                                                                                                               'trashed']),
                                                                                                           tags=(parent,
                                                                                                                 i[
                                                                                                                     'id']))
                                                else:
                                                    settings.directory[i['id']] = settings.treeview.insert(
                                                        settings.directory[key], 'end', image=settings.folderIcon,
                                                        text=' ' + i['name'],
                                                        values=(
                                                        'Folder', modified, i['owners'][0]['displayName'], i['shared'],
                                                        i['trashed']), tags=(parent, i['id']))

                                                self.folders.remove(i)
                                                break

                                if len(self.folders) == length:
                                    settings.error = 'Error parsing data. Please click on "Update".'
                                    break


                            except:  # when the data is refreshed it might cause an exception. Pass. Function will be executed again anyway.
                                pass

                        self.mainWindow.update()

                    settings.loadingData = False
                    # settings.directory = {} #save some memory.
                    self.mainWindow.update()

                except Exception as e:
                    print({e})
                    settings.error = 'Error parsing data. Please click on "Update".'

            else:
                settings.error = ' Warning: no data. Please click on "Update" to retrieve the file list'
        else:
            settings.error = ' Not connected. Please check or set up account'

    def getRootId(self):
        # GET ROOT ID
        api_service = settings.drive  # just get the first entry whose parent is root and extract the root ID, as well as the account holder's name
        try:
            param = {}
            param['pageSize'] = 1
            param['corpora'] = "user"
            param['fields'] = "files(parents, owners)"
            param['q'] = '"root" in parents'
            files = api_service.files().list(**param).execute()

            settings.rootID = files['files'][0]['parents'][0]
            settings.owner = files['files'][0]['owners'][0]['displayName']

            return settings.rootID

        except Exception as e:
            settings.error = str(e)
            pass

    def updateData(self):

        if not settings.retrievingFiles:  # and len(self.folders) == 0:

            if settings.drive:

                if tk.messagebox.askokcancel(None, 'Refresh data from GDrive?\nThis may take time.') == True:

                    settings.contentview.delete(*settings.contentview.get_children())  # clear the right panel

                    updateThread = Thread(target=listDriveFiles)
                    updateThread.start()
                    settings.error = ""  # remove any errors (the 'no data' warning, probably)
                    sleep(0.5)
                    while settings.retrievingFiles:
                        self.mainWindow.update()
                        sleep(0.5)
                    sleep(0.5)
                    self.folders = []
                    settings.files = []
                    settings.folders = []
                    settings.directory = {}
                    self.getData()  # process all

            else:
                tk.messagebox.showinfo(None, "No account is configured.\nPlease setup first.")

        else:
            tk.messagebox.showinfo(None, 'An operation is already running.\nPlease wait until it completes.')

    def selectTreeItem(self, event):  # don't care about the event. It's automatically sent)

        item = settings.treeview.focus()
        data = settings.treeview.item(item)

        # print('data:', data)

        settings.contentview.delete(*settings.contentview.get_children())  # clear the right panel

        try:
            parent = data['tags'][1]
        except:
            try:
                parent = data['tags'][
                    0]  # if Root or other system folder is selected, it has only one tag, the root ID. To prevent mix-ups in case another folder has the same name
            except:
                parent = None
                pass
            pass

        try:
            if data['text'] == ' Orphaned Data' and parent == settings.rootID:  # or parent == None):
                for i in range(len(settings.files)):
                    if settings.treeview.selection()[0] == self.theirShares:
                        if settings.files[i]['ownedByMe'] and not settings.files[i]['trashed']:
                            try:
                                fileParent = settings.files[i][
                                    'parents']  # just to test for the field's presence. If it's there (= not an orphan), do nothing and move on
                            except:
                                fileParent = None
                                modified = datetime.strftime(
                                    datetime.strptime(settings.files[i]['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                                    '%d/%m/%y %H:%M')
                                try:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], settings.files[i]['size'])
                                except KeyError:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], None)
                                settings.contentview.insert('', 'end', image=attributes[2],
                                                            text=' ' + settings.files[i]['name'],
                                                            values=(attributes[0], attributes[1],
                                                                    modified,
                                                                    settings.files[i]['owners'][0]['displayName'],
                                                                    settings.files[i]['shared'],
                                                                    settings.files[i]['trashed']),
                                                            tags=(fileParent, settings.files[i]['id']))
                                self.mainWindow.update()
                                pass
                    else:
                        break
            elif data['text'] == ' Starred' and (parent == settings.rootID or parent == None):
                for i in range(len(settings.files)):
                    if settings.treeview.selection()[0] == self.starred:
                        try:
                            try:
                                fileParent = settings.files[i][
                                    'parents']  # just to test for the field's presence. If it's there (= not an orphan), do nothing and move on
                            except:
                                fileParent = None
                            if settings.files[i]['starred'] and not settings.files[i]['trashed']:
                                modified = datetime.strftime(
                                    datetime.strptime(settings.files[i]['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                                    '%d/%m/%y %H:%M')
                                try:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], settings.files[i]['size'])
                                except KeyError:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], None)
                                settings.contentview.insert('', 'end', image=attributes[2],
                                                            text=' ' + settings.files[i]['name'],
                                                            values=(attributes[0], attributes[1],
                                                                    modified,
                                                                    settings.files[i]['owners'][0]['displayName'],
                                                                    settings.files[i]['shared'],
                                                                    settings.files[i]['trashed']),
                                                            tags=(fileParent, settings.files[i]['id']))
                                self.mainWindow.update()
                        except:
                            pass
                    else:
                        break

            elif data['text'] == ' Trash' and (parent == settings.rootID or parent == None):
                for i in range(len(settings.files)):
                    if settings.treeview.selection()[0] == self.trash:
                        try:
                            fileParent = settings.files[i]['parents'][0]
                        except:
                            fileParent = None
                        if settings.files[i]['trashed'] and (fileParent == None or fileParent == settings.rootID):
                            modified = datetime.strftime(
                                datetime.strptime(settings.files[i]['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                                '%d/%m/%y %H:%M')

                            try:
                                attributes = contextFunctions().getMimeAndSize(settings.files[i]['mimeType'],
                                                                                                 settings.files[i]['size'])
                            except KeyError:
                                attributes = contextFunctions().getMimeAndSize(settings.files[i]['mimeType'],
                                                                                                 None)

                            settings.contentview.insert('', 'end', image=attributes[2],
                                                        text=' ' + settings.files[i]['name'],
                                                        values=(attributes[0], attributes[1],
                                                                modified, settings.files[i]['owners'][0]['displayName'],
                                                                settings.files[i]['shared'],
                                                                settings.files[i]['trashed']),
                                                        tags=(fileParent, settings.files[i]['id']))
                            self.mainWindow.update()
                    else:
                        break

            elif data['text'] == ' Root' and (parent == settings.rootID or parent == None):
                for i in range(len(settings.files)):
                    if settings.treeview.selection()[0] == self.root:
                        try:
                            try:
                                fileParent = settings.files[i][
                                    'parents']  # just to test for the field's presence. If it's there (= not an orphan), do nothing and move on
                            except:
                                fileParent = None
                            if settings.files[i]['parents'][0] == settings.rootID and not settings.files[i]['trashed']:
                                modified = datetime.strftime(
                                    datetime.strptime(settings.files[i]['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                                    '%d/%m/%y %H:%M')
                                try:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], settings.files[i]['size'])
                                except KeyError:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], None)
                                settings.contentview.insert('', 'end', image=attributes[2],
                                                            text=' ' + settings.files[i]['name'],
                                                            values=(attributes[0], attributes[1],
                                                                    modified,
                                                                    settings.files[i]['owners'][0]['displayName'],
                                                                    settings.files[i]['shared'],
                                                                    settings.files[i]['trashed']),
                                                            tags=(fileParent, settings.files[i]['id']))
                                self.mainWindow.update()
                        except:
                            pass
                    else:
                        break
            elif data['text'] == ' Shared With Me' and (parent == settings.rootID or parent == None):
                for i in range(len(settings.files)):
                    if settings.treeview.selection()[0] == self.theirShares:
                        try:
                            try:
                                fileParent = settings.files[i]['parents']
                            except:
                                fileParent = None
                            if (not 'parents' in str(settings.files[i]) and not settings.files[i]['ownedByMe']) or (
                                    not settings.files[i]['ownedByMe']  # too long to display the data.
                                    and [x for x in settings.directory if x == settings.files[i]['parents'][
                                0]] == []):  # not sure there is a solution, as I need to iterate the entire directory.
                                # if files are shared and a parent is present in the metadata, but the parent isn't shared so the file can't appear anywhere except by searching.
                                modified = datetime.strftime(
                                    datetime.strptime(settings.files[i]['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                                    '%d/%m/%y %H:%M')
                                try:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], settings.files[i]['size'])
                                except KeyError:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], None)

                                settings.contentview.insert('', 'end', image=attributes[2],
                                                            text=' ' + settings.files[i]['name'],
                                                            values=(attributes[0], attributes[1],
                                                                    modified,
                                                                    settings.files[i]['owners'][0]['displayName'],
                                                                    settings.files[i]['shared'],
                                                                    settings.files[i]['trashed']),
                                                            tags=(fileParent, settings.files[i]['id']))
                                self.mainWindow.update()
                        except:
                            pass
                    else:
                        break
            elif data['text'] == ' Shared By Me' and (parent == settings.rootID or parent == None):
                for i in range(len(settings.files)):
                    if settings.treeview.selection()[0] == self.theirShares:
                        try:
                            try:
                                fileParent = settings.files[i][
                                    'parents']  # just to test for the field's presence. If it's there (= not an orphan), do nothing and move on
                            except:
                                fileParent = None
                            if not 'parents' in str(settings.files[i]) and settings.files[i]['ownedByMe'] and \
                                    settings.files[i]['shared']:
                                modified = datetime.strftime(
                                    datetime.strptime(settings.files[i]['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                                    '%d/%m/%y %H:%M')
                                try:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], settings.files[i]['size'])
                                except KeyError:
                                    attributes = contextFunctions().getMimeAndSize(
                                        settings.files[i]['mimeType'], None)
                                settings.contentview.insert('', 'end', image=attributes[2],
                                                            text=' ' + settings.files[i]['name'],
                                                            values=(attributes[0], attributes[1],
                                                                    modified,
                                                                    settings.files[i]['owners'][0]['displayName'],
                                                                    settings.files[i]['shared'],
                                                                    settings.files[i]['trashed']),
                                                            tags=(fileParent, settings.files[i]['id']))
                                self.mainWindow.update()
                        except:
                            # print(e)
                            pass
                    else:
                        break
            else:
                folder = settings.treeview.selection()[0]
                for i in range(len(settings.files)):
                    if settings.treeview.selection()[0] == folder:
                        try:
                            try:
                                fileParent = settings.files[i][
                                    'parents']  # just to test for the field's presence. If it's there (= not an orphan), do nothing and move on
                            except:
                                fileParent = None
                            if settings.files[i]['parents'][0] == parent:
                                if data['values'][4] == str(settings.files[i][
                                                                'trashed']):  # if both the file and its parent are trashed or not
                                    modified = datetime.strftime(
                                        datetime.strptime(settings.files[i]['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                                        '%d/%m/%y %H:%M')
                                    try:
                                        attributes = contextFunctions().getMimeAndSize(
                                            settings.files[i]['mimeType'], settings.files[i]['size'])
                                    except KeyError:
                                        attributes = contextFunctions().getMimeAndSize(
                                            settings.files[i]['mimeType'], None)
                                    settings.contentview.insert('', 'end', image=attributes[2],
                                                                text=' ' + settings.files[i]['name'],
                                                                values=(attributes[0], attributes[1],
                                                                        modified,
                                                                        settings.files[i]['owners'][0]['displayName'],
                                                                        settings.files[i]['shared'],
                                                                        settings.files[i]['trashed']),
                                                                tags=(fileParent, settings.files[i]['id']))
                                    self.mainWindow.update()
                        except:
                            pass

                    else:
                        break
        except Exception as e:
            settings.error = 'Error :', str({e})
            sleep(3)
            settings.error = ''
            pass

        finally:
            self.mainWindow.update()

    def selectContentItem(self, event):
        for item in settings.contentview.selection():
            print(settings.contentview.item(item))

    def spawnSearchWindow(self):
        w = self.mainWindow.winfo_width()
        h = self.mainWindow.winfo_height()
        x = self.mainWindow.winfo_x()
        y = self.mainWindow.winfo_y()  # pass main window position and dimensions to place search window appropriately.
        if not settings.loadingData:  # only enable the search function when the data is loaded, otherwise results may be incomplete.
            if not search_window_is_open:  # if search window is open already, don't reopen
                searchWindow(settings.rootID, 2 * w / 3, h - h / 6, x + w / 6, y + h / 12)  # jesus fucking christ.
                #explanation: this allows to spawn the search window with dimensions relative to the main window, and in its center.
        elif ('not connected' or 'no data') in self.statusbar.cget("text"):
            tk.messagebox.showinfo(None, "Not connected or no data. Please check and try again.")
        else:
            tk.messagebox.showinfo(None, "Please wait for current operation to complete")

if __name__ == "__main__":
    appMainWindow()

