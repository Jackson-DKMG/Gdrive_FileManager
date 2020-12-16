from random import randint, randrange, shuffle, choice, uniform
from time import sleep
from turtle import Turtle, Screen
from screeninfo import get_monitors

class forest():
    def __init__(self):
        super().__init__()

        #self.setBackground()
        self.forest()

    def setBackground(self):
        try:
            self.t = Turtle()
            self.t.shape("circle")
            self.t.speed(15)
            self.t.turtlesize(0.01)
            self.w = get_monitors()[0].width
            self.h = get_monitors()[0].height
            Screen().setup(self.w, self.h, startx=0, starty=0)
        except Exception as e:
            print(e)
            try:
                del self.t
            except:
                pass
            Screen().bye()
            Screen().exitonclick()

        self.t.screen.colormode(1.0)
        COLOR = (uniform(0,1), uniform(0,1), uniform(0,1))#(1,0,0)#(0.39, 0.57, 0.9258)
        TARGET = (uniform(0,1), uniform(0,1), uniform(0,1))#(1,1,0) #(0.5625, 0.9297, 0.5625)

        screen = Screen()
        screen.tracer(False)

    #print(screen.window_width(), screen.window_height())

    #screen.screensize(1980,1024)
    #screen.setup(width=1.0, height=1.0)
        canvas = screen.getcanvas()
        root = canvas.winfo_toplevel()
        root.overrideredirect(1)

        WIDTH, HEIGHT = get_monitors()[0].width,get_monitors()[0].height #screen.window_width(), screen.window_height()

        deltas = [(hue - COLOR[index]) / HEIGHT for index, hue in enumerate(TARGET)]

        self.t.color(COLOR)

        self.t.penup()
        self.t.goto(-WIDTH/2, HEIGHT/2)
        self.t.pendown()

        direction = 1


        for distance, y in enumerate(range(HEIGHT//2, -HEIGHT//2, -1)):

            self.t.forward(WIDTH * direction)
            self.t.color([COLOR[i] + delta * distance for i, delta in enumerate(deltas)])
            self.t.sety(y)

            direction *= -1

        screen.tracer(True)
        self.t.screen.colormode(255)


    def foliage(self):
        self.t.begin_fill()
        self.t.pen(pencolor='lime')
        self.t.fillcolor('lime')
        self.t.circle(randint(5,30))
        self.t.end_fill()
    
    def star(self):
        distance = randint(10,30)
        self.t.pensize(0.5)
        color = (randint(0, 255), randint(0, 255), randint(0, 255))
        self.t.setheading(90)
        self.t.begin_fill()
        for i in range(5):
            self.t.pencolor(color)
            self.t.fd(distance)
            self.t.rt(120)
            self.t.fd(distance)
            self.t.rt(-48)
        self.t.fillcolor(color)
        self.t.end_fill()
        self.t.setheading(0)

    
    def multistar(self):
        try:
            self.t.setheading(90)
            self.t.pensize(2)
            angle = 20
            distance = randint(10,30)
            counter = 0
            while not counter == int(360 / angle):
                color = (randint(0, 255), randint(0, 255), randint(0, 255))
                #self.t.begin_fill()
                self.t.pencolor(color)
                self.t.fd(distance)
                self.t.rt(180 - angle)
                #self.t.rt(angle)
                self.t.fd(distance)
                #self.t.fillcolor(randint(0, 255), randint(0, 255), randint(0, 255))
                self.t.rt(360 - angle)
                #self.t.rt(angle)
                self.t.fd(distance)
                #self.t.fillcolor(randint(0, 255), randint(0, 255), randint(0, 255))
                counter += 1
            self.t.setheading(0)
        except:
            pass

    def flower(self):
        try:
            i = randint(5,15)
            self.t.pensize(0.01)

            for j in range(5):
                self.t.pencolor('black')
                self.t.begin_fill()
                self.t.fillcolor('white')
                self.t.circle(i)
                self.t.end_fill()
                self.t.rt(72)
                self.t.fd(i)
            self.t.rt(108)
            self.t.fd(9 * i / 5)
            self.t.setheading(0)
            self.t.pencolor('black')
            self.t.begin_fill()
            self.t.fillcolor('red')
            self.t.circle(i)
            self.t.end_fill()
        except:
            pass

    def invertedFlower(self):
        try:
            i = randint(5,15)
            self.t.pensize(0.01)

            for j in range(5):
                self.t.pencolor('black')
                self.t.begin_fill()
                self.t.fillcolor('red')
                self.t.circle(i)
                self.t.end_fill()
                self.t.rt(72)
                self.t.fd(i)
            self.t.rt(108)
            self.t.fd(9 * i / 5)
            self.t.setheading(0)
            self.t.pencolor('black')
            self.t.begin_fill()
            self.t.fillcolor('white')
            self.t.circle(i)
            self.t.end_fill()
        except:
            pass

    def randomFlower(self):
        try:
            i = randint(5,15)
            self.t.pensize(0.01)

            colors = ('yellow', 'blue', 'red', 'lime', 'green', 'white', 'magenta', 'blue violet', 'deep pink', 'orange', 'spring green','aquamarine', 'cyan', 'black', 'slate gray', 'silver')
            petals = choice(colors)
            center = choice(colors)
            while not center != petals:
                center = choice(colors)
            for j in range(5):
                self.t.pencolor('black')
                self.t.begin_fill()
                self.t.fillcolor(petals)
                self.t.circle(i)
                self.t.end_fill()
                self.t.rt(72)
                self.t.fd(i)
            self.t.rt(108)
            self.t.fd(9 * i / 5)
            self.t.setheading(0)
            self.t.pencolor('black')
            self.t.begin_fill()
            self.t.fillcolor(center)
            self.t.circle(i)
            self.t.end_fill()
        except:
            pass

    def tree(self,x,color,size,trunk):
        try:
            self.t.penup()
            self.t.setx(x)
            self.t.sety(-500)
            self.t.pendown()
            self.t.dot(0.1, 'white')
            self.t.pen(pencolor=color,pensize=size, speed=15)
            #self.t.setheading(randrange(-20,20))
            self.t.rt(randrange(-110,-70))
            self.t.fd(trunk)
            positions = []
            [x,y] = self.t.xcor(),self.t.ycor()
            positions.append([x,y])

            templist = []

            for i in range(1,4):
                for j in positions:
                    self.t.penup()
                    self.t.goto(j[0],j[1])
                    self.t.pendown()
                    self.t.setheading(90)
                    self.t.rt(randint(40,80))
                    self.t.pensize(15/i + randrange(0, 5))
                    self.t.fd(300/i +randrange(-20, 20))
                    [x,y] = self.t.xcor(),self.t.ycor()
                    templist.append([x,y])
                    self.t.penup()
                    self.t.goto(j[0], j[1])
                    self.t.pendown()
                    self.t.setheading(90)
                    self.t.rt(randrange(-20, 20))
                    self.t.pensize(15 / i + randrange(0, 5))
                    self.t.fd(300 / i + randrange(-20, 20))
                    [x, y] = self.t.xcor(), self.t.ycor()
                    templist.append([x, y])
                    self.t.penup()
                    self.t.goto(j[0], j[1])
                    self.t.pendown()
                    self.t.setheading(90)
                    self.t.rt(-randint(40, 80))
                    self.t.pensize(15 / i + randrange(0, 5))
                    self.t.fd(300 / i + randrange(-20, 20))
                    [x, y] = self.t.xcor(), self.t.ycor()
                    if not (x > self.w/2 or x < -self.w/2):     #if the branch is out of the screen, don't bother drawing something at its tip.
                        templist.append([x, y])
                    else:
                        pass

                positions = []
                shuffle(templist)
                if i < 3 :
                    for v in templist:
                        positions.append(v)
                    templist = []

                else:
                    shuffle(templist)
                    l = [self.flower, self.invertedFlower, self.foliage, self.randomFlower]
                    shuffle(l)
                    fn = choice(l)
                    self.t.setheading(0)
                    for j in templist:
                        self.t.penup()
                        self.t.goto(j[0], j[1])
                        self.t.pendown()
                        fn()
        except:
            pass

    def forest(self):
        self.setBackground()

        try:
            positions = [-750,-600,-450,-300,-100,100,300,450,600,750]
            shuffle(positions)
            colors = ['saddle brown', 'maroon', 'dark red', 'brown', 'firebrick', 'sienna', 'peru', 'burlywood', 'tan']
            for i in range(10):
                    color = colors[randint(0,8)]
                    x = positions[i] + randrange(-50,50)
                    size = randint(20,50)
                    trunk = randint(100,400)
                    self.tree(x,color,size,trunk)

            #€del self.t
            sleep(5)
            #Screen().bye()
            Screen().clear()
            self.forest()
        except:
            #del self.t
            Screen().exitonclick()
            Screen().bye()

            #pass
        #self.t.getscreen()


