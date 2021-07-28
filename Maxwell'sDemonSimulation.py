import pygame
import random
import euclid
import math

error_probability = 0
run_time = 90

pygame.init()
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Maxwell's Demon Simulation")
background_color = (0, 100, 100)
screen.fill(background_color)
pygame.display.update()

# Initializing Important Dimensions/Values
num_particles = 60
average_speed = 500
initial_speed = average_speed
boundary_width = 20
door_height = 125
size = 10
end_time = 5
all_sorted = False

# Particle Storing Lists
all_particles = []
correct_particles = []
wrong_particles = []
left_ratio = [0, 0]  # Correct to Incorrect
right_ratio = [0, 0]

# Variables For Speed Tracking
left_sum = 0
left_num = int(num_particles/2)
right_sum = 0
right_num = int(num_particles/2)
left_startavg = 0
right_startavg = 0

# Entropy Stuff
bit_length = 16  # Each Character Has 2^16= 65536 Different Values
character_values = int(math.pow(2, bit_length))
total_entropy = 0
bit_error = 1

# Graph Lists
time_vals = []
entropy_vals = []
energy_transfer = []
percentage_vals = []

# Font Initialization for Text
font = pygame.font.Font('freesansbold.ttf', 18)
font_2 = pygame.font.Font('freesansbold.ttf', 16)

timestamp = 0

clock = pygame.time.Clock()

