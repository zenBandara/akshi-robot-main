#!/usr/bin/env python3

import time
import math
import random
import signal
import pigpio

# ================= SETTINGS =================

PIN_YAW = 24
PIN_PITCH = 25

SERVO_MIN_US = 600
SERVO_MAX_US = 2400

SERVO_MIN_DEG = 5.0
SERVO_MAX_DEG = 170.0

CENTER_YAW = 90.0
CENTER_PITCH = 90.0

# Faster update rate
STEP_DT = 0.025

# Main movement amplitudes
YAW_MAIN = 14.0
PITCH_MAIN = 8.0

# Secondary movement amplitudes
YAW_SECONDARY = 5.0
PITCH_SECONDARY = 3.5

# Slow wandering attention
MAX_WANDER_YAW = 12.0
MAX_WANDER_PITCH = 6.0

# Faster attention drift
WANDER_SMOOTHING = 0.005

# =================================================

running = True


def handle_sigint(sig, frame):
    global running
    running = False


signal.signal(signal.SIGINT, handle_sigint)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def deg_to_us(angle_deg):

    angle_deg = clamp(angle_deg, 0.0, 180.0)

    return int(
        SERVO_MIN_US
        + (angle_deg / 180.0)
        * (SERVO_MAX_US - SERVO_MIN_US)
    )


class Servo:

    def __init__(self, pi, pin, start_deg):

        self.pi = pi
        self.pin = pin

        self.pi.set_mode(pin, pigpio.OUTPUT)

        self.deg = start_deg

        self.pi.set_servo_pulsewidth(
            pin,
            deg_to_us(start_deg)
        )

    def set_angle(self, deg):

        deg = clamp(
            deg,
            SERVO_MIN_DEG,
            SERVO_MAX_DEG
        )

        self.deg = deg

        self.pi.set_servo_pulsewidth(
            self.pin,
            deg_to_us(deg)
        )

    def stop(self):

        self.pi.set_servo_pulsewidth(
            self.pin,
            0
        )


def main():

    global running

    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError(
            "pigpio daemon not running.\n"
            "Use: sudo systemctl start pigpiod"
        )

    servo_yaw = Servo(
        pi,
        PIN_YAW,
        CENTER_YAW
    )

    servo_pitch = Servo(
        pi,
        PIN_PITCH,
        CENTER_PITCH
    )

    start_time = time.time()

    wander_yaw = 0.0
    wander_pitch = 0.0

    wander_yaw_target = 0.0
    wander_pitch_target = 0.0

    next_wander = time.time()

    try:

        while running:

            now = time.time()

            # Pick a new interest point occasionally
            if now > next_wander:

                wander_yaw_target = random.uniform(
                    -MAX_WANDER_YAW,
                    MAX_WANDER_YAW
                )

                wander_pitch_target = random.uniform(
                    -MAX_WANDER_PITCH,
                    MAX_WANDER_PITCH
                )

                next_wander = (
                    now
                    + random.uniform(8, 15)
                )

            # Smoothly drift toward target
            wander_yaw += (
                wander_yaw_target
                - wander_yaw
            ) * WANDER_SMOOTHING

            wander_pitch += (
                wander_pitch_target
                - wander_pitch
            ) * WANDER_SMOOTHING

            t = now - start_time

            yaw = (

                CENTER_YAW

                + wander_yaw

                + YAW_MAIN
                * math.sin(
                    0.35 * t
                )

                + YAW_SECONDARY
                * math.sin(
                    0.85 * t + 1.5
                )

            )

            pitch = (

                CENTER_PITCH

                + wander_pitch

                + PITCH_MAIN
                * math.sin(
                    0.25 * t + 1.0
                )

                + PITCH_SECONDARY
                * math.sin(
                    0.70 * t
                )

            )

            servo_yaw.set_angle(yaw)
            servo_pitch.set_angle(pitch)

            time.sleep(STEP_DT)

    finally:

        try:
            servo_yaw.stop()
            servo_pitch.stop()
        except:
            pass

        try:
            pi.stop()
        except:
            pass

        print("Organic classroom animacy stopped.")


if __name__ == "__main__":
    main() 
