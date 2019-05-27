import math

import pygame
from pygame.color import Color
import pymunk
from pymunk import Vec2d
from pymunk.pygame_util import DrawOptions

collision_types = {
    "ball": 1,
    "brick": 2,
    "bottom": 3,
    "player": 4,
}

scr_width, scr_height = 0, 0

class PlayerBat(pymunk.Body):
    def __init__(self, space, len):
        super().__init__(mass=10, moment=pymunk.inf)
        self.len = len
        #shape = pymunk.Poly.create_box(self, (self.len, 4), 4)
        shape = pymunk.Segment(self, (-self.len//2, 0), (self.len//2, 0), 4)
        shape.elasticity = 1.0
        shape.friction = 1.0
        shape.collision_type = collision_types['player']
        #self.velocity_func = self.bat_damping
        self.joint = pymunk.constraint.GrooveJoint(space.static_body, self,
                                                   (self.len//2, 100), (scr_width-self.len//2, 100), (0, 0))

        space.add(self, shape, self.joint)

    def bat_damping(self, body, gravity, damping, dt):
        pymunk.Body.update_velocity(body, gravity, 0.96*damping, dt)

class Ball(pymunk.Body):
    ball = None
    def __init__(self, space, radius, isArmed=True):
        super().__init__(mass=1, moment=pymunk.moment_for_circle(1, 0, radius))
        self.radius = radius
        shape = pymunk.Circle(self, self.radius)
        shape.collision_type = collision_types["ball"]
        shape.elasticity = 1.0
        shape.friction = 1.0
        self.velocity_func = self.constant_velocity
        self.isArmed = isArmed
        space.add(self, shape)

    def constant_velocity(self, body, gravity, damping, dt):
        if not self.isArmed:
            body.velocity = body.velocity.normalized() * 500


class Bricks:
    vcount = 10
    hcount = 5

    def __init__(self, space):
        margin = 0.05*scr_width
        width = (scr_width-2*margin)/Bricks.vcount
        height = 0.03*scr_height

        for x in range(0, Bricks.vcount):
            xpos = math.floor(x * width + margin+width/2)
            for y in range(0, Bricks.hcount):
                ypos = math.floor(y * height + 0.75*scr_height)
                brick_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
                brick_body.position = xpos, ypos
                brick_shape = pymunk.Poly.create_box(brick_body, (math.floor(width)-5, math.floor(height)-5))
                brick_shape.elasticity = 1.0
                brick_shape.collision_type = collision_types["brick"]
                space.add(brick_body, brick_shape)

            h = space.add_collision_handler(
                collision_types["brick"],
                collision_types["ball"])
            h.separate = self.remove_brick

    # Make bricks be removed when hit by ball
    def remove_brick(self, arbiter, space, data):
        brick_shape = arbiter.shapes[0]
        space.remove(brick_shape, brick_shape.body)

class Boundary:
    def __init__(self, space):
        bottom_wall = pymunk.Segment(space.static_body, (0, 1), (scr_width, 1), 2)
        bottom_wall.sensor = True
        bottom_wall.collision_type = collision_types["bottom"]

        top_wall = pymunk.Segment(space.static_body, (0, scr_height-1), (scr_width, scr_height-1), 2)
        top_wall.elasticity = 0.99
        left_wall = pymunk.Segment(space.static_body, (0, 1), (0, scr_height-1), 2)
        left_wall.elasticity = 0.99
        right_wall = pymunk.Segment(space.static_body, (scr_width, 1), (scr_width, scr_height-1), 2)
        right_wall.elasticity = 0.99

        space.add(top_wall, left_wall, right_wall, bottom_wall)

class Window:
    window_screen_size = 800, 600

    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        #pygame.key.set_repeat(10,10)
        self.font = pygame.font.SysFont("Arial", 16)

        self.js = None
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.js = pygame.joystick.Joystick(0)
            self.js.init()
            self.axis0 = [-1, -1, -1, -1]
            self.axis = [-1, -1, -1, -1]
            # for i in range(4):
                # self.axis0[i] = self.js.get_axis(i)
            print(self.axis0)

        #self.screen = pygame.display.set_mode(Window.window_screen_size)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        global scr_width
        global scr_height
        scr_width, scr_height = self.screen.get_size()

        pygame.display.set_caption("Breakout")
        self.drawoptions = DrawOptions(self.screen)
        self.clock = pygame.time.Clock()

        self.done = False
        self.space = pymunk.Space()

        self.bat = PlayerBat(self.space, math.floor(0.25*scr_width))
        self.bat.position = scr_width//2, 100

        self.spawn_ball()

        h = self.space.add_collision_handler(
            collision_types["ball"],
            collision_types["bottom"])
        h.separate = self.remove_ball

        Bricks(self.space)
        Boundary(self.space)

    def remove_ball(self, arbiter, space, data):
        ball_shape = arbiter.shapes[0]
        space.remove(ball_shape, ball_shape.body)
        self.spawn_ball()

    def spawn_ball(self):
        radius = math.floor(0.025*scr_height)
        self.ball = Ball(self.space, radius)
        self.ball.position = self.bat.position[0], 100 + self.ball.radius+4
        self.xjoint = pymunk.constraint.GrooveJoint(self.space.static_body, self.ball,
                                                    (self.bat.len//2-1, 100+radius+4),
                                                    (scr_width-self.bat.len//2-1,  100+radius+4), (0, 0))
        self.space.add(self.xjoint)

    def loop(self):
        while not self.done:
            dt = self.clock.tick(60)
            self.space.step(dt/1000.0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.done = True
                    if event.key == pygame.K_RIGHT:
                        #self.bat_body.apply_force_at_local_point((5000*(1),0), (0,0))
                        self.bat.velocity = (600, 0)
                        if self.ball.isArmed:
                            self.ball.velocity = (600, 0)
                    if event.key == pygame.K_LEFT:
                        #self.bat_body.apply_force_at_local_point((5000*(-1),0), (0,0))
                        self.bat.velocity = (-600, 0)
                        if self.ball.isArmed:
                            self.ball.velocity = (-600, 0)
                    if event.key == pygame.K_SPACE:
                        self.ball.isArmed = False
                        print(self.xjoint)
                        self.space.remove(self.xjoint)
                        self.ball.apply_impulse_at_local_point(Vec2d((0, 10)))
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT:
                        self.bat.velocity = (0, 0)
                        if self.ball.isArmed:
                            self.ball.velocity = (0, 0)
                    if event.key == pygame.K_SPACE:
                        pass
                        #spawn_ball()

            if self.js:    
                for i in range(4):
                    self.axis[i] = 1-self.js.get_axis(i)/self.axis0[i]
                l = 0.5*(self.axis[0]+self.axis[1])
                r = 0.5*(self.axis[2]+self.axis[3])
                # t = 0.5*(self.axis[0]+self.axis[2])
                # b = 0.5*(self.axis[1]+self.axis[3])
                self.bat.velocity = (15*(l-r)*400, 0)
            if self.bat.position[0] <= self.bat.len//2+1:
                self.bat.position = self.bat.len//2+1, self.bat.position[1]
            if self.bat.position[0] >= scr_width-self.bat.len//2-1:
                self.bat.position = scr_width-self.bat.len//2-1, self.bat.position[1]

                #self.bat_body.apply_force_at_local_point((5000*(l-r),0), (0,0))

            self.screen.fill(pygame.Color('black'))
            self.space.debug_draw(self.drawoptions)
            # screen.blit(font.render("l{:+.2f} r{:+.2f} d{:+.2f}".format(l, r, l-r), 1, THECOLORS["white"]), (0,0))
            pygame.display.flip()

if __name__ == "__main__":
    window = Window()
    window.loop()
