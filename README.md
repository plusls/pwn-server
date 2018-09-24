# pwn-server

这是一个自动化部署pwn题的工具

有如下特性：

1.自动化部署pwn

2.所有的pwn题都在不同的容器中，pwn-server将会自动化的创建容器

3.只占用一个端口，会根据不同的token将连接分发到不同的容器

4.支持一题多flag

5.自动记录pwn题流量

6.自动标记出读取了flag的流量

7.防fork bomb

8.支持多镜像，既不同容器可以指定不同的docker镜像

### 依赖

fanotify

```
pip3 install git+https://github.com/google/python-fanotify.git --user
```



### 使用

第一次使用时需要build基础容器

build基础容器：

```
docker build --tag cnss/pwn ./docker/pwndocker
```



启动pwn-server

```python
sudo python3 pwnserver.py
```

目前并没有封装为服务，无守护程序

注：关闭容器后容器将会被自动删除

由于使用了fanotify，所以必须要有root权限

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
    '''参数为token 返回该token对应的题目名和flag以及image_tag'''
    if token == 'note_01':
    	return ('note', "cnss{it_is_note_01}", "cnss/pwn")
    elif token == 'note_02':
        return ('note', 'cnss{it_is_note_02}', "cnss/pwn")

    if token == 'pwn1_01':
    	return ('pwn1', "cnss{it_is_pwn1}", "cnss/pwn")

    return('', '', '')
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
    "*** Error in `./RNote3': munmap_chunk(): invalid pointer: 0x00007fad2858cafd ***\n"
*** Error in `./RNote3': munmap_chunk(): invalid pointer: 0x00007fad2858cafd ***
$ cat ../flag
[DEBUG] Sent 0xc bytes:
    'cat ../flag\n'
[DEBUG] Received 0x13 bytes:
    'cnss{it_is_note_02}'
cnss{it_is_note_02}$  

```

docker 容器列表

```bash
docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
335ac415ef15        7d472f349e2d        "/bin/sh -c /ctf/pwn…"   4 minutes ago       Up 4 minutes        1337/tcp            note_02
92de3f097e93        7d472f349e2d        "/bin/sh -c /ctf/pwn…"   7 minutes ago       Up 7 minutes        1337/tcp            note_01

```

当然，可以自定义该函数与ctf平台进行交互，从而做到反作弊

#### 多镜像支持

考虑到不同题目可能要求的运行环境不同，pwnserver支持不同题目使用不同的镜像，只需要在**get_pwn_data**中设置即可

### 关于容器

对于每个不同的token，都会启动不同的容器，也就是说同一个题会有多个容器。

但是对于相同的token则不会启动多个容器

### 关于fork bomb

每个容器都有资源限制，限制了pid的数量

正常情况下父进程被发送SIGPIPE后子进程也会被杀死，所以在socket断开后fork炸弹一般会失效

当然，例外情况也是有的，详情见BUG

### 关于log

对于流量将会被自动记录在log目录下，若是一个连接获取了flag，那条log的文件名中将会包含flag

例如：

```bash
plusls@pwn:~/pwn/pwn-server/log$ ls -al
total 44
drwxrwxr-x 2 plusls plusls  4096 Aug 18 01:34 .
drwxrwxr-x 9 plusls plusls  4096 Aug 18 01:27 ..
-rw-r--r-- 1 root   root   12949 Aug 18 01:34 log.note.note_02.1534527196.572956.log
-rw-r--r-- 1 root   root   12237 Aug 18 01:34 log.note.note_02.1534527217.5434923-flag.log
-rw-r--r-- 1 root   root    1025 Aug 18 01:31 log.sh.sh.1534527057.2515137.log
-rw-r--r-- 1 root   root     507 Aug 18 01:31 log.sh.sh.1534527099.9255965-flag.log
```

判断一个连接是否成功拿到flag使用了fainotify，想了解实现可以阅读源码

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

~~1.自动化管理容器~~

~~2.标记出成功getflag的log~~

3.细化容器权限控制

### BUG

目前已知在某些情况下socket断开后程序仍会继续运行...

socket断开后程序结束的原因是SIGPIPE，当往一个写端关闭的管道或socket连接中连续写入数据时会引发SIGPIPE信号，从而导致程序结束

若是程序无任何写操作并进入死循环，则会出现冗余进程

例如

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main()
{
    setbuf(stdout, NULL);
    setbuf(stdin, NULL);
    setbuf(stderr, NULL);

    char s[0x300];
    while (1) {
        memset(s, 0, 0x300);
        printf("Please input somthing:");
        read(0, s, 0x300);
        printf("Your input is:");
        printf(s);
    }
    return 0;
}
```

printf被改为system后程序就没有任何写操作了，因此不会触发SIGPIPE，从而不会被结束