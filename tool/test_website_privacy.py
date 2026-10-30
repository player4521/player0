"""Focused checks for company privacy pages and the authenticated dashboard shortcut."""
from copy import deepcopy
import re
import unittest

import build

DASHBOARD = "https://dash.cloudflare.com/?to=/:account/web-analytics"
REDIRECT = "https://dash.cloudflare.com/?to=%2F%3Aaccount%2Fweb-analytics"


class WebsitePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.site = build.Site()
        self.site.config = deepcopy(self.site.config)

    def test_four_privacy_routes_and_every_localized_footer(self):
        pages = build.build_all(self.site)
        for lang in self.site.languages:
            path = self.site.url(lang, "website-privacy")
            page = pages[path.strip("/") + "/index.html"]
            self.assertIn(f'<html lang="{lang}">', page)
            self.assertIn("Cloudflare Web Analytics", page)
            self.assertIn("mailto:contact@player0.dev", page)
            for alternate in self.site.languages:
                self.assertIn(f'hreflang="{alternate}"', page)
            self.assertIn("UTM", page)
            self.assertIn("localStorage", page)
        for rel, page in pages.items():
            if not rel.endswith(".html"):
                continue
            lang = re.search(r'<html lang="([^"]+)">', page).group(1)
            footer = page.split('<footer class="site-footer">', 1)[1]
            self.assertIn(f'href="{self.site.url(lang, "website-privacy")}"', footer, rel)
            self.assertIn(self.site.t(lang, "footer.websitePrivacy"), footer, rel)

    def test_generic_dashboard_has_exactly_two_302_shortcuts_and_no_public_data_page(self):
        self.site.config["analytics"] = {"dashboardUrl": DASHBOARD}
        pages = build.build_all(self.site)
        routes = [line for line in pages["_redirects"].splitlines() if line.split()[0] in {"/stats", "/stats/"}]
        self.assertEqual(routes, [f"/stats  {REDIRECT}  302", f"/stats/  {REDIRECT}  302"])
        self.assertNotIn(":account", pages["_redirects"])
        self.assertIn("Disallow: /stats\n", pages["robots.txt"])
        self.assertNotIn("/stats", pages["sitemap.xml"])
        self.assertFalse(any(rel.startswith(("stats/", "api/", "metrics/")) for rel in pages))
        for src, dst, code in self.site.config.get("redirects", []):
            if src not in {"/stats", "/stats/"}:
                self.assertIn(f"{src}  {dst}  {code}", pages["_redirects"])

    def test_opt_out_preferences_are_explicit_and_not_indexed(self):
        pages = build.build_all(self.site)
        page = pages['analytics-preferences/index.html']
        self.assertIn('noindex, nofollow', page)
        self.assertRegex(page, r'/assets/analytics_preferences\.js\?v=[0-9a-f]{12}')
        self.assertIn('id="analytics-exclude"', page)
        self.assertNotIn('/analytics-preferences', pages['sitemap.xml'])
        self.assertIn('Disallow: /analytics-preferences', pages['robots.txt'])
        self.assertIn('Cache-Control: no-store', pages['_headers'])

    def test_missing_or_invalid_dashboard_never_creates_an_open_redirect(self):
        invalid = [None, "", {}, [], "https://dash.cloudflare.com/", "http://dash.cloudflare.com/?to=/:account/web-analytics",
                   "https://dash.cloudflare.com.evil.example/?to=/:account/web-analytics",
                   "https://dash.cloudflare.com@evil.example/", "https://owner:password@dash.cloudflare.com/",
                   "https://dash.cloudflare.com/account/analytics/web-analytics?siteTag=private",
                   "https://dash.cloudflare.com/?to=/:account/web-analytics&siteTag=private",
                   "https://dash.cloudflare.com/?to=/:account/web-analytics\n/other",
                   "https://dash.cloudflare.com/?to=/:account/web-analytics%0a", "//evil.example/", "javascript:alert(1)"]
        self.site.config["redirects"].append(["/stats", "https://evil.example/", 302])
        for value in invalid:
            with self.subTest(value=value):
                self.site.config["analytics"] = {"dashboardUrl": value}
                self.assertEqual(build.stats_redirects(self.site), [])
                pages = build.build_all(self.site)
                self.assertFalse(any(line.split()[0] in {"/stats", "/stats/"} for line in pages["_redirects"].splitlines()))
        self.site.config.pop("analytics", None)
        self.assertEqual(build.stats_redirects(self.site), [])

    def test_no_manual_beacon_or_metrics_export_and_app_policy_is_separate(self):
        pages = build.build_all(self.site)
        for rel, page in pages.items():
            if rel.endswith(".html"):
                self.assertNotIn("data-cf-beacon", page, rel)
                self.assertNotIn("static.cloudflareinsights.com/beacon", page, rel)
        for lang in ("en", "ko"):
            app_policy = pages[self.site.url(lang, "legal", "meloom/privacy").strip("/") + "/index.html"]
            self.assertNotIn("Cloudflare Web Analytics", app_policy)
        self.assertFalse(any(rel.endswith(".json") for rel in pages))


if __name__ == "__main__":
    unittest.main()
