from flask import Flask, render_template, request
import math

app = Flask(__name__)

# إحداثيات تقريبية لبعض الأحياء (قابلة للتوسعة لاحقاً)
NEIGHBORHOODS = {
    "المربع":        {"lat":24.6715, "lng":46.7101, "amen": ["مترو - محطة المتحف", "حدائق", "طرق رئيسية"]},
    "حي الوزارات":   {"lat":24.6698, "lng":46.7059, "amen": ["مترو - محطة الوزارات", "طرق رئيسية"]},
    "الملز":         {"lat":24.6866, "lng":46.7320, "amen": ["حديقة الملك عبدالله", "مترو - الملز"]},
    "الرحمانية":     {"lat":24.7335, "lng":46.6408, "amen": ["قرب طريق الملك فهد", "حدائق", "خدمات"]},
    "العليا":        {"lat":24.6921, "lng":46.6858, "amen": ["مترو - العليا", "مراكز أعمال"]},
    "السليمانية":    {"lat":24.6999, "lng":46.7009, "amen": ["طرق رئيسية", "خدمات"]},
    "الورود":        {"lat":24.7268, "lng":46.6673, "amen": ["قرب الملك فهد", "حدائق"]},
    "المعذر":        {"lat":24.6850, "lng":46.6762, "amen": ["قرب الدائري", "خدمات"]},
    "النخيل":        {"lat":24.7456, "lng":46.6255, "amen": ["جامعة الملك سعود", "محطة مترو"]},
    "الواحة":        {"lat":24.7561, "lng":46.7400, "amen": ["طرق رئيسية", "خدمات"]}
}

# أماكن أعمال/جهات مع إحداثيات تقريبية — أضف ما تريد
PLACES = {
    # أمثلة مدخلة
    "وزارة الشؤون البلدية والقروية والإسكان - طريق الملك عبدالله": {"lat":24.7115, "lng":46.7165},
    "أمانة مدينة الرياض": {"lat":24.6516, "lng":46.7107},
    "الديوان الملكي": {"lat":24.6467, "lng":46.6846},
    "مستشفى الحرس الوطني": {"lat":24.7672, "lng":46.8157},

    # أمثلة عامة لأحياء/مناطق إدخال حر (يمكن للمستخدم كتابة الاسم نفسه)
    "طريق الملك عبدالله": {"lat":24.7136, "lng":46.7150},
    "حي الوزارات": {"lat":24.6698, "lng":46.7059},
    "المربع": {"lat":24.6715, "lng":46.7101},
    "الملز": {"lat":24.6866, "lng":46.7320},
    "الرحمانية": {"lat":24.7335, "lng":46.6408}
}

def haversine_km(a, b):
    R = 6371
    dlat = math.radians(b["lat"] - a["lat"])
    dlng = math.radians(b["lng"] - a["lng"])
    lat1 = math.radians(a["lat"])
    lat2 = math.radians(b["lat"])
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def approx_minutes(distance_km, period="mixed"):
    # زمن تقريبي (قابل للضبط لاحقاً). نفترض 28-35 كم/ساعة داخل المدينة.
    speed = 30
    if period == "am":   speed = 26
    if period == "pm":   speed = 24
    return int((distance_km / speed) * 60)

def two_way(minutes_one_way):
    return minutes_one_way * 2

def score_neighborhood(n_loc, people_targets):
    """
    يحسب متوسط زمن الذهاب+العودة لجميع أفراد العائلة إلى جهاتهم،
    مع وزن الفترة الصباحية والمسائية.
    people_targets = [{"who":"أحمد","place":"الديوان الملكي"}, {"who":"سارة","place":"مستشفى الحرس الوطني"}]
    """
    total = 0
    ok = 0
    for p in people_targets:
        target = PLACES.get(p["place"])
        if not target: 
            continue
        dist_km = haversine_km(n_loc, target)
        # نراعي الذهاب (صباح) والعودة (مساء)
        am = approx_minutes(dist_km, "am")
        pm = approx_minutes(dist_km, "pm")
        door_to_door = two_way((am + pm)//2)
        total += door_to_door
        ok += 1
    if ok == 0:
        return 10**9, 0
    return total // ok, ok  # متوسط الدقائق، وعدد من نجح حسابهم

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", neighborhoods=list(NEIGHBORHOODS.keys()))

@app.route("/suggest", methods=["POST"])
def suggest():
    # نجمع عدة أفراد/جهات من النموذج
    people = []
    for i in range(1, 6):  # حتى 5 أفراد الآن (نوسع لاحقاً)
        who = request.form.get(f"who_{i}", "").strip()
        place = request.form.get(f"place_{i}", "").strip()
        if who and place:
            people.append({"who": who, "place": place})

    if not people:
        return render_template("result.html", error="أدخل على الأقل شخصاً واحداً وجهته.")

    # نقيم الأحياء كلها
    scored = []
    for n_name, n_data in NEIGHBORHOODS.items():
        avg_mins, ok = score_neighborhood(n_data, people)
        if ok > 0:
            scored.append({
                "name": n_name,
                "avg_mins": avg_mins,
                "amen": NEIGHBORHOODS[n_name]["amen"]
            })

    scored.sort(key=lambda x: x["avg_mins"])
    top = scored[:8]  # أفضل 8 أحياء مبدئياً

    # نضيف تعليقات مزايا النقل/الحدائق… في البطاقة
    return render_template("result.html", people=people, results=top)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)