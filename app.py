from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB = "bokhtar_city.db"

PRICES = list(range(10, 201, 10))


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            shift TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_number TEXT NOT NULL,
            price INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            shift TEXT NOT NULL,
            worker_money REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            owner_money REAL DEFAULT 0,
            status TEXT DEFAULT 'working',
            created_at TEXT NOT NULL,
            finished_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()

    # Барои базаҳои кӯҳна
    try:
        conn.execute("ALTER TABLE workers ADD COLUMN active INTEGER DEFAULT 1")
        conn.commit()
    except:
        pass

    try:
        conn.execute("ALTER TABLE cars ADD COLUMN status TEXT DEFAULT 'working'")
        conn.commit()
    except:
        pass

    try:
        conn.execute("ALTER TABLE cars ADD COLUMN finished_at TEXT")
        conn.commit()
    except:
        pass

    conn.close()


def current_shift():
    hour = datetime.now().hour

    if 8 <= hour < 20:
        return "day"

    return "night"


def shift_name(shift):
    if shift == "day":
        return "☀️ РӮЗОНА 08:00–20:00"

    return "🌙 ШАБОНА 20:00–08:00"


def worker_balance(worker_id):
    conn = db()

    row = conn.execute("""
        SELECT COALESCE(SUM(worker_money),0) AS total
        FROM cars
        WHERE worker_id=? AND status='finished'
    """, (worker_id,)).fetchone()

    paid = conn.execute("""
        SELECT COALESCE(SUM(amount),0) AS total
        FROM payments
        WHERE worker_id=?
    """, (worker_id,)).fetchone()

    conn.close()

    return round(row["total"] - paid["total"], 2)


