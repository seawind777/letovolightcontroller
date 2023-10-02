import random
import sacn
import time
import RPi.GPIO as GPIO
import time


class Universe:
    def __init__(self, number):
        self.number = number
        self.dmx = [0] * 513
        self.busy_channels = [False] * 513
    def clear(self):
        self.dmx = [0] * 513


class Scene:
    def __init__(self, universe):
        self.groups = []
        self.universe = universe

    def add_row(self):
        self.groups.append(Group())

    def add_light(self, group, fixture_name, dmx_ch):
        if group > len(self.groups):
            self.add_row()
        self.groups[group - 1].add_light(fixture_name, dmx_ch, self.universe)

    def generate_new(self):
        colors = [(0,0,255),(255,0,0),(0,255,0), (0,255,255), (255, 255, 0), (255,0,255), (255, 255, 255)]
        fx = ['F&L', 'All', 'Every2']
        for group in self.groups:
            group.set_lights(random.choice(colors), random.choice(colors), random.choice(fx))



class Group:
    def __init__(self):
        self.lights = []

    def add_light(self, fixture_name, dmx_ch, universe):
        self.lights.append(Fixture(fixture_name, dmx_ch, universe))

    def set_lights(self, RGB1, RGB2, FX='none'):
        print(FX)
        print(RGB1)
        print(RGB2)
        if FX == 'F&L':
            for i in range(len(self.lights)):
                if i == 0 or i == len(self.lights)-1:
                    self.lights[i].set_dmx(255, RGB1)
                else:
                    self.lights[i].set_dmx(255, RGB2)

        elif FX == 'Every2':
            for i in range(len(self.lights)):
                if i%2 == 0:
                    self.lights[i].set_dmx(255, RGB1)
                else:
                    self.lights[i].set_dmx(255, RGB2)

        else:
            for light in self.lights:
                light.set_dmx(255, RGB1)




class Fixture:
    def __init__(self, fixture_name, dmx_ch, universe):
        self.dmx_protocol = ['red', 'green', 'blue','intensity', 'none']
        self.universe = universe
        self.dmx_ch = dmx_ch
        self.channels_num = len(self.dmx_protocol)
        if True in universe.busy_channels[self.dmx_ch: (self.dmx_ch + self.channels_num)]:
            print('каналы прожекторов пересекаются')

        for i in range(self.dmx_ch, (self.dmx_ch + self.channels_num)):
            universe.busy_channels[i] = True

    def set_dmx(self, intensity, RGB):
        for i in range(self.channels_num):
            if self.dmx_protocol[i]=='intensity':
                self.universe.dmx[self.dmx_ch + i] = intensity
            elif self.dmx_protocol[i] == 'red':
                self.universe.dmx[self.dmx_ch + i] = RGB[0]
            elif self.dmx_protocol[i] == 'green':
                self.universe.dmx[self.dmx_ch + i] = RGB[1]
            elif self.dmx_protocol[i] == 'blue':
                self.universe.dmx[self.dmx_ch + i] = RGB[2]
            #elif self.dmx_protocol[i] == 'pan':
            #    self.universe.dmx[self.dmx_ch - 1+ i] = pan
            #elif self.dmx_protocol[i] == 'tilt':
            #    self.universe.dmx[self.dmx_ch - 1 + i] = tilt
            else:
                self.universe.dmx[self.dmx_ch + i] = 0



uni = Universe(1)
scene = Scene(uni)

row1 = [61, 271, 276, 281]
row2 = [104, 372, 377, 387]
row3 = [53, 99, 201, 391]

scene.add_light(1, "a", 66)
scene.add_light(1, "a", 281)
scene.add_light(1, "a", 276)
scene.add_light(1, "a", 271)
scene.generate_new()

sender = sacn.sACNsender(bind_port=5569)
sender.start()
sender.activate_output(1)  # start sending out data in the 1st universe
sender[1].multicast = True

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.IN)

last_but=1
press_time=-1000

while True:
    
    if GPIO.input(5)!=last_but and last_but==1 and time.time()-press_time>=0.1:
        scene.generate_new()
        press_time = time.time()
        last_but=0
    elif GPIO.input(5)==0 and time.time()-press_time>=1:
        print(press_time)
        uni.clear()
    elif GPIO.input(5)!=last_but and last_but==0:
        last_but = 1
        
    
    
    sender[1].dmx_data = uni.dmx[1:513]
    time.sleep(0.01)