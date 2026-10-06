"""
ISEWS historical knowledge base.

Every record carries a `status` flag so verified facts are never mixed with
illustrative inputs:

  VERIFIED   - checked against the cited source during the build (Oct 2026)
  EXTRACTED  - machine-extracted from a long PDF; spot-check the page before citing
  REPORTED   - widely reported, but not re-verified for this build
  BRIEF      - taken from the ChatVE Tigray Internet Shutdown Brief (Rev. 2)
  CODED      - analyst coding derived from the cited source (judgement involved)
"""

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
SOURCES = {
    "AN25": ("Access Now, #KeepItOn: Rising and resisting in the darkness - internet shutdowns in 2025 (press release)",
             "https://www.accessnow.org/press-release/rising-and-resisting-in-the-darkness-internet-shutdowns-in-2025/"),
    "AN25R": ("Access Now, KeepItOn Internet Shutdowns 2025 Annual Report (PDF, March 2026)",
              "https://www.accessnow.org/wp-content/uploads/2026/03/KeepItOn-Internet-Shutdowns-2025-Annual-Report.pdf"),
    "ISOC": ("Internet Society Pulse, Tracking Internet Shutdowns 2019-2025",
             "https://news.internetsociety.org/tracking-internet-shutdowns-2019-2025/"),
    "AIN_IETF": ("Project Ainita, 2025 Internet Shutdown in Iran (IETF 123, HRPC slides)",
                 "https://datatracker.ietf.org/meeting/123/materials/slides-123-hrpc-project-ainita-2025-internet-shutdown-in-iran-00.pdf"),
    "AIN_MAST": ("Project Ainita on Infosec Exchange (@ProjectAinita)",
                 "https://infosec.exchange/@ProjectAinita"),
    "ARYA": ("Aryapour, A. (2025) Iran's Stealth Internet Blackout: A New Model of Censorship, arXiv:2507.14183",
             "https://arxiv.org/html/2507.14183v1"),
    "IODA": ("IODA (Georgia Tech), A Comparative Look at Internet Shutdowns in Iran: 2019, 2022, 2025 and 2026",
             "https://ioda.inetintel.cc.gatech.edu/reports/a-comparative-look-at-internet-shutdowns-in-iran-2019-2022-2026-and-2026/"),
    "AMN": ("Amnezia VPN blog, Internet censorship in Iran: Q1 2026 and forecast (VPN vendor source)",
            "https://amnezia.org/en/blog/internet-censorship-in-iran-q1-2026-and-forecast"),
    "TZ": ("The Standard (Kenya), Tanzania partially restores internet after five-day election blackout",
           "https://www.thestandard.ke/business/amp/africa/article/2001533363/tanzania-partially-restores-internet-after-five-day-election-blackout"),
    "KE": ("Internet Without Borders, Kenya: Internet Disruptions and Anti-Government Protests",
           "https://internetwithoutborders.org/kenya-internet-disruptions-and-anti-government-protests/"),
    "CM": ("The EastAfrican, Internet access cut in Cameroon amid post-election protests",
           "https://theeastafrican.co.ke/tea/news/central-africa/internet-access-cut-in-cameroon-amid-post-election-protests-5242648"),
    "TG": ("Global Voices, Togo restricts internet during June protests",
           "https://globalvoices.org/2025/07/16/togo-restricts-internet-during-june-protests/"),
    "PK": ("TechRadar, Pakistan has restored X access after a 15-month ban",
           "https://www.techradar.com/vpn/vpn-privacy-security/pakistan-has-restored-x-access-after-a-15-month-ban-heres-everything-we-know-so-far"),
    "BD": ("Wikipedia, 2024 Bangladesh internet blackouts",
           "https://en.wikipedia.org/wiki/2024_Bangladesh_internet_blackouts"),
    "RU_CPJ": ("CPJ, Russia's Telegram throttling another step toward total information control (Feb 2026)",
               "https://cpj.org/2026/02/cpj-russias-telegram-throttling-another-step-toward-total-information-control/"),
    "RU_ZONA": ("Mediazona, Russia blocks WhatsApp, Telegram calls (13 Aug 2025)",
                "https://zona.media/article/2025/08/13/callban"),
    "SN": ("CPJ, Senegal delays election, authorities cut mobile internet (Feb 2024)",
           "https://cpj.org/2024/02/senegal-delays-election-authorities-cut-mobile-internet-revoke-walf-tvs-license-harass-journalists/"),
    "CHATVE": ("ChatVE, Tigray Internet Shutdown Brief (Rev. 2), citing NetBlocks and Cloudflare Radar",
               "ChatVE internal brief"),
    "NG": ("Widely reported: Federal Government of Nigeria suspension of Twitter, 5 Jun 2021 - 13 Jan 2022",
           "https://en.wikipedia.org/wiki/2021_Twitter_ban_in_Nigeria"),
}