HTML = """
<!DOCTYPE html>
<html lang="tg">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>БОХТАР СИТИ</title>

<style>

*{
    box-sizing:border-box;
}

body{
    margin:0;
    font-family:Arial,sans-serif;
    color:white;

    background:
      linear-gradient(135deg,#061b22,#07343d,#031419);

    min-height:100vh;
}

.container{
    width:94%;
    max-width:1100px;
    margin:auto;
    padding:18px 0 40px;
}

.hero{
    min-height:300px;
    border-radius:28px;

    background:
      linear-gradient(
        rgba(0,0,0,.25),
        rgba(0,0,0,.60)
      ),
      url("https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1600&q=90");

    background-size:cover;
    background-position:center;

    box-shadow:
      0 20px 60px rgba(0,0,0,.45),
      inset 0 0 50px rgba(0,0,0,.35);

    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    text-align:center;

    padding:30px;
    margin-bottom:20px;
}

.hero h1{
    font-size:42px;
    margin:8px 0;
    text-shadow:0 5px 20px black;
}

.hero h2{
    margin:5px 0;
    font-size:22px;
}

.hero p{
    font-size:18px;
    font-weight:bold;
}

.cars{
    display:grid;
    grid-template-columns:repeat(5,1fr);
    gap:10px;
    margin-top:25px;
}

.car-img{
    height:80px;
    border-radius:16px;
    background-size:cover;
    background-position:center;
    box-shadow:0 8px 25px rgba(0,0,0,.35);
}

.car1{
    background-image:url("https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=600&q=80");
}

.car2{
    background-image:url("https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?auto=format&fit=crop&w=600&q=80");
}

.car3{
    background-image:url("https://images.unsplash.com/photo-1503736334956-4c8f8e92946d?auto=format&fit=crop&w=600&q=80");
}

.car4{
    background-image:url("https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=600&q=80");
}

.car5{
    background-image:url("https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=600&q=80");
}

.glass{
    background:rgba(255,255,255,.09);
    border:1px solid rgba(255,255,255,.14);
    backdrop-filter:blur(15px);
    -webkit-backdrop-filter:blur(15px);
    border-radius:22px;
    padding:18px;
    margin-bottom:18px;
    box-shadow:0 15px 45px rgba(0,0,0,.25);
}

h2{
    margin-top:0;
}

.shift-buttons{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:12px;
}

button,
.btn{
    border:0;
    border-radius:14px;
    padding:13px 18px;
    font-size:16px;
    font-weight:bold;
    cursor:pointer;
    text-decoration:none;
    display:inline-block;
    color:white;
    background:rgba(255,255,255,.14);
}

button:hover,
.btn:hover{
    background:rgba(255,255,255,.22);
}

.green{
    background:#087f5b;
}

.red{
    background:#a92828;
}

.blue{
    background:#1266a8;
}

.orange{
    background:#b86b00;
}

.worker-grid{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
    gap:14px;
}

.worker{
    padding:18px;
    border-radius:20px;
    background:rgba(255,255,255,.09);
    border:1px solid rgba(255,255,255,.12);
}

.worker h3{
    margin:0 0 8px;
}

.money{
    font-size:25px;
    font-weight:bold;
    margin:10px 0;
}

input,
select{
    width:100%;
    padding:14px;
    margin:7px 0;
    border-radius:13px;
    border:1px solid rgba(255,255,255,.2);
    background:#102f35;
    color:white;
    font-size:16px;
}

label{
    display:block;
    margin-top:8px;
    font-weight:bold;
}

table{
    width:100%;
    border-collapse:collapse;
    margin-top:10px;
}

th,
td{
    padding:12px 8px;
    border-bottom:1px solid rgba(255,255,255,.12);
    text-align:left;
}

.status-working{
    color:#ffd166;
    font-weight:bold;
}

.status-finished{
    color:#5cff9d;
    font-weight:bold;
}

.back{
    margin-bottom:15px;
}

.stats{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
    gap:12px;
}

.stat{
    background:rgba(255,255,255,.08);
    padding:18px;
    border-radius:18px;
}

.stat b{
    display:block;
    font-size:24px;
    margin-top:8px;
}

@media(max-width:650px){

    .hero{
        min-height:270px;
    }

    .hero h1{
        font-size:32px;
    }

    .hero h2{
        font-size:17px;
    }

    .cars{
        grid-template-columns:repeat(5,1fr);
    }

    .car-img{
        height:55px;
    }

    table{
        font-size:13px;
    }

}

</style>
</head>

<body>

<div class="container">

<div class="hero">

    <div style="font-size:20px;">🚗 МОЙКА 24/7</div>

    <h1>БОХТАР СИТИ</h1>

    <h2>✨ БЕҲТАРИН МОЙКА ДАР ШАҲРИ БОХТАР</h2>

    <p>🚕 Сифат • Суръат • Тозагӣ 🚕</p>

    <div class="cars">
        <div class="car-img car1"></div>
        <div class="car-img car2"></div>
        <div class="car-img car3"></div>
        <div class="car-img car4"></div>
        <div class="car-img car5"></div>
    </div>

</div>


<div class="glass">

<h2>🕐 СМЕНАҲО</h2>

<div class="shift-buttons">

<a class="btn blue" href="/?shift=day">
☀️ РӮЗОНА<br>
08:00–20:00
</a>

<a class="btn orange" href="/?shift=night">
🌙 ШАБОНА<br>
20:00–08:00
</a>

</div>

</div>


<div class="glass">

<h2>👷 КОРГАРОН</h2>

<div class="worker-grid">

{% for worker in workers %}

<div class="worker">

<h3>👤 {{ worker["name"] }}</h3>

<div>
{{ shift_name(worker["shift"]) }}
</div>

<div class="money">
💰 {{ "%.2f"|format(worker_balance(worker["id"])) }} с
</div>

<a class="btn blue" href="/worker/{{ worker['id'] }}">
📋 КОРГАР
</a>

<a class="btn red"
   href="/delete_worker/{{ worker['id'] }}"
   onclick="return confirm('Коргарро хориҷ кунем?')">
🚪 РАФТ
</a>

</div>

{% endfor %}

</div>

</div>


<div class="glass">

<h2>➕ ИЛОВАИ КОРГАР</h2>

<form method="post" action="/add_worker">

<label>Номи коргар</label>

<input
    type="text"
    name="name"
    placeholder="Номи коргар"
    required
>

<label>Смена</label>

<select name="shift">

<option value="day">
☀️ РӮЗОНА 08:00–20:00
</option>

<option value="night">
🌙 ШАБОНА 20:00–08:00
</option>

</select>

<button class="green" type="submit">
➕ ИЛОВА КАРДАН
</button>

</form>

</div>


<div class="glass">

<h2>🚗 ИЛОВАИ МОШИН</h2>

<form method="post" action="/add_car">

<label>Рақами мошин</label>

<input
    type="text"
    name="car_number"
    placeholder="TJ 1234 AB"
    required
>

<label>Коргар</label>

<select name="worker_id" required>

{% for worker in workers %}

<option value="{{ worker['id'] }}">
{{ worker['name'] }} — {{ shift_name(worker['shift']) }}
</option>

{% endfor %}

</select>

<label>Нарх</label>

<select name="price" required>

{% for price in prices %}

<option value="{{ price }}">
{{ price }} сомонӣ
</option>

{% endfor %}

</select>

<button class="green" type="submit">
🚗 БА КОР ГУЗОШТАН
</button>

</form>

</div>


<div class="glass">

<h2>📊 ҲИСОБОТ</h2>

<a class="btn blue" href="/report">
📊 КУШОДАНИ ҲИСОБОТ
</a>

</div>

</div>

</body>
</html>
"""


