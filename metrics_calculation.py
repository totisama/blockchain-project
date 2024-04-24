from datetime import datetime
from collections import defaultdict

def parse_log(log_file):
    transactions = defaultdict(list)
    with open(log_file, 'r') as file:
        for line in file:
            if "received transaction" in line:  # Check if the line contains the phrase
                parts = line.strip().split()
                timestamp = datetime.strptime(parts[0] + ' ' + parts[1], '%Y-%m-%d %H:%M:%S,%f')
                transaction_num = parts[7]
                node_id = parts[4][1:-1]
                transactions[transaction_num].append((node_id, timestamp))
    return transactions

def calculate_latency(transactions):
    latencies = []
    for _, transaction_events in transactions.items():
        min_time = min(event[1] for event in transaction_events)
        max_time = max(event[1] for event in transaction_events)
        latency = (max_time - min_time).total_seconds()
        latencies.append(latency)
    return latencies

def calculate_throughput(transactions, window_size=10):
    throughputs = []
    for _, transaction_events in transactions.items():
        timestamps = [event[1] for event in transaction_events]
        timestamps.sort()
        if len(timestamps) >= 2:
            time_diff = (timestamps[-1] - timestamps[0]).total_seconds()
            throughput = len(transaction_events) / time_diff
            throughputs.append(throughput)
    return throughputs

if __name__ == "__main__":
    log_file = "logfile.log"
    transactions = parse_log(log_file)
    latencies = calculate_latency(transactions)
    throughputs = calculate_throughput(transactions)
    avg_latency = sum(latencies) / len(latencies)
    avg_throughput = sum(throughputs) / len(throughputs)
    print(f"Average Latency: {avg_latency:.4f} seconds")
    print(f"Average Throughput: {avg_throughput:.4f} transactions per second")