# ---------------------------------------------------------------------------
# Global aggregates
# ---------------------------------------------------------------------------
AGGREGATES = {
    "access_now_2025": {
        "total_shutdowns": (313, "AN25", "VERIFIED"),
        "countries": (52, "AN25", "VERIFIED"),
        "total_2024_as_revised": (304, "AN25", "VERIFIED"),
        "countries_since_2016": (100, "AN25", "VERIFIED"),
        "conflict": (125, "AN25", "VERIFIED"),
        "conflict_countries": (14, "AN25", "VERIFIED"),
        "human_rights_abuse_overlap": (70, "AN25", "VERIFIED"),
        "leo_satellite": (14, "AN25", "VERIFIED"),
        "leo_satellite_2024": (4, "AN25", "VERIFIED"),
        "myanmar": (95, "AN25", "VERIFIED"),
        "protests": (64, "AN25R", "EXTRACTED"),
        "elections": (12, "AN25R", "EXTRACTED"),
        "exams": (11, "AN25R", "EXTRACTED"),
        "religious_holidays": (8, "AN25R", "EXTRACTED"),
        "platform_blocks": (94, "AN25R", "EXTRACTED"),
        "platform_block_countries": (40, "AN25R", "EXTRACTED"),
        "platform_blocks_2024": (77, "AN25R", "EXTRACTED"),
        "carried_into_2026": (75, "AN25R", "EXTRACTED"),
        "cross_border": (18, "AN25R", "EXTRACTED"),
    },
    "platform_blocks_2025": [  # Access Now 2025 annual report
        ("Facebook", 31), ("WhatsApp", 27), ("TikTok", 16),
    ],
    "triggers_2025": [
        ("Conflict", 125, "VERIFIED"), ("Protests and political instability", 64, "EXTRACTED"),
        ("Elections", 12, "EXTRACTED"), ("Exams", 11, "EXTRACTED"), ("Religious holidays", 8, "EXTRACTED"),
    ],
    "top_countries_2025": [
        ("Myanmar", 95, "VERIFIED"), ("India", 65, "EXTRACTED"), ("Pakistan", 20, "EXTRACTED"),
        ("Russia", 19, "EXTRACTED"), ("Iran", 11, "EXTRACTED"),
    ],
    "africa_2025": [  # Access Now 2025 annual report, machine-extracted
        ("Tanzania", 8), ("Cameroon", 4), ("Kenya", 3), ("Sudan", 3), ("Nigeria", 2),
        ("Ethiopia", 2), ("Guinea", 2), ("DR Congo", 2), ("Angola", 1), ("Central African Republic", 1),
        ("Chad", 1), ("Equatorial Guinea", 1), ("Guinea-Bissau", 1), ("Libya", 1), ("Togo", 1),
    ],
    "isoc_pulse": {
        "events_2019_2025": (916, "ISOC", "VERIFIED"),
        "countries_2019_2025": (61, "ISOC", "VERIFIED"),
    },
}

