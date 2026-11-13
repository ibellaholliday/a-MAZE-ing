# a-MAZE-ing
This repository is a store of all of our planning, instructions and files in order to create a maze that responds to human movement, using ML and Arduino as well as mechanical elements to actuate the movement. This was undertaken as a group project.

<img width="436" height="488" alt="Screenshot 2026-11-13 at 15 07 51" src="https://github.com/user-attachments/assets/1fa2628a-ddf4-4ba4-882d-170ee9bb08d1" />

A Wekinator model was trained to trace the movement of the centre of a green hat from above, worn by the user. Using 49 positions along a 3 by 3 grid, the model was trained to output continuous x and y values. These values were sent through a Python script for processing in order for the messages to be sent to Arduino IDE. The Arduino code was written in order to have direct control over two stepper pulleys placed below the maze. The pulleys moved independently, so that one controlled forward/backward motion, and the other left/right. Timing belts attached to these pulleys aided actuation of the maze, as well as the ball joint the maze was mounted upon. 
