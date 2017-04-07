#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <errno.h>
#include <ctype.h>
#include "input-event-codes.h"

//  arm-linux-gnueabihf-gcc-5 -O3  sendevent.c -o sendevent -lm -static
//  adb push sendevent /data/local/tmp/sendevent

// from <linux/input.h>

struct input_event {
    struct timeval time;
    uint16_t type;
    uint16_t code;
    int32_t  value;
} __attribute__((packed));

#define EVIOCGVERSION        _IOR('E', 0x01, int)            /* get driver version */
#define EVIOCGID        _IOR('E', 0x02, struct input_id)    /* get device ID */
#define EVIOCGKEYCODE        _IOR('E', 0x04, int[2])            /* get keycode */
#define EVIOCSKEYCODE        _IOW('E', 0x04, int[2])            /* set keycode */

#define EVIOCGNAME(len)        _IOC(_IOC_READ, 'E', 0x06, len)        /* get device name */
#define EVIOCGPHYS(len)        _IOC(_IOC_READ, 'E', 0x07, len)        /* get physical location */
#define EVIOCGUNIQ(len)        _IOC(_IOC_READ, 'E', 0x08, len)        /* get unique identifier */

#define EVIOCGKEY(len)        _IOC(_IOC_READ, 'E', 0x18, len)        /* get global keystate */
#define EVIOCGLED(len)        _IOC(_IOC_READ, 'E', 0x19, len)        /* get all LEDs */
#define EVIOCGSND(len)        _IOC(_IOC_READ, 'E', 0x1a, len)        /* get all sounds status */
#define EVIOCGSW(len)        _IOC(_IOC_READ, 'E', 0x1b, len)        /* get all switch states */

#define EVIOCGBIT(ev,len)    _IOC(_IOC_READ, 'E', 0x20 + ev, len)    /* get event bits */
#define EVIOCGABS(abs)        _IOR('E', 0x40 + abs, struct input_absinfo)        /* get abs value/limits */
#define EVIOCSABS(abs)        _IOW('E', 0xc0 + abs, struct input_absinfo)        /* set abs value/limits */

#define EVIOCSFF        _IOC(_IOC_WRITE, 'E', 0x80, sizeof(struct ff_effect))    /* send a force effect to a force feedback device */
#define EVIOCRMFF        _IOW('E', 0x81, int)            /* Erase a force effect */
#define EVIOCGEFFECTS        _IOR('E', 0x84, int)            /* Report number of effects playable at the same time */

#define EVIOCGRAB        _IOW('E', 0x90, int)            /* Grab/Release device */

// end <linux/input.h>

// https://android.googlesource.com/platform/system/core/+/android-7.1.1_r28/toolbox/sendevent.c
// https://android.googlesource.com/platform/frameworks/base/+/android-7.1.1_r22/cmds/input/src/com/android/commands/input/Input.java

int event_fd = -1;
int track_id = -1;
int delay = 30000;
struct input_event event;

#define MAXTOKENS 1024
#define BUFSIZE 4096



int send_event( uint16_t type, uint16_t code, int32_t value )
{
    struct timeval inc;
    int ret;
    event.type = type;
    event.code = code;
    event.value = value;
    ret = write(event_fd, &event, sizeof(event));
    if(ret < sizeof(event)) {
        fprintf( stderr, "write event failed, %s\n", strerror(errno));
        return -1;
    }
    inc.tv_sec = 0;
    inc.tv_usec= 100000;
    timeradd( &event.time, &inc, &event.time );
    //fprintf( stderr, "Event: %d %d %d Time:%ld %ld\n", type, code, value,
    //         event.time.tv_sec, event.time.tv_usec );
    return 0;
}

void init_time() {
    //gettimeofday( &event.time, NULL );
    memset( &event, 0, sizeof(event));
    usleep( delay );
}