DISCREPANCIES = [
    "CPJ (Feb 2026) states Russia recorded the highest number of shutdowns worldwide in 2025; Access Now "
    "ranks Myanmar first (95) and Russia fourth (19). The two organisations count differently, so ISEWS "
    "keeps Access Now as the single source for its training labels.",
    "Access Now's 2025 press release gives 304 shutdowns for 2024. Earlier 2024 reporting gave a lower figure, so the "
    "2024 total appears to have been revised. ISEWS uses the revised figure.",
    "Amnezia is a VPN vendor. Its Iran figures (87-day shutdown, Russian technical assistance) are used for "
    "context only and are not training labels.",
]

# ---------------------------------------------------------------------------
# Modality taxonomy
# ---------------------------------------------------------------------------
MODALITIES = [
    # key, label, severity weight, short definition, telemetry signature
    ("full_shutdown", "Full or regional shutdown", 1.00,
     "Network-wide loss of connectivity, national or confined to a region or set of ASNs.",
     "Traffic and active-probe response collapse. If BGP prefixes are withdrawn, the cut was made in routing. "
     "If BGP stays visible while traffic collapses, the cut was made by middleboxes (a stealth blackout)."),
    ("platform_block", "Social media and app blocking", 0.60,
     "A named platform or app (X, WhatsApp, Facebook, TikTok, Telegram, YouTube) is made unreachable.",
     "OONI-style reachability for the target platform falls. TLS/SNI resets and DNS anomalies rise for its domains. "
     "Total traffic barely moves."),
    ("ip_blocking", "IP and ASN blocking", 0.55,
     "Traffic to specific IP ranges, hosting providers or ASNs is dropped.",
     "TCP connect failures rise for the targeted ranges while DNS answers stay clean."),
    ("dns_http_censorship", "DNS and HTTP censorship", 0.50,
     "DNS poisoning, injected block pages and HTTP host-header filtering.",
     "Injected DNS answers (e.g. private 10.10.34.34 addresses in Iran) and HTTP 403 or TCP RST injection."),
    ("vpn_targeting", "VPN targeting", 0.60,
     "VPN protocols, servers or hosting ranges are fingerprinted and blocked, or VPN use is licensed or banned.",
     "Handshake success for WireGuard, OpenVPN and obfuscated proxies falls, often alongside IP blocking of hosting providers."),
    ("throttling", "Bandwidth throttling", 0.60,
     "Deliberate degradation of throughput across the network without a full cut.",
     "Throughput falls and latency rises, often with rhythmic instability, while probes still respond."),
    ("protocol_downgrade", "Protocol downgrade and whitelisting", 0.75,
     "Only selected protocols or ports are allowed (e.g. DNS/53, HTTP/80, HTTPS/443); QUIC/UDP and IPv6 are dropped.",
     "The QUIC/UDP share collapses to near zero and UDP-based VPNs fail. Plain TCP/TLS survives."),
    ("targeted_slowdown", "Targeted platform slowdown", 0.50,
     "One service is slowed until it is unusable while it stays nominally reachable (e.g. YouTube or Telegram in Russia).",
     "Throughput to the target platform falls while its reachability and the rest of the network stay normal."),
    ("tls_interception", "Surveillance: TLS interception", 0.80,
     "Traffic is intercepted or decrypted in transit, for example through forced root certificates or middlebox MITM.",
     "The certificate-mismatch rate rises in measurements against known-good fingerprints."),
]
MODALITY_KEYS = [m[0] for m in MODALITIES]

