import pygame
import random
import math
import euclid
import matplotlib.pyplot as plt

# Screen Initialization
pygame.init()
screen_width = 700
screen_height = 700
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Pressure Demon Simulation")
background_color = (255, 255, 255)
screen.fill(background_color)
pygame.display.update()

# Time Stuff
fps_limit = 60
clock = pygame.time.Clock()

# Initializing Important Values
avg_speed = 400
plug_y = 100
rope_width = 3
gravity = 5
max_length = 150
deflector_height = 10
deflector_on = False
runtime = 60
bit_error = 0

# Size Values
num_particles = 10
particle_radius = 10

# Mass Values
particle_mass = 10
plug_mass = 100

# Entropy Stuff
bit_length = 16  # Each Character Has 2^16= 65536 Different Values
character_values = int(math.pow(2, bit_length))
total_information = 0
energy_transfer = 0

# Graphing Vals
time_vals = []
info_vals = []
height_vals = []
energy_vals = []

# Simulation End Vals
end_simulation = 5  # In Seconds
completely_fallen = False
time_stamp = 0

# Deflector Checkers
successful_deflects = 0
failed_deflects = 0

class Particle:
    def __init__(self, color, position, radius, speed, velocity, mass, width=0):
        self.color = color
        self.position = position
        self.radius = radius
        self.speed = speed
        self.velocity = velocity
        self.mass = mass
        self.width = width
        self.deflector_trajectory = False

    def display(self):
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), self.radius, self.width)

    def display_info(self):
        print("Position: " + str(self.position) + " Velocity: " + str(self.velocity))

    def move(self):
        self.position += self.velocity * dtime
        self.perimeter_bounce()
        self.plug_bounce()
        if deflector_on:
            self.deflector_bounce()
        else:
            self.bottom_bounce()

    def perimeter_bounce(self):
        # Check for Perimeter Bounce
        if self.position.x <= self.radius:
            self.position.x = 2*self.radius - self.position.x
            self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))
        elif self.position.x >= screen_width - self.radius:
            self.position.x = 2*(screen_width - self.radius) - self.position.x
            self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))
        if self.position.y <= (plug_y + self.radius):
            self.position.y = 2 * plug_y + 2 * self.radius - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))
        elif self.position.y >= (screen_height - self.radius):
            self.position.y = 2*screen_height-2*self.radius-self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

    def plug_bounce(self):
        global energy_transfer
        if (plug.y - self.radius) <= self.position.y <= (plug.y + plug.height + self.radius):
            if (screen_width - plug.width) / 2 - self.radius <= self.position.x <= (screen_width - plug.width) / 2:
                self.position.x = screen_width - plug.width - 2 * self.radius - self.position.x
                self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))
            elif (screen_width + plug.width) / 2 <= self.position.x <= (screen_width + plug.width) / 2 + self.radius:
                self.position.x = screen_width + plug.width + 2 * self.radius - self.position.x
                self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))
        if (plug.y + plug.height <= self.position.y <= plug.y + plug.height + self.radius) and ((screen_width - plug.width) / 2) - self.radius <= self.position.x <= ((screen_width + plug.width) / 2) + self.radius:
            global successful_deflects
            old_velocity = plug.velocity.y
            new_velocities = elastic_collision(self.velocity, self.mass, plug.velocity, plug.mass)
            self.velocity = new_velocities[0]
            plug.velocity = new_velocities[1]
            energy_transfer += abs(old_velocity - plug.velocity.y)
            self.position.y = 2 * (plug.y + plug.height + self.radius) - self.position.y
            if self.deflector_trajectory:
                successful_deflects += 1
                self.deflector_trajectory = False
        if (plug.y - self.radius <= self.position.y <= plug.y) and ((screen_width - plug.width) / 2) - self.radius <= self.position.x <= ((screen_width + plug.width) / 2) + self.radius:
            old_velocity = plug.velocity.y
            new_velocities = elastic_collision(self.velocity, self.mass, plug.velocity, plug.mass)
            self.velocity = new_velocities[0]
            plug.velocity = new_velocities[1]
            energy_transfer += abs(old_velocity - plug.velocity.y)
            self.position.y = 2 * plug.y - 2 * self.radius - self.position.y

    def deflector_bounce(self):
        on_deflector = False
        if self.position.y >= screen_height - deflector_height - self.radius:
            for a_deflector in all_deflectors:
                if a_deflector.x <= self.position.x <= a_deflector.x + a_deflector.width:
                    on_deflector = True
                    self.position.y = 2*(screen_height - deflector_height - self.radius) - self.position.y
                    self.velocity = demon.redirect_particle(self)
                    self.deflector_trajectory = True
            if not on_deflector:
                self.position.y = 2 * (screen_height - self.radius - deflector_height) - self.position.y
                self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

    def bottom_bounce(self):
        if self.position.y >= (screen_height - deflector_height - self.radius):
            self.position.y = 2 * (screen_height - self.radius - deflector_height) - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

    def surface_distance(self, other_circle, time):
        radii = self.radius + other_circle.radius
        pos_self = self.position + self.velocity * time
        pos_other = other_circle.position + other_circle.velocity * time
        pos = abs(pos_self - pos_other)
        return pos - radii

    def collide(self, other_circle):
        if self.surface_distance(other_circle, dtime) <= 0:
            global failed_deflects
            collision_vector = self.position - other_circle.position
            collision_vector.normalize()
            self.velocity = self.velocity.reflect(collision_vector)
            other_circle.velocity = other_circle.velocity.reflect(collision_vector)
            while self.surface_distance(other_circle, dtime) <= 0:
                self.position += self.velocity * dtime
                other_circle.position += other_circle.velocity * dtime
            if self.deflector_trajectory:
                self.deflector_trajectory = False
                failed_deflects += 1
            if other_circle.deflector_trajectory:
                other_circle.deflector_trajectory = False
                failed_deflects += 1

    def to_binary(self):
        x_binary = int(self.position.x * character_values / screen_width)
        x_binary = bin(x_binary)
        y_binary = int(self.position.y * character_values / screen_height)
        y_binary = bin(y_binary)

        x_binary = binary_converter(x_binary)
        y_binary = binary_converter(y_binary)
        return [x_binary, y_binary]