WORKER_HTML = """
<!DOCTYPE html>
<html lang="tg">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1.0">

<title>Коргар</title>

<style>

body{
    margin:0;
    padding:20px;
    background:
    linear-gradient(135deg,#061b22,#07343d);
    color:white;
    font-family:Arial;
}

.container{
    max-width:900px;
    margin:auto;
}

.card{
    background:rgba(255,255,255,.09);
    padding:20px;
    margin-bottom:20px;
    border-radius:22px;
    backdrop-filter:blur(15px);
}

a,button{
    display:inline-block;
    padding:12px 16px;
    border-radius:12px;
    text-decoration:none;
    border:0;
    color:white;
    background:#1266a8;
    font-weight:bold;
    cursor:pointer;
}

.green{
    background:#087f5b;
}

.red{
    background:#a92828;
}

input{
    padding:13px;
    border-radius:12px;
    border:0;
    width:100%;
    box-sizing:border-box;
    margin:8px 0;
    background:#102f35;
    color:white;
}

table{
    width:100%;
    border-collapse:collapse;
}

td,th{
    padding:11px 5px;
    border-bottom:1px solid rgba(255,255,255,.15);
}

.working{
    color:#ffd166;
}

.finished{
    color:#5cff9d;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<a href="/">
⬅️ БОХТАР СИТИ
</a>

<h1>👷 {{ worker["name"] }}</h1>

<p>{{ shift_name(worker["shift"]) }}</p>

<h2>
💰 БАЛАНС:
{{ "%.2f"|format(balance) }} сомонӣ
</h2>

</div>


<div class="card">

<h2>🚗 МОШИНҲО</h2>

<table>

<tr>
<th>Мошин</th>
<th>Нарх</th>
<th>Статус</th>
<th></th>
</tr>

{% for car in cars %}

<tr>

<td>
🚕 {{ car["car_number"] }}
</td>

<td>
{{ car["price"] }} с
</td>

<td>

{% if car["status"] == "working" %}

<span class="working">
⏳ ДАР КОР
</span>

{% else %}

<span class="finished">
✅ АНҶОМ ЁФТ
</span>

{% endif %}

</td>

<td>

{% if car["status"] == "working" %}

<a class="green"
href="/finish_car/{{ car['id'] }}">
✅ АНҶОМИ КОР
</a>

{% endif %}

</td>

</tr>

{% endfor %}

</table>

</div>


<div class="card">

<h2>💵 ПАРДОХТ БА КОРГАР</h2>

<p>
Баланс:
<b>{{ "%.2f"|format(balance) }} сомонӣ</b>
</p>

<form method="post"
action="/pay/{{ worker['id'] }}">

<input
type="number"
step="0.01"
name="amount"
placeholder="Маблағи пардохт"
required
>

<button class="green">
💵 ПАРДОХТ КАРДАН
</button>

</form>

</div>


<div class="card">

<h2>💳 ТАЪРИХИ ПАРДОХТ</h2>

<table>

<tr>
<th>Маблағ</th>
<th>Сана</th>
</tr>

{% for payment in payments %}

<tr>

<td>
{{ "%.2f"|format(payment["amount"]) }} с
</td>

<td>
{{ payment["created_at"] }}
</td>

</tr>

{% endfor %}

</table>

</div>

</div>

</body>
</html>
"""


