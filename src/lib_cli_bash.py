#!/usr/bin/env python3
# coding=utf-8

import subprocess
import locale

'''
subprocess.run(args, *, # 字符串或者列表, 执行简单命令(非列表,无管道,单命令)
                        # 如果时使用列表, 命令的参数需要拆分再传入, 每个元素只能是命令或者参数中的一种, 如['ls', 'a.txt'],
                        # 如果使用字符串, 不能使用参数, 传入的需要是执行文件的绝对路径'/root/abc.sh'
                        # 如果使用字符串构造复杂命令, 请使用 shell=True 

               stdin=None,  # 标准输入, 管道 subprocess.PIPE 
               stdout=None, # 标准输出, 管道 subprocess.PIPE 
               stderr=None, # 定向标准错误输出的文件描述符, 管道 subprocess.PIPE , subprocess.STDOUT

               input=None,  # 向子进程标准输入传递的输入数据, 默认必须是一个字节序列,
                            # 如果指定了 encoding 或 errors, 或者将 text 设置为 True时, 可以是字符串

               capture_output=False,    # 自动配置stdout 和 stderr, 同时捕获输出和错误输出,不能与stdout和stderr同时工作
               shell=False,             # 等同于 /bin/sh 
               cwd=None,                # 设置工作路径
               timeout=None,            # 如果子进程超时则杀死子进程, 然后抛出  TimeoutExpired 异常
               check=False,             # 如果为True, 若执行失败则raise错误
               encoding=None,           # 输出结果编码
               errors=None,             # 指定失败时时的返回代码
               text=None,               # universal_newlines的别名 
               universal_newlines=None, #以文本形式处理 stdout 和 stderr, 将换行符统一成 '\n'
               env=None,                # 无配置则继承父进程环境
              )
'''
'''
1 提供可供封装对象是命令的进程的执行状态信息
2 所有信息会被传递到 popen 中
3 返回对象是
    class subprocess.CompletedProcess
    属性:
        args        # 命令cmd以及参数
        returncode  # 返回值
        stdout      # 标准输出 默认不捕获
        stderr      # 标准错误 默认不捕获
        check_returncode() # 检查返回值,如果非零,则直接抛出异常
'''
'''
subprocess.DEVNULL  # 等同于 /dev/null 
subprocess.PIPE     # 打开标准流的管道
subprocess.STDOUT   # stdout 

class subprocess.Popen( args,                   # 命令的字符串或列表
                        bufsize=-1,             # 缓冲大小, 负值代表使用默认值, 默认全缓冲
                        executable=None,        # 执行的命令或可执行文件, 一般不指定, 从args中获取
                        stdin=None,
                        stdout=None,
                        stderr=None,
                        preexec_fn=None,        # 在调用fork产生新程 和 调用exec在进程执行新任务之间 调用的hook函数
                        close_fds=True,         # 是否关闭 0/1/2 之外的其他文件描述符
                        shell=False,
                        cwd=None,
                        env=None,
                        universal_newlines=None,# 子进程的stdout和stderr被视为文本对象
                        startupinfo=None,       # 仅Windows 指定子进程属性
                        creationflags=0,        # 仅Windows 指定子进程属性 样式
                        restore_signals=True,
                        start_new_session=False,
                        pass_fds=(),
                        *,
                        encoding=None,
                        errors=None,
                        text=None
                      )
'''


def ez_cmd(cmd, *args, **keywords):
    if not isinstance(cmd, str):
        raise TypeError('the cmd should be a string of shell commands')
    proc_obj = subprocess.run(cmd.strip(),
                              shell  = True,
                              stdin  = subprocess.PIPE,
                              stdout = subprocess.PIPE,
                              #stderr = subprocess.PIPE,
                              stderr = subprocess.STDOUT,
                              universal_newlines = True,
                              encoding = locale.getpreferredencoding(),
                              *args, **keywords)
    #return proc_obj.stdout.split('\n')
    return proc_obj.stdout #.split('\n')

def cmd_ok(cmd, *args, **keywords):
    if not isinstance(cmd, str):
        raise TypeError('the cmd should be a string of shell commands')
    return_code_int = subprocess.call(cmd.strip(),
                                      shell  = True,
                                      stderr = subprocess.PIPE,
                                      universal_newlines = True,
                                      *args, **keywords)
    if return_code_int == 0:
        return True
    else:
        return False


if  __name__ == "__main__":
    cmd = 'lsblk -ps'
    print(ez_cmd(cmd))
