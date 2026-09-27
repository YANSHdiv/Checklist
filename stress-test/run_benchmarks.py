import sys
import os
import subprocess
import csv
import time

DEFAULT_LEVELS = [50, 100, 150, 200, 300, 500]
RUN_TIME = "20s"
HOST = "http://localhost:8000"

def run_test(config_name: str, levels=None):
    if levels is None:
        levels = DEFAULT_LEVELS
    print(f"=== Starting Benchmark Suite: {config_name.upper()} for levels {levels} ===")
    results = []

    for users in levels:
        spawn_rate = max(10, users // 3)
        prefix = f"stress-test/{config_name}_{users}"
        cmd = [
            sys.executable,
            "-m",
            "locust",
            "-f",
            "stress-test/locustfile.py",
            "--headless",
            "-u",
            str(users),
            "-r",
            str(spawn_rate),
            "--run-time",
            RUN_TIME,
            "--host",
            HOST,
            "--csv",
            prefix,
            "--csv-full-history"
        ]
        print(f"\n---> Running {config_name} with {users} users (spawn rate {spawn_rate}) for {RUN_TIME}...")
        res = subprocess.run(cmd, capture_output=True, text=True)

        stats_csv = f"{prefix}_stats.csv"
        if os.path.exists(stats_csv):
            with open(stats_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Name") == "Aggregated" or row.get("Type") == "":
                        req_count = int(row.get("Request Count", 0))
                        fail_count = int(row.get("Failure Count", 0))
                        rps = float(row.get("Requests/s", 0.0))
                        avg_lat = float(row.get("Average Response Time", 0.0))
                        p95 = float(row.get("95%", 0.0))
                        p99 = float(row.get("99%", 0.0))
                        fail_pct = (fail_count / req_count * 100.0) if req_count > 0 else 0.0
                        
                        data_point = {
                            "users": users,
                            "requests": req_count,
                            "rps": round(rps, 1),
                            "avg_latency": round(avg_lat, 1),
                            "p95": round(p95, 1),
                            "p99": round(p99, 1),
                            "failures": fail_count,
                            "failure_pct": round(fail_pct, 2),
                        }
                        results.append(data_point)
                        print(f"Result for {users} users: RPS={data_point['rps']}, Avg={data_point['avg_latency']}ms, P95={data_point['p95']}ms, Failures={data_point['failures']} ({data_point['failure_pct']}%)")
                        break
        else:
            print(f"Warning: {stats_csv} not found!")

        time.sleep(2)

    print("\n" + "=" * 80)
    print(f"SUMMARY TABLE FOR {config_name.upper()}")
    print("=" * 80)
    print("| Concurrent users | Total reqs | RPS | Avg latency | P95 | P99 | Failures | Failure % |")
    print("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for r in results:
        print(f"| {r['users']} | {r['requests']} | {r['rps']} | {r['avg_latency']} ms | {r['p95']} ms | {r['p99']} ms | {r['failures']} | {r['failure_pct']}% |")
    print("=" * 80)

if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    levels = None
    if len(sys.argv) > 2:
        levels = [int(x.strip()) for x in sys.argv[2].split(",") if x.strip()]
    run_test(config, levels)
