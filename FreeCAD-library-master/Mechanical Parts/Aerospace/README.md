# Aerospace CAD Components Library

This aerospace component library is organized around the extensive overlap between
aeronautics/aerospace engineering and robotics systems. From UAV drones to spacecraft
robotic arms, aerospace and robotics share actuators, sensors, control systems,
structural design principles, and power management architectures.

## Directory Structure & Aerospace-Robotics Overlap

### Airframe
Fuselage frames, bulkheads, longerons, stringers, skin panels, ribs, spars, wing
boxes, monocoque shells, firewalls, nacelles, fairings, and radomes.
- **Robotics overlap**: Lightweight structural design (carbon fiber monocoque, sandwich
  panels) is shared between UAV airframes and mobile robot chassis. Ribs, spars, and
  shell structures inform the design of robotic exoskeletons and load-bearing frames.

### Structural Joints
Riveted joints, Hi-Lok fasteners, clevis/lug fittings, splice plates, gusset plates,
shear pins, piano hinges, quick-release pins, and Dzus fasteners.
- **Robotics overlap**: Quick-release mechanisms enable modular robot tool changes.
  Clevis fittings attach linear actuators. Piano hinges are used on robot access panels.
  Lightweight fastening strategies from aerospace directly apply to weight-sensitive robots.

### Propulsion
Turbine/compressor/fan blades, turbine discs, combustion chambers, nozzles, inlet
ducts, propeller hubs/blades, spinners, engine mounts, thrust bearings, rocket
nozzles/casings, igniters, electric ducted fans, BLDC outrunner motors, and motor
mount plates.
- **Robotics overlap**: BLDC outrunner motors are the standard drone actuator. Electric
  ducted fans power VTOL robots. Propeller design applies to underwater ROV thrusters.
  Thrust vectoring concepts map to robotic orientation control.

### Fuel and Fluid Systems
Fuel tanks, pumps, valves, filters, line fittings, pressure regulators,
quick-disconnect couplings, accumulators, reservoirs, and check valves.
- **Robotics overlap**: Hydraulic robots use identical fluid system components.
  Quick-disconnect couplings enable modular hydraulic tool attachments. Pressure
  regulators and accumulators are shared with pneumatic robotic grippers.

### Flight Control Surfaces
Ailerons, elevators, rudders, flaps, slats, spoilers, trim tabs, canards, elevons,
and ruddervators.
- **Robotics overlap**: Aerial robots (fixed-wing drones) use all conventional control
  surfaces. Morphing wing research bridges aerospace and soft robotics. Control surface
  hinge design informs robotic fin actuators for underwater vehicles.

### Actuation
Servo actuators, linear electromechanical actuators, rotary actuators, hydraulic servo
cylinders, fly-by-wire actuators, torque tubes, push-pull rods, bell cranks, control
horns, gimbal mounts, thrust vector control, reaction control thrusters, CMG housings,
and reaction wheel assemblies.
- **Robotics overlap**: One of the deepest overlap areas. Servo actuators are universal
  across both fields. Gimbal mounts are used in camera-carrying drones and satellite
  pointing. Reaction wheels and CMGs stabilize both spacecraft and balancing robots.
  Electromechanical actuators (EMAs) are replacing hydraulics in both aircraft and robots.

### Linkages and Mechanisms
Pushrods, cable pulleys, turnbuckles, swashplates, cyclic-collective mixers, four-bar
linkages, over-center mechanisms, scissor links, and toggle clamps.
- **Robotics overlap**: Four-bar linkages are fundamental to robotic arm design.
  Swashplate mechanisms appear in multi-rotor tilt mechanisms. Scissor links are used
  in robotic lift platforms. Over-center mechanisms provide bistable locking in robotic
  grippers.

### Avionics
Flight computer housings, avionics bay racks, instrument panels, autopilot module
mounts, GPS antenna mounts, transponder housings, data recorder housings, ruggedized
connectors, EMI shield enclosures, and wire harness clamps.
- **Robotics overlap**: Ruggedized electronics packaging is shared. Flight computers
  are functionally identical to robot control computers. EMI shielding, vibration-
  isolated mounts, and mil-spec connectors apply to field robots operating in harsh
  environments.

### Sensors
Pitot tubes, static ports, angle-of-attack vanes, accelerometer/gyroscope mounts,
IMU enclosures, magnetometer housings, barometric altimeter housings, airspeed sensors,
temperature probes, strain gauge mounts, LIDAR pods, star trackers, sun/horizon
sensors, radar antenna mounts, and infrared sensor housings.
- **Robotics overlap**: IMUs, accelerometers, gyroscopes, magnetometers, LIDAR, and
  infrared sensors are core to both aerospace and robotic navigation. Star trackers
  and sun sensors are used by space robots. Strain gauges enable force-torque sensing
  in robotic joints, identical to structural health monitoring in aircraft.

### Communication
Antenna mounts, antenna dishes, waveguides, RF connector panels, telemetry module
housings, and phased array panels.
- **Robotics overlap**: Telemetry links for UAVs and remote robots share the same
  hardware. Phased array antennas enable autonomous drone swarm communication.
  Antenna mounts for GPS/radio are common to all mobile robots.

