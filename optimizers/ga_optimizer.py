import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.fitness import evaluate_weights, clip_weights, random_weights
from evaluation.fitness import W_MIN, W_MAX, N_WEIGHTS

POPULATION_SIZE = 20
GENERATIONS     = 50
CROSSOVER_RATE  = 0.8
MUTATION_RATE   = 0.1
MUTATION_SIGMA  = 0.5    
TOURNAMENT_SIZE = 3
ELITE_COUNT     = 1 

class GeneticAlgorithm:
    def __init__(
        self,
        pop_size    = POPULATION_SIZE,
        generations = GENERATIONS,
        crossover_rate = CROSSOVER_RATE,
        mutation_rate  = MUTATION_RATE,
        seed        = 0,
    ):
        self.pop_size    = pop_size
        self.generations = generations
        self.cr          = crossover_rate
        self.mr          = mutation_rate
        self.rng         = np.random.default_rng(seed)
 
        self.best_weights         = None
        self.best_fitness         = np.inf
        self.best_fitness_history = []
        self.all_fitness_history  = []
        
    def _init_population(self) -> np.ndarray:
        return np.array([
            random_weights(self.rng) for _ in range(self.pop_size)
        ])
 
    def _evaluate_population(self, population: np.ndarray) -> np.ndarray:
        return np.array([evaluate_weights(ind) for ind in population])
    
    def _tournament_select(self, population: np.ndarray,
                           fitnesses: np.ndarray) -> np.ndarray:
        candidates = self.rng.choice(len(population), size=TOURNAMENT_SIZE,
                                     replace=False)
        best_idx   = candidates[np.argmin(fitnesses[candidates])]
        return population[best_idx].copy()
 
    def _uniform_crossover(self, parent1: np.ndarray,
                           parent2: np.ndarray) -> tuple:
        if self.rng.random() > self.cr:
            return parent1.copy(), parent2.copy()
 
        mask   = self.rng.random(N_WEIGHTS) < 0.5
        child1 = np.where(mask, parent1, parent2)
        child2 = np.where(mask, parent2, parent1)
        return child1, child2
    
    def _mutate(self, individual: np.ndarray) -> np.ndarray:
        mutant = individual.copy()
        for i in range(N_WEIGHTS):
            if self.rng.random() < self.mr:
                mutant[i] += self.rng.normal(0, MUTATION_SIGMA)
        return clip_weights(mutant)
    
    def run(self, verbose: bool = True) -> dict:
        if verbose:
            print("=" * 60)
            print("  Genetic Algorithm — Weight Vector Optimization")
            print(f"  Population={self.pop_size} | Generations={self.generations}")
            print(f"  CR={self.cr} | MR={self.mr}")
            print("=" * 60)
            
        population = self._init_population()
        fitnesses  = self._evaluate_population(population)
        
        best_idx          = int(np.argmin(fitnesses))
        self.best_fitness = float(fitnesses[best_idx])
        self.best_weights = population[best_idx].copy()
        
        for gen in range(self.generations):
 
            elite_indices = np.argsort(fitnesses)[:ELITE_COUNT]
            elites        = population[elite_indices].copy()
 
            new_population = list(elites)
            
            while len(new_population) < self.pop_size:
                p1 = self._tournament_select(population, fitnesses)
                p2 = self._tournament_select(population, fitnesses)
 
                c1, c2 = self._uniform_crossover(p1, p2)
 
                c1 = self._mutate(c1)
                c2 = self._mutate(c2)
 
                new_population.append(c1)
                if len(new_population) < self.pop_size:
                    new_population.append(c2)
            
            population = np.array(new_population)
            fitnesses  = self._evaluate_population(population)
            
            gen_best_idx = int(np.argmin(fitnesses))
            gen_best_fit = float(fitnesses[gen_best_idx])
 
            if gen_best_fit < self.best_fitness:
                self.best_fitness = gen_best_fit
                self.best_weights = population[gen_best_idx].copy()
                
            self.best_fitness_history.append(self.best_fitness)
            self.all_fitness_history.append(fitnesses.tolist())
 
            if verbose and (gen % 10 == 0 or gen == self.generations - 1):
                print(f"  Gen {gen+1:>3}/{self.generations} | "
                      f"Best fitness: {self.best_fitness:.6f} | "
                      f"Gen best: {gen_best_fit:.6f}")
                
        if verbose:
            print(f"\n  [GA] Optimization complete.")
            print(f"  Best fitness : {self.best_fitness:.6f}")
            print(f"  Best weights : {np.round(self.best_weights, 4).tolist()}")
 
        return {
            "best_weights"        : self.best_weights,
            "best_fitness"        : self.best_fitness,
            "best_fitness_history": self.best_fitness_history,
            "all_fitness_history" : self.all_fitness_history,
            "optimizer"           : "Genetic Algorithm",
        }