REPORT_HTML = """
<!DOCTYPE html>
<html lang="tg">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1.0">

<title>Ҳисобот</title>

<style>

body{
    margin:0;
    padding:20px;
    background:linear-gradient(135deg,#061b22,#07343d);
    color:white;
    font-family:Arial;
}

.container{
    max-width:1000px;
    margin:auto;
}

.card{
    background:rgba(255,255,255,.09);
    padding:20px;
    border-radius:22px;
    margin-bottom:20px;
}

.stats{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
    gap:12px;
}

.stat{
    background:rgba(255,255,255,.09);
    padding:18px;
    border-radius:18px;
}

.stat b{
    display:block;
    font-size:24px;
    margin-top:8px;
}

a{
    display:inline-block;
    background:#1266a8;
    color:white;
    padding:12px 16px;
    border-radius:12px;
    text-decoration:none;
    font-weight:bold;
}

table{
    width:100%;
    border-collapse:collapse;
}

td,th{
    padding:11px;
    border-bottom:1px solid rgba(255,255,255,.15);
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<a href="/">
⬅️ БОХТАР СИТИ
</a>

<h1>📊 ҲИСОБОТИ МОЙКА</h1>

</div>


<div class="card">

<div class="stats">

<div class="stat">
🚗 Мошинҳо
<b>{{ cars_count }}</b>
</div>

<div class="stat">
💰 Даромади умумӣ
<b>{{ total }} с</b>
</div>

<div class="stat">
👑 Ҳиссаи соҳиб
<b>{{ owner }} с</b>
</div>

<div class="stat">
👷 Ҳиссаи коргарон
<b>{{ workers_money }} с</b>
</div>

<div class="stat">
🏦 Налог
<b>{{ tax }} с</b>
</div>

</div>

</div>


<div class="card">

<h2>🚗 Таърихи мошинҳо</h2>

<table>

<tr>
<th>Мошин</th>
<th>Нарх</th>
<th>Коргар</th>
<th>Смена</th>
<th>Статус</th>
</tr>

{% for car in cars %}

<tr>

<td>
🚕 {{ car["car_number"] }}
</td>

<td>
{{ car["price"] }} с
</td>

<td>
{{ car["worker_name"] }}
</td>

<td>
{{ shift_name(car["shift"]) }}
</td>

<td>

{% if car["status"] == "finished" %}

✅ АНҶОМ ЁФТ

{% else %}

⏳ ДАР КОР

{% endif %}

</td>

</tr>

{% endfor %}

</table>

</div>

</div>

</body>

</html>
"""


@app.route("/")
def index():

    shift = request.args.get("shift", current_shift())

    conn = db()

    workers = conn.execute("""
        SELECT *
        FROM workers
        WHERE active=1 AND shift=?
        ORDER BY id DESC
    """, (shift,)).fetchall()

    conn.close()

    return render_template_string(
        HTML,
        workers=workers,
        prices=PRICES,
        shift_name=shift_name,
        worker_balance=worker_balance
    )


@app.route("/add_worker", methods=["POST"])
def add_worker():

    name = request.form.get("name", "").strip()
    shift = request.form.get("shift", "day")

    if name:

        conn = db()

        conn.execute("""
            INSERT INTO workers(name,shift,active)
            VALUES(?,?,1)
        """, (name, shift))

        conn.commit()
        conn.close()

    return redirect("/")


