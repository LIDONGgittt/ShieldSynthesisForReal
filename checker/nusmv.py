__author__ = 'bkoenighofer'

import subprocess
import sys

class NuSMV(object):

    def __init__(self):
      self.DEBUG=True

    def check(self,smvData):
        p = subprocess.Popen("NuSMV", stdin=subprocess.PIPE,  stdout=subprocess.PIPE)
        out, _ = p.communicate(smvData.encode())
        if self.DEBUG:
            print(out)
        all_lines = out.decode().splitlines()
        result = all_lines[len(all_lines)-1]
        if result == "-- specification  G (!m_cshield.err & (m_deviation.err -> m_cdesign.err))  is true":
            return True
        else:
            return False