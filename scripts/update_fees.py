import requests
import json
import os
from datetime import datetime, timezone

def fetch_dex_data():
    """Fetch DEX volume data from DefiLlama API"""
    url = "https://api.llama.fi/overview/dexs?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=true"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching DEX data: {e}")
        return None
    
    protocols = data.get("protocols", [])
    
    # Process and sort by 24h volume (descending)
    processed = []
    for p in protocols:
        total_24h = p.get("total24h")
        total_7d = p.get("total7d")
        total_30d = p.get("total30d")
        total_all_time = p.get("totalAllTime")
        change_1d = p.get("change_1d")
        change_7d = p.get("change_7d")
        change_1m = p.get("change_1m")
        
        # Skip DEXs with no 24h data
        if total_24h is None or total_24h == 0:
            continue
        
        processed.append({
            "name": p.get("name", "Unknown"),
            "displayName": p.get("displayName", p.get("name", "Unknown")),
            "logo": p.get("logo", ""),
            "category": p.get("category", "DEX"),
            "chains": p.get("chains", []),
            "total24h": round(total_24h, 2) if total_24h else 0,
            "total7d": round(total_7d, 2) if total_7d else 0,
            "total30d": round(total_30d, 2) if total_30d else 0,
            "totalAllTime": round(total_all_time, 2) if total_all_time else 0,
            "change1d": round(change_1d, 2) if change_1d else None,
            "change7d": round(change_7d, 2) if change_7d else None,
            "change1m": round(change_1m, 2) if change_1m else None,
            "slug": p.get("slug", ""),
            "methodology": p.get("methodology", {}),
        })
    
    # Sort by 24h volume descending
    processed.sort(key=lambda x: x["total24h"], reverse=True)
    
    # Take top 50
    top_dexs = processed[:50]
    
    # Calculate market share for top 10
    total_volume_top10 = sum(d["total24h"] for d in top_dexs[:10])
    for d in top_dexs[:10]:
        d["marketShare"] = round((d["total24h"] / total_volume_top10) * 100, 1) if total_volume_top10 > 0 else 0
    
    # Build output
    now_utc = datetime.now(timezone.utc)
    output = {
        "lastUpdated": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lastUpdatedKST": (now_utc.replace(hour=(now_utc.hour + 9) % 24)).strftime("%Y-%m-%d %H:%M KST"),
        "totalDexs": len(processed),
        "dexs": top_dexs,
        "summary": {
            "top1_name": top_dexs[0]["name"] if top_dexs else "",
            "top1_24h": top_dexs[0]["total24h"] if top_dexs else 0,
            "top3": [{"name": d["name"], "volume": d["total24h"], "change": d["change1d"]} for d in top_dexs[:3]],
            "total_24h_all": round(sum(d["total24h"] for d in processed), 2),
        }
    }
    
    return output


def main():
    print("Fetching DEX volume data from DefiLlama...")
    
    data = fetch_dex_data()
    if not data:
        print("Failed to fetch data. Exiting.")
        return
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Save to JSON
    output_path = os.path.join("data", "dexs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(data['dexs'])} DEXs to {output_path}")
    print(f"Top DEX: {data['summary']['top1_name']} — ${data['summary']['top1_24h']:,.0f} (24h volume)")
    print(f"Total 24h volume (all DEXs): ${data['summary']['total_24h_all']:,.0f}")
    print(f"Last updated: {data['lastUpdatedKST']}")


if __name__ == "__main__":
    main()
