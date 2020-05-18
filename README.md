# Holmos - Code

Holmos is a digital holographic microscope developed at [Fraunhofer IPM](http://ipm.fraunhofer.de) with help from local schools via the [Freiburg Seminar](https://freiburg-seminar.de) and with kind support from the [BMBF](https://www.bmbf.de).
The hardware is based on the Raspberry Pi.

The setup was presented at the Conference *Digital Holography and 3D Imaging* in Bordeaux in 2019.
The [abstract and poster](http://publica.fraunhofer.de/dokumente/N-546165.html) are available online and give an overview of the technical features.

An [article](https://www.heise.de/select/make/2020/2/1587411411090155) in the German *Make Magazin* (paywalled) describes the project and gives an overview of the funtionality.

## Repositories
The holmos-ipm repositories aim to be small, but complete:
* This repository contains the code running on the Raspberry Pi to evaluate the camera images and calculate phase maps.
* The [hardware repository](https://github.com/holmos-ipm/holmos-hardware/) contains instructions to build your own copy of the setup, and files describing the 3D-printed parts.

In addition, much of the work that the student groups contributed is documented online, at [https://github.com/holmos-mikroskop/](https://github.com/holmos-mikroskop/).
That repository - especially the [Wiki](https://github.com/holmos-mikroskop/holmos/wiki) - documents the status at the end of the formal project.
The student repository is in German, and is more thourough and detailed in some places. 
It will probably not be updated as much as this IPM repository.

## Installation
Please see the separate [installation instructions](INSTALL.md) to get the software running on your Raspberry Pi.

## Usage
Run `rpi_main.py` or one of the `start_??.sh` to start the user interface for live measurements.
* Raw image: the black/white camera image, useful for navigating the sample/focusing (block the reference beam).
* FFT: always has a spot in the center, and should have two symmetrical spots (ideally: discs) near the edges.
  One of these discs needs to be selected by moving the blue rectangle onto it.
  Click to set the rectangle center, use arrow keys for fine adjustment.
* Phase image: The extracted phase (optical path length).

The phase images are wrapped (i.e. have jumps at λ or 2π). 
`start_unwrap_ui.py` provides a very(!) basic unwrapper, but it only works for very clean phase images.

To date, a fancy unwrapper and 3D visualisaion of the phase maps are outside the scope of this project:
We are striving to keep the code easy to install/run on the RPi.

## Project Status, Contributions
Code and hardware are functional. 
The main development phase of HolMOS is complete, we are only reacting to user input from now on.
Several copies have been built, especially by Freiburg students and readers of the German Make Magazine.

However, there are probably still bugs and gaps in the documentation - if you stumble upon one, feel free to contact us.
In order of preference:
* Improve the instructions yourself and request a merge.
* Open an issue here. This makes question and answer public, helping others.
* If the above are too difficult for you, write an email.

Please let us know if you attempt to build your own setup - we'd be very excited to hear from you!

## Contact
You can mail [Tobias](mailto:tobias.beckmann@ipm.fraunhofer.de) and [Alex](mailto:alexander.bertz@ipm.fraunhofer.de) with questions, comments - or just a short note if you've managed to build a working Holmos setup.

## License
The code in both repostiories is published under the GPLv3, see the [license](license.md).
For other licensing options, feel free to contact us.
