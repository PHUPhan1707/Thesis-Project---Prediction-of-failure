import requests
r = requests.get('http://localhost:5000/api/statistics/course-v1:DHQG-HCM+FM101+2025_S2', timeout=10)
s = r.json()['statistics']
print(f'Total: {s["total_students"]}')
print(f'Completed: {s["completed_count"]}')
print(f'High: {s["high_risk_count"]}')
print(f'Medium: {s["medium_risk_count"]}')
print(f'Low: {s["low_risk_count"]}')
risk_total = s["high_risk_count"] + s["medium_risk_count"] + s["low_risk_count"]
not_completed = s["not_passed_count"] + s["in_progress_count"]
print(f'Risk total: {risk_total}')
print(f'Not completed: {not_completed}')
print(f'Match: {"YES" if risk_total == not_completed else "NO"}')
