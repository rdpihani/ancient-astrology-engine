import math
from datetime import datetime
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Ancient Indian Astrology Engine")

# --- 1. सूर्य-सिद्धांत स्थिरांक और बीज संस्कार (Constants) ---
# एक महायुग (4,320,000 वर्ष) में भगण (Revolutions)
REVOLUTIONS = {
    "sun": 4320000,
    "moon": 57753336 + 488,         # बीज संस्कार (Bija Correction)
    "mars": 2296832 + 232, 
    "mercury": 17937060 - 420, 
    "jupiter": 364220 + 364, 
    "venus": 7022376 + 392, 
    "saturn": 146568 + 12, 
    "rahu": -232238  # राहु (सदैव वक्री)
}

CIVIL_DAYS_PER_MAHAYUGA = 1577917828 
UJJAIN_LON = 75.7684  # प्राचीन भारतीय शून्य रेखांश

# ग्रहों के मन्दोच्च (Apogees - मन्द फल गणना हेतु)
APOGEES = {
    "sun": 77.23, "moon": 0, "mars": 130.03, 
    "mercury": 220.45, "jupiter": 171.3, "venus": 79.8, "saturn": 236.6
}

# --- 2. कोर इंजन क्लास (The Engine) ---

class SiddhantaEngine:
    def __init__(self, lat, lon, dt_obj):
        self.lat = lat
        self.lon = lon
        self.dt = dt_obj

    def get_jd(self):
        """जूलियन डे गणना (समय को गणितीय अंकों में बदलने के लिए)"""
        year, month, day = self.dt.year, self.dt.month, self.dt.day
        hour, minute = self.dt.hour, self.dt.minute
        
        if month <= 2:
            year -= 1
            month += 12
        A = math.floor(year / 100)
        B = 2 - A + math.floor(A / 4)
        jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
        day_fraction = (hour + minute / 60.0) / 24.0
        return jd + day_fraction

    def calculate_ahargana(self, jd):
        """अहर्गण: कलियुग आरम्भ (18 Feb 3102 BC) से आज तक के दिन"""
        jd_kaliyuga_start = 588465.5
        return jd - jd_kaliyuga_start

    def get_spashta_graha(self, ahargana):
        """मध्यम ग्रह, देशान्तर और मन्द फल का पूर्ण शोधन"""
        results = {}
        # देशान्तर शोधन (Deshantara: Correction for Local Longitude)
        lon_diff = self.lon - UJJAIN_LON
        deshantara_days = lon_diff / 360.0
        corrected_ahargana = ahargana + deshantara_days

        # अयनचलन (Siddhantic Ayanamsa - Precession)
        ayanamsa = (ahargana * 54 / 365258) % 360
        if ayanamsa > 27: ayanamsa = 27 

        for planet, revs in REVOLUTIONS.items():
            # 1. मध्यम ग्रह (Mean Position)
            mean_pos = ((corrected_ahargana * revs) / CIVIL_DAYS_PER_MAHAYUGA % 1) * 360
            
            # 2. मन्द फल (Equation of Center - मन्द संस्कार)
            # यह ग्रह की गति को 'सच्चा' बनाता है
            if planet != "rahu":
                anomaly = (mean_pos - APOGEES[planet]) % 360
                manda_phala = math.sin(math.radians(anomaly)) * 2.1 # प्राचीन पद्धति के अनुसार औसत
                spashta_pos = (mean_pos + manda_phala) % 360
            else:
                spashta_pos = mean_pos # राहु के लिए मध्यम ही स्पष्ट है

            # 3. निरयण शोधन (Ayanamsa Correction)
            final_pos = (spashta_pos - ayanamsa) % 360
            
            # परिणाम को राशि, अंश, कला में बदलना
            rashi = int(final_pos // 30)
            degree = int(final_pos % 30)
            minute = int((final_pos * 60) % 60)
            
            results[planet] = {
                "total_degrees": round(final_pos, 4),
                "rashi_no": rashi + 1,
                "formatted": f"{rashi+1}R {degree}° {minute}'"
            }
        
        results["ayanamsa"] = round(ayanamsa, 4)
        return results

# --- 3. API एंडपॉइंट्स (Linking Layer) ---

@app.get("/")
def home():
    return {"message": "Siddhanta Astrology Engine is Active", "status": "Ready to Link"}

@app.get("/calculate")
def calculate(lat: float, lon: float, year: int, month: int, day: int, hour: int, minute: int):
    try:
        dt_input = datetime(year, month, day, hour, minute)
        engine = SiddhantaEngine(lat, lon, dt_input)
        
        jd = engine.get_jd()
        ahargana = engine.calculate_ahargana(jd)
        planets = engine.get_spashta_graha(ahargana)
        
        return {
            "engine": "Surya-Siddhanta-Complete",
            "coordinates": {"lat": lat, "lon": lon},
            "timestamp": dt_input.isoformat(),
            "ahargana": round(ahargana, 2),
            "data": planets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))