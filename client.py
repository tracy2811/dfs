# client.py

# Import libraries
import sys, os, socket, json

# Get message
def get_message(sock):
  message = ''
  while True:
    m = sock.recv(1024).decode()
    if not m:
      break
    message += m
  message = json.loads(message)
  return message

# Client Initialization
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

# Create file
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

# Read file
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
        with open(os.path.basename(rel_path), 'wb') as fs:
          while True:
            data = st.recv(1024)
            if not data:
              break
            fs.write(data)
          return True
  return False

# Write file
def write_file(server, port, local_path, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'put ' + rel_path
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

# Delete file
def delete(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'rm ' + rel_path
    s.send(message.encode())
    status = s.recv(1024).decode()
    if status == 'ok':
      return True
    if status == 'confirm':
      confirm = input('Are you sure (y/n)? ')
      if confirm == 'y' or confirm == 'yes':
        s.send('y'.encode())
        message = get_message(s)
        for uuid in message['uuids']:
          for storage in message['storages']:
            server, port = storage.split(' ')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
              st.connect((server, int(port)))
              msg = 'rm ' + uuid
              st.send(msg.encode())
        return True
      return False
  return False

# Get information about file
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
        print('%s\t %d bytes\t %s' %(msg['mode'], msg['size'], msg['mtime']))
        return True
  return False

# Copy file
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

# Move file
def move_file(server, port, src_rel_path, dst_rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'mv ' + src_rel_path + ' ' + dst_rel_path
    s.send(message.encode())
    status = s.recv(1024).decode()
    if status == 'ok':
      return True
  return False

# Get path
def get_path(root, new):
  return os.path.normpath(os.path.join(root, new))

# Open directory
def open_dir(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'cd ' + rel_path
    s.send(message.encode())
    status = s.recv(1024).decode()
    if status == 'ok':
      return True
  return False

# Read directory
def read_dir(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'ls ' + rel_path
    s.send(message.encode())
    message = get_message(s)
    if message['ok']:
      for d in message['dirs']:
        print('\033[1m' + d + '\033[0m')
      for f in message['files']:
        print(f)
      return True
  return False

# Make new directory
def make_dir(server, port, rel_path):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, port))
    message = 'mkdir ' + rel_path
    s.send(message.encode())
    status = s.recv(1024).decode()
    if status == 'ok':
      return True
  return False

# Create help command for client
def help():
  print("""
  Initialize:
      init
  File actions:
      touch file             Create empty file in DFS
      get file               Download file from DFS
      put local_file file    Upload local file to DFS
      rm file                Remove file from DFS
      info file              Get file's info
      cp src dst             Copy a file
      mv src dst             Move a file
  Directory actions:
      cd dir                 Change working directory
      ls dir                 List files inside directory
      mkdir dir              Make empty directory
      rm dir                 Remove directory
  Miscellaneous:
      help
      exit
  """)

# Main method
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

  while True:
    command = input('client:%s$ ' % home)
    command = str.strip(command).split(' ')
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
          print('Failed')
    elif command[0] == 'touch':
      if len(command) != 2:
        print('Usage: touch file')
      else:
        rel_path = get_path(home, command[1])
        if not create_file(server, port, rel_path):
          print('Failed')
        else:
          print(command[1], 'created')
    elif command[0] == 'get':
      if len(command) != 2:
        print('Usage: get file')
      else:
        rel_path = get_path(home, command[1])
        if not read_file(server, port, rel_path):
          print('Failed')
        else:
          print(command[1], 'downloaded')
    elif command[0] == 'put':
      if len(command) != 3:
        print('Usage: put local_file file')
      else:
        if not os.path.isfile(command[1]):
          print('No such a file')
        else:
          dst_rel_path = get_path(home, command[2])
          if not write_file(server, port, command[1], dst_rel_path):
            print('Failed')
          else:
            print(command[1], 'uploaded')
    elif command[0] == 'rm':
      if len(command) != 2:
        print('Usage: rm file | directory')
      else:
        rel_path = get_path(home, command[1])
        if not delete(server, port, rel_path):
          print('Failed')
        else:
          print(command[1], 'deleted')
    elif command[0] == 'info':
      if len(command) != 2:
        print('Usage: info file')
      else:
        rel_path = get_path(home, command[1])
        if not get_file_info(server, port, rel_path):
          print('Failed')
    elif command[0] == 'cp':
      if len(command) != 3:
        print('Usage: cp src dst')
      else:
        src_rel_path = get_path(home, command[1])
        dst_rel_path = get_path(home, command[2])
        if not copy_file(server, port, src_rel_path, dst_rel_path):
          print('Failed')
        else:
          print(command[1], 'coppied')
    elif command[0] == 'mv':
      if len(command) != 3:
        print('Usage: mv src dst')
      else:
        src_rel_path = get_path(home, command[1])
        dst_rel_path = get_path(home, command[2])
        if not move_file(server, port, src_rel_path, dst_rel_path):
          print('Failed')
        else:
          print(command[1], 'moved')
    elif command[0] == 'cd':
      if len(command) != 2:
        print('Usage: cd dir')
      else:
        rel_path = get_path(home, command[1])
        if not open_dir(server, port, rel_path):
          print('No such a directory')
        else:
          home = rel_path
    elif command[0] == 'ls':
      if len(command) != 2:
        print('Usage: ls dir')
      else:
        rel_path = get_path(home, command[1])
        if not read_dir(server, port, rel_path):
          print('Failed')
    elif command[0] == 'mkdir':
      if len(command) != 2:
        print('Usage: touch file')
      else:
        rel_path = get_path(home, command[1])
        if not make_dir(server, port, rel_path):
          print('Failed')
        else:
          print(command[1], 'created')
    else:
      print('Command not found')

if __name__ == '__main__':
  main()
