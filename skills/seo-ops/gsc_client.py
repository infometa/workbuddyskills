#!/usr/bin/env python3
"""
Google Search Console API Client

Direct API access via google-api-python-client. Token auto-refreshes on every call.

Usage as library:
    from gsc_client import GSCClient
    gsc = GSCClient()
    gsc = GSCClient(site_url="https://www.example.com/")

    # Top queries
    rows = gsc.query(dimensions=["query"], row_limit=25, days=28)

    # Page performance
    rows = gsc.query(dimensions=["page"], row_limit=100, days=7)

    # Striking distance keywords (positions 4-20)
    rows = gsc.striking_distance(days=28)

    # List all verified sites
    sites = gsc.list_sites()

Usage as CLI:
    python gsc_client.py --queries 25 --days 28
    python gsc_client.py --pages 100 --days 7
    python gsc_client.py --striking
    python gsc_client.py --sites
    python gsc_client.py --site "https://www.example.com/" --queries 10
    python gsc_client.py --raw '{"dimensions":["query","page"],"rowLimit":5}'
"""

import json, os, sys, argparse
from datetime import datetime, timedelta

# Configuration via environment variables
GSC_SITE_URL = os.environ.get("GSC_SITE_URL", "")
GSC_TOKEN_FILE = os.environ.get("GSC_TOKEN_FILE", os.path.join(os.path.dirname(__file__), ".gsc-token.json"))
GOOGLE_CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "")


class GSCClient:
    def __init__(self, site_url=None, token_file=None, creds_file=None):
        self.site_url = site_url or GSC_SITE_URL
        if not self.site_url:
            raise ValueError(
                "GSC site URL required. Set GSC_SITE_URL env var or pass site_url parameter.\n"
                "Example: GSC_SITE_URL='https://www.example.com/'"
            )
        self.token_file = token_file or GSC_TOKEN_FILE
        self.creds_file = creds_file or GOOGLE_CREDENTIALS_FILE
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        if not os.path.exists(self.token_file):
            raise FileNotFoundError(
                f"GSC token file not found: {self.token_file}\n"
                "Run gsc_auth.py first to authenticate with Google Search Console."
            )

        with open(self.token_file) as f:
            token_data = json.load(f)

        # Build credentials — client ID/secret can come from token file, creds file, or env vars
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

        if self.creds_file and os.path.exists(self.creds_file):
            with open(self.creds_file) as f:
                creds_data = json.load(f)
            client_id = client_id or creds_data.get("client_id", "")
            client_secret = client_secret or creds_data.get("client_secret", "")

        if not client_id or not client_secret:
            raise ValueError(
                "Google OAuth credentials required. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                "env vars, or set GOOGLE_CREDENTIALS_FILE to a JSON file with client_id/client_secret."
            )

        cred = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )

        # Always refresh to ensure valid token
        cred.refresh(Request())
        token_data["access_token"] = cred.token
        with open(self.token_file, "w") as f:
            json.dump(token_data, f, indent=2)

        self._service = build("searchconsole", "v1", credentials=cred)
        return self._service

    def list_sites(self):
        """List all verified Search Console sites."""
        service = self._get_service()
        result = service.sites().list().execute()
        return result.get("siteEntry", [])

    def query(self, dimensions=None, row_limit=25, days=28, start_date=None,
              end_date=None, filters=None, search_type="web", data_state="final"):
        """
        Query Search Console analytics.

        Args:
            dimensions: list of "query", "page", "device", "country", "date", "searchAppearance"
            row_limit: max rows (API max 25000)
            days: lookback window (ignored if start_date/end_date provided)
            start_date: "YYYY-MM-DD" (inclusive)
            end_date: "YYYY-MM-DD" (inclusive)
            filters: list of {"dimension": str, "operator": str, "expression": str}
            search_type: "web", "image", "video", "news", "discover", "googleNews"
            data_state: "final" or "all" (all includes fresh/unfinalized data)

        Returns:
            list of row dicts with keys, clicks, impressions, ctr, position
        """
        service = self._get_service()

        if not end_date:
            end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=days + 2)).strftime("%Y-%m-%d")

        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions or ["query"],
            "rowLimit": min(row_limit, 25000),
            "type": search_type,
            "dataState": data_state,
        }

        if filters:
            body["dimensionFilterGroups"] = [{"filters": filters}]

        result = service.searchanalytics().query(
            siteUrl=self.site_url, body=body
        ).execute()

        return result.get("rows", [])

    def top_queries(self, n=25, days=28, **kwargs):
        """Convenience: top N queries by clicks."""
        return self.query(dimensions=["query"], row_limit=n, days=days, **kwargs)

    def top_pages(self, n=100, days=28, **kwargs):
        """Convenience: top N pages by clicks."""
        return self.query(dimensions=["page"], row_limit=n, days=days, **kwargs)

    def query_page_matrix(self, n=1000, days=28, **kwargs):
        """Get query+page combos for cannibalization analysis."""
        return self.query(dimensions=["query", "page"], row_limit=n, days=days, **kwargs)

    def daily_trend(self, days=28, **kwargs):
        """Daily clicks/impressions trend."""
        return self.query(dimensions=["date"], row_limit=days, days=days, **kwargs)

    def device_split(self, days=28, **kwargs):
        """Traffic by device type."""
        return self.query(dimensions=["device"], row_limit=10, days=days, **kwargs)

    def country_split(self, n=25, days=28, **kwargs):
        """Traffic by country."""
        return self.query(dimensions=["country"], row_limit=n, days=days, **kwargs)

    def striking_distance(self, days=28, min_position=4, max_position=20, min_impressions=50):
        """Find queries in striking distance (positions 4-20 with decent impressions)."""
        rows = self.query(dimensions=["query"], row_limit=5000, days=days)
        return [
            r for r in rows
            if min_position <= r["position"] <= max_position
            and r["impressions"] >= min_impressions
        ]


