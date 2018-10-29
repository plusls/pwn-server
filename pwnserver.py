import json
import socket
import threading
import logging
import time
import hashlib
import os
import docker
import signal
from get_pwn_data import get_pwn_data
from forward import tcp_mapping_request, init_big_brother
from mysocket import recvuntil, set_keepalive_linux
# log 路径
log_dir = None
# 生成的flag路径
data_dir = None
# pwn二进制文件路径
pwn_dir = None
# pwndocker 路径 包含xinetd dockerfile
pwmdocker_dir = None
# docker_client
docker_client = None

# 容器列表
container_list = []

# 锁
lock_dict = {}

def sigint_handler(signum, frame):
    print('stop containers')
    for container in container_list:
        container.kill()
    docker_client.close()
    network = docker_client.networks.get('pwn')
    network.remove()
    exit(0)


def handle_connect(connect_socket):
    connect_time = str(time.time())
    set_keepalive_linux(connect_socket)
    connect_socket.settimeout(20)

    try:
        connect_socket.send(b'input your token:')
        token = recvuntil(connect_socket, b'\n')[:-1]
    except ConnectionResetError:
        print('write input token ConnectionResetError')
        connect_socket.close()
        return

    try:
        token = token.decode()
    except UnicodeDecodeError:
        print('UnicodeDecodeError token={}'.format(token))
        token = ''

    if token != '':
        (problem, flag, image_tag) = get_pwn_data(token)
    else:
        problem = ''
        flag = ''

    if problem == '':
        try:
            connect_socket.send(b'token error!')
        except ConnectionResetError:
            print('write token error ConnectionResetError')
        except BrokenPipeError:
            print('write token error BrokenPipeError')
        try:
            connect_socket.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print('shutdown error:{} msg:{}'.format(str(type(e)), str(e)))
            pass
        connect_socket.close()
        return
    
    #创建锁
    if token not in lock_dict:
        lock_dict[token] = threading.Lock()
    mutex = lock_dict[token]
    #锁定
    mutex.acquire()

    problem_dir = '{}/{}'.format(pwn_dir, problem)
    if os.path.isdir(problem_dir) is False:
        raise Exception('{} is not exists'.format(problem_dir))

    # log初始化
    log_name = 'log.{}.{}.{}'.format(problem, token, connect_time)
    logger = logging.getLogger(log_name)
    handler = logging.FileHandler('{}/{}.log'.format(log_dir, log_name))
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
    logger.addHandler(handler)

    logger.info('token={}, problem={}, flag={}, image_tag={}'.format(token, problem, flag, image_tag))

    # data初始化
    problem_data_dir = '{}/{}'.format(data_dir, token)

    # 不存在路径则创建
    if os.path.isdir(problem_data_dir) is False:
        if os.path.exists(problem_data_dir):
            os.remove(problem_data_dir)
        os.mkdir(problem_data_dir)
    flag_path = '{}/flag'.format(problem_data_dir)

    if os.path.exists(flag_path) is False:
        # 写入flag
        flag_file = open(flag_path, 'w')
        flag_file.write(flag)
        flag_file.close()

    # 判断是否存在当前token对应的容器
    try:
        pwn_containers = docker_client.containers.get(token)
        # 正常来说不可能走到这一步的
        if pwn_containers.status == 'exited':
            pwn_containers.remove()
            pwn_containers = None
    except docker.errors.NotFound:
        pwn_containers = None

    # 不存在容器则新建容器
    if pwn_containers is None:
        # 判断是否存在指定镜像
        pwn_image = docker_client.images.get(image_tag)

        # 判断是否存在网络
        try:
            network = docker_client.networks.get('pwn')
        except docker.errors.NotFound:
            # 可能导致越权访问
            network = docker_client.networks.create('pwn')

        volumes = {'{}/xinetd'.format(pwmdocker_dir): {'bind': '/etc/xinetd.d/xinetd', 'mode': 'ro'},
                   problem_dir: {'bind': '/ctf/pwn/bin', 'mode': 'ro'},
                   flag_path: {'bind': '/ctf/pwn/flag_{}'.format(token), 'mode': 'ro'},
                   }
        logger.info('create container:{}'.format(token))
        pwn_containers = docker_client.containers.run(image=pwn_image,
                                                      #command='sleep infinity',
                                                      auto_remove=True, detach=True,
                                                      name=token, network='pwn',
                                                      pids_limit=30, volumes=volumes)
        container_list.append(pwn_containers)

    # ip
    ip = docker_client.api.inspect_container(token)['NetworkSettings']['Networks']['pwn']['IPAddress']
    if ip == '':
        logger.info('create container fail, token = {}'.format(token))
        return
    logger.info('container ip:{}'.format(ip))
    
    #释放
    mutex.release()

    tcp_mapping_request(connect_socket, ip, 1337, log_name, log_dir, token)


def main():
    global log_dir, data_dir, pwn_dir, pwmdocker_dir, docker_client
    # 初始化配置
    json_fp = open('config.json', 'r')
    config = json.loads(json_fp.read())
    json_fp.close()
    address = (config['address']['ip'], config['address']['port'])

    # 读取路径配置
    log_dir = os.path.abspath(config['log_dir'])
    if os.path.isdir(log_dir) is False:
        os.mkdir(log_dir)
    data_dir = os.path.abspath(config['data_dir'])
    if os.path.isdir(data_dir) is False:
        os.mkdir(data_dir)
    pwn_dir = os.path.abspath(config['pwn_dir'])
    if os.path.isdir(pwn_dir) is False:
        os.mkdir(pwn_dir)
    pwmdocker_dir = os.path.abspath(config['pwmdocker_dir'])
    if os.path.isdir(pwmdocker_dir) is False:
        os.mkdir(pwmdocker_dir)

    # 初始化logging
    logger = logging.getLogger('log')
    logger.setLevel(level=logging.INFO)

    # debug
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
    logger.addHandler(console)

    # 初始化监视器
    init_big_brother(data_dir)

    # 初始化docker连接
    docker_client = docker.from_env()

    # 处理ctr+c信号
    signal.signal(signal.SIGINT, sigint_handler)



    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 端口复用
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(address)
    server_socket.listen(100)
    while True:
        connect_socket, addr = server_socket.accept()
        threading.Thread(target=handle_connect,
                         args=(connect_socket, )).start()


if __name__ == '__main__':
    main()
