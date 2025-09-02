import requests
import csv
import time
import sys
import unicodedata
from datetime import datetime

# =============================================================================
# Unicode Encoding Fix - Bu kısım eklendi
# =============================================================================

# Windows terminal encoding fix
if sys.platform == "win32":
    try:
        import os
        os.system("chcp 65001")  # UTF-8 aktif et
    except:
        pass

# Terminal encoding ayarla
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def clean_unicode_text(text):
    """Unicode kontrol karakterlerini temizler"""
    if not text:
        return ""
    try:
        # Unicode kontrol karakterlerini temizle (LTR, RTL marks vs.)
        text = ''.join(char for char in str(text) if unicodedata.category(char)[0] != 'C')
        return text.strip()
    except Exception:
        # Güvenli ASCII'ye çevir
        return str(text).encode('ascii', 'ignore').decode('ascii').strip()

def safe_print(text, end='\n'):
    """Güvenli print fonksiyonu"""
    try:
        print(text, end=end)
    except UnicodeEncodeError:
        # Unicode hatası durumunda güvenli yazdır
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(clean_text, end=end)
    except Exception as e:
        print(f"[Print Error: {e}]", end=end)

# =============================================================================
# BURASI DEGiSTiRiLECEK ALAN - SADECE BURAYI EDIT ET!
# =============================================================================

API_KEY = ""

# Taramak istedigin alan
AREA_NAME = "İstanbul genel anadolu deneme"

# TEK BOLGE KOORDINATLARI
# Format: [min_lat, max_lat, min_lng, max_lng]
BOUNDS = [40.79626, 41.11893, 28.98716, 29.46456]  #güney kuzey batı doğu

# Grid ayarlari
STEP_SIZE = 0.027    # Boşluk bırakmadan 1500m yarıçapı tarar
SEARCH_RADIUS = 1500  # Metre cinsinden

# Arama parametreleri
SEARCH_KEYWORD = "burger"
MIN_RATINGS = 5      # En az kac degerlendirme

# =============================================================================
# BURADAN SONRASI DEGiSTiRiLMEZ
# =============================================================================

def fetch_places(lat, lng, radius=SEARCH_RADIUS, keyword=SEARCH_KEYWORD):
    """Google Places API'den mekan bilgilerini ceker"""
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        status = data.get("status")
        if status == "OVER_QUERY_LIMIT":
            safe_print("API limit asildi! 24 saat bekleyin.")
            return None
        elif status == "REQUEST_DENIED":
            safe_print("API key gecersiz!")
            return None
        elif status != "OK":
            safe_print(f"API Hatasi: {status}")
            return []
            
        return data.get("results", [])
        
    except requests.exceptions.RequestException as e:
        safe_print(f"Baglanti hatasi: {e}")
        return []

def is_target_place(place):
    """Mekanin aradigimiz turde olup olmadigini kontrol eder"""
    name = clean_unicode_text(place.get("name", "")).lower()
    types = place.get("types", [])
    
    # Burger kelimeleri
    burger_keywords = ["burger", "hamburger"]
    if any(keyword in name for keyword in burger_keywords):
        return True
    
    # Fast food zincirleri
    chains = ["mcdonalds", "burger king", "kfc", "popeyes", "carl's jr", 
              "hardees", "subway", "dominos", "pizza hut", "wendys"]
    if any(chain in name for chain in chains):
        return True
    
    # Restaurant type + burger-related kelimeler
    food_keywords = ["grill", "steakhouse", "american", "diner", "bbq", "sandwich"]
    if any(ftype in types for ftype in ["restaurant", "meal_takeaway", "food"]):
        if any(keyword in name for keyword in food_keywords):
            return True
    
    return False

