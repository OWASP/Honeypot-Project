#!/usr/bin/env python3
"""
deploy_fleet.py  --  provisioning wrapper for the OWASP Honeypot multi-region fleet.

Wraps the Terraform module in this directory into a single validated command.
Checks every prerequisite before touching any infrastructure, shows a projected
monthly cost estimate, and provisions all three regions (eu-west-1, us-east-1,
ap-south-1) in one terraform apply via provider aliases.

Usage:
    # Full deployment (prompts for confirmation)
    python deploy_fleet.py \\
        --key-name honeypot-key \\
        --logstash-host 10.0.0.5:5044 \\
        --shodan-api-key XXXX

    # Plan only -- no infrastructure created
    python deploy_fleet.py --dry-run \\
        --key-name honeypot-key \\
        --logstash-host 10.0.0.5:5044 \\
        --shodan-api-key XXXX

    # Destroy existing fleet
    python deploy_fleet.py --destroy --yes

    # Skip confirmation prompt (CI/CD usage)
    python deploy_fleet.py --yes \\
        --key-name honeypot-key \\
        --logstash-host 10.0.0.5:5044 \\
        --shodan-api-key XXXX

Secrets (logstash-host, shodan-api-key) can also be supplied via environment
variables to avoid them appearing in shell history:
    export TF_VAR_logstash_host="10.0.0.5:5044"
    export TF_VAR_shodan_api_key="XXXX"
    python deploy_fleet.py --key-name honeypot-key

Prerequisites:
    - terraform >= 1.5 on PATH
    - aws CLI on PATH
    - Active AWS credentials (profile or environment variables)
    - EC2 key pair named with --key-name in every target region
    - S3 bucket for Terraform state (created automatically on first run)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TERRAFORM_DIR = Path(__file__).parent.resolve()
STATE_BUCKET = "owasp-honeypot-tfstate"
STATE_BUCKET_REGION = "eu-west-1"

# Regions defined in providers.tf / main.tf
FLEET_REGIONS = ["eu-west-1", "us-east-1", "ap-south-1"]

# Per-node monthly cost estimate (us-east-1 on-demand, August 2026 pricing).
# Other regions are within ~20% of these figures.
# Elastic IP is free while associated with a running instance.
_COSTS = {
    "EC2 t3.medium (730 hrs)": 30.37,
    "EBS gp3 30 GB":            2.40,
    "Data transfer (est.)":     1.50,
}
MONTHLY_COST_PER_NODE = sum(_COSTS.values())

MIN_TF_VERSION = (1, 5, 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd, env=None, capture=False, cwd=None):
    """Run a subprocess. Returns CompletedProcess. Never raises on non-zero exit."""
    return subprocess.run(
        cmd,
        env=env or os.environ.copy(),
        capture_output=capture,
        text=True,
        cwd=str(cwd or TERRAFORM_DIR),
    )


def _banner(msg):
    width = 62
    print()
    print("=" * width)
    print(f"  {msg}")
    print("=" * width)


def _ok(msg):
    print(f"  [OK]  {msg}")


def _fail(msg):
    print(f"  [!!]  {msg}")


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------

def _check_terraform():
    """Verify terraform is installed and meets the minimum version."""
    if not shutil.which("terraform"):
        return "terraform is not on PATH. Install from https://developer.hashicorp.com/terraform/downloads"

    result = _run(["terraform", "version", "-json"], capture=True)
    if result.returncode != 0:
        return "Could not determine terraform version."

    try:
        data = json.loads(result.stdout)
        raw = data.get("terraform_version", "")
        # Parse "1.9.3" style version strings
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", raw)
        if not match:
            return f"Could not parse terraform version string: {raw!r}"
        version = tuple(int(x) for x in match.groups())
        if version < MIN_TF_VERSION:
            needed = ".".join(str(x) for x in MIN_TF_VERSION)
            return (
                f"terraform {raw} is too old. This module requires >= {needed}. "
                "Upgrade from https://developer.hashicorp.com/terraform/downloads"
            )
    except (json.JSONDecodeError, KeyError):
        return "Could not parse terraform version JSON output."

    return None  # no error


def _check_aws_cli():
    if not shutil.which("aws"):
        return "aws CLI is not on PATH. Install from https://aws.amazon.com/cli/"
    return None


def _check_aws_credentials(profile):
    env = os.environ.copy()
    cmd = ["aws", "sts", "get-caller-identity", "--output", "json"]
    if profile and profile != "default":
        cmd += ["--profile", profile]
    result = _run(cmd, env=env, capture=True)
    if result.returncode != 0:
        return (
            "AWS credentials are not configured or have expired. "
            "Run 'aws configure' or set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY."
        )
    return None


def _check_key_pair(key_name, profile):
    """Verify the EC2 key pair exists in every fleet region."""
    errors = []
    for region in FLEET_REGIONS:
        cmd = [
            "aws", "ec2", "describe-key-pairs",
            "--key-names", key_name,
            "--region", region,
            "--output", "json",
        ]
        if profile and profile != "default":
            cmd += ["--profile", profile]
        result = _run(cmd, capture=True)
        if result.returncode != 0:
            errors.append(
                f"Key pair '{key_name}' not found in {region}. "
                "Create it in the AWS EC2 console and download the .pem file."
            )
    return errors


def _check_or_create_state_bucket(profile, dry_run):
    """Verify the S3 state bucket exists; create it on first run if not."""
    cmd = ["aws", "s3api", "head-bucket", "--bucket", STATE_BUCKET]
    if profile and profile != "default":
        cmd += ["--profile", profile]
    result = _run(cmd, capture=True)

    if result.returncode == 0:
        return None  # bucket already exists

    if dry_run:
        return (
            f"S3 state bucket '{STATE_BUCKET}' does not exist. "
            "It will be created on the first real deployment. "
            "(Skipped in dry-run mode.)"
        )

    print(f"\n  State bucket '{STATE_BUCKET}' does not exist. Creating it now...")
    create_cmd = [
        "aws", "s3api", "create-bucket",
        "--bucket", STATE_BUCKET,
        "--region", STATE_BUCKET_REGION,
        "--create-bucket-configuration", f"LocationConstraint={STATE_BUCKET_REGION}",
    ]
    if profile and profile != "default":
        create_cmd += ["--profile", profile]

    create_result = _run(create_cmd, capture=True)
    if create_result.returncode != 0:
        return (
            f"Could not create S3 state bucket '{STATE_BUCKET}': "
            f"{create_result.stderr.strip()}"
        )

    # Enable versioning so state history is recoverable
    _run([
        "aws", "s3api", "put-bucket-versioning",
        "--bucket", STATE_BUCKET,
        "--versioning-configuration", "Status=Enabled",
    ], capture=True)

    print(f"  Bucket '{STATE_BUCKET}' created in {STATE_BUCKET_REGION}.")
    return None


def run_prerequisite_checks(args):
    """Run all prerequisite checks. Returns a list of error strings."""
    errors = []

    err = _check_terraform()
    if err:
        errors.append(err)
    else:
        _ok("terraform >= 1.5 found")

    err = _check_aws_cli()
    if err:
        errors.append(err)
    else:
        _ok("aws CLI found")

    err = _check_aws_credentials(args.aws_profile)
    if err:
        errors.append(err)
    else:
        _ok("AWS credentials valid")

    # Key pair check only needed when provisioning
    if not args.destroy and args.key_name:
        key_errors = _check_key_pair(args.key_name, args.aws_profile)
        if key_errors:
            errors.extend(key_errors)
        else:
            _ok(f"Key pair '{args.key_name}' found in all regions")

    err = _check_or_create_state_bucket(args.aws_profile, args.dry_run)
    if err:
        # For dry-run this is a warning, not a fatal error
        if args.dry_run:
            print(f"\n  [--]  {err}")
        else:
            errors.append(err)
    else:
        _ok(f"S3 state bucket '{STATE_BUCKET}' ready")

    return errors


# ---------------------------------------------------------------------------
# Cost estimate
# ---------------------------------------------------------------------------

def show_cost_estimate():
    _banner("Projected Monthly Cost Estimate")
    print()
    print(f"  Per-node breakdown ({len(FLEET_REGIONS)} nodes total):")
    print()
    for label, cost in _COSTS.items():
        print(f"    {label:<35} ${cost:.2f}")
    print(f"    {'':35} ------")
    print(f"    {'Per node':<35} ${MONTHLY_COST_PER_NODE:.2f}")
    total = MONTHLY_COST_PER_NODE * len(FLEET_REGIONS)
    print()
    print(f"  Regions: {', '.join(FLEET_REGIONS)}")
    print(f"  Fleet total: ${total:.2f}/month")
    print()
    print("  Notes:")
    print("  - Based on us-east-1 on-demand rates. Other regions vary by up to 20%.")
    print("  - Elastic IP is free while attached to a running instance.")
    print("  - Data transfer estimate assumes typical honeypot log volumes.")
    print()


# ---------------------------------------------------------------------------
# Terraform operations
# ---------------------------------------------------------------------------

def _build_tf_env(args):
    """Build environment dict with TF_VAR_ secrets and AWS profile."""
    env = os.environ.copy()
    if args.aws_profile and args.aws_profile != "default":
        env["AWS_PROFILE"] = args.aws_profile
    if args.logstash_host:
        env["TF_VAR_logstash_host"] = args.logstash_host
    if args.shodan_api_key:
        env["TF_VAR_shodan_api_key"] = args.shodan_api_key
    if args.key_name:
        env["TF_VAR_key_name"] = args.key_name
    if args.admin_cidr:
        env["TF_VAR_admin_cidr"] = args.admin_cidr
    return env


def tf_init(env):
    """Run terraform init."""
    print("\n  Running terraform init...")
    result = _run(["terraform", "init", "-input=false"], env=env)
    return result.returncode == 0


def tf_plan(env, plan_file):
    """Run terraform plan. Returns (success, has_changes)."""
    print("\n  Running terraform plan...")
    result = _run(
        ["terraform", "plan", "-input=false", f"-out={plan_file}"],
        env=env,
    )
    if result.returncode != 0:
        return False, False
    # Exit code 2 means changes present; 0 means no changes
    return True, True


def tf_apply(env, plan_file):
    """Apply the saved plan."""
    print("\n  Running terraform apply...")
    result = _run(
        ["terraform", "apply", "-input=false", str(plan_file)],
        env=env,
    )
    return result.returncode == 0


def tf_destroy(env, yes):
    """Destroy the fleet."""
    print("\n  Running terraform destroy...")
    cmd = ["terraform", "destroy", "-input=false"]
    if yes:
        cmd.append("-auto-approve")
    result = _run(cmd, env=env)
    return result.returncode == 0


def tf_output(env):
    """Read terraform outputs as a dict."""
    result = _run(
        ["terraform", "output", "-json"],
        env=env,
        capture=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def show_deployment_summary(outputs):
    _banner("Fleet Deployment Summary")
    print()

    elastic_ips  = outputs.get("fleet_elastic_ips",   {}).get("value", {})
    instance_ids = outputs.get("fleet_instance_ids",  {}).get("value", {})
    public_dns   = outputs.get("fleet_public_dns",    {}).get("value", {})

    if not elastic_ips:
        print("  No output data found. Check the state file or run 'terraform output'.")
        return

    col_w = 24
    print(f"  {'Region':<{col_w}} {'Elastic IP':<18} {'Instance ID':<22} Public DNS")
    print(f"  {'-'*col_w} {'-'*18} {'-'*22} {'-'*45}")
    for region in FLEET_REGIONS:
        eip  = elastic_ips.get(region,  "n/a")
        iid  = instance_ids.get(region, "n/a")
        dns  = public_dns.get(region,   "n/a")
        print(f"  {region:<{col_w}} {eip:<18} {iid:<22} {dns}")

    print()
    total = MONTHLY_COST_PER_NODE * len(FLEET_REGIONS)
    print(f"  Estimated monthly cost: ${total:.2f}")
    print()
    print("  Each node:")
    print("  - Filebeat ships ModSecurity logs to your central Logstash host")
    print("  - persona_watchdog.py uses the Elastic IP for Shodan registration")
    print("  - Rotation logs: /home/ubuntu/honeypot/honeytraps/rotation_log.jsonl")
    print()
    print(f"  To destroy: python {Path(__file__).name} --destroy --yes")
    print()


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "deploy_fleet.py  --  provision the OWASP Honeypot multi-region fleet.\n\n"
            "Secrets (--logstash-host, --shodan-api-key) can also be supplied via\n"
            "TF_VAR_logstash_host and TF_VAR_shodan_api_key environment variables."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--key-name",
        help="EC2 key pair name (must exist in every target region).",
    )
    parser.add_argument(
        "--admin-cidr",
        default="0.0.0.0/0",
        help="CIDR allowed SSH access. Restrict to your IP in production (default: 0.0.0.0/0).",
    )
    parser.add_argument(
        "--logstash-host",
        help="host:port of the central Logstash instance, e.g. '10.0.0.5:5044'. "
             "Can also be set via TF_VAR_logstash_host.",
    )
    parser.add_argument(
        "--shodan-api-key",
        help="Shodan API key for persona_watchdog.py. "
             "Can also be set via TF_VAR_shodan_api_key.",
    )
    parser.add_argument(
        "--aws-profile",
        default="default",
        help="AWS CLI profile (default: 'default').",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run terraform plan only. No infrastructure is created or modified.",
    )
    parser.add_argument(
        "--destroy",
        action="store_true",
        help="Destroy the entire fleet. Prompts for confirmation unless --yes is set.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip all confirmation prompts (for CI/CD usage).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # Pull secrets from environment if not passed as flags
    if not args.logstash_host:
        args.logstash_host = os.environ.get("TF_VAR_logstash_host")
    if not args.shodan_api_key:
        args.shodan_api_key = os.environ.get("TF_VAR_shodan_api_key")

    _banner("OWASP Honeypot Fleet Provisioner")
    print(f"\n  Terraform dir : {TERRAFORM_DIR}")
    print(f"  Fleet regions : {', '.join(FLEET_REGIONS)}")
    mode = "destroy" if args.destroy else "dry-run (plan only)" if args.dry_run else "apply"
    print(f"  Mode          : {mode}")
    if args.key_name:
        print(f"  Key pair      : {args.key_name}")
    if args.logstash_host:
        print(f"  Logstash host : {args.logstash_host}")
    print()

    # --- Validate required variables ---
    if not args.destroy:
        missing = []
        if not args.key_name:
            missing.append(
                "--key-name is required. "
                "The EC2 key pair must already exist in every target region."
            )
        if not args.logstash_host:
            missing.append(
                "--logstash-host is required (or set TF_VAR_logstash_host). "
                "Format: 'host:port', e.g. '10.0.0.5:5044'."
            )
        if not args.shodan_api_key:
            missing.append(
                "--shodan-api-key is required (or set TF_VAR_shodan_api_key). "
                "Get a free key at https://account.shodan.io"
            )
        if missing:
            print("Error: missing required arguments:\n")
            for m in missing:
                print(f"  - {m}")
            print()
            sys.exit(1)

    # --- Prerequisites ---
    _banner("Checking Prerequisites")
    print()
    errors = run_prerequisite_checks(args)
    if errors:
        print("\nPrerequisite check failed:\n")
        for err in errors:
            _fail(err)
        print()
        sys.exit(1)
    print("\n  All prerequisites met.")

    # --- Destroy path ---
    if args.destroy:
        if not args.yes:
            answer = input(
                "\n  This will DESTROY the entire honeypot fleet. "
                "This cannot be undone.\n  Type 'yes' to confirm: "
            )
            if answer.strip().lower() != "yes":
                print("  Aborted.")
                sys.exit(0)
        env = _build_tf_env(args)
        if not tf_init(env):
            print("\n  terraform init failed. Aborting.")
            sys.exit(1)
        ok = tf_destroy(env, yes=True)
        if not ok:
            print("\n  terraform destroy failed. Check the output above.")
            sys.exit(1)
        print("\n  Fleet destroyed.\n")
        return

    # --- Cost estimate ---
    show_cost_estimate()
    if not args.dry_run and not args.yes:
        answer = input("  Proceed with deployment? [yes/no]: ")
        if answer.strip().lower() != "yes":
            print("  Aborted.")
            sys.exit(0)

    env = _build_tf_env(args)
    plan_file = TERRAFORM_DIR / "fleet.tfplan"

    # --- Init ---
    _banner("Initialising Terraform")
    if not tf_init(env):
        print("\n  terraform init failed. Aborting.")
        sys.exit(1)

    # --- Plan ---
    _banner("Planning")
    ok, _ = tf_plan(env, plan_file)
    if not ok:
        print("\n  terraform plan failed. Check the output above.")
        sys.exit(1)

    if args.dry_run:
        _banner("Dry-run complete")
        print()
        print("  Plan succeeded. No infrastructure was created or modified.")
        print(f"  Saved plan: {plan_file}")
        print()
        return

    # --- Apply ---
    _banner("Applying")
    ok = tf_apply(env, plan_file)
    if not ok:
        print("\n  terraform apply failed. Check the output above.")
        sys.exit(1)

    # Clean up the plan file
    try:
        plan_file.unlink()
    except FileNotFoundError:
        pass

    # --- Summary ---
    outputs = tf_output(env)
    show_deployment_summary(outputs)


if __name__ == "__main__":
    main()
