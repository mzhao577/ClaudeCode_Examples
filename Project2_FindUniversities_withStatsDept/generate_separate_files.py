import json

# Read the existing comprehensive results
with open('verified_statistics_departments.json', 'r') as f:
    all_results = json.load(f)

# Filter for universities with statistics departments only
stats_only = [uni for uni in all_results if uni.get('has_stats_dept', False)]

# Save JSON file with only statistics departments
with open('universities_with_statistics_only.json', 'w') as f:
    json.dump(stats_only, f, indent=2)
print(f"Universities with statistics departments saved to universities_with_statistics_only.json")

# Create a simple text list for easy reading
with open('statistics_departments_list.txt', 'w') as f:
    f.write("US UNIVERSITIES WITH VERIFIED STATISTICS DEPARTMENTS\n")
    f.write("=" * 60 + "\n\n")
    
    # Group by state
    by_state = {}
    for uni in stats_only:
        state = uni['state']
        if state not in by_state:
            by_state[state] = []
        by_state[state].append(uni)
    
    for state in sorted(by_state.keys()):
        f.write(f"{state}:\n")
        f.write("-" * len(state) + "\n")
        for uni in by_state[state]:
            f.write(f"  • {uni['name']}\n")
            f.write(f"    University: {uni['url']}\n")
            f.write(f"    Statistics Dept: {uni['dept_url']}\n")
            f.write("\n")
        f.write("\n")
    
    f.write(f"TOTAL: {len(stats_only)} universities with statistics departments\n")

print(f"Text summary saved to statistics_departments_list.txt")
print(f"Found {len(stats_only)} universities with statistics departments out of {len(all_results)} total")