### Landing Gear
Strut assemblies, oleo struts, wheel assemblies, brake assemblies, retraction
mechanisms, drag/side braces, shimmy dampers, skid plates, tail wheels, and float
struts.
- **Robotics overlap**: Retraction mechanisms use the same linkage kinematics as
  robotic leg folding. Oleo struts are shock absorbers applicable to legged robots.
  Skid plates protect ground robots. Landing gear braces are four-bar linkages used
  throughout robotics.

### Hydraulics
Hydraulic pumps, cylinders, manifolds, servo valves, relief valves, reservoirs,
filters, accumulators, AN fittings, and flexible hose assemblies.
- **Robotics overlap**: Hydraulic robots (Boston Dynamics Atlas, heavy industrial
  manipulators) use identical components. Servo valves provide proportional control
  in both aircraft flight controls and robotic joint actuators.

### Pneumatics
Bleed air valves, pneumatic actuators, pressure vessels, flow control valves,
pneumatic manifolds, and air compressor mounts.
- **Robotics overlap**: Pneumatic grippers, soft pneumatic actuators, and air-muscle
  artificial muscles are major robotics research areas. Pressure vessels store energy
  for pneumatic robotic systems.

### Thermal Management
Heat shields, thermal blanket frames, heat pipes, cold plates, radiator panels,
thermal interface mounts, louver assemblies, and ablative shields.
- **Robotics overlap**: High-performance robot actuators and processors need thermal
  management. Heat pipes and cold plates cool robotic electronics. Space robots
  require the same thermal design as spacecraft. Thermal louvers are autonomous
  thermal actuators.

### Environmental Control
Cabin pressure valves, air cycle machine housings, HEPA filter housings, oxygen
system regulators, environmental seals, and pressurization controller mounts.
- **Robotics overlap**: Sealed robot housings for underwater ROVs and hazardous
  environment robots use similar pressure management. Cleanroom robots need HEPA-
  filtered enclosures. Environmental sealing is critical for outdoor/underwater robots.

### Power Systems
Generator mounts, APU housings, battery packs, solar panel frames, solar cell array
mounts, power distribution units, voltage regulator mounts, bus bars, DC-DC converter
housings, fuel cell stack housings, and RTG housings.
- **Robotics overlap**: Nearly 1:1 overlap. Solar-powered robots and drones share
  solar array design. Battery packs, power distribution, and voltage regulation are
  identical. Fuel cells power long-endurance drones and field robots. RTGs power
  planetary rovers (Mars Curiosity/Perseverance).

### Spacecraft
Satellite bus frames, payload adapter rings, separation mechanisms, docking/berthing
ports, solar array drives, deployment hinges, antenna deployment booms, momentum
wheels, thruster brackets, propellant tanks, thermal louvers, CubeSat frames, robotic
arm joints, end effectors, and grapple fixtures.
- **Robotics overlap**: Space robotics IS aerospace. The Canadarm, Dextre, and ESA's
  ERA are spacecraft robots. Deployment mechanisms (hinges, booms) are robotic
  mechanisms. CubeSat frames are a standardized form factor applicable to modular
  robot design. Docking mechanisms parallel robot tool-change systems.

### UAV and Drone
Quadcopter frames, motor/ESC/flight controller mounts, battery trays, camera gimbals,
gimbal motors, landing skids, propeller guards, GPS/FPV camera/antenna mounts, payload
bays, fixed-wing spars, servo linkages, and VTOL tilt mechanisms.
- **Robotics overlap**: UAVs ARE flying robots. Every component is shared. Gimbal
  stabilization applies to any robot-mounted camera. VTOL tilt mechanisms are robotic
  actuators. Payload bays apply to delivery drones and inspection robots.

### Rotorcraft
Main/tail rotor hubs, swashplate assemblies, pitch links, blade grips, mast
assemblies, transmission housings, collective levers, anti-torque pedals, and
vibration dampers.
- **Robotics overlap**: Helicopter rotor mechanics inform coaxial drone design.
  Swashplates enable variable-pitch multirotors. Vibration damping is critical for
  both rotorcraft and robot sensor platforms. Transmission housings are shared with
  robotic gearboxes.

### Seals and Bearings
Labyrinth seals, carbon face seals, ceramic bearings, magnetic bearing mounts,
angular contact bearings, spherical bearings, self-aligning bearings, and rod end
bearings.
- **Robotics overlap**: High-speed bearings for robotic spindles. Spherical and rod
  end bearings enable multi-axis robotic joints. Magnetic bearings provide frictionless
  rotation for precision robots. Ceramic bearings handle extreme environments in both
  space and industrial robots.

### Gears and Drives
Epicyclic gear trains, bevel gear sets, harmonic drives, worm gear reducers, spline
couplings, freewheel clutches, overrunning clutches, and flex couplings.
- **Robotics overlap**: Harmonic drives are THE standard robotic joint reducer.
  Epicyclic (planetary) gear trains are used in both helicopter transmissions and
  robotic actuators. Spline couplings transmit torque in both turbine shafts and
  robotic tool interfaces. Flex couplings handle misalignment in both fields.
