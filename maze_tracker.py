"""
maze_tracker.py
green hat on the floor -> 10 x 10 image -> wekinator -> arduino -> maze

wekinator: 100 inputs, 2 outputs from -1 to 1 (0,0 = level). inputs on port 6448, outputs back on 12000
arduino: close the serial monitor and the processing relay first, and start with the maze level

keys (click the window first):
  1 / 2   macbook facetime camera / webcam
  k       set tape corners, then click the 4 corners in any order
  c       tune to the hat, then click the middle of the hat
  p       wekinator view, the exact 10 x 10 image wekinator gets
  q       quit (corners and hat tuning are saved for next time)
"""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import AVFoundation
import CoreMedia
import cv2
import numpy as np
import serial
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
from serial.tools import list_ports

GREEN = 8  # how much greener than the floor around it the hat has to be, C sets this
MIN_SIZE = 1000  # smaller green patch than this = not the hat (hat ~3500, a bottle ~400)
HOLD = 0.3  # if the hat blinks out for less than this many seconds, keep the last one

LOW = (320, 240)  # the hat finder works at this size
WEK = (10, 10)  # what wekinator gets, 10 x 10 = 100 inputs
DOT = 5  # hat dot size in the wekinator view (out of 40 across), about the hat's real size
STEADY = 0.15  # dot smoothing while the hat is still, lower = steadier, 1 = off
VIEW = (640, 480)  # window size
EASE = 0.1  # maze smoothing, lower = smoother but slower

BAUD = 115200  # must match Serial.begin in the arduino code
WEK_RANGE = 1  # wekinator's outputs go from -1 to 1, 0 = level
TILT_MAX = 500  # the arduino gets -500 to 500, start smaller for the first test
CORNERS = Path(__file__).with_name("corners.json")
TUNING = Path(__file__).with_name("green.json")
WINDOW = "maze"


# ---------------- camera ----------------
def find_cameras():
    """key -> (camera number, name). opencv numbers mac cameras in uniqueID order"""
    devices = AVFoundation.AVCaptureDevice.devicesWithMediaType_(AVFoundation.AVMediaTypeVideo)
    devices = sorted(devices, key=lambda d: str(d.uniqueID()))
    keys = {}
    for number, d in enumerate(devices):
        name = str(d.localizedName())
        if "Desk View" in name:  # the phone's extra cropped camera, not needed
            continue
        if "iPhone" in name:  # temporary, for testing
            keys.setdefault("3", (number, name))
        elif "FaceTime" in name:
            keys.setdefault("1", (number, name))
        else:
            keys.setdefault("2", (number, name))
    return keys


def camera_works(number):
    """try the camera in a separate program first, a stuck camera can crash opencv"""
    test = (
        f"import cv2, time\nc = cv2.VideoCapture({number}, cv2.CAP_AVFOUNDATION)\n"
        "t = time.time()\nwhile c.isOpened() and time.time() - t < 5:\n"
        "    if c.read()[0]: print('ok'); break"
    )
    try:
        out = subprocess.run(
            [sys.executable, "-c", test], capture_output=True, text=True, timeout=10
        )
        return "ok" in out.stdout
    except subprocess.TimeoutExpired:
        return False


def set_exposure(name, locked):
    """stop the camera changing its brightness by itself, so the hat's colour stays the same"""
    mode = 0 if locked else 2  # 0 = locked, 2 = keeps adjusting
    for d in AVFoundation.AVCaptureDevice.devicesWithMediaType_(AVFoundation.AVMediaTypeVideo):
        if str(d.localizedName()) == name and d.isExposureModeSupported_(mode):
            ok, _ = d.lockForConfiguration_(None)
            if ok:
                d.setExposureMode_(mode)
                # keep it at 30 frames a second, in dim light cameras (the phone) slow down
                rates = d.activeFormat().videoSupportedFrameRateRanges()
                if any(r.minFrameRate() <= 30 <= r.maxFrameRate() for r in rates):
                    d.setActiveVideoMinFrameDuration_(CoreMedia.CMTimeMake(1, 30))
                    d.setActiveVideoMaxFrameDuration_(CoreMedia.CMTimeMake(1, 30))
                d.unlockForConfiguration()
                return d.exposureMode() == mode
    return False