class Particle:
    def __init__(self, color, position, radius, speed, half, velocity=euclid.Vector2(0, 0), width=0):
        self.color = color
        self.position = position
        self.radius = radius
        self.speed = speed
        self.half = half
        self.velocity = velocity
        self.width = width
        self.correct_half = None
        self.is_passing = False

    def display(self):
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), self.radius, self.width)

    def display_info(self):
        print("Position: " + str(self.position) + " Velocity: " + str(self.velocity))
        print("Half: " + self.half + " Correct Half: " + str(self.correct_half) + " Passing: " + str(self.is_passing))

    def move(self):
        self.position += self.velocity * dtime
        self.bounce()
        self.update_half()
        self.update_passing()

    def change_velocity(self, velocity):
        self.velocity = velocity

    def perimeter_bounce(self):
        if self.position.x <= self.radius:
            self.position.x = 2*self.radius - self.position.x  # self.radius - self.position.x + self.radius
            self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))
        elif self.position.x >= screen_width - self.radius:
            self.position.x = 2*(screen_width - self.radius) - self.position.x
            self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))
        if self.position.y <= self.radius:
            self.position.y = 2 * self.radius - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))
        elif self.position.y >= screen_height - self.radius:
            self.position.y = 2 * (screen_height - self.radius) - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

    def wall_bounce(self):
        if self.position.y < (screen_height - door_height) / 2 or self.position.y > (screen_height + door_height) / 2:  # Won't Hit Door
            if self.position.x >= (screen_width - boundary_width) / 2 - self.radius and self.half == "left":
                self.position.x = screen_width - boundary_width - 2 * self.radius - self.position.x
                self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))
            elif self.position.x <= (screen_width + boundary_width) / 2 + self.radius and self.half == "right":
                self.position.x = screen_width + boundary_width + 2 * self.radius - self.position.x
                self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))

    def boundary_bounce(self):
        if self.position.x >= (screen_width - boundary_width) / 2 - self.radius and self.half == "left":
            self.position.x = screen_width - boundary_width - 2 * self.radius - self.position.x
            self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))
        elif self.position.x <= (screen_width + boundary_width) / 2 + self.radius and self.half == "right":
            self.position.x = screen_width + boundary_width + 2 * self.radius - self.position.x
            self.velocity = self.velocity.reflect(euclid.Vector2(1, 0))

    def door_bounce(self):  # Top and Bottom of Door
        if (screen_width - boundary_width) / 2 - self.radius <= self.position.x <= (screen_width + boundary_width) / 2 + self.radius:  # Particle In Door
            self.is_passing = True
            if (screen_height - door_height) / 2 <= self.position.y <= (screen_height - door_height) / 2 + self.radius:  # Door Top Bounce
                self.position.y = screen_height - door_height + 2 * self.radius - self.position.y
                self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))
            elif (screen_height + door_height) / 2 - self.radius <= self.position.y <= (screen_height + door_height) / 2:  # Door Bottom Bounce
                self.position.y = screen_height + door_height - 2 * self.radius - self.position.y
                self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

    def bounce(self):
        new_x = closest_val(self.position.x, screen_width, character_values)
        new_y = closest_val(self.position.y, screen_height, character_values)
        self.position = euclid.Vector2(new_x, new_y)
        demon.entropy(self)
        self = demon.open_door(self)

    def surface_distance(self, other_circle, time_val):
        radii = self.radius + other_circle.radius
        pos_self = self.position + self.velocity * time_val
        pos_other = other_circle.position + other_circle.velocity * time_val
        pos = abs(pos_self - pos_other)
        return pos - radii

    def collide(self, other_circle):
        if self.surface_distance(other_circle, dtime) <= 0:
            collision_vector = self.position - other_circle.position
            collision_vector.normalize()
            self.velocity = self.velocity.reflect(collision_vector)
            other_circle.velocity = other_circle.velocity.reflect(collision_vector)
            while self.surface_distance(other_circle, dtime) <= 0:
                self.position += self.velocity * dtime
                other_circle.position += other_circle.velocity * dtime

    def update_half(self):
        global left_sum
        global left_num
        global right_sum
        global right_num
        if self.half == "left" and self.position.x > (screen_width + boundary_width) / 2 + self.radius:
            # Moves From Left to Right
            self.half = "right"
            left_sum -= self.speed
            left_num -= 1
            right_sum += self.speed
            right_num += 1
            if self.speed >= average_speed:
                self.correct_half = True
                left_ratio[1] -= 1
                right_ratio[0] += 1
            else:
                self.correct_half = False
                left_ratio[0] -= 1
                right_ratio[1] += 1
            self.update_correcthalf()
        elif self.half == "right" and self.position.x < (screen_width - boundary_width) / 2 - self.radius:
            self.half = "left"
            right_sum -= self.speed
            right_num -= 1
            left_sum += self.speed
            left_num += 1
            if self.speed < average_speed:
                self.correct_half = True
                right_ratio[1] -= 1
                left_ratio[0] += 1
            else:
                self.correct_half = False
                right_ratio[0] -= 1
                left_ratio[1] += 1
            self.update_correcthalf()

    def semi_update(self):  # Updates Half and Correct Half
        if self.half == "left" and self.position.x > (screen_width + boundary_width) / 2 + self.radius:
            # Moves From Left to Right
            self.half = "right"
        elif self.half == "right" and self.position.x < (screen_width - boundary_width) / 2 - self.radius:
            self.half = "left"
        if (self.half == "left" and self.speed < average_speed) or (self.half == "right" and self.speed >= average_speed):
            self.correct_half = True
        else:
            self.correct_half = False

    def update_passing(self):  # Updates Is_Passing
        self.is_passing = False
        if (screen_width - boundary_width) / 2 - self.radius <= self.position.x <= (screen_width + boundary_width) / 2 + self.radius:
            if (screen_height-door_height)/2 <= self.position.y <= (screen_height+door_height)/2:
                self.is_passing = True

    def update_correcthalf(self):
        if self.correct_half:
            if correct_particles.count(self) == 0:
                correct_particles.append(self)
                wrong_particles.remove(self)
        else:
            if wrong_particles.count(self) == 0:
                wrong_particles.append(self)
                correct_particles.remove(self)

    def to_binary(self):
        x_binary = int(self.position.x * character_values / screen_width)
        x_binary = bin(x_binary)
        y_binary = int(self.position.y * character_values / screen_height)
        y_binary = bin(y_binary)
        angle = math.atan(self.velocity.y/self.velocity.x)
        if self.velocity.x >= 0 and self.velocity.y >= 0:
            pass
        elif self.velocity.x >= 0 > self.velocity.y:
            angle += 2*math.pi
        elif self.velocity.x < 0 <= self.velocity.y:
            angle += math.pi
        elif self.velocity.x < 0 and self.velocity.y < 0:
            angle += math.pi
        angle_binary = int(angle * character_values / (2*math.pi))
        angle_binary = bin(angle_binary)
        speed_binary = int((self.speed - initial_speed + 75) * character_values / 200)
        speed_binary = bin(speed_binary)

        x_binary = binary_converter(x_binary)
        y_binary = binary_converter(y_binary)
        angle_binary = binary_converter(angle_binary)
        speed_binary = binary_converter(speed_binary)
        return [x_binary, y_binary, angle_binary, speed_binary]

