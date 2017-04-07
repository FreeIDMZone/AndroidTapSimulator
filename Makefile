all:
	arm-linux-gnueabihf-gcc-5 sendevent.c -o sendevent -lm -static
