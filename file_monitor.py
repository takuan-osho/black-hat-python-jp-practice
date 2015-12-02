#!/usr/bin/env python3

import tempfile
import threading
import win32file
import win32con
import os

dirs_to_monitor = ['C:\\WINDOWS\\TEMP', tempfile.gettempdir()]

file_monitor_log_filename = 'file_monitor_log.txt'

# ファイルへの変更に関する定数
FILE_CREATED = 1
FILE_DELETED = 2
FILE_MODIFIED = 3
FILE_RENAMED_FROM = 4
FILE_RENAMED_TO = 5

def log_to_file(message, filename):
    with open(filename, 'a') as fd:
        fd.write('%s\r\n' % message)

def start_monitor(path_to_watch):
    # フォルダを監視するスレッド本体
    FILE_LIST_DIRECTORY = 0x0001

    h_directory = win32file.CreateFile(
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
    )

    while 1:
        try:
            results = win32file.ReadDirectoryChangesW(
                h_directory,
                1024,
                True,
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                    win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                    win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                    win32con.FILE_NOTIFY_CHANGE_SIZE |
                    win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                    win32con.FILE_NOTIFY_CHANGE_SECURITY,
                None,
                None
            )
            for action, file_name in results:
                full_filename = os.path.join(path_to_watch, file_name)
                if action == FILE_CREATED:
                    message = '[ + ] Created %s' % full_filename
                elif action == FILE_DELETED:
                    message = '[ - ] Deleted %s' % full_filename
                elif action == FILE_MODIFIED:
                    message = '[ * ] Modified %s' % full_filename
                    print(message)
                    log_to_file(message, file_monitor_log_filename)
                    # ファイル内容のダンプ出力
                    message = '[vvv] Dumping contents...'
                    print(message)
                    log_to_file(message, file_monitor_log_filename)
                    try:
                        with open(full_filename, 'rb') as fd:
                            contents = fd.read()
                            print(contents.decode('cp932'))
                            log_to_file(contents.decode('cp932'),
                                file_monitor_log_filename)
                            message = '[^^^] Dump complete.'
                            print(message)
                            log_to_file(message, file_monitor_log_filename)
                    except Exception as e:
                        message = '[!!!]Failed.'
                        print(message)
                        log_to_file(message, file_monitor_log_filename)

                        print(e)
                        log_to_file(e, file_monitor_log_filename)
                    continue
                elif action == FILE_RENAMED_FROM:
                    message = '[ > ] Renamed from: %s' % full_filename
                elif action == FILE_RENAMED_TO:
                    message = '[ < ] Renamed to: %s' % full_filename
                else:
                    message = '[???] Unknown: %s' % full_filename
                print(message)
                log_to_file(message, file_monitor_log_filename)
        except:
            pass

for path in dirs_to_monitor:
    monitor_thread = threading.Thread(target=start_monitor, args=(path,))
    print('Spawning monitoring thread for path: %s' % path)
    monitor_thread.start()
