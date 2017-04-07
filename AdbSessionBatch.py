#!/usr/bin/python
import os
import sys
import math
import re
from time import sleep
from subprocess import call, check_output, PIPE, Popen
from threading import Thread
from Queue import Queue, Empty
from random import randint
from LineAlgo import bresenham

dirname = os.path.dirname(os.path.realpath(__file__))
print dirname
# /usr/src/linux-headers-4.4.0-66/include/uapi/linux/input-event-codes.h
LABELS={}
with open('%s/input-event-codes.h' % (dirname,), 'r') as f:
    for line in f:
        m = re.match( '#define\s*(\S+)\s+(\S+)\s*', line.rstrip() )
        if m:
            try:
                key,valstr = m.groups()
                exec( "val=%s" % (valstr,) )
                LABELS[key]=val
            except Exception, e:
                pass

# tablet 1920 1200
# https://developer.android.com/studio/command-line/adb.html#shellcommands

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        line = line.strip()
        if line:
            queue.put(line)
    out.close()


class LineReader:

    def __init__( self, fin, fout ):
        self.fin = fin
        self.fout = fout
        self.queue = Queue()
        self.thread = Thread( target=enqueue_output,
                              args=(self.fout,self.queue) )
        self.thread.daemon = True
        self.thread.start()

    def write( self, line ):
        #print "Writing ", line
        self.fin.write( line )
        self.fin.flush()

    def read( self, timeout=0 ):
        while True:
            try:
                line = self.queue.get(True,timeout)
                yield line
            except Empty:
                break


ON_POSIX = 'posix' in sys.builtin_module_names


class AdbSession:
    def __init__(self):
        self.adb_location = check_output( 'which adb', shell=True ).rstrip()
        print "ADB:[%s]" % (self.adb_location,)
        self.proc = Popen( [self.adb_location,'shell'], stdin=PIPE, stdout=PIPE,
                               bufsize=4096*1024, close_fds=ON_POSIX )
        self.adb = LineReader( self.proc.stdin, self.proc.stdout )
        self.touchscreen = None
        self.touchid = randint(0,65536)
        self.commands = []

        # initialize
        self.adb.write( 'getevent -pl\n' )
        self.devices = {}
        for line in self.adb.read( 0.1 ):
            line = line.strip()
            if not line: continue
            #print "getevent:[%s]" % ( line.strip() )
            m = re.match( "add device.*(\d+):(.*)", line.strip() )
            if m:
                devnum, devfile = m.groups()
            else:
                m = re.match( "name\w*:.*\"(.*)\".*", line.rstrip() )
                if m:
                    devname = m.group(1)
                    #print devnum, devfile, devname
                    self.devices[devname] = { 'file':devfile, 'number':devnum }
        self.touchscreen = self.devices['sec_touchscreen']['file']

    def execute( self ):
        cmdstr = "echo \"%s\" | /data/local/tmp/sendevent %s\n" % (" ".join(self.commands),self.touchscreen )
        #print "Sent: ", cmdstr
        self.adb.write( cmdstr )
        for line in self.adb.read(0.25):
            print "swipe:", line.rstrip()
        self.commands  = []

    def tap( self, x, y ):
        TAP_STRING = "tap {posx} {posy} {pressure}"
        cmd = TAP_STRING.format( posx=x, posy=y, pressure=255 )
        self.commands.append( cmd )
        self.execute()

    def swipe_begin( self, x, y ):
        #print "swipe_begin %d %d" % (x,y)
        SWIPE_STRING="swipe_begin {posx} {posy} {pressure}"
        self.touchid += 1
        cmd = SWIPE_STRING.format( posx=int(x), posy=int(y), pressure=255 )
        self.commands.append( cmd )

    def swipe_move( self, x, y ):
        #print "swipe_move %d %d" % (x,y)
        SWIPE_STRING="swipe_move {posx} {posy} {pressure}"
        cmd = SWIPE_STRING.format(  posx=int(x), posy=int(y), pressure=255 )
        self.commands.append( cmd )
        if len(self.commands)>100:
            self.swipe_end()
            self.swipe_begin( x, y )

    def swipe_end(self):
        #print "swipe_end"
        self.commands.append( "swipe_end" )
        self.execute()

    def swipe( self, x1, y1, x2, y2, duration=100 ):
        print "swipe %d %d - %d %d" % (x1,y1,x2,y2)
        SWIPE_STRING= "swipe_begin {posx1:d} {posy1:d} {pressure} swipe_move  {posx2:d} {posy2:d} {pressure} swipe_end"
        cmd = SWIPE_STRING.format( devid=0,
                                device=self.touchscreen,
                                touchid=self.touchid,
                                posx1=int(x1), posy1=int(y1),
                                posx2=int(x2), posy2=int(y2),
                                delay=500000,
                                width=5, pressure=255, **LABELS )
        self.commands.append( cmd )
        self.execute()
