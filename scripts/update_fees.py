import requests
import json
import os
from datetime import datetime, timezone

def fetch_fees_data():
    """Fetch fee/revenue data from DefiLlama API"""
    url = "https://api.llama.fi/overview/fees?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=true"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching fees data: {e}")
        return None
    
    protocols = data.get("protocols", [])
    
    # Process and sort by 24h revenue (descending)
    processed = []
    for p in protocols:
        # Extract revenue fields
        total_24h = p.get("total24h")
        total_7d = p.get("total7d")
        total_30d = p.get("total30d")
        total_all_time = p.get("totalAllTime")
        
        # Skip protocols with no 24h data
        if total_24h is None or total_24h == 0:
            continue
        
        # Calculate 7d daily average for trend comparison
        avg_7d = (total_7d / 7) if total_7d and total_7d > 0 else None
        trend = None
        if avg_7d and avg_7d > 0:
            trend = round(((total_24h - avg_7d) / avg_7d) * 100, 1)
        
        processed.append({
            "name": p.get("name", "Unknown"),
            "logo": p.get("logo", ""),
            "category": p.get("category", ""),
            "chains": p.get("chains", []),
            "total24h": round(total_24h, 2) if total_24h else 0,
            "total7d": round(total_7d, 2) if total_7d else 0,
            "total30d": round(total_30d, 2) if total_30d else 0,
            "totalAllTime": round(total_all_time, 2) if total_all_time else 0,
            "trend": trend,  # % change vs 7d avg
            "module": p.get("module", ""),
            "slug": p.get("slug", ""),
        })
    
    # Sort by 24h revenue descending
    processed.sort(key=lambda x: x["total24h"], reverse=True)
    
    # Take top 50 (show 20 by default, but have extra for filtering)
    top_protocols = processed[:50]
    
    # Build output
    now_utc = datetime.now(timezone.utc)
    output = {
        "lastUpdated": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lastUpdatedKST": (now_utc.replace(hour=(now_utc.hour + 9) % 24)).strftime("%Y-%m-%d %H:%M KST"),
        "totalProtocols": len(processed),
        "protocols": top_protocols,
        "summary": {
            "top1_name": top_protocols[0]["name"] if top_protocols else "",
            "top1_24h": top_protocols[0]["total24h"] if top_protocols else 0,
            "total_24h_top20": round(sum(p["total24h"] for p in top_protocols[:20]), 2),
        }
    }
    
    return output


def main():
    print("Fetching DeFi fee/revenue data from DefiLlama...")
    
    data = fetch_fees_data()
    if not data:
        print("Failed to fetch data. Exiting.")
        return
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Save to JSON
    output_path = os.path.join("data", "fees.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(data['protocols'])} protocols to {output_path}")
    print(f"Top protocol: {data['summary']['top1_name']} — ${data['summary']['top1_24h']:,.0f} (24h)")
    print(f"Top 20 combined 24h: ${data['summary']['total_24h_top20']:,.0f}")
    print(f"Last updated: {data['lastUpdatedKST']}")


if __name__ == "__main__":
    main()
