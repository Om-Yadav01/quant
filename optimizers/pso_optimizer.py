import os
import sys
import numpy as np
 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.fitness import evaluate_weights, clip_weights, random_weights
from evaluation.fitness import W_MIN, W_MAX, N_WEIGHTS

SWARM_SIZE  = 20
ITERATIONS  = 50
W_INERTIA   = 0.7    
C1          = 1.5    
C2          = 1.5    
V_MAX       = (W_MAX - W_MIN) / 2.0   

class PSO:
    def __init__(
        self,
        swarm_size = SWARM_SIZE,
        iterations = ITERATIONS,
        w          = W_INERTIA,
        c1         = C1,
        c2         = C2,
        seed       = 1,
    ):
        self.swarm_size = swarm_size
        self.iterations = iterations
        self.w          = w
        self.c1         = c1
        self.c2         = c2
        self.rng        = np.random.default_rng(seed)
 
        self.best_weights         = None
        self.best_fitness         = np.inf
        self.best_fitness_history = []
        self.all_fitness_history  = []
        
    def _init_swarm(self) -> tuple:
        positions  = np.array([random_weights(self.rng)
                                for _ in range(self.swarm_size)])
        v_range    = (W_MAX - W_MIN) * 0.1
        velocities = self.rng.uniform(-v_range, v_range,
                                      size=(self.swarm_size, N_WEIGHTS))
        return positions, velocities
    
    def run(self, verbose: bool = True) -> dict:
        if verbose:
            print("=" * 60)
            print("  Particle Swarm Optimization — Weight Vector Optimization")
            print(f"  Swarm={self.swarm_size} | Iterations={self.iterations}")
            print(f"  w={self.w} | c1={self.c1} | c2={self.c2}")
            print("=" * 60)
            
        positions, velocities = self._init_swarm()
 
        pbest_positions = positions.copy()
        pbest_fitnesses = np.array([evaluate_weights(p) for p in positions])
 
        gbest_idx      = int(np.argmin(pbest_fitnesses))
        gbest_position = pbest_positions[gbest_idx].copy()
        gbest_fitness  = float(pbest_fitnesses[gbest_idx])
 
        self.best_fitness = gbest_fitness
        self.best_weights = gbest_position.copy()
        
        for itr in range(self.iterations):
 
            for i in range(self.swarm_size):
 
                r1 = self.rng.random(N_WEIGHTS)
                r2 = self.rng.random(N_WEIGHTS)
 
                cognitive = self.c1 * r1 * (pbest_positions[i] - positions[i])
                social    = self.c2 * r2 * (gbest_position       - positions[i])
 
                velocities[i] = (self.w * velocities[i]
                                 + cognitive + social)
 
                velocities[i] = np.clip(velocities[i], -V_MAX, V_MAX)
 
                positions[i] = clip_weights(positions[i] + velocities[i])
 
                new_fitness = evaluate_weights(positions[i])
 
                if new_fitness < pbest_fitnesses[i]:
                    pbest_fitnesses[i]  = new_fitness
                    pbest_positions[i]  = positions[i].copy()
 
                if new_fitness < gbest_fitness:
                    gbest_fitness  = new_fitness
                    gbest_position = positions[i].copy()
                    self.best_fitness = gbest_fitness
                    self.best_weights = gbest_position.copy()
        
            self.best_fitness_history.append(self.best_fitness)
            self.all_fitness_history.append(pbest_fitnesses.tolist())
     
            if verbose and (itr % 10 == 0 or itr == self.iterations - 1):
                print(f"  Iter {itr+1:>3}/{self.iterations} | "
                          f"Best fitness: {self.best_fitness:.6f} | "
                          f"GBest: {gbest_fitness:.6f}")
        
        if verbose:
            print(f"\n  [PSO] Optimization complete.")
            print(f"  Best fitness : {self.best_fitness:.6f}")
            print(f"  Best weights : {np.round(self.best_weights, 4).tolist()}")
 
        return {
            "best_weights"        : self.best_weights,
            "best_fitness"        : self.best_fitness,
            "best_fitness_history": self.best_fitness_history,
            "all_fitness_history" : self.all_fitness_history,
            "optimizer"           : "PSO",
        }
                    
            

