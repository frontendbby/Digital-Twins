import simpy
import random
import numpy as np

# Configuración del modelo BYD - Modelo Seal para Digital Twin (DT) con Fuzzy Logic

BATTERY_CAPACITY_KWH = 85.0  # Capacidad real BYD Seal
BASE_CONSUMPTION = 0.190     # kWh/km en condiciones ideales
CHARGING_SPEED_DC = 180      # kW
INITIAL_SOC = 0.90           # Porcentaje de carga inicial (90%)
TRIP_DISTANCE_KM = 98.0      # Distancia CDMX - Pachuca
SIMULATION_STEP = 2          # El auto "piensa" cada 2 minutos

# Implementación de fuzzy logic manual para Machine Learning Light:

class FuzzySurvivalBrain:
    """
    Sistema de inferencia difusa manual.
    Determina qué tan agresivo debe conducir el auto (0.4 a 1.0)
    basado en la batería restante y la distancia faltante.
    """
    def calculate_aggression(self, soc, distance_left):
# Fuzzy Logic Steps: de números a conceptos determinados por reglas 
        
        # Concepto: Batería (0 a 1.0)
        bat_critical = max(0, min(1, (0.20 - soc) / 0.10)) # 100% verdad si < 10%
        bat_low      = max(0, min(1, (soc - 0.10) / 0.10)) if soc < 0.20 else max(0, min(1, (0.40 - soc) / 0.20))
        bat_normal   = max(0, min(1, (soc - 0.30) / 0.20)) # Empieza a ser verdad desde 30%
        bat_full     = max(0, min(1, (soc - 0.60) / 0.40)) # Empieza a ser verdad desde 60%
        # Concepto: Distancia (0 a 100 km)
        dist_close = max(0, min(1, (20 - distance_left) / 20))
        dist_far   = max(0, min(1, (distance_left - 20) / 60))

        # 2. INFERENCIA (Reglas del experto):
        # A partir de estas reglas, BYD Seal será capaz de modificar de manera automatizada el rendimiento operativo de la unidad.
        # El objetivo de estas adecuaciones es mejorar la supervivencia del vehículo eléctrico en ruta, evitando quedarse sin batería.
        
        # Regla 1: Si Batería Crítica y Lejos -> Se define un modo de supervivencia extrema:
        
        rule_survival = min(bat_critical, dist_far)
        
        # Regla 2: Si Batería Baja y Lejos -> Modo ecológico = ECO - Activado
        
        rule_eco = min(bat_low, dist_far)

        # Regla 3: Si Batería Normal O (Baja y Cerca) -> Modo normal/sport activado
        rule_sport = max(bat_normal, min(bat_low, dist_close))

        # Centroide simplificado: ponderación de salidas
        
        # Definición de valores de salida por regla:
        # Valores de salida: Survival=0.4, Eco=0.7, Sport=1.0
        numerator = (rule_survival * 0.4) + (rule_eco * 0.7) + (rule_sport * 1.0)
        denominator = rule_survival + rule_eco + rule_sport
        
        if denominator == 0: return 1.0 # Por defecto Sport
        return numerator / denominator

# Digital Twin: clase del vehículo
# Simulación con lógica difusa para decisiones de conducción:
class DigitalTwinLogistics:
    def __init__(self, env, num_chargers):
        self.env = env
        self.chargers = simpy.Resource(env, num_chargers)
        self.brain = FuzzySurvivalBrain() # Instanciamos el cerebro
        
    def transport_unit(self, unit_id):
        
        # Estado inicial del vehículo
        soc = INITIAL_SOC 
        current_battery_kwh = BATTERY_CAPACITY_KWH * soc
        distance_traveled = 0
        
        print(f"--- [{self.env.now:.1f}min] 🚗 {unit_id} Iniciando (Porcentaje de batería: {soc*100:.1f}%) ---")
        
        # Bucle de conducción hasta llegar a destino - conducción dinámica paso a paso
        while distance_traveled < TRIP_DISTANCE_KM:
            
            # 1. Obtener datos del entorno
            dist_left = TRIP_DISTANCE_KM - distance_traveled
            
            # 2. Consultar al Cerebro Difuso
            aggression_factor = self.brain.calculate_aggression(soc, dist_left)
            
            # 3. Aplicar física del vehículo basada en la decisión
            # Si aggression es bajo (0.5), velocidad baja (60km/h). 
            # Si es 1.0, velocidad alta (110km/h)
            speed_kmh = 60 + (50 * aggression_factor) 
            
            # El consumo no es lineal: crece al cuadrado de la velocidad (Resistencia del aire)
            # Factor 1.0 = Consumo Base. Factor 1.2 = Consumo alto.
            consumption_factor = (speed_kmh / 80) ** 2 
            real_consumption = BASE_CONSUMPTION * consumption_factor
            
            # 4. Avanzar el tiempo (Simulation Step)
            step_time_hours = SIMULATION_STEP / 60
            distance_step = speed_kmh * step_time_hours
            
            # Ajustar si llegamos a destino en este paso
            if distance_traveled + distance_step > TRIP_DISTANCE_KM:
                distance_step = TRIP_DISTANCE_KM - distance_traveled
            
            energy_used = distance_step * real_consumption
            
            # 5. Actualizar estado
            distance_traveled += distance_step
            current_battery_kwh -= energy_used
            soc = current_battery_kwh / BATTERY_CAPACITY_KWH
            
            # Establecimiento de logging inteligente (Solo si cambia el modo de conducción drásticamente)
            mode_str = "SPORT" if aggression_factor > 0.9 else ("Modo Ecológico (EECO)" if aggression_factor > 0.6 else "⚠️ Modo supervivencia activado: rendimiento aceptable ⚠️")
            if self.env.now % 20 == 0: # Imprimir cada 20 min para no saturar
                print(f"   [{self.env.now:5.1f}m] {unit_id} | Bat: {soc*100:4.1f}% | Vel: {speed_kmh:3.0f} km/h | Modo: {mode_str}")

            # 6. Fallo catastrófico (Battery Dead)
            if current_battery_kwh <= 0:
                print(f" [{self.env.now:.1f}min] {unit_id} Sistema sin batería en el km {distance_traveled:.1f}!")
                return # Termina el proceso
            
            yield self.env.timeout(SIMULATION_STEP)

        # LLEGADA Y CARGA
        print(f"[{self.env.now:.1f}min] {unit_id} Llegada al destino: Pachuca. Porcentaje de batería final: {soc*100:.1f}%")
        
        # Lógica de Carga (Cola)
        
        with self.chargers.request() as request:
            yield request
            energy_needed = (BATTERY_CAPACITY_KWH * 0.85) - current_battery_kwh # Establecer sistemas de carga al 85%
            charge_time = (energy_needed / CHARGING_SPEED_DC) * 60
            
            print(f"⚡ [{self.env.now:.1f}min] {unit_id} Cargando {energy_needed:.1f} kWh ({charge_time:.1f} min)...")
            yield self.env.timeout(charge_time)
            print(f"[{self.env.now:.1f}min] {unit_id} Carga Completa. Desconectando.")

env = simpy.Environment()
system = DigitalTwinLogistics(env, num_chargers=2)

# Lanzamos vehículos con intervalos para ver las colas:

def traffic_generator(env):
    for i in range(3):
        env.process(system.transport_unit(f"Seal-{i}"))
        yield env.timeout(random.randint(5, 15)) # Salen con diferencia de tiempo - aplicado aleatorio.

env.process(traffic_generator(env))
env.run(until=300) # Ejecutamos la simulación por 300 minutos