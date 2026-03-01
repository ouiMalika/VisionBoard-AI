#!/usr/bin/env bash
# =============================================================
#  VisionBoard AI — Oracle Cloud Always Free VM bootstrap
#  Run once on a fresh Ubuntu 22.04 ARM instance.
#
#  Usage:
#    chmod +x setup.sh && ./setup.sh
# =============================================================
set -e

echo "==> 1. Update system and install Docker"
sudo apt-get update -q
sudo apt-get install -y docker.io docker-compose-plugin git netfilter-persistent iptables-persistent

# Allow docker to run without sudo for the current user (takes effect after re-login)
sudo usermod -aG docker "$USER"

echo "==> 2. Open port 80 in the VM firewall"
# Oracle Cloud adds extra iptables rules on top of the security group.
# Port 80 must be opened in BOTH the OCI Security List (web console) AND iptables.
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save

echo "==> 3. Clone repository"
REPO_DIR="$HOME/visionboard"
if [ ! -d "$REPO_DIR" ]; then
  git clone https://github.com/ouiMalika/VisionBoard-AI "$REPO_DIR"
else
  echo "     Repo already exists at $REPO_DIR, pulling latest..."
  git -C "$REPO_DIR" pull
fi

echo "==> 4. Create .env.prod from example"
ENV_FILE="$REPO_DIR/deploy/.env.prod"
if [ ! -f "$ENV_FILE" ]; then
  cp "$REPO_DIR/deploy/.env.prod.example" "$ENV_FILE"
  echo ""
  echo "  *** ACTION REQUIRED ***"
  echo "  Edit $ENV_FILE and fill in all values before starting."
  echo "  Minimum required:"
  echo "    SECRET_KEY        — generate with: python3 -c \"import secrets; print(secrets.token_urlsafe(50))\""
  echo "    ALLOWED_HOSTS     — your VM's public IP (find it in the OCI console)"
  echo "    POSTGRES_PASSWORD — any strong password"
  echo "    AWS_* variables   — Cloudflare R2 credentials (see README)"
  echo ""
else
  echo "     .env.prod already exists, skipping."
fi

echo "==> Done. Next steps:"
echo "    1. Edit deploy/.env.prod with your credentials"
echo "    2. Open port 80 in Oracle Cloud Security List (OCI Console → Networking → VCN → Security Lists)"
echo "    3. cd $REPO_DIR/deploy && sudo docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build"
echo "    4. Visit http://YOUR_VM_IP in your browser"
