import signal
import subprocess
import sys
import time

INTERFACE = "eth0"

# Declare network standards as variables
GPRS = {
    "name": "GPRS",
    "delay": "1000ms",
    "loss": "50%",
    "rate": "0.1Mbit",
    "duration": 10,
}

EDGE = {
    "name": "EDGE",
    "delay": "800ms",
    "loss": "40%",
    "rate": "0.1Mbit",
    "duration": 10,
}

THREE_G = {
    "name": "3G",
    "delay": "600ms",
    "loss": "30%",
    "rate": "0.1Mbit",
    "duration": 10,
}
HSPA = {
    "name": "HSPA",
    "delay": "200ms",
    "loss": "10%",
    "rate": "1.5Mbit",
    "duration": 10,
}
DC_HSPA_PLUS = {
    "name": "DC-HSPA+",
    "delay": "100ms",
    "loss": "5%",
    "rate": "4Mbit",
    "duration": 10,
}
DC_HSPA_PLUS_42 = {
    "name": "DC-HSPA+42",
    "delay": "80ms",
    "loss": "5%",
    "rate": "8Mbit",
    "duration": 10,
}
LTE_CAT4 = {
    "name": "LTE Cat4",
    "delay": "50ms",
    "loss": "5%",
    "rate": "30Mbit",
    "duration": 10,
}
LTE_ADV_CAT6 = {
    "name": "LTE-Advanced Cat6",
    "delay": "40ms",
    "loss": "1%",
    "rate": "40Mbit",
    "duration": 10,
}
LTE_ADV_CAT9 = {
    "name": "LTE-Advanced Cat9",
    "delay": "40ms",
    "loss": "1%",
    "rate": "45Mbit",
    "duration": 10,
}
LTE_ADV_CAT12 = {
    "name": "LTE-Advanced Cat12",
    "delay": "40ms",
    "loss": "1%",
    "rate": "60Mbit",
    "duration": 10,
}
LTE_ADV_CAT16 = {
    "name": "LTE-Advanced Cat16",
    "delay": "30ms",
    "loss": "1%",
    "rate": "90Mbit",
    "duration": 10,
}
FIVE_G = {
    "name": "5G",
    "delay": "20ms",
    "loss": "1%",
    "rate": "200Mbit",
    "duration": 10,
}
NO_CONN_SMALL = {
    "name": "NO_CONN",
    "delay": "1000ms",
    "loss": "80%",
    "rate": "10kbit",
    "duration": 5,
}

NO_CONN_BIG = {
    "name": "NO_CONN",
    "delay": "1000ms",
    "loss": "90%",
    "rate": "5kbit",
    "duration": 5,
}


# Combine standards into a list of scenarios
SCENARIOS = [
    GPRS,
    EDGE,
    THREE_G,
    HSPA,
    NO_CONN_SMALL,
    DC_HSPA_PLUS,
    DC_HSPA_PLUS_42,
    LTE_CAT4,
    NO_CONN_BIG,
]


def run(cmd):
    print(f"$ {cmd}")
    subprocess.run(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def clear_qdisc():
    run(f"tc qdisc del dev {INTERFACE} root || true")


def setup_initial_qdisc():
    run(f"tc qdisc add dev {INTERFACE} root netem")


def change_netem(delay, loss, rate):
    run(
        f"tc qdisc change dev {INTERFACE} root netem delay {delay} loss {loss} rate {rate}"
    )


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
                f"\n🟢 Scenario: {scenario['name']} "
                f"(delay={scenario['delay']}, loss={scenario['loss']}, rate={scenario['rate']})"
            )
            change_netem(scenario["delay"], scenario["loss"], scenario["rate"])
            time.sleep(scenario["duration"])


if __name__ == "__main__":
    main()
