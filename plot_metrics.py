# from datetime import datetime
# from collections import defaultdict
# import matplotlib.pyplot as plt

# def parse_log(log_file):
#     transactions = defaultdict(list)
#     with open(log_file, 'r') as file:
#         for line in file:
#             if "received transaction" in line:
#                 parts = line.strip().split()
#                 timestamp = datetime.strptime(parts[0] + ' ' + parts[1], '%Y-%m-%d %H:%M:%S,%f')
#                 node_id = parts[7][1:-1]  # Extract node ID from the square brackets
#                 transactions[parts[7]].append((node_id, timestamp))
#     return transactions

# def calculate_latency(transactions):
#     latency = []
#     for tx_list in transactions.values():
#         for i in range(len(tx_list) - 1):
#             latency.append((tx_list[i + 1][1] - tx_list[i][1]).total_seconds())
#     return latency

# def calculate_throughput(transactions):
#     throughput = defaultdict(int)
#     for tx_list in transactions.values():
#         for tx in tx_list:
#             throughput[tx[1]] += 1
#     return throughput

# def plot_latency(latency):
#     plt.hist(latency, bins=50, color='blue', alpha=0.7)
#     plt.xlabel('Latency (seconds)')
#     plt.ylabel('Frequency')
#     plt.title('Latency Histogram')
#     plt.grid(True)
#     plt.show()

# def plot_throughput(throughput):
#     sorted_throughput = sorted(throughput.items())
#     timestamps, counts = zip(*sorted_throughput)
#     plt.plot(timestamps, counts, marker='o', linestyle='-')
#     plt.xlabel('Time')
#     plt.ylabel('Transactions per Second')
#     plt.title('Throughput Over Time')
#     plt.grid(True)
#     plt.show()

# if __name__ == "__main__":
#     log_file = "logfile.log" 
#     transactions = parse_log(log_file)
#     latency = calculate_latency(transactions)
#     throughput = calculate_throughput(transactions)
#     plot_latency(latency)
#     plot_throughput(throughput)


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
                node_id = parts[7][1:-1]  # Extract node ID from the square brackets
                transactions[parts[7]].append((node_id, timestamp))
    return transactions

def calculate_latency(transactions):
    latency = []
    for tx_list in transactions.values():
        for i in range(len(tx_list) - 1):
            latency.append((tx_list[i + 1][1] - tx_list[i][1]).total_seconds())
    return latency

def calculate_throughput(transactions):
    throughput = defaultdict(int)
    for tx_list in transactions.values():
        for tx in tx_list:
            throughput[tx[1]] += 1
    return throughput

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

'''The x-axis represents time, timestamps.
The y-axis represents the number of transactions processed per second (TPS).
Each data point on the plot represents the throughput (TPS) at a specific timestamp.
It insights into how transaction processing fluctuates.'''

def plot_throughput(throughput, output_file):
    sorted_throughput = sorted(throughput.items())
    timestamps, counts = zip(*sorted_throughput)
    plt.plot(timestamps, counts, marker='o', linestyle='-')
    plt.xlabel('Time')
    plt.ylabel('Transactions per Second')
    plt.title('Throughput Over Time')
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    log_file = "logfile.log"
    output_latency = "latency_plot.png"
    output_throughput = "throughput_plot.png"
    transactions = parse_log(log_file)
    latency = calculate_latency(transactions)
    throughput = calculate_throughput(transactions)
    plot_latency(latency, output_latency)
    plot_throughput(throughput, output_throughput)
