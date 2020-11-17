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
from .channel import Channel
logging.basicConfig(level=logging.CRITICAL)
logging.propagate = False

# Initialise the PCA9685 using the default address (0x40).
try:
    PWM = Adafruit_PCA9685.PCA9685()
except OSError as error:
    LOG_STRING = "failed to initialise the servo driver (Adafruit PCA9685): "
    logging.error(LOG_STRING)

    # tell later parts of the code not to actually use the driver
   
    DO_NOT_USE_PCA_DRIVER = True

    PWM = ""
except:
    print("There was an error loading the adafruit driver; loading without PCA9685.")
    DO_NOT_USE_PCA_DRIVER = True # tell later parts of the code not to actually use the driver
else:
    LOG_STRING = "PCA9685 Driver loaded)."
    DO_NOT_USE_PCA_DRIVER = False # tell later parts of the code to use the driver
    logging.error(LOG_STRING)

# Configure min and max servo pulse lengths
servo_min = 150       # Min pulse length out of 4096
servo_max = 600       # Max pulse length out of 4096
SLEEP_COUNT = 0.05    # the amount of time to wait between pwm operations



# Set frequency to 60hz, good for servos.
try:
    if DO_NOT_USE_PCA_DRIVER is False:
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
    __leg_min = 150
    __leg_max = 600
    __swingangle = 0
    __bodyangle = 0
    __stretchangle = 0
    __currentangle = 0
    __invert = False
    __leg_angle = 0
    __leg_minAngle = 0
    __leg_maxAngle = 180

    @property
    def angle(self):
        """ Returns the leg angle """
        return self.__leg_angle

    def __init__(self, name, channel, leg_minangle, leg_maxangle, invert):
        # Initialises the leg object
        try:
            if DO_NOT_USE_PCA_DRIVER is False:
                pwm = Adafruit_PCA9685.PCA9685()
        except RuntimeError as error:
            logging.warning("The servo driver failed to initialise  \
            - have you installed the adafruit PCA9685 driver, \
            and is it connected?")
            logging.warning(error)

        try:
            if DO_NOT_USE_PCA_DRIVER is False:
                pwm.set_pwm_freq(60)
        except:
            logging.warning(
                "Failed to set the pwm frequency - did the servo driver initialize correctly?")

        self.__name = name
        self.__channel = channel
        self.__leg_minangle = leg_minangle
        self.__leg_maxangle = leg_maxangle
        self.__invert = invert

        if not self.__invert:
            self.__bodyangle = self.__leg_minangle
            self.__stretchangle = self.__leg_maxangle
            self.__swingangle = (self.__leg_minangle / 2) + self.__leg_minangle
        else:
            self.__bodyangle = self.__leg_maxangle
            self.__stretchangle = self.__leg_minangle
            self.__swingangle = (self.__leg_maxangle - self.__leg_minangle) / 2
        self.__currentangle = self.__bodyangle

    @property
    def invert(self):
        return self.__invert

    @invert.setter
    def invert(self,invert):
        self.__invert = invert

    def setdefault(self):
        """
        DEPRICATED METHOD - USE .default
        """
        print("This method is depricated, use .default instead")

    def default(self):
        """
        Sets the limb to the default angle, by subtracting the maximum and
        minimum angles that were set previously
        """
        self.angle(self.__leg_maxangle - self.__leg_minangle)
        self.__currentangle = self.__leg_maxangle - self.__leg_minangle

    def setbody(self):
        """
        DEPRICATED METHOD - USE .body
        """
        print("this method is depricated, use .body instead")

    def body(self):
        """
        Sets the limb to its body position.
        """
        if not self.__invert:
            self.angle(self.__leg_minangle)
            self.__bodyangle = self.__leg_minangle
        else:
            self.angle(self.__leg_maxangle)
            self.__bodyangle = self.__leg_maxangle
        self.__currentangle = self.__bodyangle

    def setstrech(self):
        """ DEPRICATED METHOD - USE .stretch """
        print("this method is depricated, use .stretch instead")

    def stretch(self):
        """
        Sets the limb to its stretch position.
        """
        if not self.__invert:
            self.angle(self.__leg_maxangle)
            self.__stretchangle = self.__leg_maxangle
        else:
            self.angle(self.__leg_minangle)
            self.__stretchangle = self.__leg_minangle
        self.__currentangle = self.__stretchangle

    def setswing(self):
        """ DEPRICATED - Use Swing instead"""
        print("This function is depricated use swing instead")

    def swing(self):
        """
        Sets the limb to its swing position, which is 45 degrees - halfway
        between the body and stretch position.
        """
        if not self.invert:
            swing_angle = (self.__leg_minangle / 2) + self.__leg_minangle
            self.angle(swing_angle)
        else:
            swing_angle = (self.__leg_maxangle - self.__leg_minangle) / 2
            self.angle(swing_angle)
        self.__swingangle = swing_angle
        self.__currentangle = self.__swingangle

    def up(self):
        """
        raises the limb to its minimum angle
        """
        if not self.invert:
            self.angle(self.__leg_minangle)
        else:
            self.angle(self.__leg_maxangle)

    def down(self):
        """
        lowers the limb to its maximum angle
        """
        if not self.invert:
            self.angle(self.__leg_maxangle)
        else:
            self.angle(self.__leg_minangle)

    def middle(self):
        """
        moves the limb to half way between up and down.
        """
        self.angle(self.__leg_maxangle - self.__leg_minangle)

    def show(self):
        """
        used for debugging - shows the servo driver channel number and the limb name
        """
        print(self.__channel)
        print(self.name)

    def setangle(self,angle):
        """
        DEPRICATED METHOD - USE .angle
        """
        print("This method is depricated - use .angle instead")

    @angle.setter
    def angle(self, angle):
        """
        Works out the value of the angle by mapping the leg_min and leg_max to
        between 0 and 180 degrees, then moves the limb to that position
        """
        pulse = 0

        if angle >= 0 and angle <= 180:
            self.__leg_angle = angle
            # Check the angle is within the boundaries for this limb
            if angle >= self.__leg_minangle and angle <= self.__leg_maxangle:
                mapmax = self.__leg_max - self.__leg_min
                percentage = (float(angle) / 180) * 100
                pulse = int(((float(mapmax) / 100) *
                             float(percentage)) + self.__leg_min)

                # send the servo the pulse, to set the angle
                try:
                    if DO_NOT_USE_PCA_DRIVER is False:
                        PWM.set_pwm(self.__channel, self.__channel, pulse)
                except RuntimeError as error:
                    logging.warning("Failed to set the pwm frequency - \
                    did the servo driver initialize correctly?")
                self.__currentangle = angle
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
        if self.__name == "right_leg_back" or self.__name == "right_leg_front":
            if self.__currentangle <= self.__leg_maxangle:
                self.__currentangle += 2
                # print self.name, "setting angle to ", self.currentAngle
                self.angle(self.__currentangle)
                return False
            return True
        elif self.__name == "left_leg_back" or self.__name == "left_leg_front":
            if self.__currentangle >= self.__leg_minangle:
                self.__currentangle -= 2
                # print self.name, "setting angle to ", self.currentAngle
                self.angle(self.__currentangle)
                return False
            return True
        return True
    def tick(self):
        """
        Used for walking forward.
        Each tick received changes the current angle of the limb, unless an
        limit is reached, which then returns a true value
        """
        if self.__name == "left_leg_front" or self.__name == "left_leg_back":
            if self.__currentangle <= self.__leg_maxangle:
                self.__currentangle += 2
                # print self.name, "setting angle to ", self.currentAngle
                self.angle(self.__currentangle)
                return False
            return True
        elif self.__name == "right_leg_front" or self.__name == "right_leg_back":
            if self.__currentangle >= self.__leg_minangle:
                self.__currentangle -= 2
                # print self.name, "setting angle to ", self.currentAngle
                self.angle(self.__currentangle)
                return False
            return True
        return True

    @property
    def name(self):
        """ gets the Robot name """
        return self.__name

    @name.setter
    def name(self, name):
        """ Sets the Robot name """
        self.__name = name

