""" SMARS Python library
Kevin McAleer September 2018
Purpose: Provides library routines for the SMARS robot and quad robots

You will need to install the following python libraries for this to work:

  # sudo apt-get install python-smbus
  # sudo apt-get install i2c-tools

You will also need to enable the I2C interface using the raspberry pi
configuration tool (raspi-config)

You will need ot install the adafruit PCA9685 servo driver python library

If you have Raspbian, not Occidentalis check /etc/modprobe.d/raspi-blacklist.conf
and comment "blacklist i2c-bcm2708" by running sudo nano /etc/modprobe.d/raspi-blacklist.conf
and adding a # (if its not there).
If you're running Wheezy or something-other-than-Occidentalis, you will need to
add the following lines to /etc/modules
 - i2c-dev
 - i2c-bcm2708

create a virtual environment (venv) and use the pip install -r requirements.txt
to install the dependencies

"""
import time
import logging
import Adafruit_PCA9685
# from constants import Channel
from constants import Channel
logging.basicConfig(level=logging.CRITICAL)
logging.propagate = False

# Initialise the PCA9685 using the default address (0x40).
try:
    PWM = Adafruit_PCA9685.PCA9685()
except OSError as error:
    LOG_STRING = "failed to initialise the servo driver (Adafruit PCA9685): "
    logging.error(LOG_STRING)

    # tell later parts of the code not to actually use the driver
    do_no_use_PCA_driver = True

    PWM = ""
except:
    print("There was an error loading the adafruit driver; loading without PCA9685.")
    do_no_use_PCA_driver = True # tell later parts of the code not to actually use the driver
else:
    LOG_STRING = "PCA9685 Driver loaded)."
    do_no_use_PCA_driver = False # tell later parts of the code to use the driver
    logging.error(LOG_STRING)

# Configure min and max servo pulse lengths
servo_min = 150       # Min pulse length out of 4096
servo_max = 600       # Max pulse length out of 4096
SLEEP_COUNT = 0.05    # the amount of time to wait between pwm operations



# Set frequency to 60hz, good for servos.
try:
    if do_no_use_PCA_driver is False:
        PWM.set_pwm_freq(60)
except ValueError as error:
    LOG_STRING = "failed to set the pwm frequency:, " + error
    logging.error(LOG_STRING)


def set_servo_pulse(channel, pulse):
    """
    Helper function to make setting a servo pulse width simpler.
    """

    if 0 <= channel <= 15 and \
       type(channel) is int and \
       pulse <= 4096 and \
       pulse >= 0:
        pulse_length = 1000000    # 1,000,000 us per second
        pulse_length //= 60       # 60 Hz
        logging.info('{0}us per period'.format(pulse_length))
        pulse_length //= 4096     # 12 bits of resolution
        logging.info('{0}us per bit'.format(pulse_length))
        pulse *= 1000
        pulse //= pulse_length
        try:
            if do_no_use_PCA_driver is False:
                PWM.set_pwm(channel, 0, pulse)
        except:
            logging.warning(
                "Failed to set pwm - did the driver initialize correctly?")
            # print("Failed to set pwm - did the driver initialize correctly?")

        return True

    print("channel less than 0 or greater than 15, or not an integer, \
    or pulse is greater than 4096:", channel, pulse)
    logging.warning(
        "channel less than 0 or greater than 15, or not an integer, or pulse is greater than 4096.")
    return False