class Demon:
    def __init__(self, magnitude, probability):
        self.magnitude = magnitude
        self.probability = probability

    def open_door(self, particle):
        particle.perimeter_bounce()
        particle.wall_bounce()
        # Update Particle Vals From Previous Move
        updated_particle = Particle(particle.color, euclid.Vector2(particle.position.x, particle.position.y), particle.radius, particle.speed, particle.half, euclid.Vector2(particle.velocity.x, particle.velocity.y))
        updated_particle.semi_update()
        updated_particle.update_passing()
        error_particle = self.bit_error(particle)
        if error_particle.is_passing or not error_particle.correct_half or particle.is_passing:  # Error_particle.is_passing is ALWAYS TRUE
            particle.door_bounce()
        else:
            updated_particle.boundary_bounce()
            particle.position = euclid.Vector2(updated_particle.position.x, updated_particle.position.y)
            particle.velocity = euclid.Vector2(updated_particle.velocity.x, updated_particle.velocity.y)
        return particle

    def bit_error(self, actual_particle):
        if self.magnitude == 0:
            return actual_particle
        else:
            particle = Particle(actual_particle.color, euclid.Vector2(actual_particle.position.x, actual_particle.position.y), actual_particle.radius, actual_particle.speed, actual_particle.half, euclid.Vector2(actual_particle.velocity.x, actual_particle.velocity.y))
            particle.correct_half = actual_particle.correct_half
            binary_vals = particle.to_binary()
            int_vals = []
            changes = []
            for counter in range(4):  # One Time For Each of X, Y, Angle, Speed
                prob =random.uniform(0, 1)
                if prob <= self.probability:
                    changes.append(True)
                    length = len(binary_vals[counter]) - 1
                    for counter_2 in range(self.magnitude):
                        prob = random.randint(0, length - 1)
                        if not(binary_vals[counter][prob]):
                            binary_vals[counter][prob] = True
                        else:
                            binary_vals[counter][prob] = False
                else:
                    changes.append(False)
                int_vals.append(int_converter(binary_vals[counter]))
            # New X, Y, Angle, Speed
            particle.position.x = int_vals[0] * screen_width / character_values
            particle.position.y = int_vals[1] * screen_height / character_values
            particle.speed = initial_speed - 75 + 200 * int_vals[3] / character_values
            particle_angle = int_vals[2] * 2 * math.pi / character_values
            particle.velocity = euclid.Vector2(particle.speed * math.cos(particle_angle), particle.speed * math.sin(particle_angle))
            if changes[0] or changes[1]:  # Position Changes
                particle.semi_update()
                particle.update_passing()
            if changes[2] or changes[3]:
                particle.semi_update()
            return particle

    def entropy(self, particle):
        global total_entropy
        if particle.half == "left":
            if particle.correct_half:
                # Left and Correct
                probability = left_ratio[0]/(left_ratio[0] + left_ratio[1])
            else:
                # Left and Wrong
                probability = left_ratio[1] / (left_ratio[0] + left_ratio[1])
        else:
            if particle.correct_half:
                # Right and Correct
                probability = right_ratio[0]/(right_ratio[0] + right_ratio[1])
            else:
                # Right and Wrong
                probability = right_ratio[1] / (right_ratio[0] + right_ratio[1])
        if probability != 0:
            total_entropy += math.log(1/probability, 2)

