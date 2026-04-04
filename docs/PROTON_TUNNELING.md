# Proton WARP+ Tunneling
# =================================

## Setup

```bash
# 1. Install Proton WARP+ relay
git clone https://github.com/protonwarp/proton-relay
cd proton-relay
cargo run

# 2. Configure relay
cp config.toml.example config.toml
nano config.toml  # Set WARP_SECRET_KEY

# 3. Add tunnel to server config
echo "WARP_RELAY_URL=warp://example.com" >> /config/tunnel.conf

# 4. Start
./setup.sh
```

## Usage

1. Open Proton WARP+ app on phone
2. Generate relay session
3. Copy session URL to web interface
4. Chat with Pi AI!
