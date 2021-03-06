import serial
from time import sleep
import threading

# class FlightControllerCommands(threading.Thread):


class FlightControllerCommands():
    """
    This is a class which allows for the communication between the pi and any flight
    controller which supports serial communication in the ibus format. When the thread
    is started it will send serial messages to the flight controller 142 times per second
    """

    def __init__(self, port='/dev/ttyS0', throttle=885, pitch=1500, yaw=1500, roll=1500):
        self.port = port
        self.connection = None
        self.armed = False
        self.throttle = throttle
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll
        self.constantmessage = False
        self.mode = "disarmed"
        self.senddelay = 0.01

    def connecttoport(self, dport=None):
        """This function connect to the desired port"""
        if dport is None:
            dport = self.port
        self.connection = serial.Serial(
            dport, 115200, timeout=10, write_timeout=10)
        print("Connected to " + self.connection.name)
        return self.connection

    def send(self, msg):
        """This function is what is used to send the final message. It takes the
        message as an argument."""
        self.connection.write(msg)

    def pack(self, channels):
        """This function packs the desired message in the ibus format. You give it the
        values for all 14 channel in an array. Unused channels must be given the
        value 0x05DC"""
        message = []

        # adds the required begining header of the message
        message.append(0x20)
        message.append(0x40)

        # puts each channel value in little endian format in the message
        for channel in channels:
            message.append(channel % 256)
            message.append(channel//256)

        # calculates and ands the required cheksum
        checksum = 0xffff - sum(message)
        message.append(checksum % 256)
        message.append(checksum // 256)

        return message

    def commands(self, channels):
        """This function will take any amount of channels given and both pack and send
        the message to the flight controller. Values given must still be given in the
        order of the channels"""
        command = []
        for i in channels:
            command.append(i)
        command += ([1000] * (14 - len(channels)))

        message = self.pack(command)

        if not self.connection:
            self.connecttoport()

        self.send(message)

    def disarm(self):
        print("Disarming Drone")
        self.armed = False
        sleep(1)

    def arm(self):
        print("Arming Drone")
        self.armed = True
        sleep(1)

    def run(self):
        self.constantmessage = True
        print('Begining communications with flight controller\n')
        while self.constantmessage:
            self.commands(
                [self.roll, self.pitch, self.throttle, self.yaw, 2000]
                if self.armed else
                [1500, 1500, 885, 1500, 1000]
            )
            sleep(self.senddelay)
        print('Ending communication')


def main():
    """This is an example of how to use this class"""
    from fccontrolclass import FlightControllerCommands as fc
    control = fc()
    t1 = threading.Thread(target=control.run)

    t1.start()
    sleep(1)

    control.arm()
    sleep(1)

    # take off
    control.throttle = 1500
    sleep(2)
    # land
    descentSize = 1
    while control.throttle > 1000:
        control.throttle -= descentSize
        sleep(control.senddelay)

    control.throttle = 1000
    sleep(2)

    control.disarm()

    control.constantmessage = False


if __name__ == '__main__':
    main()