def get_random_velocity(overall_speed):
    new_angle = random.randint(0, character_values - 1)
    new_angle = 2*math.pi*new_angle / character_values
    new_x = math.cos(new_angle)
    new_y = math.sin(new_angle)
    new_vector = euclid.Vector2(new_x, new_y)
    new_vector.normalize()
    new_vector = new_vector * overall_speed
    return new_vector

class Door:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = (screen_width - width) / 2
        self.y = (screen_height - height) / 2
        self.open = False

    def display(self):
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(self.x, self.y, self.width, self.height))

    def update_state(self, particles):
        self.open = False
        for particle in particles:
            if (screen_width-boundary_width)/2 - particle.radius < particle.position.x < (screen_width+boundary_width)/2 + particle.radius and (screen_height-self.height)/2 + particle.radius < particle.position.y < (screen_height+self.height)/2 - particle.radius:
                self.open = True
                break

class Wall:
    def __init__(self, width):
        self.width = width
        self.height = 0
        self.top_rectangle = pygame.Rect(0, 0, 0, 0)
        self.bottom_rectangle = pygame.Rect(0, 0, 0, 0)

    def find_dimensions(self, my_door):
        self.height = (screen_height - my_door.height) / 2
        new_left = (screen_width - self.width) / 2
        self.top_rectangle = pygame.Rect(new_left, 0, self.width, self.height)
        bottom_top = screen_height - self.height
        self.bottom_rectangle = pygame.Rect(new_left, bottom_top, self.width, self.height)

    def display(self):
        pygame.draw.rect(screen, (255, 255, 255), self.top_rectangle)
        pygame.draw.rect(screen, (255, 255, 255), self.bottom_rectangle)

def closest_val(val, val_range, possibilities):
    if int(int(val)-val) == 0:  # Val is Integral
        return val
    else:
        lower_bound = int(val)
        partitions = val_range/possibilities
        lower_factor = math.ceil(lower_bound/partitions)
        upper_factor = math.floor((lower_bound+1)/partitions)
        counter = 1
        difference = val - lower_factor * partitions
        while lower_factor+counter <= upper_factor:
            new_difference = val - (lower_factor + counter) * partitions
            if new_difference < difference:
                difference = new_difference
            counter += 1
        return val - difference

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

for i in range(int(num_particles/2)):  # Slow Particles
    x_coord = random.randint(size, int((screen_width - boundary_width)/2))
    y_coord = random.randint(size, screen_height - size)
    rand_speed = random.randint(1, int(character_values/2))
    rand_speed = (average_speed - 75) + (100*rand_speed/(character_values/2))
    rand_velocity = get_random_velocity(rand_speed)
    new_particle = Particle((0, 0, 150), euclid.Vector2(x_coord, y_coord), size, rand_speed, "left", rand_velocity)
    all_particles.append(new_particle)
    left_sum += rand_speed
left_startavg = int(left_sum / int(num_particles/2))
counter_leftavg = font.render("Start Velocity: " + str(left_startavg) + "u/s", True, (255, 255, 0), (0, 0, 0))
for i in range(int(num_particles/2)):  # Fast Particles
    x_coord = random.randint(int((screen_width+boundary_width)/2), screen_width - size)
    y_coord = random.randint(size, screen_height - size)
    rand_speed = random.randint(1, int(character_values/2))
    rand_speed = (average_speed - 25) + (100*rand_speed/(character_values/2))
    rand_velocity = get_random_velocity(rand_speed)
    new_particle = Particle((0, 0, 150), euclid.Vector2(x_coord, y_coord), size, rand_speed, "right", rand_velocity)
    all_particles.append(new_particle)
    right_sum += rand_speed
