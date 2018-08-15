# pwn-server

这是一个自动化部署pwn题的工具

有如下特性：

1.自动化部署pwn

2.所有的pwn题都在不同的容器中，pwn-server将会自动化的创建容器

3.只占用一个端口，会根据不同的token将连接分发到不同的容器

4.支持一题多flag

5.自动记录pwn题流量

### 使用

第一次使用时需要build基础容器

build基础容器：

```
docker build --tag cnss/pwn ./docker/pwndocker
```



启动pwn-server

```python
python3 pwnserver.py
```

目前并没有封装为服务，无守护程序，也没有关闭容器的功能，若是要关闭容器需要手动关闭

注：关闭容器后容器将会被自动删除

**请务必保证pwn目录下的文件是可执行的！！！**



### 自动化部署pwn

与其它脚本不同，用pwn-server部署pwn题只需要将pwn的二进制文件丢入pwn文件夹，pwn-server会自动的识别pwn题

#### pwn题目录结构

仓库中默认有2个题目在目录pwn下

pwn目录结构：

```sh
pwn
├── note
│   ├── RNote3
│   ├── startdocker.sh
│   └── startpwn.sh
└── pwn1
    ├── printf
    ├── startdocker.sh
    └── startpwn.sh
```

其中包含了2个pwn题 分别为note和pwn1

startdocker.sh默认为

```sh
/usr/sbin/xinetd -dontfork
```

这是docker运行时执行的命令

startpwn.sh为xinetd会执行的命令，对于pwn1而言就是

```sh
stdbuf -i 0 -o 0 -e 0 ./printf
```

#### 多flag支持

对于每一个connect，在连接上后会要求输入token，之后交由**get_pwn_data.py**处理

若是要支持多flag则可做以下设置

```python
def get_pwn_data(token):
    '''参数为token 返回该token对应的题目名和flag'''
    if token == 'note_01':
    	return ('note', "cnss{it_is_note_01}")
    elif token == 'note_02':
        return ('note', 'cnss{it_is_note_02}')

    if token == 'pwn1_01':
    	return ('pwn1', "cnss{it_is_pwn1}")

    return('','')
```

**token=note_01**

```bash
[*] Switching to interactive mode
[DEBUG] Received 0x51 bytes:
    "*** Error in `./RNote3': munmap_chunk(): invalid pointer: 0x00007fd7f0bd7afd ***\n"
*** Error in `./RNote3': munmap_chunk(): invalid pointer: 0x00007fd7f0bd7afd ***
$ ls -al ../
[DEBUG] Sent 0xb bytes:
    'ls -al ../\n'
[DEBUG] Received 0x154 bytes:
    'total 25\n'
    'drwxr-xr-x 1 pwn  pwn  4096 Aug 15 05:56 .\n'
    'drwxr-xr-x 1 root root 4096 Aug 15 03:33 ..\n'
    '-rw-r--r-- 1 pwn  pwn   220 Aug 31  2015 .bash_logout\n'
    '-rw-r--r-- 1 pwn  pwn  3771 Aug 31  2015 .bashrc\n'
    'drwxrwxrwx 1 root root    0 Aug 15 04:58 bin\n'
    '-rwxrwxrwx 1 root root   19 Aug 15 05:56 flag\n'
    '-rw-r--r-- 1 pwn  pwn   655 May 16  2017 .profile\n'
total 25
drwxr-xr-x 1 pwn  pwn  4096 Aug 15 05:56 .
drwxr-xr-x 1 root root 4096 Aug 15 03:33 ..
-rw-r--r-- 1 pwn  pwn   220 Aug 31  2015 .bash_logout
-rw-r--r-- 1 pwn  pwn  3771 Aug 31  2015 .bashrc
drwxrwxrwx 1 root root    0 Aug 15 04:58 bin
-rwxrwxrwx 1 root root   19 Aug 15 05:56 flag
-rw-r--r-- 1 pwn  pwn   655 May 16  2017 .profile
$ cat ../flag
[DEBUG] Sent 0xc bytes:
    'cat ../flag\n'
[DEBUG] Received 0x13 bytes:
    'cnss{it_is_note_01}'
cnss{it_is_note_01}$  
```

**token=note_02**

```bash
[*] Switching to interactive mode
[DEBUG] Received 0x51 bytes:
    "*** Error in `./RNote3': munmap_chunk(): invalid pointer: 0x00007fed1ff0aafd ***\n"
*** Error in `./RNote3': munmap_chunk(): invalid pointer: 0x00007fed1ff0aafd ***
$ ls -al ../
[DEBUG] Sent 0xb bytes:
    'ls -al ../\n'
[DEBUG] Received 0x154 bytes:
    'total 25\n'
    'drwxr-xr-x 1 pwn  pwn  4096 Aug 15 05:59 .\n'
    'drwxr-xr-x 1 root root 4096 Aug 15 03:33 ..\n'
    '-rw-r--r-- 1 pwn  pwn   220 Aug 31  2015 .bash_logout\n'
    '-rw-r--r-- 1 pwn  pwn  3771 Aug 31  2015 .bashrc\n'
    'drwxrwxrwx 1 root root    0 Aug 15 04:58 bin\n'
    '-rwxrwxrwx 1 root root   19 Aug 15 05:58 flag\n'
    '-rw-r--r-- 1 pwn  pwn   655 May 16  2017 .profile\n'
total 25
drwxr-xr-x 1 pwn  pwn  4096 Aug 15 05:59 .
drwxr-xr-x 1 root root 4096 Aug 15 03:33 ..
-rw-r--r-- 1 pwn  pwn   220 Aug 31  2015 .bash_logout
-rw-r--r-- 1 pwn  pwn  3771 Aug 31  2015 .bashrc
drwxrwxrwx 1 root root    0 Aug 15 04:58 bin
-rwxrwxrwx 1 root root   19 Aug 15 05:58 flag
-rw-r--r-- 1 pwn  pwn   655 May 16  2017 .profile
$ cat ../flag
[DEBUG] Sent 0xc bytes:
    'cat ../flag\n'
[DEBUG] Received 0x13 bytes:
    'cnss{it_is_note_01}'
cnss{it_is_note_01}$  

```

docker 容器列表

```bash
docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
335ac415ef15        7d472f349e2d        "/bin/sh -c /ctf/pwn…"   4 minutes ago       Up 4 minutes        1337/tcp            note_02
92de3f097e93        7d472f349e2d        "/bin/sh -c /ctf/pwn…"   7 minutes ago       Up 7 minutes        1337/tcp            note_01

```

当然，可以自定义该函数与ctf平台进行交互，从而做到反作弊



### 关于容器

对于每个不同的token，都会启动不同的容器，也就是说同一个题会有多个容器。

但是对于相同的token则不会启动多个容器



### config.json

pwn-server使用config.json来配置

```json
{
    // 监听的地址
    "address": {
        "ip": "0.0.0.0",
        "port": 8888
    },
    // 尚未使用
    "sqlserver": "",
    // 放置pwn题的位置
    "pwn_dir": "./pwn",
    // 存放log的位置
    "log_dir": "./log",
    // 该目录下存放着xinetd的配置文件
    "pwmdocker_dir": "./docker/pwndocker",
    // 数据目录 目前只用来存放flag
    "data_dir": "./data"
}
```



### TO DO

1.自动化管理容器

2.标记出成功getflag的log

3.细化容器权限控制