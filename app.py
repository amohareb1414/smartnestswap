from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/suggest", methods=["POST"])
def suggest():
    work_location = request.form.get("work_location")

    # مبدئياً: نرجع رسالة فقط للتأكد أن الإدخال يعمل
    return f"<h2>✅ تم استلام موقع العمل: {work_location}</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