right_startavg = int(right_sum / int(num_particles/2))
counter_rightavg = font.render("Start Velocity: " + str(right_startavg) + "u/s", True, (255, 255, 0), (0, 0, 0))
average_speed = (left_sum + right_sum)/num_particles
for a_particle in all_particles:
    if a_particle.half == "left":
        if a_particle.speed < average_speed:
            a_particle.correct_half = True
            correct_particles.append(a_particle)
            left_ratio[0] += 1
        else:
            a_particle.correct_half = False
            wrong_particles.append(a_particle)
            left_ratio[1] += 1
    else:
        if a_particle.speed >= average_speed:
            a_particle.correct_half = True
            correct_particles.append(a_particle)
            right_ratio[0] += 1
        else:
            a_particle.correct_half = False
            wrong_particles.append(a_particle)
            right_ratio[1] += 1
    a_particle.update_correcthalf()

fps_limit = 120
door = Door(boundary_width, door_height)
wall = Wall(boundary_width)
wall.find_dimensions(door)
demon = Demon(bit_error, error_probability)
t0 = pygame.time.get_ticks()
running = True
while running:
    if (pygame.time.get_ticks() - t0) >= (run_time * 1000):
        running = False
        break
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    dtime_ms = clock.tick(fps_limit)
    dtime = dtime_ms / 1000  # dtime is a constant

    screen.fill((0, 100, 100))
    if not all_sorted:
        door.update_state(all_particles)
        if not door.open:
            door.display()
        wall.display()
        for i, my_particle in enumerate(all_particles):
            my_particle.move()
            for second_particle in all_particles[i+1:]:
                my_particle.collide(second_particle)
            my_particle.display()
    else:
        if (pygame.time.get_ticks() - timestamp) >= (end_time * 1000):
            running = False
            break
        else:
            door.display()
            wall.display()
            for i, my_particle in enumerate(all_particles):
                my_particle.position += my_particle.velocity * dtime
                my_particle.perimeter_bounce()
                my_particle.boundary_bounce()
                for second_particle in all_particles[i + 1:]:
                    my_particle.collide(second_particle)
                my_particle.display()

    # Print Counters
    counter_left = font.render("Average Velocity: " + str(int(left_sum/left_num)) + "u/s", True, (255, 255, 0), (0, 0, 0))
    counter_right = font.render("Average Velocity: " + str(int(right_sum/right_num)) + "u/s", True, (255, 255, 0), (0, 0, 0))
    #counter_total = font_2.render("Total Velocity: " + str(int(left_sum+right_sum)), True, (255, 255, 0), (0, 0, 0))
    particles_sorted = int(100*(left_ratio[0]+right_ratio[0])/num_particles)
    percent_sorted = font_2.render(str(particles_sorted) + "% Sorted", True, (255, 255, 0), (0, 0, 0))
    percentage_vals.append(particles_sorted)
    if particles_sorted == 100 and not all_sorted:
        all_sorted = True
        timestamp = pygame.time.get_ticks()
    entropy_vals.append(total_entropy)
    time_vals.append((pygame.time.get_ticks() - t0)/1000)
    energy_transfer.append(right_sum/right_num - left_sum/left_num)
    screen.blit(counter_left, ((screen_width-boundary_width)/4 - counter_left.get_width()/2, 10))
    screen.blit(counter_right, (3*screen_width/4 + boundary_width/4 - counter_right.get_width()/2, 10))
    screen.blit(percent_sorted, ((screen_width - percent_sorted.get_width())/2, 10))
    screen.blit(counter_leftavg, ((screen_width-boundary_width)/4 - counter_leftavg.get_width()/2, screen_height-counter_leftavg.get_height()-10))
    screen.blit(counter_rightavg, (3 * screen_width / 4 + boundary_width / 4 - counter_rightavg.get_width() / 2, screen_height-counter_rightavg.get_height()-10))

    pygame.display.update()
print("Simulation Ended Successfully")