class Leg(object):
    """
    provides a model of a limb (for either a foot or a leg)
    """
    leg_min = 150
    leg_max = 600
    swingangle = 0
    bodyangle = 0
    stretchangle = 0
    currentangle = 0
    invert = False
    leg_angle = 0
    leg_minAngle = 0
    leg_maxAngle = 180

    def __init__(self, name, channel, leg_minangle, leg_maxangle, invert):
        # Initialises the leg object
        try:
            if do_no_use_PCA_driver is False:
                pwm = Adafruit_PCA9685.PCA9685()
        except RuntimeError as error:
            logging.warning("The servo driver failed to initialise  \
            - have you installed the adafruit PCA9685 driver, \
            and is it connected?")
            logging.warning(error)

        try:
            if do_no_use_PCA_driver is False:
                pwm.set_pwm_freq(60)
        except:
            logging.warning(
                "Failed to set the pwm frequency - did the servo driver initialize correctly?")

        self.name = name
        self.channel = channel
        self.leg_minangle = leg_minangle
        self.leg_maxangle = leg_maxangle
        self.invert = invert

        if not self.invert:
            self.bodyangle = self.leg_minangle
            self.stretchangle = self.leg_maxangle
            self.swingangle = (self.leg_minangle / 2) + self.leg_minangle
        else:
            self.bodyangle = self.leg_maxangle
            self.stretchangle = self.leg_minangle
            self.swingangle = (self.leg_maxangle - self.leg_minangle) / 2
        self.currentangle = self.bodyangle

    def setdefault(self):
        """
        Sets the limb to the default angle, by dividing the maximum and
        minimum angles that were set previously
        """
        self.setangle(self.leg_maxangle - self.leg_minangle)
        self.currentangle = self.leg_maxangle - self.leg_minangle

    def setbody(self):
        """
        Sets the limb to its body position.
        """
        if not self.invert:
            self.setangle(self.leg_minangle)
            self.bodyangle = self.leg_minangle
        else:
            self.setangle(self.leg_maxangle)
            self.bodyangle = self.leg_maxangle
        self.currentangle = self.bodyangle

    def setstretch(self):
        """
        Sets the limb to its stretch position.
        """
        if not self.invert:
            self.setangle(self.leg_maxangle)
            self.stretchangle = self.leg_maxangle
        else:
            self.setangle(self.leg_minangle)
            self.stretchangle = self.leg_minangle
        self.currentangle = self.stretchangle

    def setswing(self):
        """
        Sets the limb to its swing position, which is 45 degrees - halfway
        between the body and stretch position.
        """
        if not self.invert:
            swing_angle = (self.leg_minangle / 2) + self.leg_minangle
            self.setangle(swing_angle)
        else:
            swing_angle = (self.leg_maxangle - self.leg_minangle) / 2
            self.setangle(swing_angle)
        self.swingangle = swing_angle
        self.currentangle = self.swingangle

    def up(self):
        """
        raises the limb to its minimum angle
        """
        if not self.invert:
            self.setangle(self.leg_minangle)
        else:
            self.setangle(self.leg_maxangle)

    def down(self):
        """
        lowers the limb to its maximum angle
        """
        if not self.invert:
            self.setangle(self.leg_maxangle)
        else:
            self.setangle(self.leg_minangle)

    def middle(self):
        """
        moves the limb to half way between up and down.
        """
        self.setangle(self.leg_maxangle - self.leg_minangle)

    def show(self):
        """
        used for debugging - shows the servo driver channel number and the limb name
        """
        print(self.channel)
        print(self.name)

    def setangle(self, angle):
        """
        Works out the value of the angle by mapping the leg_min and leg_max to
        between 0 and 180 degrees, then moves the limb to that position
        """
        pulse = 0

        if angle >= 0 and angle <= 180:
            self.leg_angle = angle
            # Check the angle is within the boundaries for this limb
            if angle >= self.leg_minangle and angle <= self.leg_maxangle:
                mapmax = self.leg_max - self.leg_min
                percentage = (float(angle) / 180) * 100
                pulse = int(((float(mapmax) / 100) *
                             float(percentage)) + self.leg_min)

                # send the servo the pulse, to set the angle
                try:
                    if do_no_use_PCA_driver is False:
                        PWM.set_pwm(self.channel, self.channel, pulse)
                except RuntimeError as error:
                    logging.warning("Failed to set the pwm frequency - \
                    did the servo driver initialize correctly?")
                self.currentangle = angle
                return True


            # display an error message if the angle set was outside
            # the range (leg_minAngle and leg_maxAngle)
            logging.warning("Warning: angle was outside of bounds for this leg")
            return False
        else:
            logging.warning("Warning: angle was less than 0 or greater \
            than 180.")
            return False

    def untick(self):
        """ Used to walk backwards """
        if self.name == "right_leg_back" or self.name == "right_leg_front":
            if self.currentangle <= self.leg_maxangle:
                self.currentangle += 2
                # print self.name, "setting angle to ", self.currentAngle
                self.setangle(self.currentangle)
                return False
            return True
        elif self.name == "left_leg_back" or self.name == "left_leg_front":
            if self.currentangle >= self.leg_minangle:
                self.currentangle -= 2
                # print self.name, "setting angle to ", self.currentAngle
                self.setangle(self.currentangle)
                return False
            return True
        return True
    def tick(self):
        """
        Used for walking forward.
        Each tick received changes the current angle of the limb, unless an
        limit is reached, which then returns a true value
        """
        if self.name == "left_leg_front" or self.name == "left_leg_back":
            if self.currentangle <= self.leg_maxangle:
                self.currentangle += 2
                # print self.name, "setting angle to ", self.currentAngle
                self.setangle(self.currentangle)
                return False
            return True
        elif self.name == "right_leg_front" or self.name == "right_leg_back":
            if self.currentangle >= self.leg_minangle:
                self.currentangle -= 2
                # print self.name, "setting angle to ", self.currentAngle
                self.setangle(self.currentangle)
                return False
            return True
        return True

