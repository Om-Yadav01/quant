import os
import sys
import numpy as np
 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.fitness import evaluate_weights, clip_weights, random_weights
from evaluation.fitness import W_MIN, W_MAX, N_WEIGHTS

POPULATION_SIZE = 20
ITERATIONS      = 50
F               = 0.5   
CR              = 0.9   

class DifferentialEvolution:
    def __init__(
        self,
        pop_size   = POPULATION_SIZE,
        iterations = ITERATIONS,
        F          = F,
        CR         = CR,
        seed       = 2,
    ):
        self.pop_size   = pop_size
        self.iterations = iterations
        self.F          = F
        self.CR         = CR
        self.rng        = np.random.default_rng(seed)
 
        self.best_weights         = None
        self.best_fitness         = np.inf
        self.best_fitness_history = []
        self.all_fitness_history  = []
        
    def _init_population(self) -> np.ndarray:
        return np.array([random_weights(self.rng)
                         for _ in range(self.pop_size)])
    
    def _mutate(self, population: np.ndarray, target_idx: int) -> np.ndarray:
        candidates = [i for i in range(self.pop_size) if i != target_idx]
        a, b, c    = self.rng.choice(candidates, size=3, replace=False)
        mutant     = population[a] + self.F * (population[b] - population[c])
        return clip_weights(mutant)
    
    def _crossover(self, target: np.ndarray, mutant: np.ndarray) -> np.ndarray:
        j_rand = int(self.rng.integers(0, N_WEIGHTS))
        trial  = target.copy()
        for j in range(N_WEIGHTS):
            if self.rng.random() < self.CR or j == j_rand:
                trial[j] = mutant[j]
        return trial
    
    def run(self, verbose: bool = True) -> dict:
        if verbose:
            print("=" * 60)
            print("  Differential Evolution — Weight Vector Optimization")
            print(f"  Population={self.pop_size} | Iterations={self.iterations}")
            print(f"  F={self.F} | CR={self.CR}")
            print("=" * 60)
 
        population = self._init_population()
        fitnesses  = np.array([evaluate_weights(ind) for ind in population])
 
        best_idx          = int(np.argmin(fitnesses))
        self.best_fitness = float(fitnesses[best_idx])
        self.best_weights = population[best_idx].copy()
        
        for itr in range(self.iterations):
 
            for i in range(self.pop_size):
 
                mutant = self._mutate(population, i)
 
                trial = self._crossover(population[i], mutant)
 
                trial_fitness = evaluate_weights(trial)
 
                if trial_fitness <= fitnesses[i]:
                    population[i] = trial
                    fitnesses[i]  = trial_fitness
 
                    if trial_fitness < self.best_fitness:
                        self.best_fitness = trial_fitness
                        self.best_weights = trial.copy()
 
            self.best_fitness_history.append(self.best_fitness)
            self.all_fitness_history.append(fitnesses.tolist())
 
            if verbose and (itr % 10 == 0 or itr == self.iterations - 1):
                print(f"  Iter {itr+1:>3}/{self.iterations} | "
                      f"Best fitness: {self.best_fitness:.6f} | "
                      f"Pop mean: {fitnesses.mean():.6f}")
                
        if verbose:
            print(f"\n  [DE] Optimization complete.")
            print(f"  Best fitness : {self.best_fitness:.6f}")
            print(f"  Best weights : {np.round(self.best_weights, 4).tolist()}")
 
        return {
            "best_weights"        : self.best_weights,
            "best_fitness"        : self.best_fitness,
            "best_fitness_history": self.best_fitness_history,
            "all_fitness_history" : self.all_fitness_history,
            "optimizer"           : "Differential Evolution",
        }
