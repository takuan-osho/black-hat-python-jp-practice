#!/usr/bin/env python3

import sys
import os

import win32con
import win32api
import win32security

import wmi

def get_process_privileges(pid):
    try:
        # 対象のプロセスへのハンドルを取得
        hproc = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION, False, pid)

        # メインのプロセストークンを開く
        htok = win32security.OpenProcessToken(hproc, win32con.TOKEN_QUERY)

        # 有効化されている権限のリストを取得
        privs = win32security.GetTokenInformation(
            htok, win32security.TokenPrivileges)

        # 権限をチェックして、有効化されているものだけを出力するループ
        priv_list = ''
        for i in privs:
            # 権限が有効化されているかチェック
            if i[1] == 3:
                priv_list += '%s' % win32security.LookupPrivilegeName(None, i[0])
    except:
        priv_list = 'N/A'
    return priv_list

def log_to_file(message, filename):
    with open(filename, 'a') as fd:
        fd.write('%s\r\n' % message)

log_to_file('Time,User,Executable,CommandLine,PID,Parent PID,Privileges',
    'process_monitor_log.csv')

c = wmi.WMI()

process_watcher = c.Win32_Process.watch_for('creation')

vulnerable_privileges = [
    'SeBackupPrivilege', 'SeDebugPrivilege', 'SeLoadDriverPrivilege'
]

while True:
    try:
        new_process = process_watcher()
        proc_owner = new_process.GetOwner()
        proc_owner = '%s\\%s' % (proc_owner[0], proc_owner[2])
        create_date = new_process.CreationDate
        executable = new_process.ExecutablePath
        cmdline = new_process.CommandLine
        pid = new_process.ProcessId
        parent_pid = new_process.ParentProcessId

        privileges = get_process_privileges(pid)

        process_log_message = '%s,%s,%s,%s,%s,%s,%s\r\n' % (create_date,
            proc_owner, executable, cmdline, pid, parent_pid, privileges)
        print(process_log_message)
        log_to_file(process_log_message, 'process_monitor_log.csv')

        if privileges in vulnerable_privileges:
            print("Catched a vulnerable privilege!!!")
            log_to_file(process_log_message, 'process_monitor_log_vul_prv.csv')
    except:
        pass