class Plug:
    def __init__(self, width, height, y, weight, mass, velocity=0):
        self.width = width
        self.height = height
        self.y = y
        self.weight = weight
        self.mass = mass
        self.velocity = euclid.Vector2(0, velocity)
        self.contact_point = euclid.Vector2(screen_width/2, self.y + self.height)

    def move(self):
        self.y += self.velocity.y * dtime

    def update_velocity(self):
        self.velocity.y += gravity * dtime

    def display(self):
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect((screen_width-self.width)/2, self.y, self.width, self.height))

class Rope:
    def __init__(self, width):
        self.width = width
        self.wall_attachment = ((screen_width-self.width)/2, plug_y)
        self.plug_attachment = None

    def update(self):
        self.plug_attachment = ((screen_width-self.width)/2, plug.y)

    def display(self):
        #self.update()
        pygame.draw.line(screen, (169, 169, 169), self.wall_attachment, self.plug_attachment, self.width)

class Deflector:
    def __init__(self, width, height, x_val, color):
        self.width = width
        self.height = height
        self.x = x_val
        self.color = color

    def display(self):
        pygame.draw.rect(screen, self.color, pygame.Rect(self.x, screen_height - self.height, self.width, self.height))

class Demon:
    def __init__(self, probability):
        self.probability = probability

    def bit_error(self, actual_particle):
        error_particle = Particle(actual_particle.color, euclid.Vector2(actual_particle.position.x, actual_particle.position.y), actual_particle.radius, actual_particle.speed, euclid.Vector2(actual_particle.velocity.x, actual_particle.velocity.y), actual_particle.mass)
        binary_vals = error_particle.to_binary()
        new_vals = []
        for val in binary_vals:
            for bit in range(len(val) - 1):
                prob = random.uniform(0, 1)
                if prob < self.probability:
                    if val[bit]:
                        val[bit] = False
                    else:
                        val[bit] = True
            new_vals.append(int_converter(val))
        error_particle.position.x = new_vals[0] * screen_width / character_values
        error_particle.position.y = new_vals[1] * screen_height / character_values
        return error_particle

    def redirect_particle(self, given_particle):
        self.entropy()
        error_particle = self.bit_error(given_particle)
        direction = plug.contact_point - error_particle.position
        direction.normalize()
        if direction.y > 0:
            direction.y *= -1
        return direction * given_particle.speed

    def entropy(self):
        global total_information
        probability = 1 / character_values
        total_information += math.log(1/probability, 2)

def get_random_velocity(overall_speed):
    new_angle = random.uniform(0, math.pi*2)
    new_x = math.cos(new_angle)
    new_y = math.sin(new_angle)
    new_vector = euclid.Vector2(new_x, new_y)
    new_vector.normalize()
    new_vector = new_vector * overall_speed
    return new_vector

def create_deflectors(amount, width, height, color):
    deflectors = []
    gap = (screen_width - width * amount) / (amount + 1)
    x_location = gap
    for j in range(amount):
        deflectors.append(Deflector(width, height, x_location, color))
        x_location = x_location + gap + width
    return deflectors

def elastic_collision(A, mA, B, mB):
    vA = A.y
    vB = B.y
    vAf = vA*(mA-mB)/(mA+mB) + vB*(2*mB)/(mA+mB)
    vBf = vA*(2*mA)/(mA+mB) + vB*(mB-mA)/(mB+mA)
    A.y = vAf
    B.y = vBf
    return [A, B]

def binary_converter(string):  # Last Digit Signals Sign (False-neg, True-pos)
    if string[0] == '-':
        coefficient = False
        useless_chars = 3
    else:
        coefficient = True
        useless_chars = 2
    output = []
    for counter in range(bit_length):
        output.append(False)
    for counter in range(len(string) - useless_chars):
        if string[counter + useless_chars] == '1':
            output[bit_length + useless_chars - len(string) + counter] = True
    output.append(coefficient)
    return output

