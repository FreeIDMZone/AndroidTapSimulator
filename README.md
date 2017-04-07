# AndroidTapSimulator

This project creates a faster way - compared to `adb shell input` - to send tap and sweep commands to Android devices.

You will need Android ADB and the cross compile tool. On Ubuntu issue


```bash
sudo apt-get install android-tools-adb g++-5-arm-linux-gnueabihf
```

Compile our android-side driver 

```bash
cd AndroidTapSimulator
arm-linux-gnueabihf-gcc-5 -O3  sendevent.c -o sendevent -lm -static
adb push sendevent /data/local/tmp/sendevent
```

Then run an example

```bash
python draw_star.py
```
