import signal
import subprocess
import sys
import time

INTERFACE = "eth0"

# Define network scenarios
SCENARIOS = [
    {"name": "LTE", "delay": "50ms", "loss": "1%", "duration": 10},
    {"name": "EDGE", "delay": "1000ms", "loss": "30%", "duration": 10},
    {"name": "NO_CONN", "delay": "1000ms", "loss": "100%", "duration": 5},
]


def run(cmd):
    print(f"$ {cmd}")
    subprocess.run(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def clear_qdisc():
    run(f"tc qdisc del dev {INTERFACE} root || true")


def setup_initial_qdisc():
    run(f"tc qdisc add dev {INTERFACE} root netem")


def change_netem(delay, loss):
    run(f"tc qdisc change dev {INTERFACE} root netem delay {delay} loss {loss}")


def handle_interrupt(signum, frame):
    print("\n🧹 Interrupt received, clearing qdisc...")
    clear_qdisc()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, handle_interrupt)
    clear_qdisc()
    setup_initial_qdisc()

    print(f"🚨 Starting dynamic network simulation on {INTERFACE} (Ctrl+C to exit)")
    while True:
        for scenario in SCENARIOS:
            print(
                f"\n🟢 Scenario: {scenario['name']} ({scenario['delay']} delay, {scenario['loss']} loss)"
            )
            change_netem(scenario["delay"], scenario["loss"])
            time.sleep(scenario["duration"])


if __name__ == "__main__":
    main()