def int_converter(binary_val):
    length = len(binary_val) - 1
    power = length - 1
    output = 0
    for counter in range(length):
        if binary_val[counter]:
            output += math.pow(2, power - counter)
    if not binary_val[length]:
        output *= -1
    return int(output)

# Object Creation
demon = Demon(bit_error)
plug = Plug(100, 100, plug_y, 0, plug_mass)
rope = Rope(rope_width)
rope.update()
all_particles = []
all_deflectors = create_deflectors(10, 65, deflector_height, (255, 255, 0))
deflector_background = pygame.Rect(0, screen_height - deflector_height, screen_width, deflector_height)
container = pygame.Rect(0, plug_y, screen_width, screen_height-plug_y)
initial_angles = []
numberings = []
for i in range(num_particles):
    x_coord = random.randint(particle_radius, screen_width-particle_radius)
    y_coord = random.randint(plug_y + plug.height + particle_radius, screen_height - particle_radius)
    my_velocity = get_random_velocity(avg_speed)
    particle = Particle((0, 0, 200), euclid.Vector2(x_coord, y_coord), particle_radius, avg_speed, my_velocity, particle_mass)
    all_particles.append(particle)
    angle = math.atan(particle.velocity.y / particle.velocity.x)
    if particle.velocity.x >= 0 and particle.velocity.y >= 0:
        pass
    elif particle.velocity.x >= 0 > particle.velocity.y:
        angle += 2 * math.pi
    elif particle.velocity.x < 0 <= particle.velocity.y:
        angle += math.pi
    elif particle.velocity.x < 0 and particle.velocity.y < 0:
        angle += math.pi
    angle = int(angle*180/math.pi)
    initial_angles.append(angle)
    numberings.append(i + 1)

running = True
t0 = pygame.time.get_ticks()
while running:
    if (pygame.time.get_ticks() - t0) >= (runtime * 1000):
        running = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    dtime_ms = clock.tick(fps_limit)
    dtime = dtime_ms / 1000  # dtime is a constant

    screen.fill(background_color)
    pygame.draw.rect(screen, (173, 216, 230), container)
    plug.update_velocity()
    if plug.y < plug_y:
        plug.y = plug_y
        plug.velocity = euclid.Vector2(0, 0)
    elif (rope.plug_attachment[1] - rope.wall_attachment[1]) < max_length:
        plug.move()
        rope.update()
    else:
        if completely_fallen:
            if (pygame.time.get_ticks() - time_stamp) >= (end_simulation * 1000):
                running = False
                print("Plug Fell: Failure")
        else:
            completely_fallen = True
            time_stamp = pygame.time.get_ticks()
    plug.display()
    rope.display()

    pygame.draw.rect(screen, (0, 0, 0), deflector_background)
    for deflector in all_deflectors:
        deflector.display()
    for i, my_particle in enumerate(all_particles):
        my_particle.move()
        for second_particle in all_particles[i+1:]:
            my_particle.collide(second_particle)
        my_particle.display()
    pygame.display.update()

    # Variables for Graphing
    info_vals.append(total_information)
    graph_height = max_length - (plug.y - plug_y)  # Height of Plug Represents Energy Transfer
    height_vals.append(graph_height)
    time_vals.append((pygame.time.get_ticks() - t0)/1000)
    energy_vals.append(energy_transfer)
final_angles = []
for particle in all_particles:
    angle = math.atan(particle.velocity.y / particle.velocity.x)
    if particle.velocity.x >= 0 and particle.velocity.y >= 0:
        pass
    elif particle.velocity.x >= 0 > particle.velocity.y:
        angle += 2 * math.pi
    elif particle.velocity.x < 0 <= particle.velocity.y:
        angle += math.pi
    elif particle.velocity.x < 0 and particle.velocity.y < 0:
        angle += math.pi
    angle = int(angle*180/math.pi)
    final_angles.append(angle)

'''
plt.scatter(numberings, initial_angles)
plt.show()
plt.scatter(numberings, final_angles)
plt.show()
'''

# Graphing
'''
fig, axs = plt.subplots(3)
fig.suptitle("High Pressure Demon Simulation Results")
axs[0].plot(time_vals, info_vals)
axs[0].set_xlabel('Time', fontsize=8)
axs[0].set_ylabel('Information', fontsize=8)
axs[0].set_title("Information vs Time")
axs[1].plot(time_vals, energy_vals)
axs[1].set_xlabel('Time', fontsize=8)
axs[1].set_ylabel('Energy Transfer', fontsize=8)
axs[1].set_title("Energy Transfer vs Time")
axs[2].plot(energy_vals, info_vals)
axs[2].set_xlabel('Energy Transfer', fontsize=8)
axs[2].set_ylabel('Information', fontsize=8)
axs[2].set_title("Energy Transfer vs Information")
fig.align_labels()
plt.tight_layout()
#plt.savefig("High Pressure Demon Results.png")
plt.show()
'''

# Goals
# Find Probability for Entropy
