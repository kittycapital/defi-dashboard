import requests
import json
import os
from datetime import datetime, timezone
from collections import defaultdict

def fetch_bridges_data():
    """Fetch bridge volume data from DefiLlama API"""
    url = "https://api.llama.fi/bridges?includeChains=true"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching bridges data: {e}")
        return None
    
    bridges = data.get("bridges", [])
    
    # Process bridges
    processed_bridges = []
    for b in bridges:
        vol_prev_day = b.get("lastDailyVolume")
        vol_prev_week = b.get("weeklyVolume")
        vol_prev_month = b.get("monthlyVolume")
        
        # Skip bridges with no volume
        if not vol_prev_day or vol_prev_day == 0:
            continue
        
        processed_bridges.append({
            "id": b.get("id"),
            "name": b.get("displayName", b.get("name", "Unknown")),
            "logo": b.get("icon", ""),
            "chains": b.get("chains", []),
            "destinationChain": b.get("destinationChain", ""),
            "volume24h": round(vol_prev_day, 2) if vol_prev_day else 0,
            "volume7d": round(vol_prev_week, 2) if vol_prev_week else 0,
            "volume30d": round(vol_prev_month, 2) if vol_prev_month else 0,
        })
    
    # Sort by 24h volume
    processed_bridges.sort(key=lambda x: x["volume24h"], reverse=True)
    top_bridges = processed_bridges[:30]
    
    # Fetch chain-level flow data
    chain_flows = fetch_chain_flows()
    
    # Build output
    now_utc = datetime.now(timezone.utc)
    output = {
        "lastUpdated": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lastUpdatedKST": (now_utc.replace(hour=(now_utc.hour + 9) % 24)).strftime("%Y-%m-%d %H:%M KST"),
        "totalBridges": len(processed_bridges),
        "bridges": top_bridges,
        "chainFlows": chain_flows,
        "summary": {
            "top1_name": top_bridges[0]["name"] if top_bridges else "",
            "top1_24h": top_bridges[0]["volume24h"] if top_bridges else 0,
            "total_24h": round(sum(b["volume24h"] for b in processed_bridges), 2),
            "top3_bridges": [{"name": b["name"], "volume": b["volume24h"]} for b in top_bridges[:3]],
        }
    }
    
    return output


def fetch_chain_flows():
    """Fetch per-chain bridge flow data to calculate net flows"""
    # Get list of chains first
    chains_url = "https://api.llama.fi/v2/chains"
    try:
        chains_resp = requests.get(chains_url, timeout=30)
        chains_data = chains_resp.json()
    except:
        chains_data = []
    
    # Major chains to track
    major_chains = [
        "Ethereum", "Arbitrum", "Polygon", "Optimism", "Base", 
        "BSC", "Avalanche", "Solana", "Fantom", "zkSync Era",
        "Blast", "Linea", "Scroll", "Mantle", "Manta"
    ]
    
    chain_flows = []
    
    for chain in major_chains:
        url = f"https://api.llama.fi/bridges/Ethereum/{chain}?secondChain={chain}"
        
        # Try to get bridge stats for each chain
        try:
            # Get chain TVL as proxy for activity
            chain_data = next((c for c in chains_data if c.get("name") == chain), None)
            if chain_data:
                chain_flows.append({
                    "chain": chain,
                    "tvl": round(chain_data.get("tvl", 0), 2),
                })
        except:
            continue
    
    # Sort by TVL as proxy for importance
    chain_flows.sort(key=lambda x: x.get("tvl", 0), reverse=True)
    
    return chain_flows[:15]


def fetch_detailed_bridge_flows():
    """Fetch detailed bridge flow statistics"""
    stats_url = "https://api.llama.fi/bridgedaystats/1/all"  # Last 1 day, all chains
    
    try:
        response = requests.get(stats_url, timeout=30)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    return None


def main():
    print("Fetching bridge flow data from DefiLlama...")
    
    data = fetch_bridges_data()
    if not data:
        print("Failed to fetch data. Exiting.")
        return
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Save to JSON
    output_path = os.path.join("data", "bridges.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(data['bridges'])} bridges to {output_path}")
    print(f"Top bridge: {data['summary']['top1_name']} — ${data['summary']['top1_24h']:,.0f} (24h volume)")
    print(f"Total 24h bridge volume: ${data['summary']['total_24h']:,.0f}")
    print(f"Last updated: {data['lastUpdatedKST']}")


if __name__ == "__main__":
    main()
