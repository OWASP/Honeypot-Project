import os
import time
import requests

print("=======================================", flush=True)
print("🕵️  CHAMELEON EVASION LOOP ONLINE 🕵️", flush=True)
print("=======================================", flush=True)

# Get the API key from the Docker environment
SHODAN_API_KEY = os.environ.get("SHODAN_API_KEY")

def get_public_ip():
    """Dynamically fetches the AWS Public IP of the current instance."""
    try:
        return requests.get("https://api.ipify.org", timeout=5).text
    except Exception as e:
        print(f"[!] Could not determine public IP: {e}", flush=True)
        return None

def check_shodan():
    # Check against the exact dummy value in your .env.example
    if not SHODAN_API_KEY or SHODAN_API_KEY == "your_shodan_api_key_here":
        print("[!] No valid Shodan API Key found. Skipping evasion check.", flush=True)
        return

    HONEYPOT_IP = get_public_ip()
    if not HONEYPOT_IP:
        return

    print(f"[*] Querying Shodan API for our public IP: {HONEYPOT_IP}...", flush=True)
    url = f"https://api.shodan.io/shodan/host/{HONEYPOT_IP}?key={SHODAN_API_KEY}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            tags = data.get("tags", [])

            if "honeypot" in tags:
                print("\n[!!!] CRITICAL ALERT: SHODAN HAS BURNED OUR IDENTITY! [!!!]", flush=True)
                print("[*] The 'honeypot' tag was detected on our public IP.", flush=True)
                print("[*] Triggering automated AWS Elastic IP rotation sequence...", flush=True)
            else:
                print("[*] Coast is clear. No honeypot tags detected.", flush=True)

        elif response.status_code == 404:
            print("[*] IP not indexed by Shodan yet. We are completely hidden.", flush=True)
        else:
            print(f"[!] Shodan API returned status {response.status_code}", flush=True)

    except Exception as e:
        print(f"[!] Failed to connect to Shodan API: {e}", flush=True)

if __name__ == "__main__":
    while True:
        check_shodan()
        # Sleep for 60 minutes before checking again to save API credits
        print("[*] Sleeping for 60 minutes...", flush=True)
        time.sleep(3600)
