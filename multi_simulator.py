import pandas as pd
from simulator import TourSimulator
from collections import defaultdict

NUM_SIMULATIONS = 100  # You can change this as needed
NUM_STAGES = 21

# Data structures: {metric: {rider: {stage: [values]}}}
metrics = ['gc_time', 'sprint_points', 'mountain_points', 'youth_time', 'scorito_points']
results = {m: defaultdict(lambda: defaultdict(list)) for m in metrics}

for sim in range(NUM_SIMULATIONS):
    sim_obj = TourSimulator()
    sim_obj.simulate_tour()
    # Per-stage collection
    for stage in range(1, NUM_STAGES+1):
        # GC
        for rec in sim_obj.gc_records:
            if rec['stage'] == stage:
                results['gc_time'][rec['rider']][stage].append(rec['gc_time'])
        # Sprint
        for rec in sim_obj.sprint_records:
            if rec['stage'] == stage:
                results['sprint_points'][rec['rider']][stage].append(rec['sprint_points'])
        # Mountain
        for rec in sim_obj.mountain_records:
            if rec['stage'] == stage:
                results['mountain_points'][rec['rider']][stage].append(rec['mountain_points'])
        # Youth
        for rec in sim_obj.youth_records:
            if rec['stage'] == stage:
                results['youth_time'][rec['rider']][stage].append(rec['youth_time'])
        # Scorito
        for rec in sim_obj.scorito_points_records:
            if rec['stage'] == stage:
                results['scorito_points'][rec['rider']][stage].append(rec['scorito_points'])
    # Final (after all stages, use stage 22 for scorito, last for others)
    final_stage = NUM_STAGES
    # GC
    for rec in sim_obj.gc_records:
        if rec['stage'] == final_stage:
            results['gc_time'][rec['rider']]['final'].append(rec['gc_time'])
    # Sprint
    for rec in sim_obj.sprint_records:
        if rec['stage'] == final_stage:
            results['sprint_points'][rec['rider']]['final'].append(rec['sprint_points'])
    # Mountain
    for rec in sim_obj.mountain_records:
        if rec['stage'] == final_stage:
            results['mountain_points'][rec['rider']]['final'].append(rec['mountain_points'])
    # Youth
    for rec in sim_obj.youth_records:
        if rec['stage'] == final_stage:
            results['youth_time'][rec['rider']]['final'].append(rec['youth_time'])
    # Scorito (stage 22 is final)
    for rec in sim_obj.scorito_points_records:
        if rec['stage'] == 22:
            results['scorito_points'][rec['rider']]['final'].append(rec['scorito_points'])

# Prepare DataFrames for each metric
with pd.ExcelWriter(f"multi_tour_simulation_results_{NUM_SIMULATIONS}_runs.xlsx") as writer:
    for metric in metrics:
        all_riders = set(results[metric].keys())
        columns = [f"Stage {i}" for i in range(1, NUM_STAGES+1)] + ["Final"]
        data = []
        for rider in sorted(all_riders):
            row = {'Rider': rider}
            for stage in range(1, NUM_STAGES+1):
                vals = results[metric][rider][stage]
                if vals:
                    avg = sum(vals)/len(vals)
                    if metric.endswith('time'):
                        avg = avg/3600  # convert to hours
                else:
                    avg = None
                row[f"Stage {stage}"] = avg
            # Final
            vals = results[metric][rider]['final']
            if vals:
                avg = sum(vals)/len(vals)
                if metric.endswith('time'):
                    avg = avg/3600
            else:
                avg = None
            row['Final'] = avg
            data.append(row)
        df = pd.DataFrame(data)
        df = df[['Rider'] + columns]
        df.to_excel(writer, sheet_name=metric, index=False)
print(f"Averaged per-stage and final results written to multi_tour_simulation_results_{NUM_SIMULATIONS}_runs.xlsx") 