# ---------------------------------------------------------------------------
# Historical event records
# ---------------------------------------------------------------------------
EVENTS = [
    dict(id="IR-2019-11", country="Iran", iso="IRN", start="2019-11-16", end="2019-11-21",
         modalities=["full_shutdown"], scope="National", trigger="Protests",
         mechanism="BGP withdrawal ('blunt force'); active probing collapsed",
         source="IODA", status="VERIFIED"),
    dict(id="IR-2022-09", country="Iran", iso="IRN", start="2022-09", end="2022-09",
         modalities=["full_shutdown"], scope="Mobile networks (nightly)", trigger="Protests",
         mechanism="Around 100 hours of mobile shutdowns; fixed lines stayed up",
         source="IODA", status="VERIFIED"),
    dict(id="IR-2025-06", country="Iran", iso="IRN", start="2025-06-18", end="2025-06-21",
         modalities=["full_shutdown", "protocol_downgrade", "dns_http_censorship", "vpn_targeting", "platform_block"],
         scope="National", trigger="Armed conflict",
         mechanism="Censorship middleboxes, not BGP (about 97% traffic reduction). Whitelist of DNS/53, HTTP/80 and HTTPS/443 only. "
                   "DNS poisoning to 10.10.34.34 and SNI resets. WhatsApp blocked",
         source="AIN_IETF;ARYA;AN25R", status="VERIFIED"),
    dict(id="IR-2026-01", country="Iran", iso="IRN", start="2026-01-08", end="2026-01-27",
         modalities=["full_shutdown", "protocol_downgrade"], scope="National", trigger="Protests",
         mechanism="Probe responsiveness about 3%; routing not the main tool; partial restoration by 27 Jan "
                   "(IODA). Project Ainita amplified Shadowserver data showing near-zero exposure after 8 Jan",
         source="IODA;AIN_MAST", status="VERIFIED"),
    dict(id="IR-2026-02a", country="Iran", iso="IRN", start="2026-02-09", end="2026-02-09",
         modalities=["throttling"], scope="National", trigger="Protests",
         mechanism="Project Ainita: 65 independent measurements show sustained latency spikes and 'rhythmic "
                   "instability' consistent with deliberate quality-of-service degradation",
         source="AIN_MAST", status="VERIFIED"),
    dict(id="IR-2026-02b", country="Iran", iso="IRN", start="2026-02-28", end="2026-05-25",
         modalities=["full_shutdown", "vpn_targeting", "ip_blocking"], scope="National", trigger="Armed conflict",
         mechanism="Near-total cut after strikes; whitelist model; hosting providers linked to VPNs blocked. "
                   "87 days per Amnezia (vendor source)",
         source="AIN_MAST;AMN", status="VERIFIED"),
    dict(id="IR-2026-POL", country="Iran", iso="IRN", start="2026-02-26", end="",
         modalities=["surveillance_policy"], scope="Policy", trigger="Policy",
         mechanism="National Strategic Document on Electronic Passive Defense: powers to connect or disconnect "
                   "external networks from the National Information Network in a crisis; spectrum protection against satellite internet",
         source="AIN_MAST", status="CODED"),
    dict(id="ET-2026-09", country="Ethiopia (Tigray)", iso="ETH", start="2026-09-24", end="",
         modalities=["full_shutdown"], scope="Regional", trigger="Armed conflict",
         mechanism="Ethio Telecom and Safaricom down at about 22:21. National connectivity only fell to about 82%. "
                   "Two operators carry more than 99% of bytes",
         source="CHATVE", status="BRIEF"),
    dict(id="TZ-2025-10", country="Tanzania", iso="TZA", start="2025-10-29", end="2025-11-03",
         modalities=["full_shutdown", "platform_block"], scope="National", trigger="Elections",
         mechanism="Five-day blackout from election day; partial restoration with social media and messaging restrictions continuing "
                   "(Cloudflare Radar, NetBlocks)", source="TZ", status="VERIFIED"),
    dict(id="KE-2024-06", country="Kenya", iso="KEN", start="2024-06-25", end="2024-06-25",
         modalities=["throttling", "targeted_slowdown"], scope="National", trigger="Protests",
         mechanism="NetBlocks recorded a sharp drop in traffic from about 16:00. Safaricom and Airtel blamed undersea cables. "
                   "X was hard to reach", source="KE", status="VERIFIED"),
    dict(id="CM-2025-10", country="Cameroon", iso="CMR", start="2025-10-23", end="",
         modalities=["full_shutdown"], scope="National (partial)", trigger="Elections",
         mechanism="NetBlocks confirmed a significant disruption after the 12 Oct presidential election",
         source="CM", status="VERIFIED"),
    dict(id="TG-2025-06", country="Togo", iso="TGO", start="2025-06-25", end="2025-06-27",
         modalities=["throttling", "targeted_slowdown", "platform_block", "dns_http_censorship", "ip_blocking"],
         scope="National", trigger="Protests",
         mechanism="ISOC Togo Chapter recorded 1,072 anomalies (6.9% irregularity), DNS/IP filtering and TCP "
                   "interruptions. YouTube selectively blocked", source="TG", status="VERIFIED"),
    dict(id="PK-2024-02", country="Pakistan", iso="PAK", start="2024-02-17", end="2025-05-07",
         modalities=["platform_block", "vpn_targeting"], scope="Platform (X)", trigger="Elections",
         mechanism="X blocked for 15 months after election-fraud claims. VPN licensing category introduced",
         source="PK", status="VERIFIED"),
    dict(id="BD-2024-07", country="Bangladesh", iso="BGD", start="2024-07-18", end="2024-07-31",
         modalities=["full_shutdown", "platform_block"], scope="National", trigger="Protests",
         mechanism="Mobile shutdown 18 Jul; broadband restored 24 Jul, mobile 28 Jul; Facebook, Instagram and TikTok 31 Jul",
         source="BD", status="VERIFIED"),
    dict(id="BD-2024-08", country="Bangladesh", iso="BGD", start="2024-08-02", end="2024-08-05",
         modalities=["platform_block", "full_shutdown"], scope="National", trigger="Protests",
         mechanism="Facebook, WhatsApp and Telegram restricted 2 Aug; 4G shut 4 Aug; restored 5 Aug",
         source="BD", status="VERIFIED"),
    dict(id="RU-2024-YT", country="Russia", iso="RUS", start="2024", end="",
         modalities=["targeted_slowdown"], scope="Platform (YouTube)", trigger="Policy",
         mechanism="Roskomnadzor restrictions on YouTube", source="RU_CPJ", status="VERIFIED"),
    dict(id="RU-2025-08", country="Russia", iso="RUS", start="2025-08", end="",
         modalities=["platform_block"], scope="Feature (voice/video calls)", trigger="Policy",
         mechanism="Calls restricted on Telegram, WhatsApp, FaceTime and Snapchat", source="RU_CPJ;RU_ZONA", status="VERIFIED"),
    dict(id="RU-2026-02", country="Russia", iso="RUS", start="2026-02-09", end="",
         modalities=["targeted_slowdown"], scope="Platform (Telegram)", trigger="Policy",
         mechanism="Telegram throttled, which Durov says is meant to push users to the state-backed MAX app",
         source="RU_CPJ", status="VERIFIED"),
    dict(id="RU-2026-POL", country="Russia", iso="RUS", start="2026-01-27", end="",
         modalities=["surveillance_policy"], scope="Policy", trigger="Policy",
         mechanism="State Duma bill to let the FSB shut down the internet nationwide; DNS-level blocking of WhatsApp, YouTube and others",
         source="RU_CPJ", status="CODED"),
    dict(id="SN-2024-02", country="Senegal", iso="SEN", start="2024-02-04", end="",
         modalities=["full_shutdown"], scope="Mobile data", trigger="Elections",
         mechanism="Mobile internet cut after the presidential election was postponed", source="SN", status="VERIFIED"),
    dict(id="VE-2025-01", country="Venezuela", iso="VEN", start="2025-01", end="",
         modalities=["vpn_targeting"], scope="21 VPN services", trigger="Elections",
         mechanism="21 VPN services blocked", source="AN25R", status="EXTRACTED"),
    dict(id="IN-2025-12", country="India (J&K)", iso="IND", start="2025-12", end="",
         modalities=["vpn_targeting"], scope="Regional", trigger="Security",
         mechanism="Unauthorised VPN use banned in Jammu & Kashmir", source="AN25R", status="EXTRACTED"),
    dict(id="NG-2021-06", country="Nigeria", iso="NGA", start="2021-06-05", end="2022-01-13",
         modalities=["platform_block", "vpn_targeting"], scope="Platform (Twitter)", trigger="Policy",
         mechanism="Twitter suspended nationwide for about 7 months; VPN use surged",
         source="NG", status="REPORTED"),
    dict(id="HK-2026-03", country="Hong Kong", iso="HKG", start="2026-03", end="",
         modalities=["surveillance_policy"], scope="Policy", trigger="Policy",
         mechanism="Refusing to give device passwords or decryption keys criminalised, including in airport transit",
         source="AIN_MAST", status="CODED"),
]

