__author__ = 'bkoenighofer'

import subprocess
import sys
import fcntl
import os
import time

class VIS(object):

    def setNonBlocking(self,fd):
        """
        Set the file description of the given file descriptor to non-blocking.
        """
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, flags)

    def __init__(self):
      self.DEBUG=False
      self.prompt="vis> "
      self.vis = subprocess.Popen("vis", stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, bufsize = 1)
      self.setNonBlocking(self.vis.stdout)
      self.setNonBlocking(self.vis.stderr)
      str_buffer = ''
      while not str_buffer.startswith("vis> vis release 2.4"):
            try:
                str_buffer += self.vis.stdout.read()
            except IOError:
                time.sleep(0.1)

    def readVerilog(self,filename):
        self.sendCommand("read_verilog "+filename)

    def ltlModelCheck(self,ltlfile):
        result = self.sendCommand("ltl_model_check "+ltlfile)
        count=0
        prevLine=""
        for line in result.split('\n'):
            if line.startswith("# LTL_MC:"):
                count=count+1
                if line.endswith("formula passed"):
                    pass
                elif line.endswith("formula failed"):
                    print(" ERROR: checking formula #"+str(count)+": "+prevLine)
                    print(" result was: "+line)
                    return False
                else:
                    print(" ERROR: checking formula #"+str(count)+": "+prevLine)
                    print(" result was: "+line)
                    print(" ERROR: abnormal model check result! formula result was strange!! try enabling DEBUG flag in VIS checker class.")
                    sys.exit(-1)
            prevLine=line

        if count==0:
            print(" ERROR: abnormal model check result! no formulas to check found!! try enabling DEBUG flag in VIS checker class.")
            sys.exit(-1)
        return True

    def flattenHierarchy(self):
        self.sendCommand("flatten_hierarchy")

    def staticOrder(self):
        self.sendCommand("static_order")

    def buildPartitionMdds(self):
        self.sendCommand("build_partition_mdds")

    def quit(self):
        self.sendCommand("quit")

    def sendCommand(self,cmd):
        if self.DEBUG:
            print("sending cmd:"+cmd)

        self.vis.stdin.write(cmd+"\n")
        self.vis.stdin.flush()
        str_buffer = ''

        if cmd != "quit":
            while not self.prompt in str_buffer:
                    try:
                        str_buffer += self.vis.stdout.read()
                    except IOError:
                        time.sleep(0.1)

        if self.DEBUG:
             print str_buffer
        return str_buffer