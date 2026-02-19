from copy import deepcopy
from time import time

from smart_irrigation_system.server.configuration.schemas.optimization import (
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
    
class InfeasibleSolutionException(Exception):
    """
    Raised when a solution is found but it does not meet the constraints (e.g. T intersection is empty).
    """
    def __init__(self, message):
        super().__init__(message)


class PerPlantOptimizer:

    def __init__(self, request):
        self.plants = request.plants
        self.drippers = request.available_drippers


    # ===============================
    # PUBLIC METHOD
    # ===============================

    def optimize(self) -> PerPlantOptimizationResponse:
        self._best_solution = None

        # 1) Generate candidates per plant
        plant_candidates = {}

        for plant in self.plants:
            candidates = self._generate_candidates_for_plant(plant)
            if not candidates:
                raise NoSolutionException(f"No candidates found for plant {plant.plant_id} with target volume {plant.target_volume_liters}L and tolerance {plant.tolerance_percent}%")
            plant_candidates[plant.plant_id] = candidates

        # 2) Brute force all plant combinations
        best_solution = None
        best_emitters_count = float("inf")
        best_T = None

        # Recursively search for the best combination of candidates across all plants
        self._start_time = time()
        self._search_combinations(
            plant_ids=list(plant_candidates.keys()),
            plant_candidates=plant_candidates,
            index=0,
            current_selection=[],
            best_holder={
                "solution": None,
                "emitters": best_emitters_count,
                "T": best_T
            }
        )

        best_solution = self._best_solution

        if best_solution is None:
            raise NoSolutionException("No global solution found that satisfies all constraints.")

        return self._build_response(best_solution)


    # ===============================
    # GENERATE CANDIDATES PER PLANT
    # ===============================

    def _generate_candidates_for_plant(self, plant):

        candidates = []

        tolerance_volume = plant.target_volume_liters * (plant.tolerance_percent / 100)
        min_volume = plant.target_volume_liters - tolerance_volume
        max_volume = plant.target_volume_liters + tolerance_volume

        # Recursively generate all combinations of drippers for this plant and calculate their flow and T intervals
        self._generate_combinations_recursive(
            plant,
            min_volume,
            max_volume,
            dripper_index=0,
            current_allocations=[],
            current_flow=0.0,
            current_count=0,
            candidates=candidates
        )

        return candidates


    def _generate_combinations_recursive(
        self,
        plant,
        min_volume,
        max_volume,
        dripper_index,
        current_allocations,
        current_flow,
        current_count,
        candidates
    ):

        # If current flow is within the acceptable range, add it as a candidate
        if current_flow > 0:

            t_min = min_volume / current_flow
            t_max = max_volume / current_flow

            if t_min <= t_max:
                candidates.append({
                    "plant_id": plant.plant_id,
                    "allocations": deepcopy(current_allocations),
                    "total_flow": current_flow,
                    "t_min": t_min,
                    "t_max": t_max,
                    "total_emitters": current_count
                })

        # Stop conditions
        if dripper_index >= len(self.drippers):
            return

        if current_count >= plant.max_emitter_quantity:
            return

        dripper = self.drippers[dripper_index]

        max_available = dripper.count if dripper.count is not None else plant.max_emitter_quantity

        max_possible = min(
            max_available,
            plant.max_emitter_quantity - current_count
        )

        # Try all quantities of the current dripper type from 0 to max_possible
        for qty in range(0, max_possible + 1):

            new_allocations = deepcopy(current_allocations)
            new_flow = current_flow
            new_count = current_count

            if qty > 0:
                new_allocations.append({
                    "dripper_id": dripper.dripper_id,
                    "flow_rate_lph": dripper.flow_rate_lph,
                    "count": qty
                })
                new_flow += dripper.flow_rate_lph * qty
                new_count += qty

            self._generate_combinations_recursive(
                plant,
                min_volume,
                max_volume,
                dripper_index + 1,
                new_allocations,
                new_flow,
                new_count,
                candidates
            )


    # ===============================
    # GLOBAL SEARCH
    # ===============================

    def _search_combinations(
        self,
        plant_ids,
        plant_candidates,
        index,
        current_selection,
        best_holder
    ):
        if time() - self._start_time > MAX_RUNTIME_SECONDS:
            raise TimeoutError("Optimization exceeded maximum runtime of {} seconds".format(MAX_RUNTIME_SECONDS))

        if index >= len(plant_ids):
            self._evaluate_solution(current_selection, best_holder)
            return

        plant_id = plant_ids[index]

        for candidate in plant_candidates[plant_id]:
            self._search_combinations(
                plant_ids,
                plant_candidates,
                index + 1,
                current_selection + [candidate],
                best_holder
            )


    def _evaluate_solution(self, selection, best_holder):

        # 1) Check T intersection
        t_min_global = 0
        t_max_global = MAX_TIME_HOURS

        total_emitters = 0
        dripper_usage = {}

        for candidate in selection:

            t_min_global = max(t_min_global, candidate["t_min"])
            t_max_global = min(t_max_global, candidate["t_max"])

            total_emitters += candidate["total_emitters"]

            for alloc in candidate["allocations"]:
                dripper_id = alloc["dripper_id"]
                if dripper_id not in dripper_usage:
                    dripper_usage[dripper_id] = 0
                dripper_usage[dripper_id] += alloc["count"]

        if t_min_global > t_max_global:
            return

        # 2) Check global availability
        for dripper in self.drippers:
            if dripper.count is not None:
                used = dripper_usage.get(dripper.dripper_id, 0)
                if used > dripper.count:
                    return

        chosen_T = t_min_global

        # 3) Compare with best
        if best_holder["solution"] is None:
            best_holder["solution"] = selection
            best_holder["emitters"] = total_emitters
            best_holder["T"] = chosen_T
            self._best_solution = (selection, chosen_T)
            return

        if total_emitters < best_holder["emitters"]:
            best_holder["solution"] = selection
            best_holder["emitters"] = total_emitters
            best_holder["T"] = chosen_T
            self._best_solution = (selection, chosen_T)
            return

        if total_emitters == best_holder["emitters"]:
            if chosen_T < best_holder["T"]:
                best_holder["solution"] = selection
                best_holder["emitters"] = total_emitters
                best_holder["T"] = chosen_T
                self._best_solution = (selection, chosen_T)


        # ===============================
        # BUILD RESPONSE
        # ===============================

    def _build_response(self, best_solution_tuple) -> PerPlantOptimizationResponse:

        selection, chosen_T_hours = best_solution_tuple

        plants_results = []

        total_flow_lph = 0.0
        total_base_volume_liters = 0.0
        total_drippers_used = 0

        drippers_summary = {}

        for candidate in selection:

            plant_id = candidate["plant_id"]
            allocations = candidate["allocations"]
            plant_flow = candidate["total_flow"]

            # Skutečný objem pro tuto rostlinu
            actual_volume = plant_flow * chosen_T_hours

            # Zaokrouhlení pro čitelnost
            actual_volume = round(actual_volume, 3)

            # Převod alokací na Pydantic modely
            assigned_drippers = []

            for alloc in allocations:

                dripper_model = DripperAllocation(
                    dripper_id=alloc["dripper_id"],
                    flow_rate_lph=alloc["flow_rate_lph"],
                    count=alloc["count"]
                )

                assigned_drippers.append(dripper_model)

                # Aktualizace globálního summary
                if alloc["dripper_id"] not in drippers_summary:
                    drippers_summary[alloc["dripper_id"]] = DripperAllocation(
                        dripper_id=alloc["dripper_id"],
                        flow_rate_lph=alloc["flow_rate_lph"],
                        count=0
                    )

                drippers_summary[alloc["dripper_id"]].count += alloc["count"]

                total_drippers_used += alloc["count"]

            # Přidání výsledku pro rostlinu
            plants_results.append(
                PlantOptimizationResult(
                    plant_id=plant_id,
                    actual_volume_liters=actual_volume,
                    assigned_drippers=assigned_drippers
                )
            )

            total_flow_lph += plant_flow
            total_base_volume_liters += actual_volume

        # Globální zaokrouhlení
        total_flow_lph = round(total_flow_lph, 3)
        total_base_volume_liters = round(total_base_volume_liters, 3)

        base_irrigation_time_seconds = round(chosen_T_hours * 3600, 2)

        return PerPlantOptimizationResponse(
            plants=plants_results,
            total_drippers_used=total_drippers_used,
            drippers_used_detail=list(drippers_summary.values()),
            total_base_volume_liters=total_base_volume_liters,
            total_flow_lph=total_flow_lph,
            base_irrigation_time_seconds=base_irrigation_time_seconds
        )
