import argparse
import subprocess
import sys

INTERFACE = "eth0"


def run(cmd):
    print(f"$ {cmd}")
    subprocess.run(
        cmd,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=False,
    )


def clear_qdisc():
    run(f"tc qdisc del dev {INTERFACE} root")


def apply_netem(delay_ms, jitter_ms, loss_percent, rate_kbit):
    # Apply netem + tbf for realistic mobile network behavior
    run(
        f"tc qdisc add dev {INTERFACE} root handle 1: netem "
        f"delay {delay_ms}ms {jitter_ms}ms loss {loss_percent}%"
    )
    run(
        f"tc qdisc add dev {INTERFACE} parent 1: handle 10: "
        f"tbf rate {rate_kbit}kbit burst 1600 latency 200ms"
    )


def main():
    parser = argparse.ArgumentParser(description="Simulate poor LTE conditions on eth0")
    parser.add_argument(
        "--delay", type=int, default=400, help="Base delay in ms (default: 400)"
    )
    parser.add_argument(
        "--jitter", type=int, default=100, help="Jitter in ms (default: 100)"
    )
    parser.add_argument(
        "--loss", type=float, default=15.0, help="Packet loss percentage (default: 15)"
    )
    parser.add_argument(
        "--rate", type=int, default=10, help="Rate limit in kbit/s (default: 10)"
    )

    args = parser.parse_args()

    clear_qdisc()
    apply_netem(args.delay, args.jitter, args.loss, args.rate)

    print(
        f"✅ Simulating: {args.delay}ms ±{args.jitter}ms delay, "
        f"{args.loss}% loss, {args.rate} kbit/s bandwidth on {INTERFACE}"
    )


if __name__ == "__main__":
    main()
