# Digital Twin with Fuzzy Logic for Electric Vehicle Fleet Optimization

## Technical Overview

Discrete-event simulation (DES) framework implementing a digital twin of BYD Seal electric vehicles with embedded fuzzy inference system for adaptive energy management. The system models battery dynamics, velocity-dependent consumption patterns, and charging queue management for route optimization between Mexico City and Pachuca (98 km).

## Architecture

### Fuzzy Inference Engine

**Fuzzification Layer**
- Input variables: State of Charge (SOC) [0,1], Remaining Distance [0,100 km]
- Membership functions: Triangular/trapezoidal for battery states (critical, low, normal, full) and distance (close, far)
- Linguistic variables mapped via piecewise linear functions with bounded gradients

**Rule Base**
```
R1: IF battery_critical AND distance_far THEN aggression = 0.4 (survival mode)
R2: IF battery_low AND distance_far THEN aggression = 0.7 (eco mode)
R3: IF battery_normal OR (battery_low AND distance_close) THEN aggression = 1.0 (sport mode)
```

**Defuzzification**
- Centroid method: weighted average of rule activations
- Output: aggression_factor ∈ [0.4, 1.0] controlling velocity and consumption

### Physical Model

**Energy Consumption**
```python
consumption_factor = (v / 80)²  # Quadratic air resistance
real_consumption = 0.190 * consumption_factor  # kWh/km
```

**Velocity Control**
```python
v(t) = 60 + 50 * aggression_factor(SOC, d_remaining)
v ∈ [60, 110] km/h
```

**Battery Dynamics**
```
SOC(t+Δt) = SOC(t) - (Δd * consumption) / CAPACITY
CAPACITY = 85 kWh (BYD Seal specifications)
```

### Discrete-Event Simulation (SimPy)

**Process Model**
- State update interval: 2 minutes (discrete time steps)
- Event types: drive_step, arrival, charge_request, charge_complete
- Resource contention: M/M/c queue for DC fast chargers (180 kW, c=2)

**Stochastic Components**
- Vehicle arrival: Poisson process with λ ∈ [5,15] minutes inter-arrival time
- Queue discipline: FCFS (First-Come-First-Served)

## Implementation Details

### Decision Loop (Control Cycle)
```
FOR each Δt = 2 min:
  1. Sense: (SOC, distance_remaining)
  2. Fuzzy Inference: aggression ← FIS(SOC, distance)
  3. Actuate: velocity ← f(aggression)
  4. Physics: SOC_new ← SOC - energy_consumed
  5. Check: IF SOC ≤ 0 THEN terminate ELSE continue
```

### Charging Model
- Target SOC: 85% (battery longevity optimization)
- Charging time: t_charge = (E_needed / P_charger) * 60 min
- Queue management: SimPy Resource allocation with blocking semantics

## Technical Specifications

**Vehicle Parameters (BYD Seal)**
- Battery capacity: 85 kWh
- Baseline efficiency: 0.190 kWh/km (ideal conditions)
- DC fast charging: 180 kW peak power
- Operational velocity range: [60, 110] km/h

**Simulation Parameters**
- Route distance: 98 km (CDMX-Pachuca corridor)
- Initial SOC: 90%
- Simulation horizon: 300 minutes
- Fleet size: 3 units with staggered departures

**Fuzzy Set Definitions**
```
μ_critical(SOC) = max(0, min(1, (0.20 - SOC) / 0.10))
μ_low(SOC) = piecewise triangular [0.10, 0.20, 0.40]
μ_normal(SOC) = piecewise triangular [0.30, 0.50, 0.60]
μ_full(SOC) = max(0, min(1, (SOC - 0.60) / 0.40))
```

## Control Strategy

The fuzzy controller implements a survival-oriented energy management strategy:

1. **Critical Region (SOC < 20%, d > 20 km)**: Maximum efficiency mode with velocity reduction to 62 km/h
2. **Eco Region (SOC ∈ [20%, 40%], d > 20 km)**: Balanced mode at ~85 km/h
3. **Performance Region (SOC > 40% OR d < 20 km)**: Optimal travel time at 110 km/h

The quadratic consumption model captures aerodynamic drag dominance at highway speeds, enabling realistic energy prediction.

## Simulation Outputs

- Battery depletion curves per vehicle
- Mode transition logs (survival/eco/sport)
- Charging queue wait times
- Trip completion status with final SOC
- System-level metrics: fleet utilization, charger occupancy

## Applications

- Fleet route planning for electric logistics
- Charging infrastructure dimensioning (M/M/c optimization)
- Battery management system (BMS) validation
- Digital twin calibration for real-world deployments
- Adaptive cruise control parameter tuning

## Implementation Stack

- SimPy 4.x: Discrete-event simulation kernel
- NumPy: Numerical computations for membership functions
- Python 3.8+: Core language with OOP architecture

## Limitations & Future Work

- Deterministic physics model (excludes terrain elevation, weather)
- Simplified fuzzy rule base (3 rules; production systems use 10-20)
- No regenerative braking model
- Homogeneous traffic flow assumption
- Future: Integration with real BMS telemetry, machine learning-based rule optimization, multi-objective optimization (time vs. energy vs. battery degradation)

## Academic Context

Developed for Applied AI in Intelligent Systems, demonstrating fuzzy logic application in cyber-physical systems with discrete-event modeling paradigm. Implements Industry 4.0 concepts of digital twins for predictive fleet management.
