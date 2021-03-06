# storage.py

# Import libraries
import socket,  os, shutil, stat, atexit, sys, json
from datetime import datetime
from threading import Thread

STORAGE = 'storage'

# Thread to listen one particular client
class ClientListener(Thread):
  def __init__(self, sock: socket.socket):
    super().__init__(daemon=True)
    self.sock = sock

  def run(self):
    command = self.sock.recv(1024).decode().split(' ')
    if command[0] == 'init':
      if os.path.exists(STORAGE):
        shutil.rmtree(STORAGE)
      os.mkdir(STORAGE)
      total, used, free = shutil.disk_usage(STORAGE)
      self.sock.send(str(free).encode())
    elif command[0] == 'touch':
      os.mknod(STORAGE + '/' + command[1])
    elif command[0] == 'get':
      with open(STORAGE + '/' + command[1], 'rb') as fs:
        while True:
          data = fs.read(1024)
          if not data:
            break
          self.sock.send(data)
    elif command[0] == 'info':
      info = os.stat(STORAGE + '/' + command[1])
      message = {
        'size': info.st_size,
        'mode': stat.filemode(info.st_mode),
        'mtime': datetime.fromtimestamp(info.st_mtime).strftime("%m-%d-%Y %H:%M:%S")
      }
      self.sock.sendall(json.dumps(message).encode())
    elif command[0] == 'put':
      self.sock.send('ok'.encode())
      with open(STORAGE + '/' + command[1], 'wb') as fs:
        self.sock.settimeout(3)
        while True:
            try:
              data = self.sock.recv(1024)
              if not data:
                break
              fs.write(data)
            except:
              break
    elif command[0] == 'rm':
      os.remove(STORAGE + '/' + command[1])
    elif command[0] == 'cp':
      src = STORAGE + '/' + command[1]
      dst = STORAGE + '/' + command[2]
      shutil.copyfile(src, dst)
    self.sock.close()

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

def up(server, server_port, port):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, server_port))
    message = 'up ' + str(port)
    s.send(message.encode())
    message = get_message(s)
    if os.path.exists(STORAGE):
      shutil.rmtree(STORAGE)
    os.mkdir(STORAGE)
    if message['ok'] and message['storage']:
      for uuid in message['uuids']:
        server, port = message['storage'].split(' ')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as st:
          st.connect((server, int(port)))
          msg = 'get ' + uuid
          st.send(msg.encode())
          with open(STORAGE + '/' + uuid, 'wb') as fs:
            while True:
              st.settimeout(3)
              try:
                data = st.recv(1024)
                if not data:
                  break
                fs.write(data)
              except:
                break
    s.send('ok'.encode())

def down(server, server_port, port):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server, server_port))
    message = 'down ' + str(port)
    s.send(message.encode())

# Main method
def main():
  if len(sys.argv) != 4:
    print('Usage:', sys.argv[0], 'server server_port storage_port')
    sys.exit(1)
  server, server_port, port = sys.argv[1:]
  try:
    port = int(port)
    server_port = int(server_port)
  except:
    print('port must be an integer')
    sys.exit(1)
  atexit.register(down, server, server_port, port)
  up(server, server_port, port)

  # AF_INET – IPv4, SOCK_STREAM – TCP
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # Reuse address; in OS address will be reserved after app closed for a while
  # So if we close and imidiatly start server again – we'll get error
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  # Listen to all interfaces at port
  sock.bind(('', port))
  sock.listen()
  print('Listening on port', port)
  while True:
    # blocking call, waiting for new client to connect
    con, addr = sock.accept()
    # start new thread to deal with client
    ClientListener(con).start()

if __name__ == "__main__":
    main()
