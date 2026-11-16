# a-MAZE-ing
In this group project, we designed and built an interactive maze, where the user moves their body in order to tilt and navigate the maze. We endeavoured to 'embrace the whimsy' with this project, and wanted to create something the used could interact and have fun with. If we did this project again, it would be fun to add more interactive elements, such as moving walls, or 'traps' the user also has to navigate.

<img width="436" height="488" alt="Screenshot 2026-11-13 at 15 07 51" src="https://github.com/user-attachments/assets/1fa2628a-ddf4-4ba4-882d-170ee9bb08d1" />

# How it works

The user stands directly below a camera, wearing a green hat. A [Wekinator model](https://github.com/ibellaholliday/a-MAZE-ing/tree/ccba64782a08cf00f17ce129554bf7258ee6c37d/wekinator) was trained to trace the movement of the centre of the hat, using ~15,000 samples over 49 data points along a 3x3 grid, shown below. The red grid is the grid on the Wekinator camera, and the green crosses are where the green hat was positioned for each recording.

<img width="1476" height="1000" alt="IMG_A641986A7E22-1" src="https://github.com/user-attachments/assets/4e024b9f-6d31-4e08-8103-9acba3f54299" />

We used a continuous Wekinator model to ensure smooth transition between, for example, left and right motion. Through initial training, we established that we would need a large data set to enact smooth movement of the maze. On our initial attempt, we input 5 positions on the grid and recorded them: the origin, and the outermost corners. However, when we ran the model, the outputs were incredibly inaccurate. This is why we eventually settled on using 49 data points, as, while time consuming, it ensured a robust and reliable model. 

These values were sent through a [Python script](https://github.com/ibellaholliday/a-MAZE-ing/blob/0d025133c3f52a3ad0c94deb455a369dbee7362c/code/maze_tracker.py) to Arduino IDE. The Arduino board was powered by a 5V battery pack, and a circuit was built in order to finely control the stepper motors for each axis of movement. 

The [Arduino code](https://github.com/ibellaholliday/a-MAZE-ing/blob/main/code/arduino_code.ino) was written so that the user has direct control over two stepper motors, with two [pulleys](https://github.com/ibellaholliday/a-MAZE-ing/blob/860254a33da3bdf9d20b8359064f35503a75213a/physical_build/pulleyspecs.pdf) attached. The motors moved independently, so that one controlled the x-axis, and the other the y-axis of movement. Timing belts attached to the pulleys allowed smooth actuation of the maze with smaller, smoother movements than servos could provide. The maze platform was mounted on a ball joint, described below in the Physical Components section.

<img width="589" height="296" alt="Screenshot 2026-11-13 at 15 12 22" src="https://github.com/user-attachments/assets/bd6a2aff-348b-4cfc-86ab-a0476e121604" />

# Physical Components


When available, materials were selected from scrap bins on campus in order to reduce material wastage in an effort to increase the sustainability of the project. Any 3D printed parts were constructed from PLA. Any bolts used were M4x8mm to allow for continuity and ease of construction.

<img width="1000" height="1209" alt="IMG_7A5BEDCBCF96-1" src="https://github.com/user-attachments/assets/634105fd-a743-4c74-b08e-3fb475bf1083" />

The maze was laser cut from 3mm MDF found in the scrap bin, and then finished with silver reflective vinyl in an effort to obscure the maze path. 

The ensemble on which the maze sat was 3D printed; the ball joint was kindly shared on [Printables](https://www.printables.com/model/1496805-adjustable-feet-strong) for the public to use - we initially intended to use this only for our initial prototype, but it moved so well we stuck with it. 

The [Housing](https://github.com/ibellaholliday/a-MAZE-ing/blob/2ee807074f4235dbde1e6431208263f8292d3731/physical_build/maze_stand/Final%20Motor%20Housing.stl) for the motor was designed on Fusion360 and also 3D printed, and was designed to fit in-between two parts of the ball joint to make room for our belt ensemble. 

The [Stand](https://github.com/ibellaholliday/a-MAZE-ing/blob/2ee807074f4235dbde1e6431208263f8292d3731/physical_build/maze_stand/maze_stand.stl) was constructed of another part designed in Rhino and 3D printed, and held 3 rods of 10mm acrylic. [Feet](https://github.com/ibellaholliday/a-MAZE-ing/blob/0d025133c3f52a3ad0c94deb455a369dbee7362c/physical_build/maze_stand/feet%20threaded.stl) were attached to the bottom of the rods, also 3D printed, to increase stability. 

https://github.com/user-attachments/assets/2d28737a-3c62-4bdf-9d43-1f02ec241620

On each edge of the maze, [Clamps](https://github.com/ibellaholliday/a-MAZE-ing/blob/0d025133c3f52a3ad0c94deb455a369dbee7362c/physical_build/maze_stand/gt2%20clamp.stl) were 3D printed and mounted using two M4 bolts in order to allow for straightforward adjustment of belt tension. 


