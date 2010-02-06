import os,sys
import backdraft
import subprocess
import time

class Player:
  def __init__(self):
    self.proc = None
  def play(self, music_file):
    if self.proc and self.proc.poll() is not None:
      return
    self.proc = subprocess.Popen(['mplayer', music_file], shell=False)
  def stop(self):
    if self.proc:
      self.proc.terminate()
      self.proc = None

class MusicMonitor:
  def __init__(self, song):
    self.player = Player()
    self.song = song
  def power_on(self, whatever):
    self.player.play(self.song)
  def power_off(self, whatever):
    self.player.stop()

def monitor(song):
  monitor = MusicMonitor(song)
  urls = {
    "http://chb1.kcprod.info:8080/hudson/job/kc-backend-chb2/rssAll": (0, 2),
  }
  monitor = backdraft.AsyncMonitor([monitor], urls) 
  monitor.start()

def test(song):
  player = Player()
  player.play(song)
  time.sleep(5)
  player.stop()

if __name__ == '__main__':
  song = sys.argv[1]
  monitor(song)
#  test(song)
  
  

