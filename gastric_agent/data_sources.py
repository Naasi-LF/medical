from urllib.parse import urlparse


DEFAULT_SEED_URLS = [
    "https://medlineplus.gov/stomachdisorders.html",
    "https://www.niddk.nih.gov/health-information/digestive-diseases/gastritis",
    "https://www.niddk.nih.gov/health-information/digestive-diseases/peptic-ulcers-stomach-ulcers",
    "https://www.mayoclinic.org/diseases-conditions/gastritis/symptoms-causes/syc-20355805",
    "https://www.nhs.uk/conditions/stomach-ulcer/",
    "https://my.clevelandclinic.org/health/diseases/10349-gastritis",
    "https://www.webmd.com/digestive-disorders/what-is-gastritis",
]

GASTRIC_KEYWORDS = {
    "gastric",
    "stomach",
    "gastritis",
    "ulcer",
    "helicobacter",
    "h. pylori",
    "indigestion",
    "dyspepsia",
    "胃",
    "胃炎",
    "胃溃疡",
    "幽门螺杆菌",
}

URL_TOPIC_HINTS = {
    "gastr",
    "stomach",
    "ulcer",
    "dyspepsia",
    "h-pylori",
    "helicobacter",
    "digestive",
    "gastro",
}

NEGATIVE_TOPIC_KEYWORDS = {
    "crohn",
    "colitis",
    "appendic",
    "rectal",
    "colon",
    "anal",
    "hemorrhoid",
    "diverticul",
    "celiac",
    "liver",
    "pancrea",
    "gallbladder",
    "kidney",
}

NOISE_URL_HINTS = {
    "/rss",
    "rss.",
    "/news",
    "/whatsnew",
    "/lab-tests",
    "/ency/",
    "/spanish/",
    "/espanol/",
    "/español/",
}


def allowed_domains(seed_urls: list[str]) -> set[str]:
    domains: set[str] = set()
    for url in seed_urls:
        netloc = urlparse(url).netloc
        if netloc:
            domains.add(netloc)
    return domains
