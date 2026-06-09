#worldmapgenerator.py

import pygame as pg
from random import random, seed, randint
from math import sqrt
import sys

#a point representing a potential corner or a land segment
class Vertex:
    def __init__(self, p):
        self.x = p[0]
        self.y = p[1]
        self.conn = []

    def __lt__(self, v):
        return self.x < v.x

#a polygon representing a segment of land
class Land:
    def __init__(self, points):
        self.points = points
        self.temp = 0
        self.rain = 0
        self.col = (0, 0, 0)

    def climate(self, temp, rain):
        self.temp = temp
        self.rain = rain
        self.col = (min(max(255*(1-rain)+400*max(s-temp, 0)**0.8+200*max(temp-d,0), 0), 255),
                    min(max(255*(rain+0.3)+400*max(s-temp, 0)**0.8+300*max(temp-d,0), 0), 255),
                    min(max(600*max(s-temp, 0)**0.7+75*max(temp-d, 0), 0), 255))


    def draw(self):
        pg.draw.polygon(window, self.col, [veiw(p) for p in self.points])

def veiw(p):
    #translates the absolute position to the displayed position
    return (p.x+offx)*zoom+hW, (p.y+offy)*zoom+hH

def cross_prod(A, B, C):
    #finds the 2d cross product to determine the orientation of ABC
    return (C.x - A.x) * (B.y - A.y) - (B.x - A.x) * (C.y - A.y)

def intersects(l1, l2):
    #tests if the lines intersect with an orientation based method
    p1, q1 = l1
    p2, q2 = l2
    if (max(p1.x, q1.x) < min(p2.x, q2.x)
        or min(p1.x, q1.x) > max(p2.x, q2.x)
        or max(p1.y, q1.y) < min(p2.y, q2.y)
        or min(p1.y, q1.y) > max(p2.y, q2.y)):
        return False

    cp1 = cross_prod(p1, p2, q2)
    cp2 = cross_prod(q1, p2, q2)
    cp3 = cross_prod(p1, q1, p2)
    cp4 = cross_prod(p1, q1, q2)

    if ((cp1 > 0 and cp2 < 0) or (cp1 < 0 and cp2 > 0)) and ((cp3 > 0 and cp4 < 0) or (cp3 < 0 and cp4 > 0)):
        return True

    return False

def completes(v0, v, depth):
    #checking if v0 connects with v in depth number of lines
    if depth == 0:
        if v0 == v:
            return True, []
        else:
            return False, []
    for nextv in v.conn:
        done, vs = completes(v0, nextv, depth-1)
        if done:
            if v in vs:
                return False, []
            return done, vs+[v]
    return False, []

def validateline(v1, v2, lines, linetries):
    #checking if line already exists or completes a 3-4 sided shape or crosses an exisisting line
    if v1 in v2.conn:
        return False
    for v3 in v2.conn:
        if v1 in v3.conn:
            return False
        for v4 in v3.conn:
            if v1 in v4.conn:
                return False
            
    for l in sorted(lines, key=lambda l: (l[0].x-v1.x)**2+(l[0].y-v1.y)**2)[:linetries*4]:
        if intersects((v1, v2), l):
            return False
                
    return True

def generate(nv=2000, nl=400):
    #generate a list of land instances making up a "world map"
    packing_min_dist2 = W*H*0.907/(2.598*nv)
    linetries = int(4*nv/1000)
    verts = []
    for i in range(nv):
        too_close = True
        while too_close:
            v = (random()*W-hW, random()*H-hH)
            too_close = False
            for v2 in verts:
                if (v[0]-v2.x)**2 + (v[1]-v2.y)**2 < packing_min_dist2 * (0.2+8*abs(v[1])/H)**0.5:
                    too_close = True
                    break
        verts.append(Vertex(v))

    lines = []

    #let each vertex draw up to 2 lines to the nearest valid neighbours
    for v1 in verts:
        closest = sorted(verts, key=lambda v2: (v2.x-v1.x)**2+(v2.y-v1.y)**2)[:linetries]
        closest.remove(v1) #remove itself
        for i in range(2):
            valid = False
            while not valid:
                if not len(closest):
                    break
                
                valid = validateline(v1, closest[0], lines, linetries)
                if valid:
                    lines.append((v1, closest[0]))
                    v1.conn.append(closest[0])
                    closest[0].conn.append(v1)
                else:
                    closest.pop(0)

    #creates list of Land instances from completed polygons
    lands = []
    unused = verts[:]
    while len(lands) < nl:
        randx = 2*(random()*W-hW)/3
        randy = 2*(random()*H-hH)/3
        n = int(random()*50*nl/400)
        for i, v in enumerate(sorted(unused, key=lambda v: (v.x-randx)**2+(v.y-randy)**2)[:n]):
            unused.remove(v)
            for depth in range(5,10):
                complete, poly = completes(v, v, depth)
                if complete:
                    if sorted(poly) not in (sorted(l.points) for l in lands):
                        lands.append(Land(poly))

    for l1 in lands:
        n = 0
        for l2 in lands:
            if sum(v in l2.points for v in l1.points)>=2:
                n += 1
        l1.climate((1-2*abs(sum(v.y for v in l1.points)/len(l1.points))/H)**2, 1-min(n/16, 1))

    return lands[:nl]

#SETTINGS
W = 600
H = 300
BG = (100, 200, 200)
s = 0.4 #higher values mean more snow is displayed
d = 0.3 #lower values mean more desert is displayed
worldseed = None #manually force the worldseed here

hW = W//2
hH = H//2

#camera
offx, offy, zoom = 0, 0, 1
dragging = False
terrain = False

#pygame setup
pg.init()
window = pg.display.set_mode((W, H))

#by default worldseed will take a command-line argument or pick randomly
if worldseed is None:
    if len(sys.argv) >= 2:
        worldseed = int(sys.argv[1])
    else:
        worldseed = randint(1,100)
        
seed(worldseed)
print("Seed:",worldseed)
world = generate()

#main loop
running = True
while running:
    window.fill(BG)

    #drawing each lands polygon
    for l in world:
        l.draw()

    pg.display.flip()
    for e in pg.event.get():
        if e.type == pg.QUIT:
            running = False
        #zooming
        elif e.type == pg.MOUSEWHEEL:
            zoom *= 1.5**(e.y)
        #panning
        elif e.type == pg.MOUSEBUTTONDOWN:
            if e.button == 1:
                dragging = True
                dragx, dragy = pg.mouse.get_pos()
        elif e.type == pg.MOUSEBUTTONUP:
            if e.button == 1:
                dragging = False
        if dragging:
            if e.type == pg.MOUSEMOTION:
                dx = e.pos[0] - dragx
                dy = e.pos[1] - dragy
                offx += dx/zoom
                offy += dy/zoom
                dragx, dragy = e.pos

pg.quit()
