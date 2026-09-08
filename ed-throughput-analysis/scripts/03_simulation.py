"""
Discrete-event simulation of the ED as a 3-stage queueing network
(triage nurses -> beds -> physicians), built to test a concrete staffing
intervention against the bottleneck identified in 02_bottleneck_analysis.py:
the Evening shift, driven primarily by physician-queue wait.

Baseline staffing vs. "+1 physician-equivalent (APP) on Evening shift" are
each run for N_REPLICATIONS independent 120-day horizons so we can report
a confidence interval, not a single noisy run.
"""

import simpy
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Shared seasonality (same shape as the synthetic-data generator)
# ---------------------------------------------------------------------------
HOUR_MULTIPLIER = np.array([
    0.35, 0.25, 0.20, 0.18, 0.20, 0.30,
    0.45, 0.65, 0.85, 1.05, 1.20, 1.30,
    1.35, 1.30, 1.25, 1.25, 1.30, 1.35,
    1.30, 1.20, 1.05, 0.85, 0.65, 0.50
])
DOW_MULTIPLIER = {0: 1.15, 1: 1.05, 2: 1.00, 3: 0.98, 4: 1.00, 5: 0.95, 6: 0.90}
ANNUAL_VISITS_TARGET = 20000
BASE_RATE_PER_HOUR = ANNUAL_VISITS_TARGET / (365 * 24) / (
    np.mean(HOUR_MULTIPLIER) * np.mean(list(DOW_MULTIPLIER.values()))
)

BASE_STAFFING = {
    "Night":   {"nurses": 2, "beds": 14, "physicians": 2},
    "Day":     {"nurses": 3, "beds": 18, "physicians": 4},
    "Evening": {"nurses": 3, "beds": 18, "physicians": 4},
}
ESI_LEVELS = [1, 2, 3, 4, 5]
ESI_PROBS = [0.01, 0.20, 0.50, 0.24, 0.05]
PATIENCE_MIN = {1: 10_000, 2: 10_000, 3: 215, 4: 200, 5: 168}

SIM_DAYS = 120
N_REPLICATIONS = 20
AVG_REVENUE_PER_VISIT = 1500      # stated assumption; see README for basis
ANNUAL_COST_ADDED_PROVIDER = 150_000  # blended APP cost, ~1.4 FTE to cover 1 daily 8h shift