class Camera:
    """reads frames on its own thread so we always get the newest one"""

    def __init__(self, number, name):
        self.number, self.name = number, name
        self.frame, self.failed, self.running = None, False, True
        self.fresh = threading.Event()  # set when a new frame arrives
        self.times = []  # when the last second of frames arrived, for the fps readout
        self.started = time.time()
        self.thread = threading.Thread(target=self.read, daemon=True)
        self.thread.start()

    def read(self):
        if not camera_works(self.number):
            self.failed = True
            print(f"{self.name} isn't working, check it's plugged in and not open in another app")
            return
        cap = cv2.VideoCapture(self.number, cv2.CAP_AVFOUNDATION)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # plenty for a 320 x 240 hat finder,
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # bigger frames (the phone's) are slower
        set_exposure(self.name, locked=False)  # let it adjust to the room first
        locked = False
        while self.running:
            ok, frame = cap.read()
            if ok:
                self.frame = frame
                self.fresh.set()
                now = time.time()
                self.times = [t for t in self.times if now - t < 1] + [now]
            if not locked and time.time() - self.started > 3:
                locked = True
                if set_exposure(self.name, locked=True):
                    print(self.name, "brightness locked")
        cap.release()  # only release here, releasing mid-read crashes opencv

    def stop(self):
        self.running = False
        self.thread.join(timeout=3)


# ---------------- hat ----------------
def load_green():
    try:
        return float(json.loads(TUNING.read_text()))
    except (OSError, ValueError, TypeError):
        return GREEN


def greenness(frame):
    """how much greener each spot is than the floor around it, so the camera's colour
    shifts and the dark edges don't matter, only the hat standing out"""
    low = cv2.GaussianBlur(cv2.resize(frame, LOW, interpolation=cv2.INTER_AREA), (5, 5), 0)
    a = cv2.cvtColor(low, cv2.COLOR_BGR2LAB)[:, :, 1]  # green (low) to red (high)
    around = cv2.medianBlur(cv2.resize(a, (80, 60), interpolation=cv2.INTER_AREA), 31)
    return cv2.resize(around, LOW).astype(np.int16) - a


def pick_green(frame, x, y):
    """click the hat: the hat has to be at least half as green as it is right now"""
    px, py = x * LOW[0] // VIEW[0], y * LOW[1] // VIEW[1]
    patch = greenness(frame)[max(py - 6, 0) : py + 7, max(px - 6, 0) : px + 7]
    return max(float(np.median(patch)) / 2, 4)


def find_hat(frame, green):
    """returns the hat mask and the hat's middle (or None)"""
    mask = np.uint8(greenness(frame) > green) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))  # remove specks

    patches, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hat = max(patches, key=cv2.contourArea, default=None)  # biggest green patch = the hat
    if hat is None or cv2.contourArea(hat) < MIN_SIZE:
        return np.zeros_like(mask), None
    # keep only the hat, so other green things never reach wekinator
    mask = cv2.drawContours(np.zeros_like(mask), [hat], -1, 255, -1)
    m = cv2.moments(hat)
    return mask, (m["m10"] / m["m00"], m["m01"] / m["m00"])