class SmarsRobot(object):
    """
    This is used to model the robot, its legs and its sensors
    """
    def __init__(self):
        try:
            if do_no_use_PCA_driver is False:
                pwm = Adafruit_PCA9685.PCA9685()
                pwm.set_pwm_freq(60)
        except RuntimeError as error:
            logging.warning(
                "Failed to set the pwm frequency - did the servo driver initialize correctly?")

    # defines if the robot is a quad or wheel based robot
    # need to make this an enum then set the type to be one of the items in the list
    type = ['wheel', 'quad']

    # setup two arrays, one for legs, and one for feet
    legs = []
    feet = []
    name = ""  # the friendly name for the robot - used in console messages.

    # add each foot to the feet array
    feet.append(Leg(name='left_foot_front', channel=1,
                    leg_minangle=50, leg_maxangle=150, invert=False))
    feet.append(Leg(name='left_foot_back', channel=3,
                    leg_minangle=50, leg_maxangle=150, invert=True))
    feet.append(Leg(name='right_foot_front', channel=7,
                    leg_minangle=50, leg_maxangle=150, invert=True))
    feet.append(Leg(name='right_foot_back', channel=5,
                    leg_minangle=50, leg_maxangle=150, invert=False))

    # add each leg to the legs array
    legs.append(Leg(name='left_leg_front', channel=0,
                    leg_minangle=9, leg_maxangle=90, invert=True))
    legs.append(Leg(name='left_leg_back', channel=2,
                    leg_minangle=90, leg_maxangle=180, invert=False))
    legs.append(Leg(name='right_leg_front', channel=6,
                    leg_minangle=90, leg_maxangle=180, invert=False))
    legs.append(Leg(name='right_leg_back', channel=4,
                    leg_minangle=9, leg_maxangle=90, invert=True))
    # print "number of legs", len(legs)

    def setname(self, name):
        """
        Sets the robots name, used for displaying console messages.
        """
        self.name = name
        print("***", name, "Online ***")

    def leg_reset(self):
        """
        used to reset all the legs
        """
        for limb in self.legs:
            limb.setdefault()

    def middle(self):
        """
        used to position all the legs into the middle position
        """
        print("received middle command")
        for limb in self.legs:
            limb.middle()

    def sit(self):
        """
        used to sit the robot down
        """
        print(self.name, "sitting Down.")
        for limb in self.feet:
            limb.down()

    def stand(self):
        """
        used to stand the robot up
        """
        print(self.name, "standing up.")
        for limb in self.feet:
            limb.up()

    def setswing(self):
        """
        Moves the limb to the swing position
        """
        for limb in range(0, 4):
            self.feet[limb].down()
            time.sleep(SLEEP_COUNT)
            self.legs[limb].setswing()
            time.sleep(SLEEP_COUNT)
            self.feet[limb].up()
            time.sleep(SLEEP_COUNT)

    def turnright(self):
        """
        turns the robot to the right
        """

        chan = Channel()

        print(self.name, "Turning Right.")

        # move legs one at a time back to swing position
        self.setswing()

        # twist body
        self.legs[chan.RIGHT_LEG_FRONT].setstretch()
        self.legs[chan.RIGHT_LEG_BACK].setbody()
        self.legs[chan.LEFT_LEG_FRONT].setbody()
        self.legs[chan.LEFT_LEG_BACK].setstretch()
        time.sleep(SLEEP_COUNT)

        # move legs one at a time back to swing position
        self.setswing()

    def turnleft(self):
        """
        turn robot left
        """
        chan = Channel()
        print(self.name, "Turning left.")

        # move legs one at a time back to swing position
        self.setswing()

        # twist body
        self.legs[chan.LEFT_LEG_FRONT].setstretch()
        self.legs[chan.LEFT_LEG_BACK].setbody()
        self.legs[chan.RIGHT_LEG_FRONT].setbody()
        self.legs[chan.RIGHT_LEG_BACK].setstretch()
        time.sleep(SLEEP_COUNT)

        # move legs one at a time back to swing position
        self.setswing()

    def walkforward(self, steps):
        """
        Used to move the robot forward
        """

        # include the global variables
        chan = Channel()

        # set the legs to the correct position for walking.
        self.sit()
        self.legs[chan.LEFT_LEG_FRONT].setbody()
        self.legs[chan.LEFT_LEG_BACK].setbody()
        self.legs[chan.RIGHT_LEG_FRONT].setswing()
        self.legs[chan.RIGHT_LEG_BACK].setswing()
        self.stand()

        # the walking cycle, loops for the number of steps provided.
        current_step = 0
        while current_step < steps:
            current_step += 1

            for n in range(0, 4):
                if not self.legs[n].tick():
                    self.legs[n].tick()
                else:
                    self.feet[n].down()
                    time.sleep(SLEEP_COUNT)

                    # change this to left and right legs, rather than invert or not invert
                    if not self.legs[n].invert:
                        if self.legs[n].name == "right_leg_front":
                            self.legs[n].setstretch()
                        else:
                            self.legs[n].setbody()
                    elif self.legs[n].invert:
                        if self.legs[n].name == "right_leg_back":
                            self.legs[n].setbody()
                        else:
                            self.legs[n].setstretch()
                    time.sleep(SLEEP_COUNT)
                    self.feet[n].up()
                    time.sleep(SLEEP_COUNT)

    def walkbackward(self, steps):
        """ used to move the robot backward. """

        # include the global variables
        chan = Channel()

        # set the legs to the correct position for walking.
        self.sit()
        self.legs[chan.LEFT_LEG_FRONT].setbody()
        self.legs[chan.LEFT_LEG_BACK].setbody()
        self.legs[chan.RIGHT_LEG_FRONT].setswing()
        self.legs[chan.RIGHT_LEG_BACK].setswing()
        self.stand()

        # the walking cycle, loops for the number of steps provided.
        current_step = 0
        while current_step < steps:
            current_step += 1
            for n in range(0, 4):
                if not self.legs[n].untick():
                    # print self.name, "walking, step", currentStep, "of", steps
                    self.legs[n].untick()
                else:
                    # print "moving leg:", self.legs[n].name
                    self.feet[n].down()
                    time.sleep(SLEEP_COUNT)

                    # change this to left and right legs, rather than invert or not invert
                    if not self.legs[n].invert:
                        if self.legs[n].name == "left_leg_back":
                            self.legs[n].setstretch()
                        else:
                            self.legs[n].setbody()
                    elif self.legs[n].invert:
                        if self.legs[n].name == "left_leg_front":
                            self.legs[n].setbody()
                        else:
                            self.legs[n].setstretch()
                    time.sleep(SLEEP_COUNT)
                    self.feet[n].up()
                    time.sleep(SLEEP_COUNT)

    def clap(self, clap_count):
        """  Clap front two hands (the sound of two hands clapping) """
        chan = Channel()

        self.sit()
        # self.feet[left_foot_front].up()
        # self.feet[right_foot_front].up()
        for _ in range(0, clap_count):
            self.legs[chan.LEFT_LEG_FRONT].setbody()
            self.legs[chan.RIGHT_LEG_FRONT].setbody()
            time.sleep(SLEEP_COUNT * 2)
            self.legs[chan.LEFT_LEG_FRONT].setstretch()
            self.legs[chan.RIGHT_LEG_FRONT].setstretch()
            time.sleep(SLEEP_COUNT * 2)
        self.stand()

    def wiggle(self, wiggle_count):
        """ Wiggle butt """

        chan = Channel()

        self.sit()
        self.legs[chan.LEFT_FOOT_BACK].up()
        self.legs[chan.RIGHT_FOOT_BACK].up()
        time.sleep(SLEEP_COUNT * 5)

        for _ in range(0, wiggle_count):
            self.legs[chan.LEFT_LEG_BACK].setbody()
            self.legs[chan.RIGHT_LEG_BACK].setstretch()
            time.sleep(SLEEP_COUNT * 5)
            self.legs[chan.LEFT_LEG_BACK].setstretch()
            self.legs[chan.RIGHT_LEG_BACK].setbody()
            time.sleep(SLEEP_COUNT * 5)
        self.stand()

    def get_telemetry(self):
        """ returns a list of limbs and measurements """
        telemetry = []
        chan = Channel()
        telemetry.append(["left_leg_front", self.legs[chan.LEFT_LEG_FRONT].leg_angle])
        telemetry.append(["right_leg_front", self.legs[chan.RIGHT_LEG_FRONT].leg_angle])
        telemetry.append(["left_leg_back", self.legs[chan.LEFT_LEG_BACK].leg_angle])
        telemetry.append(["right_leg_back", self.legs[chan.RIGHT_LEG_BACK].leg_angle])
        telemetry.append(["left_foot_front", self.legs[chan.LEFT_FOOT_FRONT].leg_angle])
        telemetry.append(["right_foot_front", self.legs[chan.RIGHT_FOOT_FRONT].leg_angle])
        telemetry.append(["left_foot_back", self.legs[chan.LEFT_FOOT_BACK].leg_angle])
        telemetry.append(["right_foot_back", self.legs[chan.RIGHT_FOOT_BACK].leg_angle])
        return telemetry

