FROM phusion/baseimage:latest

RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirrors.tuna.tsinghua.edu.cn/g" /etc/apt/sources.list && \
    sed -i "s/http:\/\/security.ubuntu.com/http:\/\/mirrors.tuna.tsinghua.edu.cn/g" /etc/apt/sources.list && \
    dpkg --add-architecture i386 && \
    apt-get -y update && \
    apt-get -y dist-upgrade && \
    apt-get update && \
    apt-get install -y \
    lib32z1 xinetd build-essential python3 python3-dev libseccomp-dev qemu \
    libc6:i386 libc6-dbg:i386 libc6-dbg lib32stdc++6 g++-multilib --fix-missing && \
    rm -rf /var/lib/apt/list/*

RUN mkdir /ctf && \
    useradd -b /ctf -m pwn

EXPOSE 1337

CMD /ctf/pwn/bin/startdocker.sh