void process_tokens( char**token, int ntok )
{
    while ( ntok>0 )
    {
        if ( strcmp( token[0], "," )==0 ) {
            ntok--;
        }
        else if ( strcmp( token[0], "tap" )==0 ) {
            int x = atoi( token[1] );
            int y = atoi( token[2] );
            int p = atoi( token[3] );
            ntok -= 4;
            token+= 4;
            init_time();
            send_event(  EV_KEY, BTN_TOUCH, 1 );
            send_event(  EV_ABS, ABS_MT_PRESSURE, 0 );
            send_event(  EV_ABS, ABS_MT_TRACKING_ID, track_id++ );
            send_event(  EV_KEY, BTN_TOOL_FINGER, 1 );
            send_event(  EV_ABS, ABS_MT_POSITION_X, x );
            send_event(  EV_ABS, ABS_MT_POSITION_Y, y );
            send_event(  EV_ABS, ABS_MT_PRESSURE, p );
            send_event(  EV_SYN, SYN_REPORT, 0 );
            send_event(  EV_KEY, BTN_TOUCH, 0 );
            send_event(  EV_ABS, ABS_MT_TRACKING_ID, 0 );
            send_event(  EV_KEY, BTN_TOOL_FINGER, 0 );
            send_event(  EV_SYN, SYN_REPORT, 0 );
        }
        else if ( strcmp( token[0], "swipe_begin" )==0 ) {
            int x = atoi( token[1] );
            int y = atoi( token[2] );
            int p = atoi( token[3] );
            ntok -= 4;
            token+= 4;
            fprintf( stderr, "Command: swipe_begin %d %d %d \n", x, y, p );
            init_time();
            send_event(  EV_KEY, BTN_TOUCH, 1 );
            send_event(  EV_ABS, ABS_MT_PRESSURE, 0 );
            send_event(  EV_ABS, ABS_MT_TRACKING_ID, track_id++ );
            send_event(  EV_KEY, BTN_TOOL_FINGER, 1 );
            send_event(  EV_ABS, ABS_MT_POSITION_X, x );
            send_event(  EV_ABS, ABS_MT_POSITION_Y, y );
            send_event(  EV_ABS, ABS_MT_PRESSURE, p );
            send_event(  EV_SYN, SYN_REPORT, 0 );
        }
        else if ( strcmp( token[0], "swipe_move" )==0 ) {
            int x = atoi( token[1] );
            int y = atoi( token[2] );
            int p = atoi( token[3] );
            ntok -= 4;
            token += 4;
            //fprintf( stderr, "Command: swipe_move %d %d %d \n", x, y, p );
            init_time();
            send_event(  EV_ABS, ABS_MT_PRESSURE, 0 );
            send_event(  EV_ABS, ABS_MT_POSITION_X, x );
            send_event(  EV_ABS, ABS_MT_POSITION_Y, y );
            send_event(  EV_ABS, ABS_MT_PRESSURE, p );
            send_event(  EV_SYN, SYN_REPORT, 0 );
        }
        else if ( strcmp( token[0], "swipe_end" ) ==0 ) {
            ntok -= 1;
            token += 1;
            fprintf( stderr, "Command: swipe_end \n" );
            init_time();
            send_event(  EV_ABS, ABS_MT_PRESSURE, 0 );
            send_event(  EV_ABS, ABS_MT_TRACKING_ID, -1 );
            send_event(  EV_KEY, BTN_TOUCH, 0 );
            send_event(  EV_KEY, BTN_TOOL_FINGER, 0 );
            send_event(  EV_SYN, SYN_REPORT, 0 );
        }
        else {
            token++;
            ntok--;
        }
    }
}


void process_buffer( char* buf, int buflen )
{
    char* token[MAXTOKENS];
    int j;
    int curistok = 0;
    int ntok = 0;

    if ( buflen==0 ) return;

    //fprintf( stderr, "Buffer %d:[%s]\n", buflen, buf );
    for ( j=0; j<buflen; ++j ) {
        int istok = isgraph(buf[j]);
        //fprintf( stderr, "  ch[%c] istok[%d] curtok[%d]\n", buf[j], istok, curistok );
        if ( (istok!=0) && (curistok==0) ) {
            curistok = 1;
            token[ntok++] = &buf[j];
            if ( ntok == MAXTOKENS ) break;
        }
        else if ( (istok==0) && (curistok!=0) ) {
            curistok = 0;
            buf[j] = 0;
            //fprintf( stderr, " token %d: %s\n", ntok-1, token[ntok-1] );
        }
    }
    if ( curistok!=0 ) {
        buf[j] = 0;
        //fprintf( stderr, " token %d: %s\n", ntok-1, token[ntok-1] );
    }

    if ( ntok==0 ) return;

    process_tokens( token, ntok );
}

int main(int argc, char *argv[])
{
    track_id = rand() % 65536;
    int version;

    if(argc != 2 ) {
        fprintf(stderr, "use: %s device\n", argv[0]);
        return 1;
    }

    fprintf( stderr, "Device: %s\n", argv[1] );
    event_fd = open(argv[1], O_RDWR);
    if( event_fd < 0) {
        fprintf(stderr, "could not open %s, %s\n", argv[1], strerror(errno));
        return 1;
    }
    if (ioctl( event_fd, EVIOCGVERSION, &version)) {
        fprintf(stderr, "could not get driver version for %s, %s\n", argv[1], strerror(errno));
        return 1;
    }

    fprintf( stderr, "Processing input\n" );
    char*  buf = malloc(BUFSIZE);
    int buflen = 0;
    while ( 1 ) {
        int c = fgetc( stdin );
        //fprintf( stderr, "Got char %d %c\n", c, c );
        if ( c==EOF ) {
            if ( buflen>0 ) {
                process_buffer( buf, buflen );
            }
            fprintf( stderr, "Got EOF, quitting\n" );
            break;
        }
        buf[buflen++] = c;
        if ( c=='\n' ) {
            buf[buflen-1] = 0;
            process_buffer( buf, buflen-1 );
            buflen = 0;
        }
        if ( buflen==BUFSIZE ) {
            buflen = 0;
        }
    }
    close( event_fd );
    return 0;
}