def main():
    parser = argparse.ArgumentParser(description="Google Search Console CLI")
    parser.add_argument("--site", default=GSC_SITE_URL, help="Site URL (or set GSC_SITE_URL env var)")
    parser.add_argument("--queries", type=int, help="Top N queries")
    parser.add_argument("--pages", type=int, help="Top N pages")
    parser.add_argument("--days", type=int, default=28, help="Lookback days")
    parser.add_argument("--striking", action="store_true", help="Striking distance queries (pos 4-20)")
    parser.add_argument("--trend", action="store_true", help="Daily trend")
    parser.add_argument("--devices", action="store_true", help="Device split")
    parser.add_argument("--countries", type=int, help="Top N countries")
    parser.add_argument("--sites", action="store_true", help="List all verified sites")
    parser.add_argument("--raw", help="Raw query body as JSON")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    gsc = GSCClient(site_url=args.site)

    if args.sites:
        sites = gsc.list_sites()
        if args.json:
            print(json.dumps(sites, indent=2))
        else:
            print(f"{'Site URL':<60} {'Permission':<20}")
            print("-" * 80)
            for s in sorted(sites, key=lambda x: x["siteUrl"]):
                print(f"{s['siteUrl']:<60} {s['permissionLevel']:<20}")
        return

    if args.raw:
        body = json.loads(args.raw)
        rows = gsc.query(**body)
    elif args.queries:
        rows = gsc.top_queries(n=args.queries, days=args.days)
    elif args.pages:
        rows = gsc.top_pages(n=args.pages, days=args.days)
    elif args.striking:
        rows = gsc.striking_distance(days=args.days)
    elif args.trend:
        rows = gsc.daily_trend(days=args.days)
    elif args.devices:
        rows = gsc.device_split(days=args.days)
    elif args.countries:
        rows = gsc.country_split(n=args.countries, days=args.days)
    else:
        rows = gsc.top_queries(n=25, days=args.days)

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        if not rows:
            print("No data returned.")
            return
        dims = rows[0]["keys"]
        dim_count = len(dims)
        print(f"{'|'.join(f'Dim{i+1}' for i in range(dim_count)):<60} {'Clicks':>8} {'Impr':>10} {'CTR':>8} {'Pos':>6}")
        print("-" * 95)
        for r in rows:
            key_str = " | ".join(str(k)[:40] for k in r["keys"])
            print(f"{key_str:<60} {r['clicks']:>8} {r['impressions']:>10} {r['ctr']:>7.1%} {r['position']:>6.1f}")


if __name__ == "__main__":
    main()
