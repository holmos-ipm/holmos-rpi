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

## Project Status
Code and hardware are functional: several people have built copies in Freiburg.
However, there are probably still gaps in the documentation - if you stumble upon one, feel free to contact us.
You can open an issue here, or email us.
(Or improve the instructions yourself and request a merge...)

Please let us know if you attempt to build your own setup - we'd be very excited to hear from you!

## Contact
You can mail [Tobias](mailto:tobias.beckmann@ipm.fraunhofer.de) and [Alex](mailto:alexander.bertz@ipm.fraunhofer.de) with questions, comments - or just a short note if you've managed to build a working Holmos setup.

## License
The code in both repostiories is published under the GPLv3, see the [license](license.md).
For other licensing options, feel free to contact us.
