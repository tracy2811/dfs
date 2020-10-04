# naming server
import socket, os, uuid, sys, json
from threading import Thread

storages = []
dirs = []
files = {}

# Thread to listen one particular client
class ClientListener(Thread):
  def __init__(self, sock: socket.socket, addr):
    super().__init__(daemon=True)
    self.sock = sock
    self.addr = addr[0]

  def run(self):
    global storages, dirs, files
    while True:
      command = self.sock.recv(1024).decode()
      if not command and self.storage:
        continue
      command = command.split(' ')
      if command[0] == 'up':
        self.port = command[1]
        self.storage = self.addr + ' ' + self.port
        print('Storage', self.storage, 'up')
        storages.append(self.storage)
      elif command[0] == 'down':
        storages.remove(self.storage)
        print('Storage', self.storage, 'down')
        self.sock.close()
        break
      elif command[0] == 'init':
        if len(storages):
          message = {
            'ok': True,
            'storages': storages
          }
          self.sock.sendall(json.dumps(message).encode())
          dirs = []
          files = {}
        else:
          message = {
            'ok': False,
            'detail': 'No storage'
          }
          self.sock.send(json.dumps(message).encode())
        self.sock.close()
        break
      elif command[0] == 'touch':
        dir = os.path.dirname(command[1])
        if len(storages) and (dir == '/' or (dir in dirs)):
          id = str(uuid.uuid4())
          files[command[1]] =  id
          message = {
            'ok': True,
            'uuid': id,
            'storages': storages
          }
          self.sock.sendall(json.dumps(message).encode())
        else:
          message = {
            'ok': False,
            'detail': 'No storage or directory'
          }
          self.sock.sendall(json.dumps(message).encode())
        self.sock.close()
        break
      elif command[0] == 'get' or command[0] == 'info':
        if len(storages) > 0 and command[1] in files:
          message = {
            'ok': True,
            'uuid': files[command[1]],
            'storage': storages[0],
          }
          self.sock.sendall(json.dumps(message).encode())
        else:
          message = {
            'ok': False,
            'detail': 'No storage or file'
          }
          self.sock.sendall(json.dumps(message).encode())
        self.sock.close()
        break
      elif command[0] == 'put':
        dir = os.path.dirname(command[1])
        if len(storages) > 0 and (dir == '/' or (dir in dirs)):
          id = str(uuid.uuid4())
          files[command[1]] = id
          message = {
            'ok': True,
            'uuid': id,
            'storages': storages
          }
          self.sock.sendall(json.dumps(message).encode())
        else:
          message = {
            'ok': False,
            'detail': 'No storage or directory'
          }
          self.sock.sendall(json.dumps(message).encode())
        self.sock.close()
        break
      elif command[0] == 'rm':
        if len(storages) > 0:
          if command[1] in files:
            self.sock.send('ok'.encode())
            files.pop(command[1], None)
          elif command[1] == '/' or command[1] in dirs:
            subdirs = []
            subfiles = []
            uuids = []
            for dir in dirs:
              if os.path.commonpath([dir, command[1]]) == command[1] and dir != command[1]:
                subdirs.append(dir)
            for f in files:
              if os.path.commonpath([f, command[1]]) == command[1]:
                subfiles.append(f)
                uuids.append(files[f])
            if len(subdirs) > 0 or len(subfiles) > 0:
              self.sock.send('confirm'.encode())
              confirm = self.sock.recv(1024).decode()
              if confirm == 'y':
                message = {
                  'storages': storages,
                  'uuids': uuids
                }
                self.sock.sendall(json.dumps(message).encode())
                for f in subfiles:
                  files.pop(f, None)
                for d in subdirs:
                  dirs.remove(d)
                dirs.remove(command[1])
            else:
              dirs.remove(command[1])
              self.sock.send('ok'.encode())
          else:
            self.sock.send('failed'.encode())
        else:
          self.sock.send('failed'.encode())
        self.sock.close()
        break
      elif command[0] == 'cp':
        dir = os.path.dirname(command[2])
        if len(storages) > 0 and command[1] in files and (dir == '/' or (dir in dirs)):
          id = str(uuid.uuid4())
          files[command[2]] =  id
          message = {
            'ok': True,
            'uuids': [files[command[1]], id],
            'storages': storages
          }
          self.sock.sendall(json.dumps(message).encode())
        else:
          message = {
            'ok': False,
            'detail': 'No storage, file or directory'
          }
          self.sock.sendall(json.dumps(message).encode())
        self.sock.close()
        break
      elif command[0] == 'mv':
        dir = os.path.dirname(command[2])
        if len(storages) > 0 and command[1] in files and (dir == '/' or (dir in dirs)):
          if command[2] in dirs:
            f = os.path.join(command[2], os.path.basename(command[1]))
            files[f] = files[command[1]]
          else:
            files[command[2]] = files[command[1]]
          files.pop(command[1], None)
          self.sock.send('ok'.encode())
        else:
          self.sock.send('failed'.encode())
        self.sock.close()
        break
      elif command[0] == 'cd':
        if len(storages) > 0 and (command[1] == '/' or (command[1] in dirs)):
          self.sock.send('ok'.encode())
        else:
          self.sock.send('failed'.encode())
        self.sock.close()
        break
      elif command[0] == 'ls':
        if len(storages) > 0 and (command[1] == '/' or (command[1] in dirs)):
          subdirs = []
          subfiles = []
          for dir in dirs:
            if os.path.dirname(dir) == command[1]:
              subdirs.append(os.path.basename(dir))
          for f in files:
            if os.path.dirname(f) == command[1]:
              subfiles.append(os.path.basename(f))
          message = {
            'ok': True,
            'dirs': subdirs,
            'files': subfiles
          }
          self.sock.sendall(json.dumps(message).encode())
        else:
          message = {
            'ok': False,
            'detail': 'No storage or directory'
          }
          self.sock.sendall(json.dumps(message).encode())
        self.sock.close()
        break
      elif command[0] == 'mkdir':
        if len(storages) > 0 and command[1] not in dirs and command[1] not in files:
          dirs.append(command[1])
          self.sock.send('ok'.encode())
        else:
          self.sock.send('failed'.encode())
        self.sock.close()
        break

def main():
  if len(sys.argv) != 2:
    print('Usage:', sys.argv[0], 'port')
    sys.exit(1)
  port = sys.argv[1]
  try:
    port = int(port)
  except:
    print('port must be an integer')
    sys.exit(1)

  # AF_INET – IPv4, SOCK_STREAM – TCP
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # reuse address; in OS address will be reserved after app closed for a while
  # so if we close and imidiatly start server again – we'll get error
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  # listen to all interfaces at port
  sock.bind(('', port))
  sock.listen()
  print('Listening on port', port)
  while True:
    # blocking call, waiting for new client to connect
    con, addr = sock.accept()
    # start new thread to deal with client
    ClientListener(con, addr).start()

if __name__ == "__main__":
    main()