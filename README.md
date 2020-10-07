# Distributed Systems: Project 2 (Distributed File System)

Students: **Trang Nguyen (BS18-DS-01)** and **Marko Pezer (BS18-SE-01)**

Date: **October 2020**

This project is created for Distributed Systems course at Innopolis University, Russia.

![Demo](diagrams/demo.gif)

## System launching and using

To download source code use

```bash
git clone https://github.com/tracy2811/dfs.git
```

or use public docker image [tracy2811/dfs:base](https://hub.docker.com/repository/docker/tracy2811/dfs)

**NOTE:** For rich and latest features, please use code from [latest](https://github.com/tracy2811/dfs/tree/latest) branch or docker image [tracy2811/dfs:latest](https://hub.docker.com/repository/docker/tracy2811/dfs). Documentation can also be found there.


### 1. Launching naming server

To start the naming server run `naming.py` with `NAMING_PORT` as an argument:

```bash
# From source code
python naming.py PORT

# From Docker image
docker run --network=host tracy2811/dfs:base python naming.py NAMING_PORT
```

### 2. Launching storage servers

Multiple storage servers can join to the DFS network. 
To start any of them, run `storage.py` with three arguments (`NAMING_ADDR`, `NAMING_PORT`, `STORAGE_PORT`):

```bash
# From source code
python storage.py NAMING_ADDR NAMING_PORT STORAGE_PORT

# From Docker image
docker run --network=host tracy2811/dfs:base python storage.py NAMING_ADDR NAMING_PORT STORAGE_PORT
```

### 3. Client usage

`client.py` provides an interactive shell for user to take actions on the DFS. It requires two arguments (`NAMING_ADDR`, `NAMING_PORT`). 
For the new system, `init` action is required. Client at any time can execute this `init` action to format the system.

```bash
# From source code
python client.py NAMING_ADDR NAMING_PORT

# From Docker image
docker run -it --network=host tracy2811/dfs:base python client.py NAMING_ADDR NAMING_PORT
```

The table below shows command supported by the current client shell. For more flexible experience, please refer to [latest](https://github.com/tracy2811/dfs/tree/latest) branch.

Command | Description
--- | ---
`init` | Initialize the client storage on the new system. Can be used to format the system.
`touch file` | Create a new empty file.
`get file` | Download a file from DFS to the client side.
`put local_file file` | Upload file from the client side local_file to DFS.
`info file` | Get file's information (mode, size, and modification time).
`cp src_file dst_file` | Create a copy of a file src_file under the name dst_file.
`mv src_file dst` | Move a file from src_file to dst. Can be used to rename a file.
`rm target` | Delete a file or a directory.
`cd dir` | Change current working directory.
`ls dir`  | List files and directories.
`mkdir dir` | Make a directory.
`help` | Show help.
`exit` | Quit interactive shell.

## Architectural diagrams

![Diagram_01](diagrams/diagram_01.JPG)

## Description of communication protocols

We have used TCP IPv4 as communication protocol.

TCP IPv4 protocol works at the Network layer of the OSI model and at the Internet layer of the TCP/IP model. Thus, this protocol identifies hosts based upon their logical addresses (IP addresses).

## Contribution of each team member

During the working process we were helping each other in every part of the process. 

However, here is the graph that shows contribution of each team member.

![Diagram_02](diagrams/diagram_02.JPG)