# ---------------- tape grid ----------------
class Grid:
    """the 4 tape corners: draws the red grid, turns the hat into x / y from -1 to 1"""

    def __init__(self):
        try:
            self.corners = json.loads(CORNERS.read_text())
        except (OSError, ValueError):
            self.corners = [[0.25, 0.3], [0.75, 0.3], [0.95, 0.95], [0.05, 0.95]]
        self.setting = -1  # -1 = not setting corners right now
        self.clicked = []
        self.mirror = False
        self.update()

    def update(self):
        # put the corners in order by where they are on screen, so x / y and the wekinator view
        # always match what you see, whatever order they were clicked in
        c = np.float32(self.corners)
        on_screen = c * (-1 if self.mirror else 1, 1)
        angle = np.arctan2(*(on_screen - on_screen.mean(0)).T[::-1])
        c = c[np.argsort(angle)]  # top-left, top-right, bottom-right, bottom-left
        self.corners = c.tolist()
        square = np.float32([[-1, 1], [1, 1], [1, -1], [-1, -1]])  # y = 1 at the top
        self.to_xy = cv2.getPerspectiveTransform(np.float32(c * LOW), square)  # camera -> floor
        self.to_view = cv2.getPerspectiveTransform(square, np.float32(c * VIEW))  # floor -> window

    def pt(self, x, y):
        """the window pixel for a spot on the floor, x / y from -1 to 1"""
        p = cv2.perspectiveTransform(np.float32([[[x, y]]]), self.to_view)[0, 0]
        return int(p[0]), int(p[1])

    def draw(self, img):
        # same maths as x / y, so the middle of the middle cell is 0,0
        for t in (-1, -1 / 3, 1 / 3, 1):
            cv2.line(img, self.pt(t, 1), self.pt(t, -1), (0, 0, 255), 2)  # columns
            cv2.line(img, self.pt(-1, t), self.pt(1, t), (0, 0, 255), 2)  # rows

    def set_mirror(self, mirror):
        if mirror != self.mirror:
            self.mirror = mirror
            self.update()

    def click(self, x, y):
        self.clicked.append([x / VIEW[0], y / VIEW[1]])
        if len(self.clicked) == 4:
            self.corners, self.setting = self.clicked, -1
            self.update()
        else:
            self.setting = len(self.clicked)

    def dot(self, spot):
        """the hat as a same size dot at its x / y, squashed to 10 x 10. only x / y count,
        so the tape can be moved or the area made bigger or smaller with K, no retraining"""
        floor = np.zeros((40, 40), np.uint8)
        if spot is not None:
            x, y = spot
            middle = (round((19.5 + 20 * x) * 16), round((19.5 - 20 * y) * 16))  # -1..1 -> 40 x 40
            cv2.circle(floor, middle, DOT * 16, 255, -1, cv2.LINE_AA, shift=4)
        return cv2.resize(floor, WEK, interpolation=cv2.INTER_AREA) / 255

    def xy(self, hat):
        x, y = cv2.perspectiveTransform(np.float32([[hat]]), self.to_xy)[0, 0]
        return np.clip(x, -1, 1), np.clip(y, -1, 1)


# ---------------- arduino ----------------
def open_arduino():
    for p in list_ports.comports():
        if "usbmodem" in p.device or "usbserial" in p.device:
            print("arduino on", p.device)
            return serial.Serial(p.device, BAUD, timeout=0, write_timeout=0)
    print("no arduino, running without it")
    return None