@app.route("/add_car", methods=["POST"])
def add_car():

    car_number = request.form.get("car_number", "").strip()
    worker_id = request.form.get("worker_id")
    price = int(request.form.get("price"))
    shift = current_shift()

    if car_number and worker_id:

        conn = db()

        conn.execute("""
            INSERT INTO cars(
                car_number,
                price,
                worker_id,
                shift,
                worker_money,
                tax,
                owner_money,
                status,
                created_at
            )
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            car_number,
            price,
            worker_id,
            shift,
            0,
            0,
            0,
            "working",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

    return redirect("/")


@app.route("/finish_car/<int:car_id>")
def finish_car(car_id):

    conn = db()

    car = conn.execute("""
        SELECT *
        FROM cars
        WHERE id=?
    """, (car_id,)).fetchone()

    if car and car["status"] == "working":

        price = car["price"]

        owner_money = price * 0.50
        worker_money = price * 0.50

        conn.execute("""
            UPDATE cars

            SET
                owner_money=?,
                worker_money=?,
                status='finished',
                finished_at=?

            WHERE id=?
        """, (
            owner_money,
            worker_money,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            car_id
        ))

        conn.commit()

    conn.close()

    return redirect(
        url_for("worker_page",
                worker_id=car["worker_id"])
        if car else "/"
    )


@app.route("/worker/<int:worker_id>")
def worker_page(worker_id):

    conn = db()

    worker = conn.execute("""
        SELECT *
        FROM workers
        WHERE id=?
    """, (worker_id,)).fetchone()

    cars = conn.execute("""
        SELECT *
        FROM cars
        WHERE worker_id=?
        ORDER BY id DESC
    """, (worker_id,)).fetchall()

    payments = conn.execute("""
        SELECT *
        FROM payments
        WHERE worker_id=?
        ORDER BY id DESC
    """, (worker_id,)).fetchall()

    conn.close()

    if not worker:
        return "Коргар ёфт нашуд", 404

    return render_template_string(
        WORKER_HTML,
        worker=worker,
        cars=cars,
        payments=payments,
        balance=worker_balance(worker_id),
        shift_name=shift_name
    )


@app.route("/pay/<int:worker_id>", methods=["POST"])
def pay_worker(worker_id):

    try:
        amount = float(request.form.get("amount", 0))
    except:
        amount = 0

    balance = worker_balance(worker_id)

    if amount > 0 and amount <= balance:

        conn = db()

        conn.execute("""
            INSERT INTO payments(
                worker_id,
                amount,
                created_at
            )
            VALUES(?,?,?)
        """, (
            worker_id,
            amount,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

    return redirect(
        url_for("worker_page",
                worker_id=worker_id)
    )


@app.route("/delete_worker/<int:worker_id>")
def delete_worker(worker_id):

    conn = db()

    conn.execute("""
        UPDATE workers
        SET active=0
        WHERE id=?
    """, (worker_id,))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/report")
def report():

    conn = db()

    cars = conn.execute("""
        SELECT
            cars.*,
            workers.name AS worker_name
        FROM cars

        LEFT JOIN workers
        ON cars.worker_id=workers.id

        ORDER BY cars.id DESC
    """).fetchall()

    total_row = conn.execute("""
        SELECT COALESCE(SUM(price),0) AS total
        FROM cars
        WHERE status='finished'
    """).fetchone()

    owner_row = conn.execute("""
        SELECT COALESCE(SUM(owner_money),0) AS total
        FROM cars
        WHERE status='finished'
    """).fetchone()

    worker_row = conn.execute("""
        SELECT COALESCE(SUM(worker_money),0) AS total
        FROM cars
        WHERE status='finished'
    """).fetchone()

    conn.close()

    total = total_row["total"]
    owner = owner_row["total"]
    workers_money = worker_row["total"]

    # Налог 10 сом барои ҳар коргар як бор дар смена
    # Дар ҳисоботи умумӣ ҳоло ҳамчун маълумоти ҷудогона нишон дода мешавад.
    tax = 0

    return render_template_string(
        REPORT_HTML,
        cars=cars,
        cars_count=len(cars),
        total=total,
        owner=owner,
        workers_money=workers_money,
        tax=tax,
        shift_name=shift_name
    )


if __name__ == "__main__":

    init_db()

    print("=" * 32)
    print("       БОХТАР СИТИ")
    print("=" * 32)
    print("🚗 МОЙКА 24/7")
    print("💧 БЕҲТАРИН МОЙКА ДАР ШАҲРИ БОХТАР")
    print("🌐 http://127.0.0.1:5050")
    print("=" * 32)

    app.run(
        host="0.0.0.0",
        port=5050,
        debug=True
    )
