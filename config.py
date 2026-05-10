"""Octa Project Progress Tracker — Configuration."""

APP_NAME    = "Project Progress Tracker"
APP_ICON    = "🏗️"
APP_VERSION = "1.0.0"

DARK = {
    "bg":      "#0f1421",
    "bg2":     "#1a2235",
    "bg3":     "#232f45",
    "border":  "rgba(255,255,255,0.09)",
    "text":    "#e2e8f0",
    "muted":   "#8899b0",
    "accent":  "#00BCD4",
    "accent2": "#FF6B35",
    "sidebar": "#1B2A4A",
    "success": "#6fcf97",
    "warning": "#f6cc52",
    "danger":  "#fc8181",
}

# Status colours consistent with KPI app
TASK_STATUS_COLORS = {
    "planned":    "#8899b0",
    "ongoing":    "#00BCD4",
    "completed":  "#6fcf97",
    "delayed":    "#fc8181",
    "cancelled":  "#4a4a6a",
}

DELIVERABLE_STATUS_COLORS = {
    "planned":     "#8899b0",
    "in_progress": "#f6cc52",
    "submitted":   "#00BCD4",
    "accepted":    "#6fcf97",
    "delayed":     "#fc8181",
    "cancelled":   "#4a4a6a",
}

MILESTONE_STATUS_COLORS = {
    "planned":            "#8899b0",
    "achieved":           "#6fcf97",
    "partially_achieved": "#f6cc52",
    "delayed":            "#fc8181",
    "not_achieved":       "#e74c3c",
}

# Country → ISO alpha-3 for Plotly maps
COUNTRY_ISO = {
    "Afghanistan":"AFG","Albania":"ALB","Algeria":"DZA","Argentina":"ARG",
    "Armenia":"ARM","Australia":"AUS","Austria":"AUT","Azerbaijan":"AZE",
    "Bangladesh":"BGD","Belarus":"BLR","Belgium":"BEL","Bolivia":"BOL",
    "Bosnia and Herzegovina":"BIH","Brazil":"BRA","Bulgaria":"BGR",
    "Cambodia":"KHM","Canada":"CAN","Chile":"CHL","China":"CHN",
    "Colombia":"COL","Croatia":"HRV","Cyprus":"CYP","Czech Republic":"CZE",
    "Denmark":"DNK","Ecuador":"ECU","Egypt":"EGY","Estonia":"EST",
    "Ethiopia":"ETH","Finland":"FIN","France":"FRA","Georgia":"GEO",
    "Germany":"DEU","Ghana":"GHA","Greece":"GRC","Guatemala":"GTM",
    "Honduras":"HND","Hungary":"HUN","Iceland":"ISL","India":"IND",
    "Indonesia":"IDN","Iran":"IRN","Iraq":"IRQ","Ireland":"IRL",
    "Israel":"ISR","Italy":"ITA","Japan":"JPN","Jordan":"JOR",
    "Kazakhstan":"KAZ","Kenya":"KEN","Kosovo":"XKX","Kuwait":"KWT",
    "Kyrgyzstan":"KGZ","Latvia":"LVA","Lebanon":"LBN","Libya":"LBY",
    "Lithuania":"LTU","Luxembourg":"LUX","Malaysia":"MYS","Malta":"MLT",
    "Mexico":"MEX","Moldova":"MDA","Montenegro":"MNE","Morocco":"MAR",
    "Netherlands":"NLD","New Zealand":"NZL","Nigeria":"NGA",
    "North Macedonia":"MKD","Norway":"NOR","Pakistan":"PAK",
    "Palestine":"PSE","Panama":"PAN","Paraguay":"PRY","Peru":"PER",
    "Philippines":"PHL","Poland":"POL","Portugal":"PRT","Romania":"ROU",
    "Russia":"RUS","Saudi Arabia":"SAU","Senegal":"SEN","Serbia":"SRB",
    "Slovakia":"SVK","Slovenia":"SVN","South Africa":"ZAF",
    "South Korea":"KOR","Spain":"ESP","Sri Lanka":"LKA","Sweden":"SWE",
    "Switzerland":"CHE","Syria":"SYR","Tajikistan":"TJK","Thailand":"THA",
    "Tunisia":"TUN","Turkey":"TUR","Turkmenistan":"TKM","Uganda":"UGA",
    "Ukraine":"UKR","United Arab Emirates":"ARE","United Kingdom":"GBR",
    "United States":"USA","Uruguay":"URY","Uzbekistan":"UZB",
    "Venezuela":"VEN","Vietnam":"VNM","Yemen":"YEM","Zimbabwe":"ZWE",
    "Liechtenstein":"LIE",
}

LIFECYCLE_STATUSES = [
    "draft_proposal", "submitted_proposal", "rejected_proposal",
    "funded_project", "ongoing_project", "ended_project",
]

FUNDED_STATUSES = {"funded_project","ongoing_project","ended_project"}
