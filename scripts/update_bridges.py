import requests
import json
import os
from datetime import datetime, timezone

def fetch_chain_tvl_data():
    """
    Fetch chain TVL data from DefiLlama free API.
    Note: Bridge-specific endpoints require Pro API key, so we use chain TVL as proxy.
    """
    chains_url = "https://api.llama.fi/v2/chains"
    
    try:
        response = requests.get(chains_url, timeout=30)
        response.raise_for_status()
        chains_data = response.json()
    except Exception as e:
        print(f"Error fetching chain data: {e}")
        return None
    
    # Process chains - filter to major ones with significant TVL
    processed_chains = []
    for c in chains_data:
        tvl = c.get("tvl", 0)
        if tvl and tvl > 100000000:  # Only chains with >$100M TVL
            processed_chains.append({
                "chain": c.get("name", "Unknown"),
                "tvl": round(tvl, 2),
                "tokenSymbol": c.get("tokenSymbol", ""),
                "chainId": c.get("chainId"),
            })
    
    # Sort by TVL
    processed_chains.sort(key=lambda x: x["tvl"], reverse=True)
    
    # Calculate 7d TVL change by fetching historical data
    chain_flows = calculate_chain_flows(processed_chains[:20])
    
    # Build output
    now_utc = datetime.now(timezone.utc)
    output = {
        "lastUpdated": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lastUpdatedKST": (now_utc.replace(hour=(now_utc.hour + 9) % 24)).strftime("%Y-%m-%d %H:%M KST"),
        "totalChains": len(processed_chains),
        "bridges": [],  # Bridge data requires Pro API
        "chainFlows": chain_flows,
        "summary": {
            "top1_name": chain_flows[0]["chain"] if chain_flows else "",
            "top1_tvl": chain_flows[0]["tvl"] if chain_flows else 0,
            "total_tvl": round(sum(c["tvl"] for c in chain_flows), 2),
            "note": "Bridge volume data requires DefiLlama Pro API"
        }
    }
    
    return output


def calculate_chain_flows(chains):
    """
    Fetch historical TVL for each chain to calculate 7d change.
    This gives us a proxy for capital flow direction.
    """
    chain_flows = []
    
    for chain_info in chains:
        chain_name = chain_info["chain"]
        current_tvl = chain_info["tvl"]
        
        # Fetch historical TVL for this chain
        try:
            hist_url = f"https://api.llama.fi/v2/historicalChainTvl/{chain_name}"
            resp = requests.get(hist_url, timeout=15)
            
            if resp.status_code == 200:
                hist_data = resp.json()
                
                if hist_data and len(hist_data) >= 7:
                    # Get TVL from 7 days ago
                    tvl_7d_ago = hist_data[-7].get("tvl", current_tvl) if len(hist_data) >= 7 else current_tvl
                    
                    # Calculate net flow (TVL change)
                    net_flow = current_tvl - tvl_7d_ago
                    flow_direction = "inflow" if net_flow >= 0 else "outflow"
                    
                    chain_flows.append({
                        "chain": chain_name,
                        "tvl": current_tvl,
                        "tvl7dAgo": round(tvl_7d_ago, 2),
                        "netFlow7d": round(net_flow, 2),
                        "flowDirection": flow_direction,
                        "change7dPct": round((net_flow / tvl_7d_ago) * 100, 2) if tvl_7d_ago > 0 else 0
                    })
                else:
                    # No historical data, just add current TVL
                    chain_flows.append({
                        "chain": chain_name,
                        "tvl": current_tvl,
                        "tvl7dAgo": current_tvl,
                        "netFlow7d": 0,
                        "flowDirection": "neutral",
                        "change7dPct": 0
                    })
            else:
                # API failed, add with current data only
                chain_flows.append({
                    "chain": chain_name,
                    "tvl": current_tvl,
                    "netFlow7d": 0,
                    "flowDirection": "neutral"
                })
                
        except Exception as e:
            print(f"  Warning: Could not fetch history for {chain_name}: {e}")
            chain_flows.append({
                "chain": chain_name,
                "tvl": current_tvl,
                "netFlow7d": 0,
                "flowDirection": "neutral"
            })
    
    # Sort by TVL
    chain_flows.sort(key=lambda x: x["tvl"], reverse=True)
    
    return chain_flows[:15]


def main():
    print("Fetching chain TVL data from DefiLlama...")
    print("Note: Bridge volume endpoints require Pro API key")
    
    data = fetch_chain_tvl_data()
    if not data:
        print("Failed to fetch data. Exiting.")
        return
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Save to JSON
    output_path = os.path.join("data", "bridges.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(data['chainFlows'])} chains to {output_path}")
    print(f"Top chain by TVL: {data['summary']['top1_name']} — ${data['summary']['top1_tvl']:,.0f}")
    print(f"Total TVL tracked: ${data['summary']['total_tvl']:,.0f}")
    print(f"Last updated: {data['lastUpdatedKST']}")


if __name__ == "__main__":
    main()
