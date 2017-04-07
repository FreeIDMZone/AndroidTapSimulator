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

print """
AdbSession: This is the SLOW version of the algorithm. It will use the adb shell input feature to send commands to the tablet, albeit it will be optimized in a way that the ADB shell session will be kept open, saving some time.
Compile sendevent.c using the provided Makefile and import from AdbSessionBatch to get the fast algorithm.
"""

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

    def tap( self, x, y ):
        TAP_STRING = """
sendevent {device} {EV_KEY} {BTN_TOUCH}  1
sendevent {device} {EV_ABS} {ABS_MT_TRACKING_ID} {touchid}
sendevent {device} {EV_KEY} {BTN_TOOL_FINGER} 1

sendevent {device} {EV_ABS} {ABS_MT_POSITION_X} {posx}
sendevent {device} {EV_ABS} {ABS_MT_POSITION_Y} {posy}
sendevent {device} {EV_ABS} {ABS_MT_PRESSURE} {pressure}
sendevent {device} {EV_SYN} {SYN_REPORT} 0

sendevent {device} {EV_ABS} {ABS_MT_TRACKING_ID} -1
sendevent {device} {EV_KEY} {BTN_TOUCH} 0
sendevent {device} {EV_KEY} {BTN_TOOL_FINGER} 0
sendevent {device} {EV_SYN} {SYN_REPORT} 0
"""
        cmd = TAP_STRING.format( devid=0,
                                device=self.touchscreen,
                                posx=x, posy=y,
                                width=5, pressure=50, **LABELS )
        self.adb.write( cmd )


    def swipe_old( self, x1, y1, x2, y2, duration=100 ):
        cmd = 'input swipe %d %d %d %d %d\n' % (x1,y1,x2,y2,duration)
        self.adb.write( cmd )
        for line in self.adb.read(0.1):
            print "swipe:", line.rstrip()

    def swipe_begin( self, x, y ):
        print "swipe_begin %d %d" % (x,y)
        SWIPE_STRING="""
sendevent {device} {EV_KEY} {BTN_TOUCH}  1
sendevent {device} {EV_ABS} {ABS_MT_SLOT} 0
sendevent {device} {EV_ABS} {ABS_MT_TRACKING_ID} {touchid:d}
sendevent {device} {EV_KEY} {BTN_TOOL_FINGER} 1
sendevent {device} {EV_ABS} {ABS_MT_POSITION_X} {posx:d}
sendevent {device} {EV_ABS} {ABS_MT_POSITION_Y} {posy:d}
sendevent {device} {EV_ABS} {ABS_MT_PRESSURE} {pressure:d}
sendevent {device} {EV_SYN} {SYN_REPORT} 0
"""
        self.touchid += 1
        cmd = SWIPE_STRING.format( devid=0,
                                device=self.touchscreen,
                                touchid=self.touchid,
                                posx=int(x), posy=int(y),
                                width=5, pressure=50, **LABELS )
        self.adb.write( "%s\n" % (cmd,) )
        for line in self.adb.read(0.01):
            print "swipe:", line.rstrip()

    def swipe_move( self, x, y ):
        print "swipe_move %d %d" % (x,y)
        SWIPE_STRING="""
sendevent {device} {EV_ABS} {ABS_MT_POSITION_X} {posx:d}
sendevent {device} {EV_ABS} {ABS_MT_POSITION_Y} {posy:d}
sendevent {device} {EV_ABS} {ABS_MT_PRESSURE} {pressure:d}
sendevent {device} {EV_SYN} {SYN_REPORT} 0
"""
        cmd = SWIPE_STRING.format( devid=0,
                                device=self.touchscreen,
                                posx=int(x), posy=int(y),
                                pressure=255, **LABELS )
        self.adb.write( "%s\n" % (cmd,) )
        for line in self.adb.read(0.05):
            print "swipe:", line.rstrip()

    def swipe_end(self):
        print "swipe_end"
        SWIPE_STRING="""
sendevent {device} {EV_ABS} {ABS_MT_TRACKING_ID} -1
sendevent {device} {EV_KEY} {BTN_TOUCH} 0
sendevent {device} {EV_KEY} {BTN_TOOL_FINGER} 0
sendevent {device} {EV_SYN} {SYN_REPORT} 0
"""
        cmd = SWIPE_STRING.format( device=self.touchscreen, **LABELS )
        self.adb.write( "%s\n" % (cmd,) )
        for line in self.adb.read(0.1):
            print "swipe:", line.rstrip()

    def swipe( self, x1, y1, x2, y2, duration=100 ):
        print "swipe %d %d - %d %d" % (x1,y1,x2,y2)
        SWIPE_STRING="""
sendevent {device} {EV_KEY} {BTN_TOUCH}  1
sendevent {device} {EV_ABS} {ABS_MT_TRACKING_ID} {touchid:d}
sendevent {device} {EV_KEY} {BTN_TOOL_FINGER} 1

sendevent {device} {EV_ABS} {ABS_MT_POSITION_X} {posx1:d}
sendevent {device} {EV_ABS} {ABS_MT_POSITION_Y} {posy1:d}
sendevent {device} {EV_ABS} {ABS_MT_PRESSURE} {pressure:d}
sendevent {device} {EV_SYN} {SYN_REPORT} 0

sendevent {device} {EV_ABS} {ABS_MT_POSITION_X} {posx2:d}
sendevent {device} {EV_ABS} {ABS_MT_POSITION_Y} {posy2:d}
sendevent {device} {EV_ABS} {ABS_MT_PRESSURE} {pressure:d}
sendevent {device} {EV_SYN} {SYN_REPORT} 0

sendevent {device} {EV_ABS} {ABS_MT_POSITION_X} {posx2:d}
sendevent {device} {EV_ABS} {ABS_MT_POSITION_Y} {posy2:d}
sendevent {device} {EV_ABS} {ABS_MT_TOUCH_MAJOR} 1
sendevent {device} {EV_ABS} {ABS_MT_TOUCH_MINOR} 1
sendevent {device} {EV_ABS} {ABS_MT_PRESSURE} {pressure:d}
sendevent {device} {EV_SYN} {SYN_REPORT} 0

sendevent {device} {EV_ABS} {ABS_MT_TRACKING_ID} -1
sendevent {device} {EV_KEY} {BTN_TOUCH} 0
sendevent {device} {EV_KEY} {BTN_TOOL_FINGER} 0
sendevent {device} {EV_SYN} {SYN_REPORT} 0

"""
        self.touchid += 1
        cmd = SWIPE_STRING.format( devid=0,
                                device=self.touchscreen,
                                touchid=self.touchid,
                                posx1=int(x1), posy1=int(y1),
                                posx2=int(x2), posy2=int(y2),
                                delay=500000,
                                width=5, pressure=255, **LABELS )
        self.adb.write( "%s\n" % (cmd,) )
        sleep(0.050)
        for line in self.adb.read(0.01):
            print "swipe:", line.rstrip()
