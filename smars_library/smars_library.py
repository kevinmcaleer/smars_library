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

Create a virtual environment (venv) and use the pip install -r requirements.txt
to install the dependencies

"""
import time
import logging
import Adafruit_PCA9685
from .channel import Channel
from .morse import Morse
logging.basicConfig(level=logging.CRITICAL)
logging.propagate = False

chans = { 'LEFT_LEG_FRONT': 0,    # channel 0
        'LEFT_LEG_BACK': 2,     # channel 2
        'RIGHT_LEG_FRONT': 6,   # channel 6
        'RIGHT_LEG_BACK': 4,    # channel 4

        'LEFT_FOOT_FRONT':  1,   # channel 1
        'LEFT_FOOT_BACK': 3,    # channel 3
        'RIGHT_FOOT_FRONT': 7,  # channel 7
        'RIGHT_FOOT_BACK': 5,   # channel 5
}

# Set DEBUG to True using the debug property
DEBUG = False

# Initialise the PCA9685 using the default address (0x40).
try:
    PWM = Adafruit_PCA9685.PCA9685()

    # the short delay should help the PCA9685 settle and not produce errors
    time.sleep(1)

except OSError as error:
    LOG_STRING = "failed to initialise the servo driver (Adafruit PCA9685): "
    logging.error(LOG_STRING)

    # tell later parts of the code not to actually use the driver

    DO_NOT_USE_PCA_DRIVER = True

    PWM = ""
except (RuntimeError) as ex:
    print("There was an error loading the adafruit driver; loading without PCA9685.")
    DO_NOT_USE_PCA_DRIVER = True # tell later parts of the code not to actually use the driver
else:
    LOG_STRING = "PCA9685 Driver loaded)."
    DO_NOT_USE_PCA_DRIVER = False # tell later parts of the code to use the driver
    logging.error(LOG_STRING)

SLEEP_COUNT = 0.05    # the amount of time to wait between pwm operations

# Set frequency to 60hz, good for servos.
try:
    if DO_NOT_USE_PCA_DRIVER is False:
        PWM.set_pwm_freq(60)
        time.sleep(1)
except ValueError as error:
    LOG_STRING = "failed to set the pwm frequency:, " + error
    logging.error(LOG_STRING)

def set_servo_pulse(channel, pulse):
    """
    Helper function to make setting a servo pulse width simpler.
    """

    if 0 <= channel <= 15 and \
       isinstance(channel,int)  and \
       pulse <= 4096 and \
       pulse >= 0:
        pulse_length = 1000000    # 1,000,000 us per second
        pulse_length //= 60       # 60 Hz
        logging.info('%s us per period', pulse_length)
        pulse_length //= 4096     # 12 bits of resolution
        logging.info('%s us per bit', pulse_length)
        pulse *= 1000
        pulse //= pulse_length
        try:
            if DO_NOT_USE_PCA_DRIVER is False:
                PWM.set_pwm(channel, 0, pulse)
        except (RuntimeError) as ex:
            logging.warning(
                """Failed to set pwm
                    - did the driver initialize correctly? %s""", ex)
        # print("Failed to set pwm - did the driver initialize correctly?")

        return True

    print("channel less than 0 or greater than 15, or not an integer, \
    or pulse is greater than 4096:", channel, pulse)
    logging.warning(
        "channel less than 0 or greater than 15, or not an integer, or pulse is greater than 4096.")
    return False


class Leg():
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
    __leg_minangle = 0
    __leg_maxangle = 180

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
        except (RuntimeError) as ex:
            logging.warning(
                """Failed to set the pwm frequency
                 - did the servo driver initialize correctly?, %s""", ex)

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
    def leg_minangle(self):
        """ Gets the minimum limb angle """
        return self.__leg_minangle

    @leg_minangle.setter
    def leg_minangle(self,value:int) -> bool:
        """ Sets the minimum limb angle """

        if not isinstance(value, int):
            print("Oops Limb Minimum Angle setter was expected the value to be an integer, \
                please try again but with a valid number between 0 and 180.")
            return False

        if 0<= value <= 180:
            self.__leg_minangle = value
            return True

        return False

    @property
    def leg_maxangle(self):
        """ Gets the maximum limb angle """
        return self.__leg_maxangle

    @leg_maxangle.setter
    def leg_maxangle(self,value:int) -> bool:
        """ Sets the maximum limb angle """

        if not isinstance(value, int):
            print("Oops Limb Maximum Angle setter was expected the value to be an integer, \
                please try again but with a valid number between 0 and 180.")
            return False

        if 0<= value <= 180:
            self.__leg_maxangle = value
            return True

        return False

    @property
    def channel(self):
        """ Returns the PCA9685 channel this servo/limb uses"""
        return self.__channel

    @channel.setter
    def channel(self, value:int) -> bool:
        """ Set the channel for this servo/limb """

        if not isinstance(value, int):
            print("Oops Limb channel setter was expected the value to be an integer, \
                please try again but with a valid number between 0 and 15.")
            return False

        # Check its a valid channel number
        if 0 <= value <= 15:
            self.__channel = value
            return True
        print("Oops Limb channel setter was expected the value to be an integer, \
             between 0 and 15.")
        return False


    @property
    def invert(self):
        """ returns the invert value """
        return self.__invert

    @invert.setter
    def invert(self,value):
        """ sets the invert value"""
        self.__invert = value


    def default(self):
        """
        Sets the limb to the default angle, by subtracting the maximum and
        minimum angles that were set previously
        """
        self.angle = self.__leg_maxangle - self.__leg_minangle
        self.__currentangle = self.__leg_maxangle - self.__leg_minangle


    def body(self):
        """
        Sets the limb to its body position.
        """
        if not self.__invert:
            self.angle = self.__leg_minangle
            self.__bodyangle = self.__leg_minangle
        else:
            self.angle = self.__leg_maxangle
            self.__bodyangle = self.__leg_maxangle
        self.__currentangle = self.__bodyangle


    def stretch(self):
        """
        Sets the limb to its stretch position.
        """
        if not self.__invert:
            self.angle = self.__leg_maxangle
            self.__stretchangle = self.__leg_maxangle
        else:
            self.angle = self.__leg_minangle
            self.__stretchangle = self.__leg_minangle
        self.__currentangle = self.__stretchangle

    def identify(self):
        """ Wiggles the limb between the angles of 85 - 95 for a couple of seconds """

        # wiggle
        for _ in range(1,5):
            self.angle = 80
            time.sleep(.25)
            self.angle = 100
            time.sleep(.25)
        self.angle = 90

    def swing(self):
        """
        Sets the limb to its swing position, which is 45 degrees - halfway
        between the body and stretch position.
        """
        if not self.invert:
            swing_angle = (self.__leg_minangle / 2) + self.__leg_minangle
            self.angle = swing_angle
        else:
            swing_angle = (self.__leg_maxangle - self.__leg_minangle) / 2
            self.angle = swing_angle
        self.__swingangle = swing_angle
        self.__currentangle = self.__swingangle

    def up(self):
        """
        raises the limb to its minimum angle
        """
        if not self.invert:
            self.angle = self.__leg_minangle
        else:
            self.angle = self.__leg_maxangle

    def down(self):
        """
        lowers the limb to its maximum angle
        """
        if not self.invert:
            self.angle = self.__leg_maxangle
        else:
            self.angle = self.__leg_minangle

    def middle(self):
        """
        moves the limb to half way between up and down.
        """
        self.angle = self.__leg_maxangle - self.__leg_minangle

    def show(self):
        """
        used for debugging - shows the servo driver channel number and the limb name
        """
        print(self.__channel)
        print(self.name)

    @angle.setter
    def angle(self, user_angle:int) -> bool:
        """
        Works out the value of the angle by mapping the leg_min and leg_max to
        between 0 and 180 degrees, then moves the limb to that position
        """
        pulse = 0

        if 0 <= user_angle <= 180:
            self.__leg_angle = user_angle
            # Check the angle is within the boundaries for this limb
            if self.__leg_minangle <= user_angle <= self.__leg_maxangle:
                mapmax = self.__leg_max - self.__leg_min
                percentage = (float(user_angle) / 180) * 100
                pulse = int(((float(mapmax) / 100) *
                             float(percentage)) + self.__leg_min)

                # send the servo the pulse, to set the angle
                try:
                    if DO_NOT_USE_PCA_DRIVER is False:
                        PWM.set_pwm(self.__channel, self.__channel, pulse)
                except RuntimeError as error:
                    logging.warning("Failed to set the pwm frequency - \
                    did the servo driver initialize correctly?")
                    logging.warning(error)
                self.__currentangle = user_angle
                return True


            # display an error message if the angle set was outside
            # the range (leg_minAngle and leg_maxAngle)
            logging.warning("Warning: angle was outside of bounds for this leg")
            return False
        return False

    def untick(self):
        """ Used to walk backwards """
        if self.__name == "RIGHT_LEG_BACK" or self.__name == "RIGHT_LEG_FRONT":
            if self.__currentangle <= self.__leg_maxangle:
                self.__currentangle += 2
                # print self.name, "setting angle to ", self.currentAngle
                self.angle = self.__currentangle
                return False
            return True
        if self.__name == "LEFT_LEG_BACK" or self.__name == "LEFT_LEG_FRONT":
            if self.__currentangle >= self.__leg_minangle:
                self.__currentangle -= 2
                # print self.name, "setting angle to ", self.currentAngle
                self.angle = self.__currentangle
                return False
            return True
        return True
    def tick(self):
        """
        Used for walking forward.
        Each tick received changes the current angle of the limb, unless an
        limit is reached, which then returns a true value
        """
        if self.__name == "LEFT_LEG_FRONT" or self.__name == "LEFT_LEG_BACK":
            if self.__currentangle <= self.__leg_maxangle:
                self.__currentangle += 2
                print(self.name, "Tick - setting angle to ", self.__currentangle)
                self.angle = self.__currentangle
                return False
            return True
        if self.__name == "RIGHT_LEG_FRONT" or self.__name == "RIGHT_LEG_BACK":
            if self.__currentangle >= self.__leg_minangle:
                self.__currentangle -= 2
                print(self.name, "Tick - setting angle to ", self.__currentangle)
                self.angle = self.__currentangle
                return False
            return True
        return True

    @property
    def name(self)->str:
        """ gets the Robot name """
        return self.__name

    @name.setter
    def name(self, name:str):
        """ Sets the Robot name """
        self.__name = name

class SmarsRobot():
    """
    This is used to model the robot, its legs and its sensors
    """
    def __init__(self):
        print("*** Initialising Robot ***")
        try:
            if DO_NOT_USE_PCA_DRIVER is False:
                pwm = Adafruit_PCA9685.PCA9685()
                pwm.set_pwm_freq(60)
        except RuntimeError as error:
            logging.warning(
                "Failed to set the pwm frequency - did the servo driver initialize correctly? %s",
                 error)

    # defines if the robot is a quad or wheel based robot
    # need to make this an enum then set the type to be one of the items in the list
    type = ['wheel', 'quad']

    # setup two arrays, one for legs, and one for feet
    __legs = []
    __feet = []

    # the friendly name for the robot - used in console messages
    __name = ""

    # debug status, default if off / False
    __debug = False

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

    def tap_message(self, message:str)->bool:
        """
        Taps out a character

        Provide the text string you want the robot to tap out via the message parameter.
        Make sure it is only lowercase alphabetic or numeric values. Spaces are allowed too.
        It will convert all the text to lower case if there are any uppercase characters.

        Parameters:
        ----------
        message : str
            This is the message to be tapped out by the Robot.

        Returns
        -------
        bool
            Returns True is the message was a valid Morse code compatible
            string (alpha-numeric characters)

            Returns False if the message is invalid.
        """

        message = message.lower()
        for character in message:
            if character not in Morse.alphabet and character != " ":
                print("Sorry the character", character, "isn't part of Morse Code, please try again")
                return False
        self.__feet[Channel.LEFT_FOOT_FRONT].up()
        for character in message:
            dot = 0.175
            dash = 0.5
            duration = 0.0
            if character == " ":
                duration = 1.5
            else:
                for dot_dash in Morse.alphabet[character]:
                    if dot_dash == '.':
                        duration = dot
                        print(".")
                    if dot_dash == "-":
                        duration = dash
                        print("-")
                        time.sleep(duration/2)  
                    self.__feet[Channel.LEFT_FOOT_FRONT].up()
                    time.sleep(duration)
                    self.__feet[Channel.LEFT_FOOT_FRONT].down()
                    time.sleep(0.1)
        return True

    def identify(self, channel:int)->str:
        """
        Identies the limb by the channel passed in, returns the limb name

        This function will wiggle the limb (between 80 and 100 degrees), so
        that you can easily identify if you have the correct limb wired up
        to the PCA9685 board.

        It will also indiciate if the limb is a foot or a leg.

        Parameters:
        -----------

        channel : int
            this is the channel you want to probe - to identify which servo
            or limb is connected to it.

        Returns
        -------

        str
            Returns the name of the channel - that is the foot or the limb name.

        """
        for limb in self.__feet:
            if limb.channel == channel:
                print("limb found in Feet")
                limb.identify()
                return limb.name
        for limb in self.__legs:
            if limb.channel == channel:
                print("limb found in Legs")
                limb.identify()
                return limb.name
        return "Limb not found"

    def set_limb_channel(self, limb_name:str, channel:int)->bool:
        """
        Sets the limb name to the channel provided, returns True if complete, False if not

        This sets the channel to the limb name provided.

        Parameters:
        -----------

        limb_name : str
            this is the name of the limb, e.g. LEFT_LEG_FRONT
        channel : int
            this is the channel number on the PCA9685 board, e.g. channel = 0

        Returns
        -------

        bool
            Returns True if the channel name was found and successfully set to
            the new channel number.
            Returns False if the channel name was not found.
        """

        index = chans.get(limb_name)
        print(index)

        found = False
        for limb in self.__legs:
            if limb.name == limb_name:
                self.__legs[index].channel = channel
                found = True
        for limb in self.__feet:
            if limb.name == limb_name:
                self.__feet[index].channel = channel
                found = True

        if found:
            # need to check which other limb still has this number
            for limb in self.__legs:
                if (limb.channel == channel) and (limb.name != limb_name):
                    print("Remember to change", limb.name, "as this is still \
                        using channel", channel)
            return True
        print("Limb name not found, sorry")
        return False


    @property
    def config(self)->dict:
        """
        Get the current limb configuration as a dictionary of settings

        This function provides a dictionary of all the limbs and their settings.
        These settings include:
        * name - the limb name
        * channel - the PCA9685 channel the limb.servo is connected to
        * invert - if the servo is upside down or not, and if the 0 - 180 degress
                   should be reversed to 180 - 0
        * min_angle - the minimum angle the servo can move to, to prevent damaging the robot
        * max_angle - the maximum angle the servo can move to

        Parameters:
        ----------

        n/a

        Returns
        -------

        dict
            Returns a dictionary of legs and feetm with all the information for each outlined
            above.

        """
        limb_config = []
        temp_limb = []
        for limb in self.__feet:
            temp_limb = {'name': limb.name,
                         'channel': limb.channel,
                         'invert':limb.invert,
                         'min_angle':limb.leg_minangle,
                         'max_angle':limb.leg_maxangle
                         }
            limb_config.append(temp_limb)
        for limb in self.__legs:
            temp_limb = {'name': limb.name,
                         'channel': limb.channel,
                         'invert':limb.invert,
                         'min_angle':limb.leg_minangle,
                         'max_angle':limb.leg_maxangle
                         }
            limb_config.append(temp_limb)
        return limb_config

    @property
    def debug(self)->bool:
        """
        Returns the debug status

        The Debug flag is used to provide more verbose output in some of the functions.
        Setting this flag to true will provide that more detailed output to the console.

        Parameters:
        -----------
        n/a

        Returns
        -------

        bool
            Returns True if the debug flag is set
            Returns False if the debug flag is not set
        """
        return self.__debug


    @debug.setter
    def debug(self, value:bool):
        """
        Sets the debug flag status.

        The Debug flag is used to provide more verbose output in some of the functions.
        Setting this flag to true will provide that more detailed output to the console.

        Parameters:
        -----------
        value : bool
            The status to change the debug flag to.

        Returns
        -------

        n/a

        """

        if value:
            self.__debug = True
        elif not value:
            self.__debug = False
        else:
            print(f"Unknown value: {value}")

    def invert_feet(self):
        """
        Inverts the feet

        This Function swaps all the 'Invert' status of the feet,
        from False to True or True to False. This is useful if you have
        printed the robot with the servo holders upside down and the feet
        at the top of the leg, rather than at the bottom.

        Parameters:
        -----------
        n/a

        Returns
        -------
        n/a
        """
        for limb in self.__feet:
            if limb.invert:
                limb.invert = False
            else:
                limb.invert = True

    def default(self):
        """
        Sets the limb to the default position.

        This function sets the legs and feet to the 'default' position, that is
        at the 90 degree position.

        Parameters:
        -----------
        n/a

        Returns
        -------
        n/a
        """
        for limb in self.__legs:
            limb.default()
        for limb in self.__feet:
            limb.default()


    @property
    def name(self)->str:
        """
        Gets the robots name.

        The name property can be used to get or set the name of the Robot.

        Parameters:
        -----------

        n/a

        Returns
        -------

        str
            Returns the name of the robot as a text string.
        """
        return self.__name

    @name.setter
    def name(self, name:str):
        """
        Sets the robots name, used for displaying console messages.

        This function sets the name of the robot, and then taps out
        the name of the Robot in Morse code.

        Parameters:
        -----------

        name : str
            The new name of the Robot to be set

        Returns
        -------

            n/a
        """
        self.__name = name
        print("***", name, "Online ***")
        self.tap_message(self.__name)
        if self.debug:
            logging.info("changed name to %s", name)

    def leg_reset(self):
        """
        Used to reset all the legs.

        This is the same as the default function, it sets each
        limb to its defualt, 90 degree position.

        Parameters:
        -----------

        n/a

        Returns
        -------

        n/a
        """
        for limb in self.__legs:
            limb.default()
            if self.debug:
                print(f"setting limb {limb} to default position")

    def middle(self):
        """
        Used to position all the legs into the middle position.

        This function moves each leg to the middle position, which is
        half way between the minimum angle and the maximum angle.

        Parameters:
        -----------

        n/a

        Returns
        -------

        n/a
        """
        print("received middle command")
        for limb in self.__legs:
            limb.middle()

    def sit(self):
        """
        Used to sit the robot down.

        This function sits the robot down by setting each of the feet
        to the Down position.

        Parameters:
        -----------

        n/a

        Returns
        -------

        n/a

        """
        print(self.__name, "sitting Down.")
        for limb in self.__feet:
            limb.down()

    def stand(self):
        """
        Used to stand the robot up.

        This function stands the Robot up by setting each of the feet
        to the up position.

        Parameters:
        -----------

        n/a

        Returns
        -------

        n/a
        """
        print(self.name, "standing up.")
        for limb in self.__feet:
            # self.__feet[limb].up()
            limb.up()

    def swing(self):
        """
        Moves the limb to the swing position.

        This function moves the legs to the swing position, which makes the
        Robot form a giant X shape. It lifts each foot up, moves the leg and then
        puts the foot back down again.

        Parameters:
        -----------

        n/a

        Returns
        -------

        n/a
        """
        for limb in range(0, 4):
            self.__feet[limb].down()
            time.sleep(SLEEP_COUNT)
            self.__legs[limb].swing()
            time.sleep(SLEEP_COUNT)
            self.__feet[limb].up()
            time.sleep(SLEEP_COUNT)

    def body(self):
        """
        Moves all the limbs to the body position.

        This function moves the legs to the body position, which makes the
        Limbs move close to the chassis. It lifts each foot up, moves the leg and then
        puts the foot back down again.

        Parameters:
        -----------

        n/a

        Returns
        -------

        n/a
        """
        for limb in range(0, 4):
            self.__feet[limb].down()
            time.sleep(SLEEP_COUNT)
            self.__legs[limb].body()
            time.sleep(SLEEP_COUNT)
            self.__feet[limb].up()
            time.sleep(SLEEP_COUNT)

    def stretch(self):
        """
        Moves all the limbs to the body position.

        This function moves the legs to the Stretch position, which makes the
        Robot legs stretch out towards the head and tail. It lifts each foot up,
        moves the leg and then puts the foot back down again.

        Parameters:
        -----------

        n/a

        Returns
        -------

        n/a
        """
        for limb in range(0, 4):
            self.__feet[limb].down()
            time.sleep(SLEEP_COUNT)
            self.__legs[limb].stretch()
            time.sleep(SLEEP_COUNT)
            self.__feet[limb].up()
            time.sleep(SLEEP_COUNT)

    def turnright(self):
        """
        Turns the robot to the right.

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
        Turns the robot to the left
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

    def forward(self, steps:int=None):
        """
        Move the Robot Forward.

        The Robot will walk forward by the number of steps provided, if no steps are provided
        it will walk a single step.

        Parameters:
        -----------

        steps : int
            The number of steps to walk forward

        Returns
        -------
        
        n/a
        """
        if steps is None:
            steps = 1
        self.walkforward(steps)

    def backward(self, steps:int=None):
        """
        Move the Robot Backward

        The Robot will walk backwards by the number of steps provided, if no steps are provided
        it will walk a single step.

        Parameters:
        -----------

        steps : int
            The number of steps to walk backwards

        Returns
        -------
        
        n/a
        """
        if steps is None:
            steps = 1
        self.walkbackward(steps)

    def help(self):
        """ displays information about which functions can be used"""
        print("This Robot accepts the following commands:")
        print("forward(<steps>)")
        print("backward(<steps>)")
        print("turnleft()")
        print("turnright()")
        print("clap()")
        print("wiggle()")
        print("get_telemetry()")
        print("stand()")
        print("sit()")
        print("swing()")
        print("body()")
        print("default()")
        print("tap_message(<the message to tap in Morse Code>)")

    def walkforward(self, steps:int=None):
        """
        Used to move the robot forward

        The Robot will walk forward by the number of steps provided, if no steps are provided
        it will walk a single step.

        Parameters:
        -----------

        steps : int
            The number of steps to walk forward

        Returns
        -------

        n/a
        """

        print("Moving Forward")

        if steps is None:
            steps = 1

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

            for tick_count in range(0, 4):
                if not self.__legs[tick_count].tick():
                    self.__legs[tick_count].tick()
                else:
                    self.__feet[tick_count].down()
                    time.sleep(SLEEP_COUNT)

                    if not self.__legs[tick_count].invert:
                        # if self.__legs[tick_count].name == "LEFT_LEG_BACK":
                        if self.__legs[tick_count].name == "RIGHT_LEG_FRONT":
                            self.__legs[tick_count].stretch()
                        else:
                            self.__legs[tick_count].body()
                    elif self.__legs[tick_count].invert:
                        # if self.__legs[tick_count].name == "LEFT_LEG_FRONT":
                        if self.__legs[tick_count].name == "RIGHT_LEG_BACK":
                            self.__legs[tick_count].body()
                        else:
                            self.__legs[tick_count].stretch()
                    time.sleep(SLEEP_COUNT)
                    self.__feet[tick_count].up()
                    time.sleep(SLEEP_COUNT)

    def walkbackward(self, steps):
        """
        Used to move the robot backward.

        The Robot will walk backward by the number of steps provided, if no steps are provided
        it will walk a single step.

        Parameters:
        -----------

        steps : int
            The number of steps to walk backward

        Returns
        -------

        n/a

        """
        print("Moving Backward")

        if steps is None:
            steps = 1

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
            for tick_count in range(0, 4):
                if not self.__legs[tick_count].untick():
                    # print self.name, "walking, step", currentStep, "of", steps
                    self.__legs[tick_count].untick()
                else:
                    # print "moving leg:", self.legs[n].name
                    self.__feet[tick_count].down()
                    time.sleep(SLEEP_COUNT)

                    # change this to left and right legs, rather than invert or not invert
                    if not self.__legs[tick_count].invert:
                        if self.__legs[tick_count].name == "LEFT_LEG_BACK":
                            self.__legs[tick_count].stretch()
                        else:
                            self.__legs[tick_count].body()
                    elif self.__legs[tick_count].invert:
                        if self.__legs[tick_count].name == "LEFT_LEG_FRONT":
                            self.__legs[tick_count].body()
                        else:
                            self.__legs[tick_count].stretch()
                    time.sleep(SLEEP_COUNT)
                    self.__feet[tick_count].up()
                    time.sleep(SLEEP_COUNT)

    def clap(self, clap_count:int=None):
        """
        Clap front two hands (the sound of two hands clapping).

        Claps the number of times as defined in by clap_count, if no clap_count if provided
        it defaults to 1 clap.

        Parameters:
        -----------
        clap_count : int
            The number of times the Robot should perform the Clap action.

        Returns
        -------

        n/a
        """
        chan = Channel()

        print("Clapping")

        if clap_count is None:
            clap_count = 1

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

    def wiggle(self, wiggle_count:int=None):
        """
        Performs a cheeky Wiggle butt Action

        This is another fun action - it will make the robot wiggle by the
        number of times as specificed in the wiggle_count; if no number is
        provided it will default to 1 wiggle.

        Parameters:
        -----------
        wiggle_count : int
            The number of times to perform the wiggle action

        Returns
        -------
        
        n/a
        """
        print("Wiggling")

        if wiggle_count is None:
            wiggle_count = 1

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
        """
        Returns a list of limbs and measurements.

        This is used to provide detailed meaurements for each limb; the current angle
        the limb is set to.

        Parameters:
        -----------

        n/a

        Returns
        -------

        n/a
        """
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

class CommandHistory():
    """
    Models the command history object

    This class can be used to capture each of the commands the Robot has performed
    into a list so that this can be displayed or used later.
    """

    # Private property History
    __history = []

    def __init__(self):
        """ Initialises the CommandHistory Class
        """
        self.__history.append("*** new history ***")

    def append(self, command:str):
        """ Adds a command to the command history

        Appends a command passed via the command parameter to the history list.

        Parameters:
        -----------

        command : str
            The command to be appended to the history list

        Returns
        -------

        n/a
        """
        self.__history.append(command)

    def clear(self):
        """ clears the command history
        
        This function wipes the command history.
        """
        self.__history = []

    @property
    def history(self):
        """ Gets all command history """
        return self.__history

    @property
    def last_ten(self):
        """ Get last 10 command history """
        return self.__history[-10:]
