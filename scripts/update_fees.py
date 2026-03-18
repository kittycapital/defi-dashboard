import requests
import json
import os
from datetime import datetime, timezone, timedelta

def fetch_fees_data():
    """Fetch protocol fees/revenue data from DefiLlama API"""
    url = "https://api.llama.fi/overview/fees?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=true"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching fees data: {e}")
        return None

    protocols = data.get("protocols", [])

    processed = []
    for p in protocols:
        total_24h = p.get("total24h")
        total_7d = p.get("total7d")
        total_30d = p.get("total30d")
        total_all_time = p.get("totalAllTime")
        change_1d = p.get("change_1d")
        change_7d = p.get("change_7d")
        change_1m = p.get("change_1m")

        if total_24h is None or total_24h == 0:
            continue

        processed.append({
            "name": p.get("name", "Unknown"),
            "displayName": p.get("displayName", p.get("name", "Unknown")),
            "logo": p.get("logo", ""),
            "category": p.get("category", ""),
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

    processed.sort(key=lambda x: x["total24h"], reverse=True)

    now_kst = datetime.now(timezone.utc) + timedelta(hours=9)
    output = {
        "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lastUpdatedKST": now_kst.strftime("%Y-%m-%d %H:%M KST"),
        "totalProtocols": len(processed),
        "protocols": processed,
    }

    return output


def main():
    print("Fetching fees/revenue data from DefiLlama...")

    data = fetch_fees_data()
    if not data:
        print("Failed to fetch data. Exiting.")
        return

    os.makedirs("data", exist_ok=True)

    output_path = os.path.join("data", "fees.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    top = data["protocols"][0] if data["protocols"] else None
    print(f"Saved {data['totalProtocols']} protocols to {output_path}")
    if top:
        print(f"Top protocol: {top['name']} — ${top['total24h']:,.0f} (24h fees)")
    print(f"Last updated: {data['lastUpdatedKST']}")


if __name__ == "__main__":
    main()
