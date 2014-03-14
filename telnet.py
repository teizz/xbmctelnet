#!/usr/bin/env python
import sys
import socket
import threading
import xbmc
import time

class Puppy(threading.Thread):
  def __init__(self, (socket,address)):
    threading.Thread.__init__(self)
    self.socket=socket
    self.address=address
    self.living=True
    self.player=xbmc.Player()

  def drown(self):
    if self.socket:
      self.socket.close()
      self.socket=None
    self.living=False

  def run(self):
    #print '%s:%s connected.' % self.address
    self.socket.sendall("\xFF\xFB\x03\xFF\xFB\x01") # IAC WILL SUPRESS IAC WILL ECHO
    while self.living:
      try:
        data = self.socket.recv(8)
        if not data:
          self.socket.close()
          self.living=False
        else:
          # received (chars represented in decimal)
          #print("b %s" % str([ord(c) for c in data]))
          shifted=sum([ord(c)<<8*i for i,c in enumerate(reversed(data))])
          # this is the whole (max 8 bytes) shifted into one int:
          #print("i %s" % shifted)
          data=self.parseBytecode(shifted)
          #print("r %s" % str([ord(c) for c in data]))
          self.socket.sendall(data)
      except socket.error as e:
        xbmc.sleep(10)
    self.drown()
    #print '%s:%s disconnected.' % self.address

  def parseBytecode(self, v):
    # Special secret hidden keys
    if v == 4:
      self.living=False
      return "\x04" # end of transmission byte
    elif v == 16: # ^P
      xbmc.executebuiltin("PlayerControl(Play)")
    elif v == 24: # ^X
      xbmc.executebuiltin("PlayerControl(Stop)")

    ### These are just some keys that I could map
    elif v == 8: # backspace or ^H
      xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.Back", "id": 1 }')
    elif v == 3328: # enter
      xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.Select", "id": 1 }')
    elif v == 1792833: # up
      xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.Up", "id": 1 }')
    elif v == 1792834: # down
      xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.Down", "id": 1 }')
    elif v == 1792835: # right
      xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.Right", "id": 1 }')
    elif v == 1792836: # left
      xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.Left", "id": 1 }')
    return "" # empty string

class TelnetMonitor(xbmc.Monitor):
  def __init__(self):
    self.living=True
    self.pool=set()

  def listen(self):
    port=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    xbmc.log("Binding to port")
    while not port.getsockname()[1] and self.living:
      try: port.bind(('', 51234))
      except: xbmc.sleep(1000) # try once a second
    xbmc.log("BOUND")
    port.settimeout(1)
    port.listen(4)

    while self.living: # wait for socket to connect
      try:
        leash=port.accept()
        puppy=Puppy(leash)
        self.pool.add(puppy)
        puppy.start()
      except socket.timeout:
        xbmc.sleep(10) # this is needed to give XBMC some time to bud in
        self.prune() # clean dead puppy threads
      except KeyboardInterrupt:
        print("user sent ctrl+c")
        self.living=False

  def prune(self):
    deadpuppies=[puppy for puppy in self.pool if not puppy.isAlive()]
    if deadpuppies:
      print("pruning these dead puppies: %s" % str(deadpuppies))
      map(self.pool.discard,deadpuppies)

  def onAbortRequested(self):
    xbmc.log("xbmc called for shutdown of plugin")
    self.living=False
    for puppy in self.pool: puppy.drown()
    xbmc.sleep(50) # give puppies time to die
    self.prune()

  def onSettingsChanged(self):
    xbmc.log("settings changed")

if __name__ == "__main__":
  m=TelnetMonitor()
  m.listen()
  print("Main thread has ended!")
