INTRODUCTION

------------

WinterLab is an open-source integrated electronics test and measurement platform, designed for use at the undergraduate level. The full platform consists of the WinterLab board (a microcontroller-based development board) and a graphical user interface (GUI). It is named after the cold weather commonly encountered around the institution at which it was developed.


ARCHIVE CONTENTS

-----------

- executables: self-contained programs, runnable out of the box on Mac, Ubuntu, and Windows
- winterlab: source code for the GUI (Python)
- winterlab_firmware: source code for the microcontroller (C++ / Arduino scripting language). The firmware was designed to run on a Teensy 3.6, but can be adapted for other similar development boards by changing pinout and updating some register assignments.
- hardware: photographs of assembled boards and circuit schematics. Printed circuit board design files, such as Gerber files and/or Altium projects, are available upon request; please contact maclean.rouble@mail.mcgill.ca.
- winterlab_howto.pdf: a brief introduction to using an assembled WinterLab board


INSTALLATION / USE

-----------

You can either download the appropriate executable package for your operating system, or run the python source code (see README.md in /winterlab/). If going the way of the executable, simply unpack the archive, and open the executable file within (typically "winterlab.exe" or similar).

It is recommended to use the Arduino IDE to upload the winterlab firmware to your Teensy 3.6 board. Make sure to include the pdb.h file in the same project folder as your .ino file (same configuration as the winterlab_firmware folder).


HARDWARE

------------

A functional diagram is included in the hardware folder. This illustrates which circuit topologies are used as the I/O interfaces for which WinterLab functions (oscilloscope, function generator, etc). The details of these circuits, including component values and Teensy 3.6 pin connections, can be found in the full circuit schematics (hardware/schematics/WinterLab.pdf). This should provide the framework for assembling your own device, if you wish.

If you would prefer to have circuit boards printed, the PCB design files are freely available upon demand -- contact us!
