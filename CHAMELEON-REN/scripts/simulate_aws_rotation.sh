#!/bin/bash
# --- CHAMELEON-REN: Live AWS Elastic IP Rotation ---

echo "[*] INITIATING EVASION PROTOCOL: Rotating AWS Elastic IP..."

# 1. Get the current EC2 Instance ID using the AWS metadata service
INSTANCE_ID="i-0f6423de97edd4fa2"
if [ -z "$INSTANCE_ID" ]; then
    echo "[!] ERROR: Could not fetch Instance ID. Are we running on AWS?"
    exit 1
fi
echo "[*] Current Instance ID: $INSTANCE_ID"

# 2. Find the currently attached Elastic IP Allocation ID
OLD_ALLOC_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].NetworkInterfaces[0].Association.AllocationId' --output text)

# 3. Allocate a brand new Elastic IP
echo "[*] Allocating new AWS Elastic IP..."
ALLOCATION_RESULT=$(aws ec2 allocate-address --domain vpc --output json)
NEW_ALLOC_ID=$(echo $ALLOCATION_RESULT | grep -oP '"AllocationId": "\K[^"]+')
NEW_IP=$(echo $ALLOCATION_RESULT | grep -oP '"PublicIp": "\K[^"]+')

# 4. Associate the new IP to this EC2 Instance
echo "[*] Associating new IP ($NEW_IP) to Instance $INSTANCE_ID..."
aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $NEW_ALLOC_ID

# 5. Release the burned IP back to AWS (so you don't get billed for it!)
if [ "$OLD_ALLOC_ID" != "None" ] && [ -n "$OLD_ALLOC_ID" ]; then
    echo "[*] Releasing burned IP allocation ($OLD_ALLOC_ID)..."
    aws ec2 release-address --allocation-id $OLD_ALLOC_ID
fi

echo "[*] EVASION COMPLETE. Server is now hiding behind new IP: $NEW_IP"
