# a-MAZE-ing
This repository is a store of all of our planning, instructions and files in order to create a maze that responds to human movement, using ML and Arduino as well as mechanical elements to actuate the movement. This was undertaken as a group project.

<img width="436" height="488" alt="Screenshot 2026-11-13 at 15 07 51" src="https://github.com/user-attachments/assets/1fa2628a-ddf4-4ba4-882d-170ee9bb08d1" />

# How it works

A [Wekinator model](https://github.com/ibellaholliday/a-MAZE-ing/tree/ccba64782a08cf00f17ce129554bf7258ee6c37d/wekinator) was trained to trace the movement of the centre of a green hat from above, worn by the user. Using ~15,000 samples over 49 data points along a 3x3 grid, the model was trained to output continuous x and y values. These values were sent through a Python script to Arduino IDE. 

The [Arduino code](https://github.com/ibellaholliday/a-MAZE-ing/blob/main/code/arduino_code.ino) was written so that the user has direct control over two stepper motors, with two pulleys attached. The motors moved independently, so that one controlled the x-axis, and the other the y-axis of movement. Timing belts attached to the pulleys allowed actuation of the maze. The maze platform was mounted on a ball joint. 

<img width="589" height="296" alt="Screenshot 2026-11-13 at 15 12 22" src="https://github.com/user-attachments/assets/bd6a2aff-348b-4cfc-86ab-a0476e121604" />

# Physical Components

When available, materials were selected from scrap bins on campus in order to reduce material wastage in an effort to increase the sustainability of the project. Any 3D printed parts were constructed from PLA. 

The maze was laser cut from 3mm MDF found in the scrap bin, and then finished with silver reflective vinyl in an effort to obscure the maze path. 

The ensemble on which the maze sat was 3D printed; the ball joint was kindly shared on [Printables](https://www.printables.com/model/1496805-adjustable-feet-strong) for the public to use - we initially intended to use this only for our initial prototype, but it moved so well we stuck with it. 

The [Housing](https://github.com/ibellaholliday/a-MAZE-ing/blob/2ee807074f4235dbde1e6431208263f8292d3731/physical_build/maze_stand/Final%20Motor%20Housing.stl) for the motor was designed on Fusion360 and also 3D printed, and was designed to fit in-between two parts of the ball joint to make room for our belt ensemble. 


The [Stand](https://github.com/ibellaholliday/a-MAZE-ing/blob/2ee807074f4235dbde1e6431208263f8292d3731/physical_build/maze_stand/maze_stand.stl) was constructed of another part designed in Rhino and 3D printed, and held 3 rods of 10mm acrylic. 



https://github.com/user-attachments/assets/2d28737a-3c62-4bdf-9d43-1f02ec241620