# ---------------- main ----------------
def main():
    cams = find_cameras()
    grid = Grid()
    port = open_arduino()

    # wekinator: send to 6448, it replies on 12000
    wek = SimpleUDPClient("127.0.0.1", 6448)
    opened = time.time()  # opening the port restarts the arduino, it needs ~2 seconds
    out = [0.0, 0.0]  # wekinator's answer

    def on_outputs(_address, *values):
        if len(values) >= 2:
            out[:] = values[:2]

    d = Dispatcher()
    d.map("/wek/outputs", on_outputs)
    try:
        server = ThreadingOSCUDPServer(("127.0.0.1", 12000), d)
    except OSError:
        sys.exit("port 12000 is busy, the tracker is probably already running")
    threading.Thread(target=server.serve_forever, daemon=True).start()

    green = load_green()
    picking = False  # true after C, until the hat is clicked

    def on_click(e, x, y, *_):
        nonlocal green, picking
        if e != cv2.EVENT_LBUTTONDOWN:
            return
        if grid.mirror:  # the picture is mirrored, the click shouldn't be
            x = VIEW[0] - x
        if picking and cam.frame is not None:
            green, picking = pick_green(cam.frame, x, y), False
        elif grid.setting >= 0:
            grid.click(x, y)

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, on_click)

    cam = Camera(*cams.get("1", cams.get("2")))  # start on facetime
    maze = np.zeros(2)  # smoothed answer, goes to the motors
    wek_view = False
    last_send, sent = 0, [0, 0]
    seen = None  # the last time the hat was found: (mask, hat, time)
    spot = None  # the hat's steadied x / y

    while True:
        if cam.failed and time.time() - cam.started > 5:  # broken camera, try again
            cam.stop()
            cam = Camera(cam.number, cam.name)

        # wait for the next frame instead of redoing the same one, leaves the camera thread
        # free to keep up
        cam.fresh.wait(0.05)
        cam.fresh.clear()

        if cam.frame is None:  # wait for the first frame
            img = np.zeros((VIEW[1], VIEW[0], 3), np.uint8)
            status = "not working, retrying" if cam.failed else "starting"
            cv2.putText(img, f"{cam.name}: {status}...", (10, 240), 0, 0.5, (255, 255, 255))
        else:
            # facetime is mirrored like a selfie camera, the webcam and phone aren't
            grid.set_mirror("FaceTime" in cam.name)
            mask, hat = find_hat(cam.frame, green)
            if hat:
                seen = (mask, hat, time.time())
            elif seen and time.time() - seen[2] < HOLD:  # blinked out for a moment, keep the last
                mask, hat = seen[0], seen[1]

            # steady the hat's x / y: still = smoothed, moving = follows straight away
            if hat is None:
                spot = None
            elif spot is None:
                spot = np.array(grid.xy(hat))
            else:
                move = np.array(grid.xy(hat)) - spot
                spot = spot + move * min(1, STEADY + np.hypot(*move) / 0.2)

            # send the hat's spot inside the tape to wekinator, 10 x 10, each cell 0 to 1
            small = grid.dot(spot)
            wek.send_message("/wek/inputs", small.flatten().tolist())

            # ease to wekinator's answer, or back to level if no hat
            maze += ((np.array(out) if hat else 0) - maze) * EASE

            # arduino gets "x,y" like "-35,80", only when it changes, up to 20 times a second
            tilt = np.rint(np.clip(maze / WEK_RANGE, -1, 1) * TILT_MAX).astype(int).tolist()
            ready = time.time() - opened > 2 and time.time() - last_send > 0.05
            if port and ready and tilt != sent:
                port.write(f"{tilt[0]},{tilt[1]}\n".encode())
                last_send, sent = time.time(), tilt

            # draw
            if wek_view:  # already the same way round as the screen
                img = cv2.resize(small * 255, VIEW, interpolation=cv2.INTER_NEAREST)
                img = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_GRAY2BGR)
                for i in (1, 2):
                    x, y = VIEW[0] * i // 3, VIEW[1] * i // 3
                    cv2.line(img, (x, 0), (x, VIEW[1]), (0, 0, 255), 2)
                    cv2.line(img, (0, y), (VIEW[0], y), (0, 0, 255), 2)
            else:
                img = cv2.resize(cam.frame, VIEW)
                grid.draw(img)
                if hat:
                    dot = (int(hat[0] * VIEW[0] / LOW[0]), int(hat[1] * VIEW[1] / LOW[1]))
                    cv2.circle(img, dot, 10, (255, 0, 255), -1)  # pink dot on the hat
                if grid.mirror:
                    img = cv2.flip(img, 1)
            top = "1/2 cam   K corners   C tune to hat   P wek view"
            if grid.setting >= 0:
                top = f"click corner {grid.setting + 1} of 4"
            if picking:
                top = "click the middle of the hat"
            bottom = "no hat"
            if spot is not None:
                x, y = spot
                bottom = f"hat x {x:+.2f}  y {y:+.2f}  size {np.count_nonzero(mask)}"
            if port:
                bottom += f"     arduino {sent[0]},{sent[1]}"
            gaps = np.diff(cam.times + [time.time()]) * 1000
            fps = f"{len(cam.times)} fps, worst gap {gaps.max():.0f} ms"
            cv2.putText(img, fps, (10, 448), 0, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(img, top, (10, 20), 0, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(img, bottom, (10, 468), 0, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(WINDOW, img)

        key = chr(cv2.waitKey(1) & 0xFF)
        if key == "q" or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break
        if key in "123":  # 1 = facetime, 2 = webcam, 3 = phone (temporary, for testing)
            cams = find_cameras()  # look again, in case one was plugged in or connected since
            if key in cams:
                cam.stop()
                cam = Camera(*cams[key])
            else:
                print(f"camera {key} not found")
        if key == "k":
            grid.clicked, grid.setting = [], 0
        if key == "c":
            picking = True
        if key == "p":
            wek_view = not wek_view

    CORNERS.write_text(json.dumps(grid.corners))
    TUNING.write_text(json.dumps(green))
    cam.stop()
    server.shutdown()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
