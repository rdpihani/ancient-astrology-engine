import math
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- इंजन की शुरुआत और सुरक्षा (CORS Setup) ---
app = FastAPI(title="Siddhanta Mahashakti Engine - Ultimate")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. मौलिक डेटा और बीज-संस्कार (Constants) ---
REVOLUTIONS = {
    "sun": 4320000, "moon": 57753336 + 488, 
    "mars": 2296832 + 232, "mercury": 17937060 - 420, 
    "jupiter": 364220 + 364, "venus": 7022376 + 392, 
    "saturn": 146568 + 12, "rahu": -232238
}

PARIDHI = {
    "sun": {"manda": 14, "shighra": 0}, "moon": {"manda": 32, "shighra": 0},
    "mars": {"manda": 75, "shighra": 235}, "mercury": {"manda": 30, "shighra": 133},
    "jupiter": {"manda": 33, "shighra": 70}, "venus": {"manda": 12, "shighra": 262},
    "saturn": {"manda": 49, "shighra": 39}
}

APOGEES = {"sun": 77.23, "mars": 130.03, "mercury": 220.45, "jupiter": 171.3, "venus": 79.8, "saturn": 236.6}
UJJAIN_LON = 75.7684

# अपना गुप्त पासवर्ड यहाँ बदलें (Acode वाले पासवर्ड से मैच होना चाहिए)
MY_SECRET_KEY = "000000" 

class SiddhantaMaster:
    def __init__(self, lat, lon, dt):
        self.lat, self.lon, self.dt = lat, lon, dt

    def get_ahargana(self):
        y, m, d = self.dt.year, self.dt.month, self.dt.day
        if m <= 2: y -= 1; m += 12
        jd = math.floor(365.25*(y+4716)) + math.floor(30.6001*(m+1)) + d + (2-math.floor(y/100)+math.floor(math.floor(y/100)/4)) - 1524.5
        jd += (self.dt.hour + self.dt.minute/60.0)/24.0
        return jd - 588465.5

    def calculate_engine(self):
        ahargana = self.get_ahargana()
        ayanamsa = (ahargana * 54 / 365258) % 27
        
        planets = self._get_planets(ahargana, ayanamsa)
        lagna = self._get_lagna(planets['sun']['degrees'], ayanamsa)
        panchang = self._get_panchang(planets)
        dasha = self._get_dasha(planets['moon']['degrees'])
        shadbala = self._get_shadbala(planets, lagna)

        return {
            "status": "Siddhanta Pure",
            "ahargana": round(ahargana, 2),
            "ayanamsa": round(ayanamsa, 4),
            "panchang": panchang,
            "lagna": self._format_deg(lagna),
            "planets": planets,
            "dasha": dasha,
            "shadbala": shadbala
        }

    def _get_planets(self, ahargana, ayanamsa):
        sun_mean = ((ahargana * REVOLUTIONS["sun"]) / 1577917828 % 1) * 360
        res = {}
        for p, rev in REVOLUTIONS.items():
            mean = ((ahargana * rev) / 1577917828 % 1) * 360
            vaki = False
            if p in ["sun", "moon", "rahu"]:
                final = mean 
            else:
                m_anomaly = (mean - APOGEES.get(p, 0)) % 360
                m_phala = math.degrees(math.asin((PARIDHI[p]["manda"]/360) * math.sin(math.radians(m_anomaly))))
                m_spashta = mean - m_phala
                s_anomaly = (sun_mean - m_spashta) % 360
                if 160 < s_anomaly < 200: vaki = True
                s_phala = math.degrees(math.atan2(math.sin(math.radians(s_anomaly)), (360/PARIDHI[p]["shighra"]) + math.cos(math.radians(s_anomaly))))
                final = (m_spashta + s_phala) % 360
            
            nirayana = (final - ayanamsa) % 360
            res[p] = {"degrees": round(nirayana, 4), "formatted": self._format_deg(nirayana), "is_vaki": vaki}
        return res

    def _get_lagna(self, sun_deg, ayanamsa):
        local_factor = (self.dt.hour + self.dt.minute/60.0) / 24.0
        return (sun_deg + (local_factor * 360) - ayanamsa) % 360

    def _get_panchang(self, planets):
        sun, moon = planets['sun']['degrees'], planets['moon']['degrees']
        tithi = math.ceil(((moon - sun + 360) % 360) / 12)
        nakshatra_list = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
        n_idx = math.floor(moon / (360/27)) % 27
        return {"tithi": tithi if tithi <= 30 else tithi % 30, "nakshatra": nakshatra_list[n_idx]}

    def _get_dasha(self, moon_deg):
        masters = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
        n_idx = math.floor((moon_deg / (360/27))) % 9
        return {"mahadasha": masters[n_idx]}

    def _get_shadbala(self, planets, lagna):
        balas = {}
        for p in planets:
            balas[p] = {"dig_bala": "Pure", "naisargika_bala": "Pure", "rank": "High"}
        return balas

    def _format_deg(self, deg):
        r = int(deg // 30)
        d = int(deg % 30)
        m = int((deg * 60) % 60)
        return f"{r+1}R {d}° {m}'"

@app.get("/calculate")
def calculate(lat: float, lon: float, year: int, month: int, day: int, hour: int, minute: int, secret: str):
    if secret != MY_SECRET_KEY: raise HTTPException(status_code=403, detail="Unauthorized: Key mismatch")
    engine = SiddhantaMaster(lat, lon, datetime(year, month, day, hour, minute))
    return engine.calculate_engine()

# स्वास्थ्य जांच के लिए (Root Path)
@app.get("/")
def home():
    return {"status": "Siddhanta Engine is Live", "version": "Ultimate"}