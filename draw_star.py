#!/usr/bin/python
import os
import sys
import math
import subprocess
from AdbSessionBatch import AdbSession
from LineAlgo import bresenham

def runcmd( cmd ):
    print cmd
    status = subprocess.call( cmd, shell=True )
    return status

class TrivialAdbSession:
    def __init__(self):
        pass

    def tap( x, y ):
        runcmd( "adb shell input touchscreen tap %d %d" % (x,y) )

    def swipe( self, x1, y1, x2, y2, duration=100 ):
        #print swipe
        runcmd( "adb shell input touchscreen swipe %d %d %d %d %d" % (x1,y1,x2,y2,duration) )

    def draw( self, points ):
        allcmd=[]
        for p in zip(points[:-1],points[1:]):
            cmd="input swipe %d %d %d %d" % (p[0][0],p[0][1],p[1][0],p[1][1])
            allcmd.append(cmd)
        runcmd( "echo \"%s;exit\" | adb shell"% ( "; ".join(allcmd), ) )

class PrintAdbSession:

    def __init__(self):
        pass

    def swipe( self, x1, y1, x2, y2, duration=100 ):
        print "input touchscreen swipe %d %d %d %d %d" % (x1,y1,x2,y2,duration)


class Turtle:
    def __init__( self, adb_session ):
        self.x = 0
        self.y = 0
        self.ang = 0
        self.drawing = False
        self.session = adb_session
        self.step = 50

    def angle( self, a ):
        self.ang = a

    def penup( self ):
        if self.drawing:
            self.drawing = False
            self.session.swipe_end()

    def pendown( self ):
        if not self.drawing:
            self.session.swipe_begin( self.x, self.y )
            self.drawing = True

    def moveTo( self, x, y ):
        if self.drawing:
            self.session.swipe_move( x, y )
        self.x = x
        self.y = y

    def moveRel( self, dx, dy ):
        if self.drawing:
            self.session.swipe_move( self.x+dx, self.y+dy )
        self.x = self.x + dx
        self.y = self.y + dy

    def forward( self, amt ):
        dx = amt*math.cos(self.ang*(math.pi/180))
        dy = amt*math.sin(self.ang*(math.pi/180))
        self.moveRel( dx, dy )

    def left( self, a ):
        self.ang = self.ang - a

    def right( self, a ):
        self.ang = self.ang + a

def side( t, L, n ):
    if n==0:
        t.forward( L )
    else:
        side( t, L/3., n-1 )
        t.left( 60 )
        side( t, L/3., n-1 )
        t.right( 120 )
        side( t, L/3., n-1 )
        t.left( 60 )
        side( t, L/3., n-1 )

def star( t, L, n ):
    t.penup()
    x0 = L/2
    y0 = L*math.sqrt(3)/4
    t.moveRel( -x0, -y0 )
    t.pendown()
    side( t, L, n )
    t.right( 120 )
    side( t, L, n )
    t.right( 120 )
    side( t, L, n )
    t.right( 120 )
    t.penup()
    t.moveRel( x0, y0 )

#p = TrivialAdbSession()
p = AdbSession()
t = Turtle( p )

if False:
    t.moveTo( 500, 500 )
    t.pendown()
    t.forward( 300 )
    t.right( 90 )
    t.forward( 300 )
    t.right( 90 )
    t.forward( 300 )
    t.right( 90 )
    t.forward( 300 )
    t.right( 90 )

t.angle(0)
t.moveTo( 1200/2, 1920/2 )

star( t, 800, 4 )

sys.exit(0)

sz = 500
while sz<1000:

    n = math.log(sz/20.)/math.log(3)
    star( t, sz, int(n) )

    sz = sz + sz/3