def scan_area():
    """Tek bolgeyi tarar"""
    min_lat, max_lat, min_lng, max_lng = BOUNDS
    
    safe_print(f"\n=== {AREA_NAME} Taramasi ===")
    safe_print(f"Koordinatlar: {min_lat:.4f}-{max_lat:.4f}, {min_lng:.4f}-{max_lng:.4f}")
    
    # Grid hesaplama
    lat_steps = int((max_lat - min_lat) / STEP_SIZE) + 1
    lng_steps = int((max_lng - min_lng) / STEP_SIZE) + 1
    total_points = lat_steps * lng_steps
    
    safe_print(f"Grid: {lat_steps} x {lng_steps} = {total_points} nokta")
    safe_print(f"Tahmini sure: {int(total_points * 1.2 / 60)} dakika")
    safe_print(f"Tahmini maliyet: ${total_points * 0.017:.2f}")
    safe_print(f"\n{total_points} API cagrisi yapilacak. Tarama basliyor...")
    time.sleep(2)
    
    # CSV dosyasi olustur
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{AREA_NAME.lower()}_{timestamp}.csv"
    
    found_places = []
    seen_places = set()
    request_count = 0
    start_time = time.time()
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "name", "address", "lat", "lng", "rating", 
            "user_ratings_total", "place_id", "types", "price_level"
        ])
        
        lat = min_lat
        grid_point = 0
        
        while lat <= max_lat:
            lng = min_lng
            while lng <= max_lng:
                grid_point += 1
                progress = (grid_point / total_points) * 100
                
                safe_print(f"[{grid_point:3d}/{total_points}] ({progress:5.1f}%) "
                          f"{lat:.4f}, {lng:.4f}", end=" ")
                
                # API cagrisi
                results = fetch_places(lat, lng)
                request_count += 1
                
                if results is None:  # API limit
                    safe_print("\nAPI limiti! Tarama durduruluyor.")
                    break
                
                # Sonuclari isle
                new_places = 0
                for place in results:
                    place_id = place.get("place_id")
                    
                    # Duplicate kontrol + burger kontrol
                    if place_id not in seen_places and is_target_place(place):
                        seen_places.add(place_id)
                        found_places.append(place)
                        new_places += 1
                        
                        # CSV'ye yaz - Unicode temizle
                        clean_name = clean_unicode_text(place.get("name", ""))
                        clean_address = clean_unicode_text(place.get("vicinity", ""))
                        
                        writer.writerow([
                            clean_name,
                            clean_address,
                            place["geometry"]["location"]["lat"],
                            place["geometry"]["location"]["lng"],
                            place.get("rating", "N/A"),
                            place.get("user_ratings_total", "N/A"),
                            place_id,
                            "|".join(place.get("types", [])),
                            place.get("price_level", "N/A")
                        ])
                        
                        # Anlık goster - Unicode temizle
                        rating = place.get("rating", "N/A")
                        safe_print(f"\n    -> {clean_name} ({rating}/5)")
                
                if new_places == 0:
                    safe_print("-> 0")
                
                time.sleep(1.2)  # Rate limiting
                lng += STEP_SIZE
                
            if results is None:  # API limit durumu
                break
            lat += STEP_SIZE
    
    # Sonuclar
    elapsed = time.time() - start_time
    safe_print(f"\n=== TARAMA TAMAMLANDI ===")
    safe_print(f"Sure: {int(elapsed/60)} dakika {int(elapsed%60)} saniye")
    safe_print(f"Toplam mekan: {len(found_places)}")
    safe_print(f"API cagrisi: {request_count}")
    safe_print(f"Dosya: {filename}")
    
    # Istatistikler
    show_stats(found_places)
    return found_places

def show_stats(places):
    """Bulunan yerlerin istatistiklerini gosterir"""
    if not places:
        return
    
    # Rating'e gore sirala
    rated_places = []
    for place in places:
        rating = place.get("rating")
        total_ratings = place.get("user_ratings_total", 0)
        if rating and rating != "N/A":
            try:
                rating_float = float(rating)
                total_int = int(total_ratings) if total_ratings != "N/A" else 0
                if total_int >= MIN_RATINGS:
                    rated_places.append({
                        "name": clean_unicode_text(place.get("name", "")),
                        "rating": rating_float,
                        "total_ratings": total_int,
                        "address": clean_unicode_text(place.get("vicinity", ""))
                    })
            except (ValueError, TypeError):
                continue
    
    if not rated_places:
        safe_print("Yeterli puanli mekan bulunamadi.")
        return
    
    # En iyi 10
    best_places = sorted(rated_places, key=lambda x: x["rating"], reverse=True)[:10]
    safe_print(f"\nEN IYI 10 HAMBURGERCI:")
    safe_print("-" * 50)
    for i, place in enumerate(best_places, 1):
        safe_print(f"{i:2d}. {place['name']}")
        safe_print(f"    Puan: {place['rating']}/5.0 ({place['total_ratings']} degerlendirme)")
        safe_print(f"    Adres: {place['address']}")
        safe_print("")
    
    # En kotu 10
    worst_places = sorted(rated_places, key=lambda x: x["rating"])[:10]
    safe_print(f"EN KOTU 10 HAMBURGERCI:")
    safe_print("-" * 50)
    for i, place in enumerate(worst_places, 1):
        safe_print(f"{i:2d}. {place['name']}")
        safe_print(f"    Puan: {place['rating']}/5.0 ({place['total_ratings']} degerlendirme)")
        safe_print(f"    Adres: {place['address']}")
        safe_print("")

def main():
    safe_print(f"{AREA_NAME} Hamburgerci Taramasi")
    safe_print("=" * 50)
    
    min_lat, max_lat, min_lng, max_lng = BOUNDS
    
    # Grid hesaplama
    lat_range = max_lat - min_lat
    lng_range = max_lng - min_lng
    lat_steps = int(lat_range / STEP_SIZE) + 1
    lng_steps = int(lng_range / STEP_SIZE) + 1
    total_points = lat_steps * lng_steps
    
    safe_print(f"Alan: {lat_range:.3f}° x {lng_range:.3f}°")
    safe_print(f"Grid: {lat_steps} x {lng_steps} = {total_points} nokta")
    safe_print(f"Step size: {STEP_SIZE} (yaklaşik {STEP_SIZE * 111:.1f} km)")
    
    scan_area()

if __name__ == "__main__":
    main()