# ---------------------------------------------------------------------------
# Surveillance & control indicators (CODED from cited sources; None = no data)
# ---------------------------------------------------------------------------
SURV_INDICATORS = [
    ("legal_disconnect", "Legal power to disconnect", 0.20),
    ("centralised_gateway", "Centralised gateway, national intranet or operator concentration", 0.20),
    ("dpi_whitelisting", "DPI or whitelisting deployed", 0.20),
    ("vpn_controls", "VPN licensing, bans or blocking", 0.15),
    ("state_platform", "State platform push or decryption mandate", 0.15),
    ("tls_mitm", "Observed TLS interception", 0.10),
]
SURVEILLANCE = {
    "Iran": dict(legal_disconnect=1, centralised_gateway=1, dpi_whitelisting=1, vpn_controls=1, state_platform=None, tls_mitm=None,
                 note="Passive Defense document (Feb 2026), NIN and whitelisting (Project Ainita, Aryapour)"),
    "Russia": dict(legal_disconnect=1, centralised_gateway=None, dpi_whitelisting=None, vpn_controls=None, state_platform=1, tls_mitm=None,
                   note="FSB shutdown bill (Jan 2026); MAX app push (CPJ)"),
    "Pakistan": dict(legal_disconnect=None, centralised_gateway=None, dpi_whitelisting=None, vpn_controls=1, state_platform=None, tls_mitm=None,
                     note="VPN licensing category; reported China-assisted firewall (TechRadar, unverified)"),
    "Ethiopia (Tigray)": dict(legal_disconnect=None, centralised_gateway=1, dpi_whitelisting=None, vpn_controls=None, state_platform=None, tls_mitm=None,
                              note="Two operators carry more than 99% of bytes (ChatVE brief); no surveillance data coded"),
    "Togo": dict(legal_disconnect=None, centralised_gateway=None, dpi_whitelisting=1, vpn_controls=None, state_platform=None, tls_mitm=None,
                 note="DNS/IP filtering and selective app blocking (ISOC Togo Chapter via Global Voices)"),
    "Kenya": dict(legal_disconnect=None, centralised_gateway=None, dpi_whitelisting=None, vpn_controls=None, state_platform=None, tls_mitm=None,
                  note="No surveillance indicators coded"),
    "Tanzania": dict(legal_disconnect=None, centralised_gateway=None, dpi_whitelisting=None, vpn_controls=None, state_platform=None, tls_mitm=None,
                     note="No surveillance indicators coded"),
    "Nigeria": dict(legal_disconnect=None, centralised_gateway=None, dpi_whitelisting=None, vpn_controls=None, state_platform=None, tls_mitm=None,
                    note="No surveillance indicators coded; Twitter suspension 2021 (reported)"),
}
