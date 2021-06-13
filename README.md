# SMARS

Screwless Modular Assemblable Robotic System

![Build Status](https://travis-ci.com/kevinmcaleer/smars_library.svg)

## SMARSfan.com

Visit www.smarsfan.com for more information about this project. The site includes build instructions, videos, an interview with the designer and much more.

## About this library

This library will enable you to get the quad robot walking and detecting its environment.

Link to thingiverse original model:
<https://www.thingiverse.com/thing:2662828>

Link to Quad version
<https://www.thingiverse.com/thing:2755973>

## Version 2.0 Released
Version 2.0 has now been released, including:
- fixes for the walking cycle
- new Morse code feature - use `tap_message()` to tap out message
- changing the name with `name = "name"` also taps out the new name
- Added a new `config` function to return the current configuration
- Added a new identify feature, for identifying each limb - use `identify(channel)` to make each limb wiggle one at a time
- added a new channel property so that PCA9685 channels can be set at runtime

## Overview and Background

*From the Creator - Kevin Thomas*
> *This robot is really easy and cheap to 3d print, build and program. It can be assembled without screws or 
> soldering and it's modular so it can be adapted for different purposes. I'm Swiss, so I don't know American 
> scholastic system but I would use SMARS in last year of middle school, high school or universities/ colleges. 
> There is more "open electronics" compared to a Lego NXT or similar, so students need a few knowledges about 
> security, electrical laws and so on. It can be use to improve software development skills, CAD skills or 
> electronics skills, students can design their own modules and customize their SMARS.*

## Programming SMARS

You can use most common small hardware platforms as the brains inside SMARS, the Arduino platform (and compatible) was used in the original design as its cheap, commonly available, and the tools for programming it are easy to use. 

For the quad version of the robot a Raspberry Pi Zero was used. The language commonly used on the Pi (and where it gets it name from) is Python. A library module has been written for both Arduino and Python to help you get started.

---

## Getting the Arduino IDE

Visit <http://www.arduino.cc> to download the latest Arduino Integrated Development Environment (IDE).

## Learn Python

To quickly get up to speed with Python, checkout the SMARS Learning Platform - <https://www.smarsfan.com/learn/python_101>