class SMARSColor(object):
    """ Some standard console colors for use with terminal display output """

    # Foreground Colours
    WHITE = u'\001b[30m'
    RED = u'\001b[31m'
    GREEN = u'\001b[32m'
    YELLOW = u'\001b[33m'
    BLUE = u'\001b[34m'
    MAGENTA = u'\001b[35m'
    CYAN = u'\001b[36m'
    BLACK = u'\001b[30m'
    DARKPINK = u'\033[95m'
    PINK = u'\033[94m'
    RESET = u'\033[0m'
    NORMAL = u'\033[0m'

    # Bright Colours
    BRIGHTWHITE = u'\001b[30;1m'
    BRIGHTRED = u'\001b[31;1m'
    BRIGHTGREEN = u'\001b[32;1m'
    BRIGHTYELLOW = u'\001b[33;1m'
    BRIGHTBLUE = u'\001b[34;1m'
    BRIGHTMAGENTA = u'\001b[35;1m'
    BRIGHTCYAN = u'\001b[36m;1m'
    DARKGRAY = u'\u001b[30;1m'
    BRIGHTPINK = u'\033[94m;1m'

    # Decoration
    REVERSED = u'\u001b[7m'
    BOLD = u'\033[1m'
    UNDERLINE = u'\033[4m'

    # Background Colours
    BG_BLUE = u'\033[44m'
    BG_BLACK = u'\u001b[40m'
    BG_RED = u'\u001b[41m'
    BG_GREEN = u'\u001b[42m'
    BG_YELLOW = u'\u001b[43m'
    BG_MAGENTA = u'\u001b[45m'
    BG_CYAN = u'\u001b[46m'
    BG_WHITE = u'\u001b[47m'

    # Clear screen or line
    # clears the screen from the cursor
    CLEAR_SCREEN_FROM_CURSOR = u'\u001b[0J'

    # Clears the screen from the beginning of the screen to the cursor
    CLEAR_SCREEN_TO_CURSOR = u'\u001b[1J'

    # Clears the screen
    CLEAR_SCREEN = u'\u001b[2J'

    CLEAR_LINE = u'\u001b[2K'
    CLEAR_LINE_FROM_CURSOR = u'\u001b[0K'
    CLEAR_LINE_TO_CURSOR = u'\u001b[1K'

    # Move cursor
    @classmethod
    def cursor_left(cls, no_of_chars):
        """ moves the cursor left """
        print(u'\u001b[' + str(no_of_chars) + 'D')

    @classmethod
    def cursor_right(cls, no_of_chars):
        """ moves the cursor right """
        print(u'\u001b[' + str(no_of_chars) + 'C')

    @classmethod
    def cursor_up(cls, no_of_chars):
        """ moves the cursor up"""
        print(u'\u001b[' + str(no_of_chars) + 'A')

    @classmethod
    def cursor_down(cls, no_of_chars):
        """ moves the cursor down """
        print(u'\u001b[' + str(no_of_chars) + 'B')

    @classmethod
    def set_position(cls, x_pos, y_pos):
        """ sets the cursor position """
        position = u'\u001b[' + str(x_pos) + ';' + str(y_pos) + 'H'
        print(position)


class CommandHistory(object):
    """ models the command history object """

    history = []

    def __init__(self):
        self.history.append("*** new history ***")

    def append(self, command):
        """ adds a command to the command history """
        self.history.append(command)

    def clear(self):
        """ clears the command history """
        self.history = []

    def get_history(self):
        """ get all command history """
        return self.history

    def get_last_ten(self):
        """ get last 10 command history """
        return self.history[-10:]
