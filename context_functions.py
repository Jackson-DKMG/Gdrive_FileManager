#All functions to handle the file operations (upload, copy, move, download, delete, star)
#Kinda blown out of proportions due to adding features.
#Lots of comments though, so hopefully it remains understandable.

from json import dump
from os import mkdir, path
from threading import Thread, active_count
from time import sleep
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import settings

class contextFunctions(Thread):
    def __init__(self):
        super().__init__()

    def exportGApps(self,name,id,type, targetdir=None):
        settings.fileDownloading = name
        try:
            if 'Document' in type:
                mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ext = 'docx'
            elif 'Form' in type:
                mimeType = 'application/zip'
                ext = 'zip'
            elif 'Spreadsheet' in type:
                mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ext = 'xlsx'
            elif 'Presentation' in type:
                mimeType = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                ext = 'pptx'
            elif 'Image' in type:
                mimeType = 'image/jpeg'
                ext = 'jpeg'
            else:
                raise Exception('unknown file type')
                pass
            if name.startswith(" "):
                name = name[1:].replace('?', '').replace('/', '-')
            else:
                name = name.replace('?', '').replace('/', '-')

            request = settings.drive.files().export_media(fileId=id, mimeType=mimeType).execute()
            filename = ('{0}.{1}').format(name,ext)
            if targetdir == None:
                filepath = path.join(settings.downloadFolder, filename)
            else:
                filepath = path.join(settings.downloadFolder, targetdir, filename)
            with open(filepath, 'wb') as f:
                f.write(request)

        except Exception as e:
            #print(name, {e})
            settings.error = 'Cannot download {0}: {1}. Please try to download it directly from GDrive'.format(name,type)
            sleep(3)
            settings.error = 'Original error is : {0}'.format(str(e))
            sleep(3)
            settings.error = ''
            pass

    def download(self,items, targetdir=None):
        settings.downloadIsRunning = True
        for i in items:
            try:
                if 'Google Apps' in i['values'][0]:#if they're gapps docs, can't download directly, must export to another format.
                    id = i['tags'][1]
                    if i['text'].startswith(" "):
                        name = i['text'][1:].replace('?', '').replace('/', '-')
                    else:
                        name = i['text'].replace('?', '').replace('/','-')  # there's a space at the beginning of each name (for readability purposes on the main window). Remove it.
                    type = i['values'][0]
                    self.exportGApps(name, id, type, targetdir=targetdir)
                elif 'Folder' in i['values'][0]:
                    if i['text'].startswith(" "):
                        name = i['text'][1:].replace('?', '').replace('/', '-')
                    else:
                        name = i['text'].replace('?', '').replace('/', '-')
                    id = i['tags'][1]
                    self.downloadFolder(name, id)
                else:
                    self.downloadFile(i, targetdir=targetdir)
            except Exception as e:
                try:
                    settings.error = i['text'] + ': ' + str(e).split('"')[1].split('"')[0]
                except:
                    settings.error = i['text'] + ': ' + str(e)
                sleep(3)
                settings.error = ''
                pass

        settings.downloadIsRunning = False

    def downloadFile(self,file,targetdir=None):

        try:
            settings.fileDownloadingSize = file['values'][1] #[s for s in items if fileIDs[i] in str(s)][0]['values'][1]
            settings.fileDownloading = file['text']
            request = settings.drive.files().get_media(fileId=file['tags'][1])
            fh = BytesIO()#(settings.downloadFolder + i, 'wb')
            downloader = MediaIoBaseDownload(fh, request) #, chunksize=20000000)
            #if using the chunksize parameter, it allows to get the download progress, however the download speed is significantly reduced (+10s for a 50MB file
            #with a chunk size of 10 MB). The smaller the chunk size, the slower the download.
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            #print("%d%%." % int(status.progress() * 100), downloader._progress, downloader._total_size)
        except Exception as e:
                        #print('Download error:', {e})
                        try:
                            settings.error = file['text'] + ': ' + str(e).split('"')[1].split('"')[0]
                        except:
                            settings.error = file['text'] + ': ' + str(e)
                        sleep(3)
                        settings.error = ''
                        pass
        if file['text'].startswith(" "):
            filename = file['text'][1:].replace('?', '').replace('/', '-')
        else:
            filename = file['text'].replace('?', '').replace('/', '-')

        try:
            if targetdir == None:
                filepath = path.join(settings.downloadFolder, filename)
            else:
                filepath = path.join(settings.downloadFolder, targetdir, filename)
            with open(filepath, 'wb') as f:
                f.write(fh.getbuffer())

        except Exception as e:
            settings.error = 'FileWrite error:', str({e})
            sleep(3)
            settings.error = ''
            pass

    def downloadFolder(self,folderName,folderId):
        # start by creating the folder
        try:
            mkdir(path.join(settings.downloadFolder, folderName))
        except OSError as e:
            if 'FileExists' in str(e): #if the directory exists already, nevermind and continue
                pass
            elif 'Permission denied'in str(e): #more annoying if can't write to disk. Abort.
                settings.downloadIsRunning = False
                settings.error = ('Cannot write to directory. Please check the permissions and retry.')
                sleep(5)
                settings.error = ''
        #get all files within that folder and download them:
        trashedStatus = settings.treeview.item(settings.directory[folderId])['values'][4]
        for i in settings.files:
            try:
                if i['parents'][0] == folderId and str(i['trashed']) == trashedStatus:
                            filedata = {}
                            filedata['text'] = i['name'].replace('?', ' ').replace('/', '-')
                            try:
                                size = i['size'] #google apps files don't have a size
                            except:
                                size = None
                            attributes = self.getMimeAndSize(i['mimeType'],size)
                            filedata['values'] = [attributes[0], attributes[1]]
                            filedata['tags'] = [folderId, i['id']]
                            self.download([filedata], targetdir=folderName)
            except:
                pass
        #Now need to find all the subfolders, and their subfolders...
        #Make a list to associate each subfolder with its parent. Once the list is complete (= no more subfolders),
        #download from the top and place each folder at its place.
        #Fuck.

        childrenFolders = []
        for i in settings.folders:
            try:
                if i['parents'][0] == folderId:
                    childrenFolders.append([i['id'], i['parents'][0], i['name']])
            except:
                pass
        for i in childrenFolders:
            #print(i)
            self.downloadFolder(folderName +'/' + i[2], i[0])
        #ça marche, mais je comprends pas pourquoi...

    def getMimeAndSize(self, mime, value):

        if 'image' in mime:
            type = 'Image'
            icon = settings.imageIcon
        elif 'folder' in mime:
            type = 'Folder'
            icon = settings.folderIcon
        elif 'video' in mime:
            type = 'Video'
            icon = settings.videoIcon
        elif 'pdf' in mime:
            type = 'PDF'
            icon = settings.pdfIcon
        elif 'opendocument.text' in mime:
            type = 'OpenOffice Writer'
            icon = settings.writerIcon
        elif 'opendocument.spreadsheet' in mime:
            type = 'OpenOffice Calc'
            icon = settings.spreadsheetIcon
        elif 'officedocument.word' in mime:
            type = 'Microsoft Word'
            icon = settings.wordIcon
        elif any(x in mime for x in ['officedocument.spreadsheet', 'csv']):
            type = 'Microsoft Excel'
            icon = settings.excelIcon
        elif 'shortcut' in mime:
            type = 'Shortcut'
            icon = settings.shortcutIcon
        elif any(x in mime for x in ['zip', 'x-tar']):
            type = 'Archive'
            icon = settings.compressedIcon
        elif 'google-apps' in mime:  #need to get the actual type, for the download/export function
            if 'form' in mime:
                type = 'Google Apps Form'
            elif 'spreadsheet' in mime:
                type = 'Google Apps Spreadsheet'
            elif  'presentation' in mime:
                type = 'Google Apps Presentation'
            elif 'drawing' in mime or 'photo' in mime:# or 'photo' in mime:
                type = 'Google Apps Image'
            elif 'document' in mime:
                type = 'Google Apps Document'
            else:
                type = 'Google Apps Other'
            icon = settings.gappsIcon
        elif 'audio' in mime:
            type = 'Audio File'
            icon = settings.audioIcon

        else:
            type = 'Document'
            icon = settings.documentIcon

        size = ''
        if value != None:
            try:
                value = int(value)
                if 0 <= value < 1000:
                    size = str(value) + ' B'
                    #return size
                elif 1000 <= value < 100000:
                    size = str(round(value/1000, 2)) + ' KB'

                elif 100000 <= value < 1000000000:
                    size = str(round(value/1000000, 2)) + ' MB'
                #return size
                elif value >= 1000000000:
                    size = str(round(value/1000000000, 2)) + ' GB'
                #return size
            except:
                size = 'Unknown'

        return (type, size, icon)


    def copy(self, items, targetFolder):
        settings.copyInProgress = True
        batch = settings.drive.new_batch_http_request(callback=self.callback)
        counter = 0
        for i in items:  # should be a list
            settings.itemCopying = i['text']

            if 'Folder' in i['values'][0]:
                # if it's a folder, will have to recreate it : folders can't be copied and aren't folders anyway.
                if i['text'].startswith(" "):
                    sourceFolderName = i['text'][1:].replace('?', '').replace('/', '-')
                else:
                    sourceFolderName = i['text'].replace('?', '').replace('/', '-')

                sourceFolderID = i['tags'][1]  # however I'll need its ID for later.

                try:
                    targetFolderID = targetFolder['tags'][1]  # the parent of the new folder
                except:
                    targetFolderID = 'root'  # faster like that. #targetFolder['tags'][0] #if the target is the root.

                targetID = self.createFolder(sourceFolderName, targetFolderID)  # the ID of the new folder.
                # needed to copy the files from original folder to destination afterwards
                # copy the files now

                for j in settings.files:

                    try:
                        if (j['parents'][0] == sourceFolderID and str(j['trashed']) == i['values'][4]):
                            settings.itemCopying = j['name']
                            #print(j['name'])
                            if j['name'].startswith(" "):
                                filename = j['name'][1:].replace('?', '').replace('/', '-')
                            else:
                                filename = j['name'].replace('?', '').replace('/', '-')
                            body = {'name': filename, 'parents': [targetID]}
                            batch.add(settings.drive.files().copy(fileId=j['id'], body=body))
                            counter += 1

                        if counter > 9:
                            batch.execute()
                            batch = settings.drive.new_batch_http_request(callback=self.callback)
                            counter = 0

                    except:
                        pass

                try:
                    Thread(target=batch.execute()).start()  # execute the copy of these files
                except:
                    pass

                batch = settings.drive.new_batch_http_request(callback=self.callback)
                # Now copy the folders within the source folder and their files, and keep recursing.
                childrenFolders = []
                for k in settings.folders:
                    try:
                        if k['parents'][0] == sourceFolderID:
                            folder = settings.treeview.item(settings.directory[k['id']]) #[key for key in settings.directory if settings.directory[key] == k['id']][0]
                            #print(x)
                            #folder = {}
                            #folder['text'] = k['name']
                            #folder['values'] = k['values']
                            folder['tags'] = [None, k['id']]
                            childrenFolders.append(folder)
                    except:  # just a KeyError when there is no parents[0]
                        pass
                for i in childrenFolders:
                    settings.itemCopying = i['text']
                    target = {}
                    target['tags'] = [None, targetID]
                    # now, to copy each folder's files into the destination one.
                    settings.copyInProgress = True
                    #Thread(target=self.copy, args=([i], target)).start()
                    self.copy([i], target)

            else:
                settings.itemCopying = i['text']
                if i['text'].startswith(" "):
                    filename = i['text'][1:].replace('?', '').replace('/', '-')
                else:
                    filename = i['text'].replace('?', '').replace('/', '-')
                try:
                    targetFolderID = targetFolder['tags'][1]
                except:
                    targetFolderID = 'root'
                body = {'name': filename, 'parents': [targetFolderID]}
                batch.add(settings.drive.files().copy(fileId=i['tags'][1], body=body))
                counter += 1

                if counter > 9:
                    batch.execute()
                    batch = settings.drive.new_batch_http_request(callback=self.callback)
                    counter = 0

        try:
            batch.execute()
        except:
            pass

        settings.itemCopying = ""
        settings.copyInProgress = False
        Thread(target=self.updateFiles).start()

    def callback(self, request_id, response, exception):
        print(response.get())
        if exception:
            # Handle error
            settings.error = str(exception).split('"')[1].split('"')[0]
            sleep(3)
            settings.error = ""
            pass
        else:
            filedata = settings.drive.files().get(fileId=response.get('id'),fields='name, id, parents, trashed, size, mimeType, modifiedTime, starred, ownedByMe, '
                                                         'shared, owners/displayName, shortcutDetails/targetId,shortcutDetails/targetMimeType').execute()
            settings.files.append(filedata)

    def callback2(self, request_id, response, exception):
        if exception:
            # Handle error
            settings.error = str(exception).split('"')[1].split('"')[0]
            sleep(3)
            settings.error = ""
            pass

    def createFolder(self,folderName, parentID, treeRef=None):
        try:
            metadata = {'name': folderName, 'parents': [parentID], 'mimeType': 'application/vnd.google-apps.folder'}
            folder = settings.drive.files().create(body=metadata, fields='id').execute()
            #need to update the treeview now, to avoid having to refresh the data.
            filedata = settings.drive.files().get(fileId=folder.get('id'),fields='name, id, parents, trashed, size, mimeType, modifiedTime, starred, ownedByMe, '
                                                         'shared, owners/displayName, shortcutDetails/targetId,shortcutDetails/targetMimeType').execute()

            #modified = datetime.utcfromtimestamp(time()).strftime('%d/%m/%y %H:%m')

            if not treeRef:
                for key in settings.directory:
                    if parentID in key:
                        treeRef = settings.directory[key]
            settings.directory[filedata['id']] = settings.treeview.insert(treeRef, 'end',image=settings.folderIcon,
                                        text=' ' + folderName, values=('Folder', filedata['modifiedTime'], settings.owner, 'False', 'False'),tags=(parentID, filedata['id']))

            settings.folders.append(filedata)

            Thread(target=self.updateFiles).start()

            return filedata['id']

        except Exception as e:
            settings.error = folderName + ': ' + str(e)
            sleep(3)
            settings.error = ''
            pass

    def move(self,items,targetFolder):  #Just need to update the parentID, and the folder/file is moved instantly.
        settings.moveInProgress = True
        batch = settings.drive.new_batch_http_request(callback=self.callback2)
        counter = 0
        try:
            targetFolderID = targetFolder['tags'][1]  #the id of the new folder
        except:
            targetFolderID = 'root'  # faster like that. #targetFolder['tags'][0] #if the target is the root.
        for i in items:  # should be a list
            try:
                settings.itemMoving = i['text']  #don't care whether a file or a folder
                #now to update the treeview and the directory, or settings.files
                if 'Folder' in i['values'][0]:
                    #single folder, no point using a batch
                    settings.drive.files().update(fileId=i['tags'][1], addParents=targetFolderID,removeParents=i['tags'][0]).execute()

                    x = [y for y in settings.folders if y['id'] == i['tags'][1]][0]
                    x['parents'] = targetFolderID


                    newparent = settings.directory[targetFolderID]
                    for key in settings.directory:
                        if i['tags'][1] in key:  #update directory entry with new data, and insert into the treeview.
                           # newdata = settings.treeview.item(settings.directory[i['tags'][1]])
                            oldentry = settings.directory[i['tags'][1]]
                            settings.treeview.move(oldentry, newparent, 'end')
                            settings.treeview.item(oldentry, tags=(targetFolderID, i['tags'][1]))
                            break

                else:
                    #maybe multiple files, so batch.
                    counter += 1
                    batch.add(settings.drive.files().update(fileId=i['tags'][1], addParents=targetFolderID,removeParents=i['tags'][0]))
                    for j in range(len(settings.files)):
                        if settings.files[j]['id'] == i['tags'][1]:
                            if targetFolderID == 'root':
                                targetFolderID = settings.rootID
                            settings.files[j]['parents'][0] = targetFolderID
                            for k in settings.contentview.get_children():
                                if settings.files[j]['id'] in str(settings.contentview.item(k)):
                                    settings.contentview.delete(k)
                            break
                    if counter > 9:
                        batch.execute()
                        batch = settings.drive.new_batch_http_request(callback=self.callback2)
                        counter = 0

            except Exception as e:
                try:
                    settings.error = i['text'] + ': ' + str(e).split('"')[1].split('"')[0]
                except:
                    settings.error = i['text'] + ': ' + str(e)
                sleep(3)
                settings.error = ''
                pass

        batch.execute()

        settings.itemMoving = ''
        settings.moveInProgress = False
        Thread(target=self.updateFiles).start()

    def getsubchildren(self, child, attribute, flag):
        try:
            counter = 0
            body = {attribute: flag}
            #print(child, body)
            batch = settings.drive.new_batch_http_request(callback=self.callback2)
            for i in range(len(settings.files)):
                try:
                    if settings.files[i]['parents'][0] == [key for key in settings.directory if settings.directory[key] == child][0]:  # update local data to display in contentview
                        settings.files[i][attribute] = flag
                        batch.add(settings.drive.files().update(fileId=settings.files[i]['id'], body=body))
                        for k in settings.contentview.get_children():
                            if settings.files[i]['id'] in str(settings.contentview.item(k)):
                                settings.contentview.delete(k)
                                break
                        counter += 1
                        if counter > 9:
                            batch.execute()
                            batch = settings.drive.new_batch_http_request(callback=self.callback2)
                            counter = 0
                except:
                    pass

            for subchild in settings.treeview.get_children(child):
                for key in settings.directory:
                    if settings.directory[key] == subchild:
                        settings.drive.files().update(fileId=key, body=body).execute()  #no need to add to a batch here, it's a single folder.
                        values = settings.treeview.item(subchild, "values")
                        if attribute == 'trashed':
                            settings.treeview.item(subchild, values=(values[0], values[1], values[2], values[3], str(flag)))  # update local treeview
                        elif attribute == 'starred':
                            settings.treeview.item(subchild,values=(values[0], values[1], values[2], flag, values[4]))
                        x = [y for y in settings.folders if y['id'] == settings.treeview.item(subchild)['tags'][1]][0]
                        x[attribute] = flag
                        for i in range(len(settings.files)):
                            try:
                                if settings.files[i]['parents'][0] == [key for key in settings.directory if settings.directory[key] == child][0]:
                                    settings.files[i][attribute] = flag
                                    batch.add(settings.drive.files().update(fileId=settings.files[i]['id'], body=body))
                                    if attribute == 'trashed':
                                        for k in settings.contentview.get_children():
                                            if settings.files[i]['id'] in str(settings.contentview.item(k)):
                                                settings.contentview.delete(k)
                                                break
                                    counter += 1
                                if counter > 9:
                                    batch.execute()
                                    batch = settings.drive.new_batch_http_request(callback=self.callback2)
                                    counter = 0
                            except:
                                pass

                if settings.treeview.get_children(subchild):
                        batch.execute()
                        batch = settings.drive.new_batch_http_request(callback=self.callback2)
                        self.getsubchildren(subchild, attribute, flag)
        except:
            pass

    def removeRestore(self, items, flag):
        settings.moveInProgress = True
        batch = settings.drive.new_batch_http_request(callback=self.callback2)  # set up the batch object
        body = {'trashed': flag}

        if flag == True:  # remove elements
            counter = 0
            for i in items:
                settings.itemMoving = i['text']

                if 'Folder' in i['values'][0]: #no point using batch if there is only one item.
                    try:
                        settings.drive.files().update(fileId=i['tags'][1], body=body).execute()
                        x = [y for y in settings.folders if y['id'] == i['tags'][1]][0]
                        x['trashed'] = flag

                        counter = 0
                        for j in range(len(settings.files)):  #add files contained in this folder to the batch
                            try:
                                if settings.files[j]['parents'][0] == i['tags'][1]:
                                    batch.add(settings.drive.files().update(fileId=i['tags'][1], body=body))
                                    settings.files[j]['trashed'] = flag
                                    counter += 1

                                if counter > 9:
                                    batch.execute()
                                    batch = settings.drive.new_batch_http_request(callback=self.callback2)
                                    counter = 0
                            except:
                                pass


                        self.getsubchildren(settings.directory[i['tags'][1]], 'trashed', flag)
                        oldentry = settings.directory[i['tags'][1]]
                        values = settings.treeview.item(oldentry, "values")
                        settings.treeview.move(oldentry, settings.directory['trash'], 'end')
                        settings.treeview.item(oldentry, values=(values[0], values[1], values[2], values[3], str(flag)))

                    except FileNotFoundError: #the folder does not exist in the drive.
                        oldentry = settings.directory[i['tags'][1]]
                        settings.treeview.delete(oldentry)
                        pass

                    except Exception as e:
                        if 'File Not Found' in str(e):
                            oldentry = settings.directory[i['tags'][1]]
                            settings.treeview.delete(oldentry)
                        else:
                            try:
                                settings.error = i['text'] + ': ' + str(e).split('"')[1].split('"')[0]
                            except:
                                settings.error = i['text'] + ': ' + str(e)
                            sleep(3)
                            settings.error = ''
                        pass

                else:
                    batch.add(settings.drive.files().update(fileId=i['tags'][1], body=body))
                    for j in settings.files:
                        try:
                            if j['id'] == i['tags'][1]:
                                j['trashed'] = flag
                                for k in settings.contentview.get_children():
                                    if j['id'] in str(settings.contentview.item(k)):
                                        settings.contentview.delete(k)
                                        break
                                break
                            counter += 1

                            if counter > 9:
                                batch.execute()
                                batch = settings.drive.new_batch_http_request(callback=self.callback2)
                                counter = 0
                        except:
                            pass
        else:  # restore elements. Issue is if restoring a children of a deleted folder, not its parent. In that case, it must be restored at root.
            counter = 0
            for i in items:
                settings.itemMoving = i['text']
                id = i['tags'][1]

                if 'Folder' in i['values'][0]:
                    # find its parent and whether trashed or not
                    if i['tags'][0] == settings.rootID:
                        parent = 'root'
                    else:
                        parent = i['tags'][0]
                    #print(settings.treeview.item(settings.directory[parentId]))
                    try:
                        parent = settings.treeview.item(settings.directory[parent])['tags'][1] #just checking for the field. Exception if not present. (Ok, that's if the
                        parentTrashed = settings.treeview.item(settings.directory[parent])['values'][4]   # file was shared and belongs to someone else. Can't see the parent).
                    except:
                        parent = 'root'
                        parentTrashed = 'False'
                    if parentTrashed == 'True':
                        #newparent = settings.directory['root']
                        settings.drive.files().update(fileId=id, body=body, removeParents=parent).execute()
                        x = [y for y in settings.folders if y['id'] == i['tags'][1]][0]
                        x['trashed'] = flag
                        x['parents'] = settings.rootID
                        #removing the parent automatically puts the folder at root.
                        #parent = newparent
                    else:
                        settings.drive.files().update(fileId=id, body=body).execute()

                        x = [y for y in settings.folders if y['id'] == i['tags'][1]][0]
                        x['trashed'] = flag

                    #update treeview
                    oldentry = settings.directory[id]
                    values = settings.treeview.item(oldentry, "values")
                    settings.treeview.move(oldentry, settings.directory[parent], 'end')
                    settings.treeview.item(oldentry, values=(values[0], values[1], values[2], values[3], str(flag)))
                    # now restore the potential subchildren of this folder, and their files.
                    self.getsubchildren(settings.directory[id], 'trashed', flag)

                else:
                    batch.add(settings.drive.files().update(fileId=id, body=body))
                    for j in settings.files:
                        try:
                            if j['id'] == id:
                                j['trashed'] = flag
                                for k in settings.contentview.get_children():
                                    if j['id'] in str(settings.contentview.item(k)):
                                        settings.contentview.delete(k)
                                        break
                                break
                        except:
                            pass
                    counter += 1
                    if counter > 9:
                        batch.execute()
                        batch = settings.drive.new_batch_http_request(callback=self.callback2)
                        counter = 0

        batch.execute()

        settings.itemMoving = ''
        settings.moveInProgress = False
        Thread(target=self.updateFiles).start()

    def rename(self, treeRef, item, newName):

        try:
            if newName:   #don't execute if no new name is provided...
                body = {'name': newName}
                settings.drive.files().update(fileId=item['tags'][1], body=body).execute()
            #now update te treeview. If contentview, update also settings.files ; if treeview update also settings.directory
                if 'treeview2' in str(settings.widget):
                    for i in range(len(settings.files)):
                        if item['tags'][1] in str(settings.files[i]):
                            settings.files[i]['name'] = newName
                            settings.widget.item(treeRef, text=newName)
                            break
                else:
                    settings.widget.item(treeRef, text=newName)
                    settings.directory[item['tags'][1]] = treeRef

                    x = [y for y in settings.folders if y['id'] == item['tags'][1]][0]
                    x['name'] = newName

                Thread(target=self.updateFiles).start() #bit stupid to load and rewrite the entire file for just one entry.

        except Exception as e:
            settings.error = item['text'] + ': ' + str(e)
            sleep(3)
            settings.error = ''
            pass

    def starUnstar(self, items):
        batch = settings.drive.new_batch_http_request(callback=self.callback2)
        counter = 0
        if len(items) == 1:
            for i in items:
                if [x for x in settings.files+settings.folders if x['id'] == i['tags'][1]][0]['starred']:
                    flag = False
                else:
                    flag = True
                body = {'starred': flag}
                settings.drive.files().update(fileId=i['tags'][1], body=body).execute()
        else:
            for i in items:
                if [x for x in settings.files+settings.folders if x['id'] == i['tags'][1]][0]['starred']:
                    flag = False
                else:
                    flag = True
                body = {'starred': flag}
                batch.add(settings.drive.files().update(fileId=i['tags'][1], body=body))
                counter += 1

                if counter > 9:
                    batch.execute()
                    batch = settings.drive.new_batch_http_request(callback=self.callback2)
                    counter = 0
            batch.execute()

        for i in items:
            if 'Folder' in i['values'][0]:
                data = settings.treeview.item(settings.directory[i['tags'][1]])
                if flag:
                    settings.directory[i['tags'][1] + '-starred'] = settings.treeview.insert(settings.directory['starred'], 'end', text=data['text'], image=data['image'], values=data['values'], tags=data['tags'])
                else:
                    settings.treeview.delete(settings.directory[i['tags'][1]+'-starred'])
                    settings.directory.pop(i['tags'][1]+'-starred')
                    # need to update settings.files/folders too
                x = [y for y in settings.folders if y['id'] == i['tags'][1]][0]
                x['starred'] = flag
                    #and now to update the children

                childrenFolders = []
                for k in settings.folders:
                    try:
                        if k['parents'][0] == i['tags'][1]:
                            folder = settings.treeview.item(settings.directory[k['id']])  # [key for key in settings.directory if settings.directory[key] == k['id']][0]
                            print(folder)
                            folder['starred'] = True
                            childrenFolders.append(folder)
                    except:  # just a KeyError when there is no parents[0]
                        pass
                for i in childrenFolders:
                    # Thread(target=self.copy, args=([i], target)).start()
                    self.starUnstar([i])

            else:
                x = [y for y in settings.files if y['id'] == i['tags'][1]][0]
                x['starred'] = flag
                if not flag:
                    for k in settings.contentview.get_children():
                        if x['id'] in str(settings.contentview.item(k)):
                            settings.contentview.delete(k)

        Thread(target=self.updateFiles).start()

    def upload(self, items, target):  #only files can be uploaded

        settings.moveInProgress = True
        try:
            target = target['tags'][1]
        except:
            target = target['tags'][0]
        #apparently, batch is not supported for upload/download ?
        #have to remove the path and keep the filename only. Assume there are no "/" in the filenames, otherwise well, upload will fail.
        for i in items:
            name = i[0].split('/')[-1]
            size = self.getMimeAndSize('None', i[1])[1]
            settings.itemMoving = "{0}: {1}".format(name, size)
            metadata = {'name': name, 'parents': [target] }
            media = MediaFileUpload(i[0])
            request = settings.drive.files().create(body=metadata, media_body=media).execute()
            filedata = settings.drive.files().get(fileId=request.get('id'),fields='name, id, parents, trashed, size, mimeType, modifiedTime, starred, ownedByMe, '
                                                         'shared, owners/displayName, shortcutDetails/targetId,shortcutDetails/targetMimeType').execute()
            settings.files.append(filedata)

            attributes = self.getMimeAndSize(filedata['mimeType'], filedata['size'])

            settings.contentview.insert('', 'end', image=attributes[2], text=' ' + filedata['name'],values=(attributes[0], attributes[1],filedata['modifiedTime'], filedata['owners'][0]['displayName'],
                                                filedata['shared'], filedata['trashed']), tags=(target, filedata['id']))
        settings.itemMoving = ''
        settings.moveInProgress = False
        Thread(target=self.updateFiles).start()

    def updateFiles(self): #function to dump the folders and settings lists to 'files' where the data loaded on startup is stored. Otherwise, on the next start the modifications won't appear
                            #until the data is updated from Drive.
       #print("Threads:", active_count())
       if active_count() <= 5:  #when copying, if there are subfolders, each copy spawns a new thread. Wait until the last thread is running before executing this function,
                            # otherwise it's ran once per subfolder. For some reason, there are 4 threads running permanently in the application.
            #print("Executing Update. Threads:", active_count())
            with open('files', 'w') as f:
                dump(settings.folders+settings.files, f, indent=2)

