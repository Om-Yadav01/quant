import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.fitness import evaluate_weights, clip_weights, W_MIN, W_MAX

POP_SIZE        = 20
ITERATIONS      = 50
INJECT_INTERVAL = 10   

DE_INDICES  = [0, 4]   # w1 (speed),   w5 (capacity)
PSO_INDICES = [1, 2]   # w2 (queue),   w3 (latency)
GA_INDICES  = [3, 5]   # w4 (failure), w6 (cost)

DIM_SUB = 2

# DE parameters
DE_F  = 0.5
DE_CR = 0.9
 
# PSO parameters
PSO_W  = 0.7
PSO_C1 = 1.5
PSO_C2 = 1.5
V_MAX  = (W_MAX - W_MIN) / 2.0
 
# GA parameters
GA_CR    = 0.8
GA_MR    = 0.15   # standard mutation rate for 2D sub-space
GA_SIGMA = 0.5   # standard perturbation — GA contributes equally to search
GA_TOUR  = 3

class HybridCCEOptimizer:
    def __init__(
        self,
        pop_size        = POP_SIZE,
        iterations      = ITERATIONS,
        inject_interval = INJECT_INTERVAL,
        seed            = 3,
    ):
        self.pop_size        = pop_size
        self.iterations      = iterations
        self.inject_interval = inject_interval
        self.rng             = np.random.default_rng(seed)
 
        self.best_weights         = None
        self.best_fitness         = np.inf
        self.best_fitness_history = []
        self.subgroup_history     = {"DE": [], "PSO": [], "GA": []}
        
    def _rand_sub(self, size) -> np.ndarray:
        return self.rng.uniform(W_MIN, W_MAX, size=(size, DIM_SUB))
 
    def _init_de(self):
        pop      = self._rand_sub(self.pop_size)
        fits     = np.full(self.pop_size, np.inf)
        return pop, fits
 
    def _init_pso(self):
        pos     = self._rand_sub(self.pop_size)
        v_range = (W_MAX - W_MIN) * 0.1
        vel     = self.rng.uniform(-v_range, v_range,
                                   size=(self.pop_size, DIM_SUB))
        pb_pos  = pos.copy()
        pb_fit  = np.full(self.pop_size, np.inf)
        return pos, vel, pb_pos, pb_fit
 
    def _init_ga(self):
        pop  = self._rand_sub(self.pop_size)
        fits = np.full(self.pop_size, np.inf)
        return pop, fits
    
    def _assemble(self, de_sub, pso_sub, ga_sub) -> np.ndarray:
        w = np.zeros(6)
        w[DE_INDICES[0]],  w[DE_INDICES[1]]  = de_sub[0],  de_sub[1]
        w[PSO_INDICES[0]], w[PSO_INDICES[1]] = pso_sub[0], pso_sub[1]
        w[GA_INDICES[0]],  w[GA_INDICES[1]]  = ga_sub[0],  ga_sub[1]
        return w
 
    def _decompose(self, full_w: np.ndarray):
        de_sub  = np.array([full_w[DE_INDICES[0]],  full_w[DE_INDICES[1]]])
        pso_sub = np.array([full_w[PSO_INDICES[0]], full_w[PSO_INDICES[1]]])
        ga_sub  = np.array([full_w[GA_INDICES[0]],  full_w[GA_INDICES[1]]])
        return de_sub, pso_sub, ga_sub
    
    def _de_mutate(self, pop: np.ndarray, idx: int) -> np.ndarray:
        candidates = [i for i in range(self.pop_size) if i != idx]
        a, b, c    = self.rng.choice(candidates, size=3, replace=False)
        mutant     = pop[a] + DE_F * (pop[b] - pop[c])
        return np.clip(mutant, W_MIN, W_MAX)
 
    def _de_crossover(self, target: np.ndarray, mutant: np.ndarray) -> np.ndarray:
        j_rand = int(self.rng.integers(0, DIM_SUB))
        trial  = target.copy()
        for j in range(DIM_SUB):
            if self.rng.random() < DE_CR or j == j_rand:
                trial[j] = mutant[j]
        return trial
    
    def _pso_update(self, pos, vel, pb_pos, gb_pos, i):
        r1  = self.rng.random(DIM_SUB)
        r2  = self.rng.random(DIM_SUB)
        vel[i] = (PSO_W * vel[i]
                  + PSO_C1 * r1 * (pb_pos[i] - pos[i])
                  + PSO_C2 * r2 * (gb_pos    - pos[i]))
        vel[i] = np.clip(vel[i], -V_MAX, V_MAX)
        pos[i] = np.clip(pos[i] + vel[i], W_MIN, W_MAX)
        return pos, vel
    
    def _ga_tournament(self, pop: np.ndarray, fits: np.ndarray) -> np.ndarray:
        idx  = self.rng.choice(self.pop_size, size=GA_TOUR, replace=False)
        best = idx[np.argmin(fits[idx])]
        return pop[best].copy()
 
    def _ga_crossover(self, p1: np.ndarray, p2: np.ndarray) -> tuple:
        if self.rng.random() > GA_CR:
            return p1.copy(), p2.copy()
        mask = self.rng.random(DIM_SUB) < 0.5
        c1   = np.where(mask, p1, p2)
        c2   = np.where(mask, p2, p1)
        return c1, c2
 
    def _ga_mutate(self, ind: np.ndarray) -> np.ndarray:
        mutant = ind.copy()
        for j in range(DIM_SUB):
            if self.rng.random() < GA_MR:
                mutant[j] += self.rng.normal(0, GA_SIGMA)
        return np.clip(mutant, W_MIN, W_MAX)
    
    def _inject_global_best(
        self,
        best_w,
        de_pop, de_fits,
        pso_pos, pso_pb_pos, pso_pb_fit,
        ga_pop, ga_fits,
    ):
        de_sub, pso_sub, ga_sub = self._decompose(best_w)
 
        worst_de= int(np.argmax(de_fits))
        de_pop[worst_de]= de_sub
        de_fits[worst_de]= np.inf
 
        worst_pso= int(np.argmax(pso_pb_fit))
        pso_pos[worst_pso]= pso_sub
        pso_pb_pos[worst_pso] = pso_sub
        pso_pb_fit[worst_pso] = np.inf
 
        worst_ga= int(np.argmax(ga_fits))
        ga_pop[worst_ga]= ga_sub
        ga_fits[worst_ga]= np.inf
 
        return de_pop, de_fits, pso_pos, pso_pb_pos, pso_pb_fit, ga_pop, ga_fits
    
    def _select_representative(self, pop, fits):
        best_idx = int(np.argmin(np.where(np.isinf(fits), 1e9, fits)))
        return pop[best_idx].copy()
    
    def run(self, verbose: bool = True) -> dict:
        """
        Run the Cooperative Co-Evolution Hybrid optimizer.
 
        Returns
        -------
        dict with keys:
            best_weights, best_fitness, best_fitness_history,
            subgroup_history, optimizer
        """
        if verbose:
            print("=" * 60)
            print("  Cooperative Co-Evolution Hybrid (CCE)")
            print(f"  Groups: DE(w1,w5) | PSO(w2,w3) | GA(w4,w6)")
            print(f"  Pop={self.pop_size} | Iterations={self.iterations} | "
                  f"Inject every {self.inject_interval} iters")
            print("=" * 60)
 
        # ── Initialise all three sub-optimizers ───────────────────────────────
        de_pop,  de_fits                         = self._init_de()
        pso_pos, pso_vel, pso_pb_pos, pso_pb_fit = self._init_pso()
        ga_pop,  ga_fits                         = self._init_ga()
 
        # Global best tracking
        best_w   = np.zeros(6)
        best_fit = np.inf
 
        # PSO global best sub-vector
        pso_gb     = pso_pos[0].copy()
        pso_gb_fit = np.inf
 
        for itr in range(self.iterations):
 
            # ── Step 1: Set global context vector ────────────────────────────
            # Use the single global best weight vector as context for all
            # sub-optimizers. This ensures consistent fitness evaluation —
            # all candidates are assessed against the same reference point
            # rather than inconsistent per-subgroup representatives.
            if best_fit == np.inf:
                # First iteration fallback: use first individual from each group
                de_rep, pso_rep, ga_rep = de_pop[0], pso_pos[0], ga_pop[0]
            else:
                de_rep, pso_rep, ga_rep = self._decompose(best_w)
 
            # ── Step 2: Balanced cooperative evaluation — DE → PSO → GA ─────
            # Each sub-optimizer runs exactly once per iteration.
            # No sub-optimizer is given extra updates or priority.
            # Each step updates the global context so subsequent steps
            # benefit from any improvement found in the current iteration.
 
            # ── DE step — differential mutation for precise exploitation ──────
            for i in range(self.pop_size):
                # Evaluate current DE individual in global context
                full_w_de = self._assemble(de_pop[i], pso_rep, ga_rep)
                fit_de    = evaluate_weights(full_w_de)
                de_fits[i] = fit_de
                if fit_de < best_fit:
                    best_fit = fit_de
                    best_w   = full_w_de.copy()
                    de_rep, pso_rep, ga_rep = self._decompose(best_w)
 
                # DE mutation + crossover + greedy selection
                mutant     = self._de_mutate(de_pop, i)
                trial      = self._de_crossover(de_pop[i], mutant)
                full_trial = self._assemble(trial, pso_rep, ga_rep)
                trial_fit  = evaluate_weights(full_trial)
                if trial_fit <= fit_de:
                    de_pop[i]  = trial
                    de_fits[i] = trial_fit
                    if trial_fit < best_fit:
                        best_fit = trial_fit
                        best_w   = full_trial.copy()
                        de_rep, pso_rep, ga_rep = self._decompose(best_w)
 
            # ── PSO step — velocity-based exploration (single pass) ───────────
            for i in range(self.pop_size):
                # Evaluate PSO particle in global context
                full_w_pso = self._assemble(de_rep, pso_pos[i], ga_rep)
                fit_pso    = evaluate_weights(full_w_pso)
                if fit_pso < pso_pb_fit[i]:
                    pso_pb_fit[i] = fit_pso
                    pso_pb_pos[i] = pso_pos[i].copy()
                if fit_pso < pso_gb_fit:
                    pso_gb_fit = fit_pso
                    pso_gb     = pso_pos[i].copy()
                if fit_pso < best_fit:
                    best_fit = fit_pso
                    best_w   = full_w_pso.copy()
                    de_rep, pso_rep, ga_rep = self._decompose(best_w)
                # Update particle velocity and position
                pso_pos, pso_vel = self._pso_update(
                    pso_pos, pso_vel, pso_pb_pos, pso_gb, i
                )
 
            # ── GA step — crossover + mutation for diversity ───────────────────
            for i in range(self.pop_size):
                # Evaluate GA individual in global context
                full_w_ga = self._assemble(de_rep, pso_rep, ga_pop[i])
                fit_ga    = evaluate_weights(full_w_ga)
                ga_fits[i] = fit_ga
                if fit_ga < best_fit:
                    best_fit = fit_ga
                    best_w   = full_w_ga.copy()
                    de_rep, pso_rep, ga_rep = self._decompose(best_w)
 
            # ── GA generation update ──────────────────────────────────────────
            # Elitism: keep best GA individual
            elite_idx = int(np.argmin(ga_fits))
            elite     = ga_pop[elite_idx].copy()
            new_ga_pop = [elite]
            while len(new_ga_pop) < self.pop_size:
                p1 = self._ga_tournament(ga_pop, ga_fits)
                p2 = self._ga_tournament(ga_pop, ga_fits)
                c1, c2 = self._ga_crossover(p1, p2)
                new_ga_pop.append(self._ga_mutate(c1))
                if len(new_ga_pop) < self.pop_size:
                    new_ga_pop.append(self._ga_mutate(c2))
            ga_pop = np.array(new_ga_pop)
            # Reset fitnesses for new generation (will be re-evaluated)
            ga_fits = np.full(self.pop_size, np.inf)
 
            # ── Global best injection every inject_interval iterations ─────────
            if (itr + 1) % self.inject_interval == 0 and best_w is not None:
                (de_pop, de_fits,
                 pso_pos, pso_pb_pos, pso_pb_fit,
                 ga_pop, ga_fits) = self._inject_global_best(
                    best_w,
                    de_pop, de_fits,
                    pso_pos, pso_pb_pos, pso_pb_fit,
                    ga_pop, ga_fits,
                )
 
            # ── Track history ─────────────────────────────────────────────────
            self.best_fitness_history.append(best_fit)
            self.subgroup_history["DE"].append(float(np.min(de_fits[de_fits < 1e5])) if np.any(de_fits < 1e5) else best_fit)
            self.subgroup_history["PSO"].append(float(pso_gb_fit) if pso_gb_fit < np.inf else best_fit)
            self.subgroup_history["GA"].append(float(np.min(ga_fits[ga_fits < 1e5])) if np.any(ga_fits < 1e5) else best_fit)
 
            if verbose and (itr % 10 == 0 or itr == self.iterations - 1):
                print(f"  Iter {itr+1:>3}/{self.iterations} | "
                      f"Best fitness: {best_fit:.6f} | "
                      f"DE best: {self.subgroup_history['DE'][-1]:.6f} | "
                      f"PSO best: {self.subgroup_history['PSO'][-1]:.6f} | "
                      f"GA best: {self.subgroup_history['GA'][-1]:.6f}")
 
        self.best_fitness = best_fit
        self.best_weights = best_w
 
        if verbose:
            print(f"\n  [CCE] Optimization complete.")
            print(f"  Best fitness : {self.best_fitness:.6f}")
            print(f"  Best weights : {np.round(self.best_weights, 4).tolist()}")
 
        return {
            "best_weights"        : self.best_weights,
            "best_fitness"        : self.best_fitness,
            "best_fitness_history": self.best_fitness_history,
            "subgroup_history"    : self.subgroup_history,
            "optimizer"           : "Hybrid CCE",
        }
        
 
