import sys
import os
import six
import re
import io
import signal
import socket
import subprocess

class Socket(object):

    def __init__(self, hostname, port, option=None):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((hostname, port))
        except:
            raise
        if option is not None:
            self.sock.send(option)
        data = ""
        while "OK" not in data:
            data = self.sock.recv(1024)

    def __del__(self):
        if self.sock:
            self.sock.close()

    def query(self, sentence, pattern):
        assert(isinstance(sentence, six.text_type))
        self.sock.sendall("%s\n" % sentence.encode('utf-8').strip())
        data = self.sock.recv(1024)
        recv = data
        while not re.search(pattern, recv):
            data = self.sock.recv(1024)
            recv = "%s%s" % (recv, data)
        return recv.strip().decode('utf-8')


class Subprocess(object):

    def __init__(self, command, timeout=180):
        subproc_args = {'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT, 'cwd': '.',
                'close_fds': sys.platform != "win32"}
        try:
            env = os.environ.copy()
            self.process = subprocess.Popen(command, env=env, **subproc_args)
            self.process_command = command
            self.process_timeout = timeout
        except OSError:
            raise

    def __del__(self):
        self.process.stdin.close()
        self.process.stdout.close()
        try:
            self.process.kill()
            self.process.wait()
        except OSError:
            pass
        except TypeError:
            pass
        except AttributeError:
            pass


    def query(self, sentence, pattern):
        assert(isinstance(sentence, six.text_type))
        def alarm_handler(signum, frame):
            raise subprocess.TimeoutExpired(self.process_command, self.process_timeout)
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(self.process_timeout)
        result = ""
        try:
            outs, _ = self.process.communicate(sentence.encode('utf-8')+six.b('\n'))
            for line in io.StringIO(outs.decode('utf-8')):
                line = line.rstrip()
                if re.search(pattern, line):
                    break
                result = "%s%s\n" % (result, line)
        finally:
            signal.alarm(0)
        return result
