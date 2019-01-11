# Installation

## Hardware
Tested on Rpi3B+ and Pre-Installed Noobs (rs 121-3897), 2019-01

* Insert Noobs microSD card into Rpi
* Connect camera (see [tutorial](https://projects.raspberrypi.org/en/projects/getting-started-with-picamera/4]))
* Connect mouse, keyboard, monitor
* Finally, connect microUSB Power. 

LEDs on the Rpi should light up instantly, and you should see some rapsberries on the screen. 
After a while, the Raspbian Desktop appears.


## Software

### Raspbian Setup
Af first boot, a Welcome screen appears. Follow the instruction to setup your keyboard, password, and Wifi.
Updating all packages takes some time, and reboot(s) may be required.
If updates fail, you may need to setup your proxy first, see below.

Once everything is done, click the raspberry in the upper left and choose "Preferences" -> "Raspberry Pi Configuration".
Select "Interfaces" at the top, and enable the camera.

Now, open a Terminal (black icon at top of screen or Ctrl-Alt-T) and enter `raspistill -f`.
You should see a full-screen view of the camera.

### Proxy
If you are behind a proxy, configure apt:
```
cd /etc/apt/apt.conf.d
sudo nano 10proxy
```
...to create the file `10proxy`, which needs to contain the line `Acquire::http::Proxy "http://153.96.204.21:80/";`, 
including quotation marks and semicolon - and using the IP:port of your networks proxy.

For all oder programs, edit `/etc/environment` and add the line ```export http_proxy="http://proxyaddress:port/"```

### Holmos Software
Get a copy ("clone") of this repository by running `git clone https://<git server>/holmos-rpi` in a terminal.
A subfolder to your current folder will be created and the software copied there.

Almost all packages required for the holmos-rpi software are preinstalled. Run 
`sudo apt-get install python3-pil.imagetk` to install the final missing package.

`cd holmos_rpi` to change into that newly created folder

Start the software with `python3 rpi_main.py`
