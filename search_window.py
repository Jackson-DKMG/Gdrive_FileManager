#Class to spawn a window to search files and folders within the drive.

from datetime import datetime
from threading import Thread
import tkinter as tk
from tkinter import ttk
from unidecode import unidecode
import settings
import context_functions

class searchWindow():
    def __init__(self, rootID, w, h, x, y):  # get all existing data to search into and display
        super().__init__()
        settings.rootID = rootID
        global search_window_is_open
        search_window_is_open = True
        self.searchIsRunning = False
        self.searchWindow(w, h, x, y)
        self.stop = False

    def abort(self):
        if self.searchIsRunning:
            self.searchIsRunning = False
            self.statusbar.configure(
                text=" Search aborted. Displayed results may be incomplete. Ready to search again.",
                background='yellow', foreground='black')
            self.statusbar.update()

        else:
            global search_window_is_open
            search_window_is_open = None
            self.mainWindow.destroy()

    def showContextMenu(self,
                        event):  # show a contextual menu. If nothing is selected already, or if another single item is selected,

        try:
            if self.contextMenu:
                self.contextMenu.destroy()
        except:
            pass

        self.contextMenu = tk.Menu(self.mainWindow, tearoff=0)
        self.contextMenu.add_command(label="Download", command=lambda: self.downloadSelected())
        self.contextMenu.add_command(label="Copy/Move", command=lambda: self.copyMoveSelected())
        self.contextMenu.add_command(label="Remove", command=lambda: self.removeRestore(flag=True))
        self.contextMenu.add_command(label="Star/Unstar", command=lambda: self.starUnstar())

        self.contextMenu.bind("<FocusOut>", lambda event: self.contextMenu.destroy())

        try:
            # automatically select the item below the mouse. Otherwise multiple items are selected, keep it that way.
            if len(self.searchview.selection()) > 1:
                if self.searchview.item(self.searchview.selection()[0])['values'][-1:][0] == (
                        'True' or True):  # the value item for trashed is the last element of [values]

                    self.contextMenu.delete(2)  # delete the 'Remove' option and replace with a 'Restore' one
                    self.contextMenu.add_command(label="Restore", command=lambda: self.removeRestore(flag=False))
            else:
                item = self.searchview.identify_row(event.y)
                self.searchview.selection_set(item)
                if self.searchview.item(self.searchview.selection()[0])['values'][-1:][0] == (
                        'True' or True):  # the value item for trashed is the last element of [values]
                    self.contextMenu.delete(2)  # delete the 'Remove' option and replace with a 'Restore' one
                    self.contextMenu.add_command(label="Restore", command=lambda: self.removeRestore(flag=False))

            self.contextMenu.tk_popup(event.x_root, event.y_root)

        except:
            pass

        finally:
            self.contextMenu.grab_release()

    def starUnstar(self):
        data = []
        items = self.searchview.selection()
        for i in items:
            i = self.searchview.item(i)
            i['text'] = [j['name'] for j in settings.files + settings.folders if i['tags'][1] == j['id']][
                0]  # search in both lists at once.
            data.append(i)
        Thread(target=context_functions.contextFunctions().starUnstar, args=[data]).start()

    def removeRestore(self, flag):
        if not (
                settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
            data = []
            items = self.searchview.selection()
            for i in items:
                i = self.searchview.item(i)
                i['text'] = [j['name'] for j in settings.files + settings.folders if i['tags'][1] == j['id']][
                    0]  # search in both lists at once.
                data.append(i)
            Thread(target=context_functions.contextFunctions().removeRestore, args=(data, flag)).start()
        else:
            tk.messagebox.showinfo(None, "Please wait for the current operation to complete.")

    def downloadSelected(self):
        if not settings.downloadIsRunning:
            data = []  # create list to store the item(s) to process.
            try:
                items = self.searchview.selection()
                for i in items:  # item names contain their full path. Need to keep the file/folder name only. It may contain a '/' so can't just split on this.
                    # get the id and search in settings.files/folders ?
                    i = self.searchview.item(i)
                    i['text'] = [j['name'] for j in settings.files + settings.folders if i['tags'][1] == j['id']][
                        0]  # search in both lists at once.
                    data.append(i)
                self.download = Thread(target=context_functions.contextFunctions().download, args=[data])
                self.download.start()
            # contextFunctions().download(data) #send
            except Exception as e:
                print({e})

    def searchWindow(self, w, h, x, y):
        # create the new window on top of the existing one.
        self.mainWindow = tk.Toplevel()
        self.mainWindow.geometry("%dx%d+%d+%d" % (w, h, x, y))
        self.mainWindow.title("Search Engine")
        global appIcon
        appIcon = tk.PhotoImage(file="./resources/GoogleDrive.png")

        self.mainWindow.iconphoto(False, appIcon)
        self.mainWindow.rowconfigure(0, weight=0)
        self.mainWindow.rowconfigure(1, weight=1)
        self.mainWindow.rowconfigure(2, weight=1)
        self.mainWindow.rowconfigure(3, weight=1)
        self.mainWindow.columnconfigure(0, weight=1)

        self.toolbar = ttk.Frame(self.mainWindow)
        self.toolbar.columnconfigure(0, weight=1)
        self.toolbar.columnconfigure(1, weight=1)
        self.toolbar.grid(row=0, sticky="we", padx=2, pady=2)

        self.searchEntry = ttk.Entry(self.toolbar)
        self.searchEntry.config(background='lightgrey', foreground='black')
        self.searchButton = ttk.Button(self.toolbar, text='Search', command=self.search)
        self.searchEntry.grid(column=0, row=0, sticky='e', padx=2, pady=2)
        self.searchButton.grid(column=1, row=0, sticky='w', padx=2, pady=2)

        self.statusbar = ttk.Label(self.mainWindow, text="", anchor=tk.W)
        # self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbar.grid(row=4, sticky="we", padx=2, pady=2)

        self.searchEntry.bind('<Return>', self.search)  # launch search by pressing Enter

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", highlightthickness=0, bd=0, font=('Calibri', 11), background="#e0e0e0",
                        foreground="black", rowheight=25)  # Modify the font of the body
        style.configure("Treeview.Heading", font=('Calibri', 11, 'bold'))  # Modify the font of the headings
        style.layout("Treeview", [('Treeview', {'sticky': 'nswe'})], )  # Remove the borders
        style.map("Treeview", foreground=[('selected', '#000000')],
                  background=[('selected', '#ffcc00'), (['invalid', '!disabled'], '#e0e0e0'),
                              (['invalid', 'disabled'], '#e0e0e0')])

        self.searchview = ttk.Treeview(self.mainWindow, style="Treeview", columns=("#1", "#2", "#3", "#4", "#5", "#6"),
                                       selectmode='extended')
        self.searchview.grid(column=0, row=1, rowspan=3, sticky="nsew", padx=2)
        self.searchview.heading('#0', text="Path")
        self.searchview.heading('#1', text="Type")
        self.searchview.heading('#2', text="Size")
        self.searchview.heading('#3', text="Modified (UTC)")
        self.searchview.heading('#4', text="Owner")
        self.searchview.heading('#5', text="Shared")
        self.searchview.heading('#6', text="Trashed")
        self.searchview.columnconfigure(0, weight=3)
        self.searchview.rowconfigure(0, weight=1)
        self.searchview.column('#0#', stretch=True)
        self.searchview.column('#1#', width=int(w / 8), stretch=False)
        self.searchview.column('#2#', width=int(w / 16), stretch=False)
        self.searchview.column('#3#', width=int(w / 8), stretch=False)
        self.searchview.column('#4#', width=int(w / 7), stretch=False)
        self.searchview.column('#5#', width=int(w / 15), stretch=False)
        self.searchview.column('#6#', width=int(w / 15), stretch=False)

        # add a scrollbar
        self.scrollbar = ttk.Scrollbar(self.mainWindow, orient="vertical", command=self.searchview.yview)
        # self.scrollbar.place(relx=0.978, rely=0.175, relheight=0.713, relwidth=0.020)
        self.searchview.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(column=0, row=1, rowspan=3, sticky="sne", padx=2, pady=50)

        self.statusbar.configure(text=" Ready to search. Press Esc to close the window.", background='green',
                                 foreground='black')

        # make a contextual menu on item selection
        self.contextMenu = tk.Menu(self.mainWindow, tearoff=0)
        self.contextMenu.add_command(label="Download", command=lambda: self.downloadSelected())
        self.contextMenu.add_command(label="Copy/Move", command=lambda: self.copyMoveSelected())
        self.contextMenu.add_command(label="Star/Unstar", command=lambda: self.starUnstar())

        self.mainWindow.bind("<Button-3>", lambda event: self.showContextMenu(event))

        self.mainWindow.protocol("WM_DELETE_WINDOW", self.abort)
        self.mainWindow.bind('<Escape>', lambda e: self.abort())
        self.mainWindow.mainloop()

        self.statusbar.update()

    def search(self,
               *args):  # a 2d argument is passed when starting the search by hitting Enter (the event itself), but not when clicking on the button.
        # variable arguments on the function to prevent an exception.
        self.searchview.delete(*self.searchview.get_children())  # clear the view upon a new search

        if not self.searchEntry.get() == "":
            self.statusbar.configure(text=" Searching...", background='blue', foreground='orange')
            self.statusbar.update()
            self.searchIsRunning = True

            query = unidecode(self.searchEntry.get()).lower()
            results = [i for i in settings.files + settings.folders if query in str(i).lower()]


            self.statusbar.configure(
                text=" Found {0} results. Displaying... Press escape to cancel.".format(len(results)),
                background='blue', foreground='orange')
            self.statusbar.update()

            for i in range(len(results)):
                if self.searchIsRunning:  # press on Escape switches this to False and interrupts the search results display.
                    # try:
                    try:
                        attributes = context_functions.contextFunctions().getMimeAndSize(results[i]['mimeType'],
                                                                                         results[i]['size'])
                    except KeyError:
                        attributes = context_functions.contextFunctions().getMimeAndSize(results[i]['mimeType'], None)

                    # START BUILDING PATH FOR EACH RESULT#
                    try:
                        parent = results[i]['parents'][0]
                    except:
                        parent = ''
                    path = ''
                    y = results[i]
                    while not parent == 'None':
                        try:
                            z = [x for x in settings.folders if x['id'] == parent][0]
                            y = z
                            parent = y['id']
                            path = y['name'] + '/' + path
                            parent = settings.treeview.item(settings.directory[parent])['tags'][0]
                            # print("parent:", parent)

                        except Exception as e:
                            # print(e) #a shared file has a parent, which is present in the metadata but not shared, generates an exception.
                            break

                    if not y['ownedByMe']:
                        treeBasis = 'Shared With Me/'
                    else:
                        try:
                            test = y['parents']
                            treeBasis = 'Root/'
                        except:
                            treeBasis = 'Orphaned Data/'
                            pass
                        if y['trashed']:
                            treeBasis = 'Trash/'

                    try:
                        fileparent = results[i]['parents'][0]
                    except:
                        fileparent = None
                        pass

                    text = ' ' + treeBasis + path + results[i]['name']
                    modified = datetime.strftime(datetime.strptime(results[i]['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                                                 '%d/%m/%y %H:%M')
                    self.searchview.insert('', 'end', image=attributes[2], text=text,
                                           values=(attributes[0], attributes[1],
                                                   modified, results[i]['owners'][0]['displayName'],
                                                   results[i]['shared'], results[i]['trashed']),
                                           tags=(fileparent, results[i]['id']))
                    # first tag is "None" instead of being the parent ID. Won't be needed, but having something avoids additional processing when downloading.
                    self.mainWindow.update()

            if self.searchIsRunning:  # search and result display weren't interrupted by user input
                self.statusbar.configure(text=" Ready to search.", background='green', foreground='black')
                self.statusbar.update()
                self.searchIsRunning = False

            # if searchIsRunning is already false, do nothing. Status bar was updated by the abort function.

    def copyMoveSelected(self):
        if not (
                settings.downloadIsRunning or settings.moveInProgress or settings.copyInProgress or settings.retrievingFiles or settings.loadingData):
            self.data = []
            items = self.searchview.selection()
            for i in items:
                i = self.searchview.item(i)
                i['text'] = [j['name'] for j in settings.files + settings.folders if i['tags'][1] == j['id']][
                    0]  # search in both lists at once.
                self.data.append(i)
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
        Thread(target=context_functions.contextFunctions().copy, args=(self.data, destination)).start()

    def moveSelected(self):
        destination = self.selectview.item(self.selectview.selection())
        self.selectWindow.destroy()
        Thread(target=context_functions.contextFunctions().move, args=(self.data, destination)).start()

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

        for child in settings.treeview.get_children():  # duplicate folder tree in the new window
            # remove Starred, Orphaned and Trash from the selectview. Can't copy or move there
            if not (settings.treeview.item(child)['text'] == ' Starred' or settings.treeview.item(child)[
                'text'] == ' Orphaned Data' or settings.treeview.item(child)['text'] == ' Trash'):
                try:
                    item = self.selectview.insert('', 'end', image=settings.treeview.item(child)['image'],
                                                  text=settings.treeview.item(child)['text'],
                                                  values=settings.treeview.item(child)['values'],
                                                  tags=settings.treeview.item(child)['tags'])
                    self.getsubchildren(item, child)
                except Exception as e:
                    print(e)
                    print(settings.treeview.item(child))
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
            print({e})
            pass
