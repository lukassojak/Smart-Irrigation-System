from time import time
 
from app.schemas.optimization import (
    PerPlantOptimizationRequest,
    PerPlantOptimizationResponse,
    DripperAllocation,
    PlantOptimizationResult
)
 
MAX_TIME_HOURS = 3
MAX_RUNTIME_SECONDS = 30
 
# TODO (Phase 2 improvement):
# Currently irrigation time is limited by hard constant MAX_TIME_HOURS.
# In the future this should:
# - be configurable
# - or replaced with time penalty in optimization score
 
 
# Custom exceptions
class NoSolutionException(Exception):
    """
    Raised when no solution can be found for a plant or globally.
    """
    def __init__(self, message):
        super().__init__(message)
 
 
class PerPlantOptimizer:
 
    def __init__(self, request: PerPlantOptimizationRequest):
        self.plants = request.plants
        self.drippers = request.available_drippers
        # Pre-build a lookup for dripper availability to avoid repeated iteration
        self._dripper_limits: dict[str, int | None] = {
            d.dripper_id: d.count for d in self.drippers
        }
 
 
    # ===============================
    # PUBLIC METHOD
    # ===============================
 
    def optimize(self) -> PerPlantOptimizationResponse:
 
        # 1) Generate candidates per plant
        plant_candidates: dict[str, list[dict]] = {}
 
        for plant in self.plants:
            candidates = self._generate_candidates_for_plant(plant)
            if not candidates:
                raise NoSolutionException(
                    f"No candidates found for plant {plant.plant_id} "
                    f"with target volume {plant.target_volume_liters}L "
                    f"and tolerance {plant.tolerance_percent}%"
                )
            # Remove dominated candidates before searching
            candidates = self._filter_dominated(candidates)
            # Sort by emitter count ascending so branch-and-bound
            # finds a good solution early and can prune aggressively
            candidates.sort(key=lambda c: c["total_emitters"])
            plant_candidates[plant.plant_id] = candidates
 
        # 2) Branch-and-bound search across all plant combinations
        self._start_time = time()
        best_holder: dict = {
            "solution": None,
            "emitters": float("inf"),
            "T": float("inf"),
        }
 
        self._search_combinations(
            plant_ids=list(plant_candidates.keys()),
            plant_candidates=plant_candidates,
            index=0,
            current_selection=[],
            current_usage={},
            t_min_so_far=0.0,
            t_max_so_far=MAX_TIME_HOURS,
            emitters_so_far=0,
            best_holder=best_holder,
        )
 
        if best_holder["solution"] is None:
            raise NoSolutionException(
                "No global solution found that satisfies all constraints."
            )
 
        return self._build_response(best_holder["solution"], best_holder["T"])
 
 
    # ===============================
    # GENERATE CANDIDATES PER PLANT
    # ===============================
 
    def _generate_candidates_for_plant(self, plant) -> list[dict]:
 
        tolerance_volume = plant.target_volume_liters * (plant.tolerance_percent / 100)
        min_volume = plant.target_volume_liters - tolerance_volume
        max_volume = plant.target_volume_liters + tolerance_volume
 
        candidates: list[dict] = []
 
        self._generate_combinations_recursive(
            plant=plant,
            min_volume=min_volume,
            max_volume=max_volume,
            dripper_index=0,
            current_allocations=[],
            current_flow=0.0,
            current_count=0,
            candidates=candidates,
        )
 
        return candidates
 
 
    def _generate_combinations_recursive(
        self,
        plant,
        min_volume: float,
        max_volume: float,
        dripper_index: int,
        current_allocations: list[dict],
        current_flow: float,
        current_count: int,
        candidates: list[dict],
    ) -> None:
 
        # If we already have some flow, check whether it yields a valid T interval
        if current_flow > 0:
            t_min = min_volume / current_flow
            t_max = max_volume / current_flow
 
            # t_min <= t_max is always true here since min_volume <= max_volume,
            # but guard against floating-point edge cases
            if t_min <= t_max + 1e-9:
                candidates.append({
                    "plant_id": plant.plant_id,
                    "allocations": current_allocations,   # no deepcopy needed — list is never mutated after append
                    "total_flow": current_flow,
                    "t_min": t_min,
                    "t_max": t_max,
                    "total_emitters": current_count,
                })
 
        # Stop conditions
        if dripper_index >= len(self.drippers):
            return
 
        if current_count >= plant.max_emitter_quantity:
            return
 
        dripper = self.drippers[dripper_index]
        max_available = (
            dripper.count if dripper.count is not None else plant.max_emitter_quantity
        )
        max_possible = min(max_available, plant.max_emitter_quantity - current_count)
 
        for qty in range(0, max_possible + 1):
            if qty == 0:
                new_allocations = current_allocations
                new_flow = current_flow
                new_count = current_count
            else:
                # List concatenation creates a new list — no deepcopy required
                new_allocations = current_allocations + [{
                    "dripper_id": dripper.dripper_id,
                    "flow_rate_lph": dripper.flow_rate_lph,
                    "count": qty,
                }]
                new_flow = current_flow + dripper.flow_rate_lph * qty
                new_count = current_count + qty
 
            self._generate_combinations_recursive(
                plant=plant,
                min_volume=min_volume,
                max_volume=max_volume,
                dripper_index=dripper_index + 1,
                current_allocations=new_allocations,
                current_flow=new_flow,
                current_count=new_count,
                candidates=candidates,
            )
 
 
    # ===============================
    # DOMINANCE PRUNING
    # ===============================
 
    def _filter_dominated(self, candidates: list[dict]) -> list[dict]:
        """
        Remove dominated candidates from the list.
 
        Candidate A is dominated by candidate B if:
          - B uses fewer or equal emitters than A, AND
          - B's T interval [t_min, t_max] fully contains A's interval
            (i.e. B is at least as flexible in timing as A)
 
        A dominated candidate can never be part of a better global solution
        than the candidate that dominates it, so it is safe to discard it.
 
        Complexity: O(N^2) per plant — acceptable because N is bounded by
        (max_qty+1)^D which is already pruned before this step.
        """
        # Sort by emitters asc, then by t_min asc — dominant candidates tend
        # to appear early, so we hit them before the candidates they dominate
        candidates.sort(key=lambda c: (c["total_emitters"], c["t_min"]))
 
        filtered: list[dict] = []
 
        for candidate in candidates:
            dominated = False
            for other in filtered:
                # other has <= emitters (guaranteed by sort order)
                # check if other's interval fully contains candidate's interval
                if (
                    other["total_emitters"] <= candidate["total_emitters"]
                    and other["t_min"] <= candidate["t_min"] + 1e-9
                    and other["t_max"] >= candidate["t_max"] - 1e-9
                ):
                    dominated = True
                    break
            if not dominated:
                filtered.append(candidate)
 
        return filtered
 
 
    # ===============================
    # GLOBAL SEARCH (branch-and-bound)
    # ===============================
 
    def _search_combinations(
        self,
        plant_ids: list[str],
        plant_candidates: dict[str, list[dict]],
        index: int,
        current_selection: list[dict],
        current_usage: dict[str, int],      # running dripper usage across selected plants
        t_min_so_far: float,                # running lower bound of T interval
        t_max_so_far: float,                # running upper bound of T interval
        emitters_so_far: int,               # running total emitter count
        best_holder: dict,
    ) -> None:
 
        if time() - self._start_time > MAX_RUNTIME_SECONDS:
            raise TimeoutError(
                f"Optimization exceeded maximum runtime of {MAX_RUNTIME_SECONDS} seconds"
            )
 
        # ---- Pruning ----
 
        # T interval already empty — no point going deeper
        if t_min_so_far > t_max_so_far + 1e-9:
            return
 
        # Emitter count already at least as large as best known — cannot improve
        if emitters_so_far >= best_holder["emitters"]:
            return
 
        # ---- Base case ----
 
        if index >= len(plant_ids):
            # All plants assigned — record solution
            best_holder["solution"] = current_selection
            best_holder["emitters"] = emitters_so_far
            best_holder["T"] = t_min_so_far
            return
 
        # ---- Recurse ----
 
        plant_id = plant_ids[index]
 
        for candidate in plant_candidates[plant_id]:
 
            # Fast emitter bound: prune if adding this candidate already meets/exceeds best
            if emitters_so_far + candidate["total_emitters"] >= best_holder["emitters"]:
                # Candidates are sorted by emitter count, so remaining ones are at least as bad
                break
 
            # Intersect T interval
            new_t_min = max(t_min_so_far, candidate["t_min"])
            new_t_max = min(t_max_so_far, candidate["t_max"])
 
            if new_t_min > new_t_max + 1e-9:
                # This candidate makes the T interval empty — skip, but keep trying others
                continue
 
            # Check and update dripper availability incrementally
            new_usage = self._apply_candidate_usage(current_usage, candidate)
            if new_usage is None:
                # Dripper limit exceeded — skip
                continue
 
            self._search_combinations(
                plant_ids=plant_ids,
                plant_candidates=plant_candidates,
                index=index + 1,
                current_selection=current_selection + [candidate],
                current_usage=new_usage,
                t_min_so_far=new_t_min,
                t_max_so_far=new_t_max,
                emitters_so_far=emitters_so_far + candidate["total_emitters"],
                best_holder=best_holder,
            )
 
 
    def _apply_candidate_usage(
        self,
        current_usage: dict[str, int],
        candidate: dict,
    ) -> dict[str, int] | None:
        """
        Returns an updated usage dict if the candidate's drippers fit within
        global availability limits, or None if any limit is exceeded.
        """
        new_usage = dict(current_usage)  # shallow copy of int values — fine
 
        for alloc in candidate["allocations"]:
            dripper_id = alloc["dripper_id"]
            limit = self._dripper_limits.get(dripper_id)
 
            if limit is not None:
                used = new_usage.get(dripper_id, 0) + alloc["count"]
                if used > limit:
                    return None
                new_usage[dripper_id] = used
            else:
                new_usage[dripper_id] = new_usage.get(dripper_id, 0) + alloc["count"]
 
        return new_usage
 
 
    # ===============================
    # BUILD RESPONSE
    # ===============================
 
    def _build_response(
        self,
        selection: list[dict],
        chosen_T_hours: float,
    ) -> PerPlantOptimizationResponse:
 
        plants_results: list[PlantOptimizationResult] = []
        drippers_summary: dict[str, DripperAllocation] = {}
        total_flow_lph = 0.0
        total_base_volume_liters = 0.0
        total_drippers_used = 0
 
        for candidate in selection:
 
            plant_flow = candidate["total_flow"]
            actual_volume = round(plant_flow * chosen_T_hours, 3)
            assigned_drippers: list[DripperAllocation] = []
 
            for alloc in candidate["allocations"]:
                dripper_id = alloc["dripper_id"]
 
                assigned_drippers.append(DripperAllocation(
                    dripper_id=dripper_id,
                    flow_rate_lph=alloc["flow_rate_lph"],
                    count=alloc["count"],
                ))
 
                if dripper_id not in drippers_summary:
                    drippers_summary[dripper_id] = DripperAllocation(
                        dripper_id=dripper_id,
                        flow_rate_lph=alloc["flow_rate_lph"],
                        count=0,
                    )
                drippers_summary[dripper_id].count += alloc["count"]
                total_drippers_used += alloc["count"]
 
            plants_results.append(PlantOptimizationResult(
                plant_id=candidate["plant_id"],
                actual_volume_liters=actual_volume,
                assigned_drippers=assigned_drippers,
            ))
 
            total_flow_lph += plant_flow
            total_base_volume_liters += actual_volume
 
        return PerPlantOptimizationResponse(
            plants=plants_results,
            total_drippers_used=total_drippers_used,
            drippers_used_detail=list(drippers_summary.values()),
            total_base_volume_liters=round(total_base_volume_liters, 3),
            total_flow_lph=round(total_flow_lph, 3),
            base_irrigation_time_seconds=round(chosen_T_hours * 3600, 2),
        )