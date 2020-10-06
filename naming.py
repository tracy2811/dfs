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

  def _up(self, port):
    global storages, dirs, files
    self.port = port
    storage = self.addr + ' ' + self.port
    uuids = [files[f] for f in files]
    message = {
      'ok': True,
      'uuids': uuids,
      'storage': storages[0] if storages else None
    }
    self.sock.sendall(json.dumps(message).encode())
    status = self.sock.recv(1024).decode()
    if status == 'ok' and storage not in storages:
      storages.append(storage)
      print('Storage', storage, 'up')

  def _down(self, port):
    global storages, dirs, files
    self.port = port
    storage = self.addr + ' ' + self.port
    if storage in storages:
      storages.remove(storage)
      print('Storage', storage, 'down')

  def _init(self):
    global storages, dirs, files
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
  
  def _touch(self, path):
    global storages, dirs, files
    dir = os.path.dirname(path)
    if len(storages) and path not in dirs and (dir == '/' or (dir in dirs)):
      id = str(uuid.uuid4())
      files[path] =  id
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

  def _get_or_info(self, path):
    global storages, dirs, files
    if len(storages) > 0 and path in files:
      message = {
        'ok': True,
        'uuid': files[path],
        'storage': storages[0],
      }
      self.sock.sendall(json.dumps(message).encode())
    else:
      message = {
        'ok': False,
        'detail': 'No storage or file'
      }
      self.sock.sendall(json.dumps(message).encode())
  
  def _put(self, src, dst):
    global storages, dirs, files
    dir = os.path.dirname(dst)
    if len(storages) > 0 and (dir == '/' or (dir in dirs)):
      id = str(uuid.uuid4())
      if dst == '/' or dst in dirs:
        f = os.path.join(dst, src)
        files[f] = id
      else:
        files[dst] = id
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

  def _rm(self, path):
    global storages, dirs, files
    if len(storages) > 0:
      if path in files:
        message = {
          'ok': True,
          'storages': storages,
          'uuid': files[path]
        }
        files.pop(path, None)
        self.sock.sendall(json.dumps(message).encode())
      elif path == '/' or path in dirs:
        subdirs = []
        subfiles = []
        uuids = []
        for dir in dirs:
          if os.path.commonpath([dir, path]) == path and dir != path:
            subdirs.append(dir)
        for f in files:
          if os.path.commonpath([f, path]) == path:
            subfiles.append(f)
            uuids.append(files[f])
        if len(subdirs) > 0 or len(subfiles) > 0:
          message = {
            'ok': True,
            'storages': storages,
            'uuids': uuids
          }
          self.sock.sendall(json.dumps(message).encode())
          confirm = self.sock.recv(1024).decode()
          if confirm == 'y':
            for f in subfiles:
              files.pop(f, None)
            for d in subdirs:
              dirs.remove(d)
            dirs.remove(path)
        else:
          dirs.remove(path)
          message = {
            'ok': True,
          }
          self.sock.sendall(json.dumps(message).encode())
      else:
          message = {
            'ok': False,
            'detail': 'No storage, file or directory'
          }
          self.sock.sendall(json.dumps(message).encode())
    else:
      message = {
        'ok': False,
        'detail': 'No storage, file or directory'
      }
      self.sock.sendall(json.dumps(message).encode())

  def _cp(self, src, dst):
    global storages, dirs, files
    dir = os.path.dirname(dst)
    dst_is_file = dir == '/' or (dir in dirs)
    dst_is_dir = dst == '/' or (dst in dirs)
    id = str(uuid.uuid4())
    if len(storages) > 0 and src in files and (dst_is_dir or dst_is_file):
      if dst_is_dir:
        files[os.path.normpath(os.path.join(dst, os.path.basename(src)))] = id
      else:
        files[dst] =  id
      message = {
        'ok': True,
        'uuids': [files[src], id],
        'storages': storages
      }
      self.sock.sendall(json.dumps(message).encode())
    else:
      message = {
        'ok': False,
        'detail': 'No storage, file or directory'
      }
      self.sock.sendall(json.dumps(message).encode())

  def _mv(self, src, dst):
    global storages, dirs, files
    dir = os.path.dirname(dst)
    if len(storages) > 0 and src in files and (dir == '/' or (dir in dirs)):
      if dst in dirs:
        f = os.path.join(dst, os.path.basename(src))
        files[f] = files[src]
      else:
        files[dst] = files[src]
      files.pop(src, None)
      self.sock.send('ok'.encode())
    else:
      self.sock.send('failed'.encode())

  def _cd(self, path):
    global storages, dirs, files
    if len(storages) > 0 and (path == '/' or (path in dirs)):
      self.sock.send('ok'.encode())
    else:
      self.sock.send('failed'.encode())

  def _ls(self, path):
    global storages, dirs, files
    if len(storages) > 0 and (path == '/' or (path in dirs)):
      subdirs = []
      subfiles = []
      for dir in dirs:
        if os.path.dirname(dir) == path:
          subdirs.append(os.path.basename(dir))
      for f in files:
        if os.path.dirname(f) == path:
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

  def _mkdir(self, path):
    global storages, dirs, files
    if len(storages) > 0 and path not in dirs and path not in files:
      dirs.append(path)
      self.sock.send('ok'.encode())
    else:
      self.sock.send('failed'.encode())

  def run(self):
    command = self.sock.recv(1024).decode()
    command = command.split(' ')
    if command[0] == 'up':
      self._up(command[1])
    elif command[0] == 'down':
      self._down(command[1])
    elif command[0] == 'init':
      self._init()
    elif command[0] == 'touch':
      self._touch(command[1])
    elif command[0] == 'get' or command[0] == 'info':
      self._get_or_info(command[1])
    elif command[0] == 'put':
      self._put(command[1], command[2])
    elif command[0] == 'rm':
      self._rm(command[1])
    elif command[0] == 'cp':
      self._cp(command[1], command[2])
    elif command[0] == 'mv':
      self._mv(command[1], command[2])
    elif command[0] == 'cd':
      self._cd(command[1])
    elif command[0] == 'ls':
      self._ls(command[1])
    elif command[0] == 'mkdir':
      self._mkdir(command[1])
    self.sock.close()

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
