import sys, os, socket, json

def get_message(sock):
  message = ''
  sock.settimeout(3)
  while True:
    try:
      m = sock.recv(1024).decode()
      if not m:
        break
      message += m
    except:
      break
  message = json.loads(message)
  return message

def init(server, port):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    s.send('init'.encode())
    message = get_message(s)
    if message['ok']:
      min_free = None
      for storage in message['storages']:
        server, port = storage.split(' ')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
          st.connect((server, int(port)))
          st.send('init'.encode())
          free = int(st.recv(1024).decode())
          if not min_free or free < min_free:
            min_free = free
      print(min_free, 'bytes free')
      return True
  return False

def create_file(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'touch ' + rel_path
    s.send(message.encode())
    message = get_message(s)
    if message['ok']:
      for storage in message['storages']:
        server, port = storage.split(' ')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
          st.connect((server, int(port)))
          msg = 'touch ' + message['uuid']
          st.send(msg.encode())
      return True
  return False

def read_file(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'get ' + rel_path
    s.send(message.encode())
    message = get_message(s)
    if message['ok']:
      server, port = message['storage'].split(' ')
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
        st.connect((server, int(port)))
        msg = 'get ' + message['uuid']
        st.send(msg.encode())
        st.settimeout(3)
        with open(os.path.basename(rel_path), 'wb') as fs:
          while True:
            try:
              data = st.recv(1024)
              if not data:
                break
              fs.write(data)
            except:
              break
          return True
  return False

def write_file(server, port, local_path, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'put ' + os.path.basename(local_path) + ' ' + rel_path
    s.send(message.encode())
    message = get_message(s)
    if message['ok']:
      for storage in message['storages']:
        server, port = storage.split(' ')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
          st.connect((server, int(port)))
          msg = 'put ' + message['uuid']
          st.send(msg.encode())
          st.recv(1024)
          with open(local_path, 'rb') as fs:
            while True:
              data = fs.read(1024)
              if not data:
                break
              st.send(data)
            return True
  return False

def delete(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'rm ' + rel_path
    s.send(message.encode())
    message = get_message(s)
    if message['ok']:
      if 'uuids' in message:
        confirm = input('%s not empty. Are you sure (y/n)? ' % (rel_path))
        if confirm == 'y' or confirm == 'yes':
          s.send('y'.encode())
          for uuid in message['uuids']:
            for storage in message['storages']:
              server, port = storage.split(' ')
              with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
                st.connect((server, int(port)))
                msg = 'rm ' + uuid
                st.send(msg.encode())
          return True
        else:
          s.send('n'.encode())
      else:
        if 'uuid' in message:
          for storage in message['storages']:
            server, port = storage.split(' ')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
              st.connect((server, int(port)))
              msg = 'rm ' + message['uuid']
              st.send(msg.encode())
        return True
  return False

def get_file_info(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'info ' + rel_path
    s.send(message.encode())
    message = get_message(s)
    if message['ok']:
      server, port = message['storage'].split(' ')
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
        st.connect((server, int(port)))
        msg = 'info ' + message['uuid']
        st.send(msg.encode())
        msg = get_message(st)
        print('%s\t %d bytes\t %s\t %s' %(msg['mode'], msg['size'], msg['mtime'], rel_path))
        return True
  return False

def copy_file(server, port, src_rel_path, dst_rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'cp ' + src_rel_path + ' ' + dst_rel_path
    s.send(message.encode())
    message = get_message(s)
    if message['ok']:
      src_uuid, dst_uuid = message['uuids']
      for storage in message['storages']:
        server, port = storage.split(' ')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
          st.connect((server, int(port)))
          msg = 'cp ' + src_uuid + ' ' + dst_uuid
          st.send(msg.encode())
      return True
  return False

def move_file(server, port, src_rel_path, dst_rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'mv ' + src_rel_path + ' ' + dst_rel_path
    s.send(message.encode())
    status = s.recv(1024).decode()
    if status == 'ok':
      return True
  return False

def get_path(root, new):
  return os.path.normpath(os.path.join(root, new))

def open_dir(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'cd ' + rel_path
    s.send(message.encode())
    status = s.recv(1024).decode()
    if status == 'ok':
      return True
  return False

def read_dir(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'ls ' + rel_path
    s.send(message.encode())
    message = get_message(s)
    if message['ok']:
      for d in message['dirs']:
        print('\033[1m' + d + '\033[0m', end='\t')
      for f in message['files']:
        print(f, end='\t')
      print()
      return True
  return False

def make_dir(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'mkdir ' + rel_path
    s.send(message.encode())
    status = s.recv(1024).decode()
    if status == 'ok':
      return True
  return False

def help():
  print("""Miscellaneous:
  init                   Initalize storage
  help                   Show help
  exit                   Exit

File actions:
  touch files...         Create empty files in DFS
  get files...           Download files from DFS
  put src dst            Upload local file to DFS
  rm files...            Remove files from DFS
  info files...          Get files' information
  cp src dst             Copy a file from src to dst
  mv src dst             Move a file from src to dst

Directory actions:
  cd dir                 Change working directory
  ls dir                 List a directory
  mkdir dirs...          Make empty directories
  rm dirs...             Remove directories""")

def greeting():
  print("""First time connect to the server? Type:
      \033[1minit\033[0m
For help, type:
      \033[1mhelp\033[0m""")

def main():
  if len(sys.argv) != 3:
    print('Usage:', sys.argv[0], 'server port')
    sys.exit(1)
  home = '/'
  server, port = sys.argv[1:]
  try:
    port = int(port)
  except:
    print('port must be an integer')
    sys.exit(1)

  greeting()

  while True:
    command = input('\033[92mclient\033[0m:\033[94m%s\033[0m$ ' % home).split()
    if (len(command)) == 0:
      continue
    if command[0] == 'help':
      help()
    elif command[0] == 'exit':
      break
    elif command[0] == 'init':
      if len(command) != 1:
        print('Usage: init')
      else:
        if not init(server, port):
          print('Failed to initalize storage')
    elif command[0] == 'touch':
      if len(command) < 2:
        print('Usage: touch files...')
      else:
        for f in command[1:]:
          rel_path = get_path(home, f)
          if not create_file(server, port, rel_path):
            print('Failed to create', f)
          else:
            print(f, 'created')
    elif command[0] == 'get':
      if len(command) < 2:
        print('Usage: get files...')
      else:
        for f in command[1:]:
          rel_path = get_path(home, f)
          if not read_file(server, port, rel_path):
            print('Failed to download', f)
          else:
            print(f, 'downloaded')
    elif command[0] == 'put':
      if len(command) != 3:
        print('Usage: put local_file file')
      else:
        if not os.path.isfile(command[1]):
          print(command[1], 'not exist')
        else:
          dst_rel_path = get_path(home, command[2])
          if not write_file(server, port, command[1], dst_rel_path):
            print('Failed to upload', command[1])
          else:
            print(command[1], 'uploaded')
    elif command[0] == 'rm':
      if len(command) < 2:
        print('Usage: rm files... | directories...')
      else:
        for t in command[1:]:
          rel_path = get_path(home, t)
          if not delete(server, port, rel_path):
            print('Failed to delete', t)
          else:
            print(t, 'deleted')
    elif command[0] == 'info':
      if len(command) < 2:
        print('Usage: info files...')
      else:
        for f in command[1:]:
          rel_path = get_path(home, f)
          if not get_file_info(server, port, rel_path):
            print('Failed to get', f, 'info')
    elif command[0] == 'cp':
      if len(command) != 3:
        print('Usage: cp src dst')
      else:
        src_rel_path = get_path(home, command[1])
        dst_rel_path = get_path(home, command[2])
        if not copy_file(server, port, src_rel_path, dst_rel_path):
          print('Failed to copy from', command[1], 'to', command[2])
        else:
          print(command[1], 'coppied')
    elif command[0] == 'mv':
      if len(command) != 3:
        print('Usage: mv src dst')
      else:
        src_rel_path = get_path(home, command[1])
        dst_rel_path = get_path(home, command[2])
        if not move_file(server, port, src_rel_path, dst_rel_path):
          print('Failed to move', command[1], 'to', command[2])
        else:
          print(command[1], 'moved')
    elif command[0] == 'cd':
      if len(command) > 2:
        print('Usage: cd dir')
      else:
        rel_path = get_path(home, command[1])if len(command) == 2 else '/'
        if not open_dir(server, port, rel_path):
          print('Failed to change to', command[1])
        else:
          home = rel_path
    elif command[0] == 'ls':
      if len(command) > 2:
        print('Usage: ls dir')
      else:
        rel_path = get_path(home, command[1] if len(command) == 2 else '.')
        if not read_dir(server, port, rel_path):
          print('Failed to list', command[1])
    elif command[0] == 'mkdir':
      if len(command) < 2:
        print('Usage: mkdir dirs...')
      else:
        for d in command[1:]:
          rel_path = get_path(home, d)
          if not make_dir(server, port, rel_path):
            print('Failed to create', d)
          else:
            print(d, 'created')
    else:
      print('Command not found')

if __name__ == '__main__':
  main()