def shift_of(minute_of_day):
    hour = int((minute_of_day // 60) % 24)
    if 0 <= hour < 8:
        return "Night"
    elif 8 <= hour < 16:
        return "Day"
    else:
        return "Evening"


def run_one_replication(rng, staffing_overrides=None):
    """staffing_overrides: dict like {'Evening': {'physicians': +1}} applied on top of BASE_STAFFING."""
    env = simpy.Environment()
    nurses = simpy.Resource(env, capacity=BASE_STAFFING["Night"]["nurses"])
    beds = simpy.Resource(env, capacity=BASE_STAFFING["Night"]["beds"])
    physicians = simpy.Resource(env, capacity=BASE_STAFFING["Night"]["physicians"])

    results = []  # dict per patient

    def effective_capacity(shift_name, resource_key):
        base = BASE_STAFFING[shift_name][resource_key]
        if staffing_overrides and shift_name in staffing_overrides:
            base += staffing_overrides[shift_name].get(resource_key, 0)
        return base

    def shift_scheduler():
        while True:
            minute_of_day = env.now % (24 * 60)
            current_shift = shift_of(minute_of_day)
            nurses._capacity = effective_capacity(current_shift, "nurses")
            beds._capacity = effective_capacity(current_shift, "beds")
            physicians._capacity = effective_capacity(current_shift, "physicians")
            # advance to the next shift boundary (8h blocks)
            next_boundary = (minute_of_day // (8 * 60) + 1) * (8 * 60)
            yield env.timeout(next_boundary - minute_of_day)

    def patient(pid, esi):
        t_arrive = env.now
        with nurses.request() as req:
            yield req
            t_triage_start = env.now
            yield env.timeout(max(rng.lognormal(np.log(15), 0.4), 1))
        door_to_triage = t_triage_start - t_arrive

        # --- Bed queue (manual request; NOT a `with` block, since the bed is
        #     held beyond this function via a background release process) ---
        patience_left = max(PATIENCE_MIN[esi] - (env.now - t_arrive), 0)
        bed_req = beds.request()
        outcome = yield bed_req | env.timeout(patience_left)
        if bed_req not in outcome:
            bed_req.cancel()
            results.append({"esi": esi, "lwbs": True, "shift": shift_of(t_arrive)})
            return
        t_room_start = env.now
        triage_to_room = t_room_start - t_triage_start

        esi_md_speed = {1: 0.10, 2: 0.45, 3: 1.0, 4: 1.20, 5: 1.35}[esi]

        # --- Physician queue (manual request; released explicitly below) ---
        patience_left2 = max(PATIENCE_MIN[esi] - (env.now - t_arrive), 0)
        preq = physicians.request()
        outcome2 = yield preq | env.timeout(patience_left2)
        if preq not in outcome2:
            preq.cancel()
            # patient leaves the room; short cleanup hold rather than a full stay
            env.process(release_bed_after(bed_req, max(rng.lognormal(np.log(10), 0.3), 2), beds))
            results.append({"esi": esi, "lwbs": True, "shift": shift_of(t_arrive)})
            return
        t_md_start = env.now
        room_to_physician = t_md_start - t_room_start
        yield env.timeout(max(rng.lognormal(np.log(73 * esi_md_speed), 0.4), 1))
        physicians.release(preq)

        # Bed occupied for the remainder of the visit (turnover constraint),
        # released in the background so it doesn't block this patient's flow.
        bed_hold = max(rng.lognormal(np.log(178), 0.5), 15)
        env.process(release_bed_after(bed_req, bed_hold, beds))

        results.append({
            "esi": esi, "lwbs": False, "shift": shift_of(t_arrive),
            "door_to_triage": door_to_triage,
            "triage_to_room": triage_to_room,
            "room_to_physician": room_to_physician,
            "door_to_provider": door_to_triage + triage_to_room + room_to_physician,
        })

    def release_bed_after(bed_req, hold_time, bed_resource):
        yield env.timeout(hold_time)
        bed_resource.release(bed_req)

    def arrival_generator():
        pid = 0
        for day in range(SIM_DAYS):
            dow = day % 7
            for hour in range(24):
                lam = BASE_RATE_PER_HOUR * HOUR_MULTIPLIER[hour] * DOW_MULTIPLIER[dow]
                n_arrivals = rng.poisson(lam)
                arrival_offsets = np.sort(rng.uniform(0, 60, n_arrivals))
                for offset in arrival_offsets:
                    target_time = day * 24 * 60 + hour * 60 + offset
                    delay = target_time - env.now
                    if delay > 0:
                        yield env.timeout(delay)
                    esi = rng.choice(ESI_LEVELS, p=ESI_PROBS)
                    env.process(patient(pid, esi))
                    pid += 1

    env.process(shift_scheduler())
    env.process(arrival_generator())
    env.run(until=SIM_DAYS * 24 * 60)

    rdf = pd.DataFrame(results)
    return rdf


def summarize(rdf):
    lwbs_rate = rdf["lwbs"].mean()
    completed = rdf[~rdf["lwbs"]]
    avg_dtp = completed["door_to_provider"].mean()
    return lwbs_rate, avg_dtp, len(rdf)


if __name__ == "__main__":
    baseline_lwbs, baseline_dtp = [], []
    scenario_lwbs, scenario_dtp = [], []
    n_visits_per_rep = []

    for rep in range(N_REPLICATIONS):
        rng = np.random.default_rng(1000 + rep)
        base_result = run_one_replication(rng, staffing_overrides=None)
        l, d, n = summarize(base_result)
        baseline_lwbs.append(l); baseline_dtp.append(d); n_visits_per_rep.append(n)

        rng2 = np.random.default_rng(1000 + rep)  # same arrival stream for paired comparison
        scenario_result = run_one_replication(rng2, staffing_overrides={"Evening": {"physicians": 1}})
        l2, d2, _ = summarize(scenario_result)
        scenario_lwbs.append(l2); scenario_dtp.append(d2)

    def ci95(arr):
        arr = np.array(arr)
        m = arr.mean()
        se = arr.std(ddof=1) / np.sqrt(len(arr))
        return m, m - 1.96 * se, m + 1.96 * se

    b_lwbs_m, b_lwbs_lo, b_lwbs_hi = ci95(baseline_lwbs)
    s_lwbs_m, s_lwbs_lo, s_lwbs_hi = ci95(scenario_lwbs)
    b_dtp_m, b_dtp_lo, b_dtp_hi = ci95(baseline_dtp)
    s_dtp_m, s_dtp_lo, s_dtp_hi = ci95(scenario_dtp)

    avg_annual_visits = np.mean(n_visits_per_rep) * (365 / SIM_DAYS)
    lwbs_avoided_per_year = (b_lwbs_m - s_lwbs_m) * avg_annual_visits
    revenue_recovered = lwbs_avoided_per_year * AVG_REVENUE_PER_VISIT
    net_annual_benefit = revenue_recovered - ANNUAL_COST_ADDED_PROVIDER

    print("=" * 70)
    print(f"BASELINE  ({N_REPLICATIONS} reps x {SIM_DAYS} days)")
    print("=" * 70)
    print(f"LWBS rate:            {b_lwbs_m*100:.2f}%  (95% CI: {b_lwbs_lo*100:.2f}-{b_lwbs_hi*100:.2f}%)")
    print(f"Avg door-to-provider: {b_dtp_m:.1f} min  (95% CI: {b_dtp_lo:.1f}-{b_dtp_hi:.1f})")

    print("\n" + "=" * 70)
    print("SCENARIO: +1 physician-equivalent (APP) on Evening shift")
    print("=" * 70)
    print(f"LWBS rate:            {s_lwbs_m*100:.2f}%  (95% CI: {s_lwbs_lo*100:.2f}-{s_lwbs_hi*100:.2f}%)")
    print(f"Avg door-to-provider: {s_dtp_m:.1f} min  (95% CI: {s_dtp_lo:.1f}-{s_dtp_hi:.1f})")

    print("\n" + "=" * 70)
    print("IMPACT")
    print("=" * 70)
    print(f"Door-to-provider reduction: {b_dtp_m - s_dtp_m:.1f} min ({(b_dtp_m-s_dtp_m)/b_dtp_m*100:.1f}%)")
    print(f"LWBS reduction:             {(b_lwbs_m - s_lwbs_m)*100:.2f} pts ({(b_lwbs_m-s_lwbs_m)/b_lwbs_m*100:.1f}% relative)")
    print(f"Est. annual visits:         {avg_annual_visits:,.0f}")
    print(f"Est. LWBS visits avoided/yr:{lwbs_avoided_per_year:,.0f}")
    print(f"Revenue recovered/yr:       ${revenue_recovered:,.0f}  (@ ${AVG_REVENUE_PER_VISIT}/visit assumption)")
    print(f"Added provider cost/yr:     ${ANNUAL_COST_ADDED_PROVIDER:,.0f}")
    print(f"NET annual benefit:         ${net_annual_benefit:,.0f}")

    out = {
        "baseline_lwbs_pct": round(b_lwbs_m*100, 2),
        "scenario_lwbs_pct": round(s_lwbs_m*100, 2),
        "baseline_dtp_min": round(b_dtp_m, 1),
        "scenario_dtp_min": round(s_dtp_m, 1),
        "dtp_reduction_min": round(b_dtp_m - s_dtp_m, 1),
        "dtp_reduction_pct": round((b_dtp_m-s_dtp_m)/b_dtp_m*100, 1),
        "lwbs_reduction_pts": round((b_lwbs_m - s_lwbs_m)*100, 2),
        "lwbs_reduction_relative_pct": round((b_lwbs_m-s_lwbs_m)/b_lwbs_m*100, 1),
        "annual_visits_est": round(avg_annual_visits),
        "lwbs_avoided_per_year": round(lwbs_avoided_per_year),
        "revenue_recovered_per_year": round(revenue_recovered),
        "added_provider_cost_per_year": ANNUAL_COST_ADDED_PROVIDER,
        "net_annual_benefit": round(net_annual_benefit),
    }
    pd.Series(out).to_json("/home/claude/ed-throughput-analysis/output/simulation_results.json", indent=2)
    print("\nSaved -> output/simulation_results.json")
