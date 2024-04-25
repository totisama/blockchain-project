from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt

def parse_log(log_file):
    transactions = defaultdict(list)
    with open(log_file, 'r') as file:
        for line in file:
            if "received transaction" in line:
                parts = line.strip().split()
                timestamp = datetime.strptime(parts[0] + ' ' + parts[1], '%Y-%m-%d %H:%M:%S,%f')
                node_id = parts[7][1:-1]  # Extract node ID
                transactions[parts[7]].append((node_id, timestamp))
    return transactions

def calculate_latency(transactions):
    latency = []
    for tx_list in transactions.values():
        for i in range(len(tx_list) - 1):
            latency.append((tx_list[i + 1][1] - tx_list[i][1]).total_seconds())
    return latency

def calculate_throughput(transactions, experiment_time):
    total_transactions = sum(len(tx_list) for tx_list in transactions.values())
    return total_transactions / experiment_time

'''The x-axis represents the latency in seconds, and the y-axis represents the frequency of occurrence of each latency value.
Each bar in the histogram represents a range of latency values, and the height of the bar indicates how many transactions fall within that range.
For example, if a bar is taller, it means there are more transactions with that particular latency value.'''

def plot_latency(latency, output_file):
    plt.hist(latency, bins=50, color='blue', alpha=0.7)
    plt.xlabel('Latency (seconds)')
    plt.ylabel('Frequency')
    plt.title('Latency Histogram')
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

'''x-axis represents time, timestamps.
y-axis represents the number of transactions processed per second (TPS).
Each data point on the plot represents the throughput (TPS) at a specific timestamp.
It insights into how transaction processing fluctuates.'''

def plot_throughput(transactions, experiment_time, output_file):
    transaction_counts = [sum(len(tx_list) for tx_list in transactions.values() if len(tx_list) >= i) for i in range(1, len(transactions))]
    throughput = [transaction_count / experiment_time for transaction_count in transaction_counts]
    plt.plot(range(1, len(transactions)), throughput, marker='o', linestyle='-')
    plt.xlabel('Number of Transactions')
    plt.ylabel('Throughput (Transactions per Second)')
    plt.title('Throughput vs. Number of Transactions')
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    log_file = "logfile.log"
    output_latency = "metrics/latency_plot.png"
    output_throughput = "metrics/throughput_plot.png"
    transactions = parse_log(log_file)
    latency = calculate_latency(transactions)
    experiment_time = (max(timestamp for tx_list in transactions.values() for _, timestamp in tx_list) -
                       min(timestamp for tx_list in transactions.values() for _, timestamp in tx_list)).total_seconds()
    throughput = calculate_throughput(transactions, experiment_time)
    plot_latency(latency, output_latency)
    plot_throughput(transactions, experiment_time, output_throughput)