class SmarsRobot(object):
    """
    This is used to model the robot, its legs and its sensors
    """
    def __init__(self):
        try:
            if DO_NOT_USE_PCA_DRIVER is False:
                pwm = Adafruit_PCA9685.PCA9685()
                pwm.set_pwm_freq(60)
        except RuntimeError as error:
            logging.warning(
                "Failed to set the pwm frequency - did the servo driver initialize correctly?")

    # defines if the robot is a quad or wheel based robot
    # need to make this an enum then set the type to be one of the items in the list
    type = ['wheel', 'quad']

    # setup two arrays, one for legs, and one for feet
    __legs = []
    __feet = []
    __name = ""  # the friendly name for the robot - used in console messages.

    # add each foot to the feet array
    __feet.append(Leg(name='LEFT_FOOT_FRONT', channel=1,
                    leg_minangle=50, leg_maxangle=150, invert=False))
    __feet.append(Leg(name='LEFT_FOOT_BACK', channel=3,
                    leg_minangle=50, leg_maxangle=150, invert=True))
    __feet.append(Leg(name='RIGHT_FOOT_FRONT', channel=7,
                    leg_minangle=50, leg_maxangle=150, invert=True))
    __feet.append(Leg(name='RIGHT_FOOT_BACK', channel=5,
                    leg_minangle=50, leg_maxangle=150, invert=False))

    # add each leg to the legs array
    __legs.append(Leg(name='LEFT_LEG_FRONT', channel=0,
                    leg_minangle=9, leg_maxangle=90, invert=True))
    __legs.append(Leg(name='LEFT_LEG_BACK', channel=2,
                    leg_minangle=90, leg_maxangle=180, invert=False))
    __legs.append(Leg(name='RIGHT_LEG_FRONT', channel=6,
                    leg_minangle=90, leg_maxangle=180, invert=False))
    __legs.append(Leg(name='RIGHT_LEG_BACK', channel=4,
                    leg_minangle=9, leg_maxangle=90, invert=True))
    # print "number of legs", len(legs)

    @property
    def name(self):
        """
        gets the robots name
        """
        return self.__name

    @name.setter
    def name(self, name):
        """
        Sets the robots name, used for displaying console messages.
        """
        self.__name = name

        # TODO: add a logging level to output messages
        print("***", name, "Online ***")

    def setname(self,name):
        """
        Depricated - use the .name property
        """
        print("Depricated - use the .name property")
        self.name = name

    def leg_reset(self):
        """
        used to reset all the legs
        """
        for limb in self.__legs:
            limb.default()

    def middle(self):
        """
        used to position all the legs into the middle position
        """
        print("received middle command")
        for limb in self.__legs:
            limb.middle()

    def sit(self):
        """
        used to sit the robot down
        """
        print(self.__name, "sitting Down.")
        for limb in self.__feet:
            limb.down()

    def stand(self):
        """
        used to stand the robot up
        """
        print(self.name, "standing up.")
        for limb in self.__feet:
            limb.up()

    def swing(self):
        """
        Moves the limb to the swing position
        """
        for limb in range(0, 4):
            self.__feet[limb].down()
            time.sleep(SLEEP_COUNT)
            self.__legs[limb].setswing()
            time.sleep(SLEEP_COUNT)
            self.__feet[limb].up()
            time.sleep(SLEEP_COUNT)

    def turnright(self):
        """
        turns the robot to the right
        """

        chan = Channel()

        print(self.name, "Turning Right.")

        # move legs one at a time back to swing position
        self.swing()

        # twist body
        self.__legs[chan.RIGHT_LEG_FRONT].stretch()
        self.__legs[chan.RIGHT_LEG_BACK].body()
        self.__legs[chan.LEFT_LEG_FRONT].body()
        self.__legs[chan.LEFT_LEG_BACK].stretch()
        time.sleep(SLEEP_COUNT)

        # move legs one at a time back to swing position
        self.swing()

    def turnleft(self):
        """
        turn robot left
        """
        chan = Channel()
        print(self.name, "Turning left.")

        # move legs one at a time back to swing position
        self.swing()

        # twist body
        self.__legs[chan.LEFT_LEG_FRONT].stretch()
        self.__legs[chan.LEFT_LEG_BACK].body()
        self.__legs[chan.RIGHT_LEG_FRONT].body()
        self.__legs[chan.RIGHT_LEG_BACK].stretch()
        time.sleep(SLEEP_COUNT)

        # move legs one at a time back to swing position
        self.swing()

    def walkforward(self, steps):
        """
        Used to move the robot forward
        """

        # include the global variables
        chan = Channel()

        # set the legs to the correct position for walking.
        self.sit()
        self.__legs[chan.LEFT_LEG_FRONT].setbody()
        self.__legs[chan.LEFT_LEG_BACK].setbody()
        self.__legs[chan.RIGHT_LEG_FRONT].setswing()
        self.__legs[chan.RIGHT_LEG_BACK].setswing()
        self.stand()

        # the walking cycle, loops for the number of steps provided.
        current_step = 0
        while current_step < steps:
            current_step += 1

            for n in range(0, 4):
                if not self.__legs[n].tick():
                    self.__legs[n].tick()
                else:
                    self.__feet[n].down()
                    time.sleep(SLEEP_COUNT)

                    # change this to left and right legs, rather than invert or not invert
                    if not self.__legs[n].invert:
                        if self.__legs[n].name == "right_leg_front":
                            self.__legs[n].stretch()
                        else:
                            self.__legs[n].body()
                    elif self.__legs[n].invert:
                        if self.__legs[n].name == "right_leg_back":
                            self.__legs[n].body()
                        else:
                            self.__legs[n].stretch()
                    time.sleep(SLEEP_COUNT)
                    self.__feet[n].up()
                    time.sleep(SLEEP_COUNT)

    def walkbackward(self, steps):
        """ used to move the robot backward. """

        # include the global variables
        chan = Channel()

        # set the legs to the correct position for walking.
        self.sit()
        self.__legs[chan.LEFT_LEG_FRONT].body()
        self.__legs[chan.LEFT_LEG_BACK].body()
        self.__legs[chan.RIGHT_LEG_FRONT].swing()
        self.__legs[chan.RIGHT_LEG_BACK].swing()
        self.stand()

        # the walking cycle, loops for the number of steps provided.
        current_step = 0
        while current_step < steps:
            current_step += 1
            for n in range(0, 4):
                if not self.__legs[n].untick():
                    # print self.name, "walking, step", currentStep, "of", steps
                    self.__legs[n].untick()
                else:
                    # print "moving leg:", self.legs[n].name
                    self.__feet[n].down()
                    time.sleep(SLEEP_COUNT)

                    # change this to left and right legs, rather than invert or not invert
                    if not self.__legs[n].invert:
                        if self.__legs[n].name == "left_leg_back":
                            self.__legs[n].stretch()
                        else:
                            self.__legs[n].body()
                    elif self.__legs[n].invert:
                        if self.__legs[n].name == "left_leg_front":
                            self.__legs[n].body()
                        else:
                            self.__legs[n].stretch()
                    time.sleep(SLEEP_COUNT)
                    self.__feet[n].up()
                    time.sleep(SLEEP_COUNT)

    def clap(self, clap_count):
        """  Clap front two hands (the sound of two hands clapping) """
        chan = Channel()

        self.sit()
        # self.feet[left_foot_front].up()
        # self.feet[right_foot_front].up()
        for _ in range(0, clap_count):
            self.__legs[chan.LEFT_LEG_FRONT].body()
            self.__legs[chan.RIGHT_LEG_FRONT].body()
            time.sleep(SLEEP_COUNT * 2)
            self.__legs[chan.LEFT_LEG_FRONT].stretch()
            self.__legs[chan.RIGHT_LEG_FRONT].stretch()
            time.sleep(SLEEP_COUNT * 2)
        self.stand()

    def wiggle(self, wiggle_count):
        """ Wiggle butt """

        chan = Channel()

        self.sit()
        self.__legs[chan.LEFT_FOOT_BACK].up()
        self.__legs[chan.RIGHT_FOOT_BACK].up()
        time.sleep(SLEEP_COUNT * 5)

        for _ in range(0, wiggle_count):
            self.__legs[chan.LEFT_LEG_BACK].body()
            self.__legs[chan.RIGHT_LEG_BACK].stretch()
            time.sleep(SLEEP_COUNT * 5)
            self.__legs[chan.LEFT_LEG_BACK].stretch()
            self.__legs[chan.RIGHT_LEG_BACK].body()
            time.sleep(SLEEP_COUNT * 5)
        self.stand()

    def get_telemetry(self):
        """ returns a list of limbs and measurements """
        telemetry = []
        chan = Channel()
        telemetry.append(["left_leg_front", self.__legs[chan.LEFT_LEG_FRONT].angle])
        telemetry.append(["right_leg_front", self.__legs[chan.RIGHT_LEG_FRONT].angle])
        telemetry.append(["left_leg_back", self.__legs[chan.LEFT_LEG_BACK].angle])
        telemetry.append(["right_leg_back", self.__legs[chan.RIGHT_LEG_BACK].angle])
        telemetry.append(["left_foot_front", self.__legs[chan.LEFT_FOOT_FRONT].angle])
        telemetry.append(["right_foot_front", self.__legs[chan.RIGHT_FOOT_FRONT].angle])
        telemetry.append(["left_foot_back", self.__legs[chan.LEFT_FOOT_BACK].angle])
        telemetry.append(["right_foot_back", self.__legs[chan.RIGHT_FOOT_BACK].angle])
        return telemetry

class CommandHistory(object):
    """ models the command history object """

    # Private property History
    __history = []

    def __init__(self):
        self.__history.append("*** new history ***")

    def append(self, command):
        """ adds a command to the command history """
        self.__history.append(command)

    def clear(self):
        """ clears the command history """
        self.__history = []

    @property
    def history(self):
        """ gets all command history """
        return self.__history

    def get_history(self):
        """ DEPRICATED - use .history property"""
        print("This function is depricated - use .history property")

    @property
    def last_ten(self):
        """ get last 10 command history """
        return self.__history[-10:]

    def get_last_ten(self):
        """ DEPRICATED - Use .last_ten property """
        print("This function is deprecated - use .last_ten property instead")
