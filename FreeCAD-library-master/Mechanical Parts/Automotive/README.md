# Automotive CAD Components Library

This expanded automotive component library is organized around the significant overlap
between automotive engineering and robotics systems. Many of these components are directly
reusable or adaptable for robotic platforms.

## Directory Structure & Automotive-Robotics Overlap

### Drivetrain
Differential, driveshaft, CV joints, universal joints, axles, and transfer cases.
- **Robotics overlap**: Mobile robots use differentials for skid-steer and Ackermann
  steering. CV and U-joints appear in multi-DOF robotic arms and legged robots.

### Transmission
Gearbox housings, gear sets, synchronizers, shift mechanisms, clutch assemblies,
flywheels, and torque converters.
- **Robotics overlap**: Robotic actuators require gear reduction (planetary, harmonic,
  cycloidal). Clutch mechanisms enable torque-limited compliant joints.

### Engine
Crankshafts, camshafts, pistons, connecting rods, cylinder heads, valve trains,
timing systems, intake/exhaust manifolds, turbochargers, and superchargers.
- **Robotics overlap**: Crank-slider and cam-follower mechanisms are used in robotic
  end-effectors, pick-and-place machines, and reciprocating motion systems.

### Suspension
Shock absorbers, coil/leaf/torsion springs, control arms, ball joints, stabilizer
bars, strut assemblies, and bushings.
- **Robotics overlap**: Legged robots require suspension and compliance. Shock absorbers
  and springs provide passive compliance in walking/running robots. Control arms map
  directly to robotic linkage design.

### Chassis
Frame rails, subframes, cross members, roll cages, and mounting brackets.
- **Robotics overlap**: Structural frames for mobile robots, drone frames, and industrial
  robot bases share identical design principles: rigidity, weight optimization, and
  mounting point integration.

### Steering
Rack and pinion, steering columns, tie rods, pitman/idler arms, steering knuckles,
power steering pumps, and steering wheels.
- **Robotics overlap**: Ackermann steering geometry is used in autonomous ground vehicles.
  Rack-and-pinion converts rotary to linear motion in many robotic systems.

### Braking
Brake discs/rotors, calipers, pads, drums, master cylinders, brake lines, ABS
modules, and parking brakes.
- **Robotics overlap**: Braking and holding mechanisms are essential for robotic joints
  (electromagnetic brakes, mechanical locks). ABS control algorithms parallel robotic
  slip control.

### Wheels
Wheel hubs, bearings, rims, tires, and lug nuts.
- **Robotics overlap**: Wheeled robots directly use hub motors, bearings, and wheel
  assemblies. Omni-wheels and mecanum wheels extend this category.

### Sensors
LIDAR mounts, camera mounts, ultrasonic sensor housings, radar mounts, wheel speed
sensors, IMU mounts, throttle position sensors, oxygen sensors, temperature/pressure
sensor housings, encoder mounts, and proximity sensor brackets.
- **Robotics overlap**: Nearly 1:1 overlap. LIDAR, cameras, IMUs, encoders, ultrasonic
  and proximity sensors are fundamental to both ADAS and robotic perception/navigation.

### Electronics
ECU housings, motor controllers, wiring harness brackets, fuse boxes, relay modules,
CAN bus connectors, OBD ports, voltage regulator mounts, PCB enclosures, and battery
management systems.
- **Robotics overlap**: Robots use identical electronic packaging: motor controllers,
  CAN/EtherCAT buses, BMS for battery packs, and ruggedized PCB enclosures.

### Actuators
Linear actuators, solenoid valves, stepper/servo/DC/BLDC motor mounts, pneumatic and
hydraulic cylinder mounts, electric linear actuators, wiper motors, and window regulators.
- **Robotics overlap**: This is the single largest overlap area. Every actuator type
  used in automotive systems has a direct robotics counterpart. Motor mounts, linear
  actuators, and hydraulic/pneumatic cylinders are core to both fields.

### Cooling
Radiators, water pumps, thermostat housings, coolant reservoirs, fan shrouds, heat
exchangers, oil coolers, and heatsinks.
- **Robotics overlap**: High-performance robotic actuators and electronics require active
  cooling. Heatsinks, fans, and liquid cooling loops are shared solutions.

### Electrical Power
Alternators, starter motors, battery trays/terminals, DC-DC converter housings,
inverter housings, high-voltage connectors, and charging ports.
- **Robotics overlap**: Robot power systems mirror EV architectures: battery packs,
  DC-DC converters, inverters, and charging infrastructure.

### Body
Door/hood/trunk hinges, latch mechanisms, mirror mounts, wiper arms, panel clips,
grommets, and weatherstrip channels.
- **Robotics overlap**: Hinge mechanisms, latches, and panel attachment methods apply
  to robot enclosures, access panels, and protective housings.

### Exhaust
Exhaust pipes, mufflers, catalytic converter shells, flanges, and hangers.
- **Robotics overlap**: Relevant for combustion-powered robots, generators, and thermal
  exhaust routing in high-power industrial systems.

### Fuel System
Fuel rails, injectors, fuel pump mounts, fuel filter housings, and fuel tanks.
- **Robotics overlap**: Combustion-powered drones and large mobile robots use fuel
  systems. Fluid routing principles apply to hydraulic robot systems.

### EV Components
Battery pack housings, cell holders, electric motors, reduction gearboxes, charging
connectors, bus bars, battery cooling plates, and motor controller housings.
- **Robotics overlap**: Nearly identical to mobile robot power systems. Battery pack
  design, BLDC motors with reduction drives, and thermal management are shared.

### Joints and Linkages
Ball joints, tie rod ends, clevis joints, spherical bearings, rod end bearings,
linkage arms, pivot pins, bellcranks, and Heim joints.
- **Robotics overlap**: Direct mapping to robotic joint design. Ball joints for
  spherical wrists, clevis joints for linear actuator attachments, bellcranks for
  force redirection in mechanisms.

### Power Transmission
Belt/timing pulleys, chain sprockets, gear pairs (spur, worm, bevel, planetary),
harmonic drives, belt tensioners, and idler pulleys.
- **Robotics overlap**: Core to robotic actuator design. Harmonic drives and planetary
  gearsets are the most common robotic joint reducers. Belt/chain drives are used in
  3D printers, CNC machines, and robotic arms.

### Seals and Gaskets
O-rings, oil seals, head gaskets, valve stem seals, dust boots, and lip seals.
- **Robotics overlap**: Environmental sealing is critical for outdoor robots, underwater
  ROVs, and any robot operating in harsh conditions. Dust boots protect linear actuators.
