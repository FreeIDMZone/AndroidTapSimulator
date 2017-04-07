# AndroidTapSimulator

This project creates a faster way - compared to `adb shell input` - to send tap and sweep commands to Android devices.

## Motivation 

The reasons why the stock adb shell method is slow are several: 

1. The `input` binary in the android side is a Java program = slow to start, slow to execute
2. It executes just one command at a time. 
3. It is very conservative on the internal delay time necessary for talking to the kernel 

## Building 

You will need Android ADB and the cross compile tool. On Ubuntu issue

```bash
sudo apt-get install android-tools-adb g++-5-arm-linux-gnueabihf
```

Compile our android-side driver 

```bash
cd AndroidTapSimulator
arm-linux-gnueabihf-gcc-5 -O3  sendevent.c -o sendevent -lm -static
```
Then push the binary to the android side

```bash
adb push sendevent /data/local/tmp/sendevent
```

## Running 

The default location (/data/local/tmp/) is hardcoded in AdbSessionBatch.py line 97. Change if necessary - you have the code.
```python
cmdstr = "echo \"%s\" | /data/local/tmp/sendevent %s\n" % (" ".join(self.commands),self.touchscreen )
```
The kernel delay is also hardcoded in the same file, two lines below
```python
        for line in self.adb.read(0.25):
```
If you start seeing missing lines, increase this value.
        
Then run an example

```bash
python draw_star.py
```
