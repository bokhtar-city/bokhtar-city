from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB = "bokhtar_city.db"

PRICES = list(range(10, 201, 10))


# =========================
# DATABASE
# =========================

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            shift TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_number TEXT NOT NULL,
            price REAL NOT NULL,
            worker_id INTEGER NOT NULL,
            shift TEXT NOT NULL,
            worker_money REAL NOT NULL,
            tax REAL NOT NULL,
            owner_money REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    con.commit()
    con.close()


# =========================
# HELPERS
# =========================

def shift_name(shift):
    if shift == "day":
        return "☀️ Рӯзона"
    return "🌙 Шабона"


def current_shift():
    hour = datetime.now().hour

    if 8 <= hour < 20:
        return "day"

    return "night"


def worker_balance(worker_id):
    con = db()

    earned = con.execute("""
        SELECT COALESCE(SUM(worker_money), 0)
        FROM cars
        WHERE worker_id=?
    """, (worker_id,)).fetchone()[0]

    paid = con.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE worker_id=?
    """, (worker_id,)).fetchone()[0]

    con.close()

    return earned - paid


# =========================
# DESIGN
# =========================

STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #f2f4f7;
    font-family: Arial, sans-serif;
    color: #17202a;
}

.header {
    background: #111827;
    color: white;
    padding: 22px 15px;
    text-align: center;
}

.header h1 {
    margin: 0;
    font-size: 29px;
}

.header p {
    margin: 6px 0 0;
    color: #d1d5db;
}

.container {
    max-width: 720px;
    margin: auto;
    padding: 15px;
}

.tabs {
    display: flex;
    gap: 10px;
    margin: 15px 0;
}

.tab {
    flex: 1;
    padding: 17px 8px;
    border-radius: 15px;
    text-align: center;
    text-decoration: none;
    font-weight: bold;
    background: white;
    color: #111827;
    box-shadow: 0 2px 8px #0001;
}

.active {
    background: #111827;
    color: white;
}

.card {
    background: white;
    border-radius: 17px;
    padding: 18px;
    margin: 13px 0;
    box-shadow: 0 2px 10px #0001;
}

.card h2 {
    margin-top: 0;
}

input,
select,
button {
    width: 100%;
    padding: 14px;
    margin: 7px 0;
    border-radius: 11px;
    border: 1px solid #ddd;
    font-size: 16px;
}

button {
    background: #111827;
    color: white;
    border: none;
    font-weight: bold;
}

.danger {
    background: #c62828;
}

.price-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
}

.price-box {
    background: #eef2ff;
    padding: 13px 4px;
    border-radius: 11px;
    text-align: center;
    font-weight: bold;
    cursor: pointer;
}

.price-box input {
    display: none;
}

.price-box:has(input:checked) {
    background: #111827;
    color: white;
}

.worker {
    display: block;
    background: white;
    padding: 18px;
    margin: 10px 0;
    border-radius: 15px;
    text-decoration: none;
    color: #111827;
    box-shadow: 0 2px 8px #0001;
}

.worker-name {
    font-size: 20px;
    font-weight: bold;
}

.balance {
    color: #16803c;
    font-weight: bold;
}

.stat {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    padding: 11px 0;
    border-bottom: 1px solid #eee;
}

.big {
    font-size: 28px;
    font-weight: bold;
}

.green {
    color: #16803c;
}

.red {
    color: #c62828;
}

.gray {
    color: #6b7280;
    font-size: 13px;
}

.back {
    display: block;
    text-align: center;
    padding: 15px;
    margin-top: 12px;
    background: #111827;
    color: white;
    text-decoration: none;
    border-radius: 12px;
}

@media(max-width:450px) {
    .price-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

</style>
"""


# =========================
# INIT
# =========================

init_db()


# =========================
# HOME
# =========================

@app.route("/")
def index():

    shift = request.args.get("shift", current_shift())

    con = db()

    workers = con.execute("""
        SELECT *
        FROM workers
        WHERE shift=?
        AND active=1
        ORDER BY name
    """, (shift,)).fetchall()

    stats = con.execute("""
        SELECT
            COALESCE(SUM(price), 0) AS total,
            COALESCE(SUM(owner_money), 0) AS owner,
            COALESCE(SUM(tax), 0) AS tax,
            COALESCE(SUM(worker_money), 0) AS workers
        FROM cars
        WHERE shift=?
    """, (shift,)).fetchone()

    con.close()

    return render_template_string(
        STYLE + """

<div class="header">

    <h1>🚗 БОХТАР СИТИ</h1>

    <p>Системаи ҳисобу китоби мойка</p>

</div>


<div class="container">


    <!-- SHIFTS -->

    <div class="tabs">

        <a class="tab {% if shift == 'day' %}active{% endif %}"
           href="/?shift=day">

            ☀️ РӮЗОНА

            <br>

            <span class="gray">
                08:00 – 20:00
            </span>

        </a>


        <a class="tab {% if shift == 'night' %}active{% endif %}"
           href="/?shift=night">

            🌙 ШАБОНА

            <br>

            <span class="gray">
                20:00 – 08:00
            </span>

        </a>

    </div>


    <!-- ADD WORKER -->

    <div class="card">

        <h2>
            👷 Коргар — {{ shift_name(shift) }}
        </h2>

        <form method="post"
              action="/add_worker">

            <input
                type="hidden"
                name="shift"
                value="{{ shift }}"
            >

            <input
                type="text"
                name="name"
                placeholder="Номи коргар"
                required
            >

            <button>
                ➕ Илова кардани коргар
            </button>

        </form>

    </div>


    <!-- WORKERS -->

    <div class="card">

        <h2>👷 Коргарон</h2>


        {% if workers %}

            {% for w in workers %}

                <a class="worker"
                   href="/worker/{{ w.id }}">

                    <div class="worker-name">

                        {{ w.name }}

                    </div>

                    <div class="gray">

                        {{ shift_name(w.shift) }}

                    </div>

                    <br>

                    💰 Баланс:

                    <span class="balance">

                        {{ "%.2f"|format(worker_balance(w.id)) }}с

                    </span>

                </a>

            {% endfor %}

        {% else %}

            <p>
                Ҳоло коргар илова нашудааст.
            </p>

        {% endif %}

    </div>


    <!-- ADD CAR -->

    <div class="card">

        <h2>🚗 Мошини нав</h2>


        <form method="post"
              action="/add_car">


            <input
                type="text"
                name="car_number"
                placeholder="Рақами мошин"
                required
            >


            <select
                name="worker_id"
                required
            >

                <option value="">
                    Коргарро интихоб кунед
                </option>

                {% for w in workers %}

                    <option value="{{ w.id }}">

                        {{ w.name }}

                    </option>

                {% endfor %}

            </select>


            <h3>
                💰 Нархи мошин
            </h3>


            <div class="price-grid">

                {% for p in prices %}

                    <label class="price-box">

                        <input
                            type="radio"
                            name="price"
                            value="{{ p }}"
                            required
                        >

                        {{ p }}с

                    </label>

                {% endfor %}

            </div>


            <button>

                🚗 Сабти мошин

            </button>


        </form>

    </div>


    <!-- SHIFT REPORT -->

    <div class="card">

        <h2>
            📊 Ҳисоби {{ shift_name(shift) }}
        </h2>


        <div class="stat">

            <span>
                💰 Даромад
            </span>

            <b>
                {{ stats.total }}с
            </b>

        </div>


        <div class="stat">

            <span>
                🏢 Соҳиби мойка
            </span>

            <b>
                {{ stats.owner }}с
            </b>

        </div>


        <div class="stat">

            <span>
                🧾 Налог
            </span>

            <b>
                {{ stats.tax }}с
            </b>

        </div>


        <div class="stat">

            <span>
                👷 Коргарон
            </span>

            <b>
                {{ stats.workers }}с
            </b>

        </div>

    </div>


    <!-- 24 HOURS -->

    <div class="card">

        <h2>
            📊 Ҳисоби 24 соат
        </h2>

        <a class="worker"
           href="/report">

            Дидани ҳисоботи пурраи 24 соат →

        </a>

    </div>


</div>

        """,
        shift=shift,
        workers=workers,
        stats=stats,
        prices=PRICES,
        shift_name=shift_name,
        worker_balance=worker_balance
    )


# =========================
# ADD WORKER
# =========================

@app.route("/add_worker", methods=["POST"])
def add_worker():

    name = request.form["name"].strip()
    shift = request.form["shift"]

    if name:

        con = db()

        con.execute("""
            INSERT INTO workers
            (name, shift, active)
            VALUES (?, ?, 1)
        """, (name, shift))

        con.commit()
        con.close()

    return redirect("/?shift=" + shift)


# =========================
# ADD CAR
# =========================

@app.route("/add_car", methods=["POST"])
def add_car():

    car_number = request.form["car_number"].strip()

    price = float(request.form["price"])

    worker_id = int(request.form["worker_id"])


    con = db()


    worker = con.execute("""
        SELECT shift
        FROM workers
        WHERE id=?
        AND active=1
    """, (worker_id,)).fetchone()


    if not worker:

        con.close()

        return redirect("/")


    shift = worker["shift"]


    # 50% OWNER

    owner_money = price * 0.50


    # 50% WORKER

    worker_share = price * 0.50


    # TAX

    tax = 10


    # FINAL WORKER MONEY

    worker_money = worker_share - tax


    con.execute("""
        INSERT INTO cars
        (
            car_number,
            price,
            worker_id,
            shift,
            worker_money,
            tax,
            owner_money,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        car_number,
        price,
        worker_id,
        shift,
        worker_money,
        tax,
        owner_money,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))


    con.commit()

    con.close()


    return redirect("/?shift=" + shift)


# =========================
# WORKER PAGE
# =========================

@app.route("/worker/<int:worker_id>")
def worker_page(worker_id):

    con = db()


    worker = con.execute("""
        SELECT *
        FROM workers
        WHERE id=?
    """, (worker_id,)).fetchone()


    if not worker:

        con.close()

        return "Коргар ёфт нашуд"


    cars = con.execute("""
        SELECT *
        FROM cars
        WHERE worker_id=?
        ORDER BY id DESC
    """, (worker_id,)).fetchall()


    payments = con.execute("""
        SELECT *
        FROM payments
        WHERE worker_id=?
        ORDER BY id DESC
    """, (worker_id,)).fetchall()


    earned = con.execute("""
        SELECT COALESCE(SUM(worker_money), 0)
        FROM cars
        WHERE worker_id=?
    """, (worker_id,)).fetchone()[0]


    paid = con.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE worker_id=?
    """, (worker_id,)).fetchone()[0]


    con.close()


    balance = earned - paid


    return render_template_string(
        STYLE + """

<div class="header">

    <h1>
        👷 {{ worker.name }}
    </h1>

    <p>
        БОХТАР СИТИ
    </p>

</div>


<div class="container">


    <!-- BALANCE -->

    <div class="card">

        <div class="stat">

            <span>
                💰 Пули коркарда
            </span>

            <b>
                {{ "%.2f"|format(earned) }}с
            </b>

        </div>


        <div class="stat">

            <span>
                💸 Пули гирифта
            </span>

            <b>
                {{ "%.2f"|format(paid) }}с
            </b>

        </div>


        <div class="stat">

            <span>
                💵 Баланс
            </span>

            <b class="big green">

                {{ "%.2f"|format(balance) }}с

            </b>

        </div>

    </div>


    <!-- PAY -->

    <div class="card">

        <h2>
            💸 Ба коргар пул додан
        </h2>


        <form
            method="post"
            action="/pay/{{ worker.id }}"
        >

            <input
                type="number"
                name="amount"
                min="0.01"
                step="0.01"
                placeholder="Масалан: 20"
                required
            >


            <button>
                ➖ Аз баланс кам кардан
            </button>

        </form>

    </div>


    <!-- DELETE -->

    {% if worker.active == 1 %}

    <div class="card">

        <h2>
            ⚠️ Хориҷ кардани коргар
        </h2>


        <form
            method="post"
            action="/delete_worker/{{ worker.id }}"
            onsubmit="return confirm(
                'Коргарро хориҷ мекунед? Ҳисобҳои пешина нигоҳ дошта мешаванд.'
            )"
        >

            <button class="danger">

                ❌ Удалить коргар

            </button>

        </form>

    </div>

    {% else %}

    <div class="card">

        <h2>
            ❌ Коргар хориҷ шудааст
        </h2>

        <p class="gray">
            Ҳисобҳои пешинаи ин коргар нигоҳ дошта шудаанд.
        </p>

    </div>

    {% endif %}


    <!-- CARS -->

    <div class="card">

        <h2>
            🚗 Мошинҳои коргар
        </h2>


        {% for c in cars %}

            <div class="stat">

                <span>

                    🚗 {{ c.car_number }}

                    <br>

                    <span class="gray">

                        {{ c.created_at }}

                    </span>

                </span>


                <b>

                    {{ c.price }}с

                    →

                    {{ "%.2f"|format(c.worker_money) }}с

                </b>

            </div>

        {% else %}

            <p>
                Мошин нест.
            </p>

        {% endfor %}

    </div>


    <!-- PAYMENTS -->

    <div class="card">

        <h2>
            💸 Таърихи пардохтҳо
        </h2>


        {% for p in payments %}

            <div class="stat">

                <span>
                    {{ p.created_at }}
                </span>

                <b class="red">

                    -{{ p.amount }}с

                </b>

            </div>

        {% else %}

            <p>
                Ҳоло пардохт нест.
            </p>

        {% endfor %}

    </div>


    <a
        class="back"
        href="/?shift={{ worker.shift }}"
    >

        ← Бозгашт

    </a>


</div>

        """,
        worker=worker,
        cars=cars,
        payments=payments,
        earned=earned,
        paid=paid,
        balance=balance
    )


# =========================
# PAY WORKER
# =========================

@app.route("/pay/<int:worker_id>", methods=["POST"])
def pay_worker(worker_id):

    amount = float(request.form["amount"])


    if amount > 0:

        con = db()


        balance = worker_balance(worker_id)


        # Бештар аз баланс додан иҷозат нест

        if amount <= balance:

            con.execute("""
                INSERT INTO payments
                (
                    worker_id,
                    amount,
                    created_at
                )

                VALUES (?, ?, ?)
            """, (
                worker_id,
                amount,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ))


            con.commit()


        con.close()


    return redirect(
        "/worker/" + str(worker_id)
    )


# =========================
# DELETE / DEACTIVATE WORKER
# =========================

@app.route(
    "/delete_worker/<int:worker_id>",
    methods=["POST"]
)
def delete_worker(worker_id):

    con = db()


    worker = con.execute("""
        SELECT shift
        FROM workers
        WHERE id=?
    """, (worker_id,)).fetchone()


    if worker:

        con.execute("""
            UPDATE workers
            SET active=0
            WHERE id=?
        """, (worker_id,))


        con.commit()


        shift = worker["shift"]

    else:

        shift = current_shift()


    con.close()


    return redirect(
        "/?shift=" + shift
    )


# =========================
# 24 HOUR REPORT
# =========================

@app.route("/report")
def report():

    con = db()


    day = con.execute("""
        SELECT
            COALESCE(SUM(price), 0) total,
            COALESCE(SUM(owner_money), 0) owner,
            COALESCE(SUM(tax), 0) tax,
            COALESCE(SUM(worker_money), 0) workers
        FROM cars
        WHERE shift='day'
    """).fetchone()


    night = con.execute("""
        SELECT
            COALESCE(SUM(price), 0) total,
            COALESCE(SUM(owner_money), 0) owner,
            COALESCE(SUM(tax), 0) tax,
            COALESCE(SUM(worker_money), 0) workers
        FROM cars
        WHERE shift='night'
    """).fetchone()


    total = con.execute("""
        SELECT
            COALESCE(SUM(price), 0) total,
            COALESCE(SUM(owner_money), 0) owner,
            COALESCE(SUM(tax), 0) tax,
            COALESCE(SUM(worker_money), 0) workers
        FROM cars
    """).fetchone()


    con.close()


    return render_template_string(
        STYLE + """

<div class="header">

    <h1>
        📊 ҲИСОБОТИ 24 СОАТ
    </h1>

    <p>
        🚗 БОХТАР СИТИ
    </p>

</div>


<div class="container">


    <!-- DAY -->

    <div class="card">

        <h2>
            ☀️ Рӯзона — 12 соат
        </h2>


        <div class="stat">

            <span>
                Даромад
            </span>

            <b>
                {{ day.total }}с
            </b>

        </div>


        <div class="stat">

            <span>
                Соҳиб
            </span>

            <b>
                {{ day.owner }}с
            </b>

        </div>


        <div class="stat">

            <span>
                Налог
            </span>

            <b>
                {{ day.tax }}с
            </b>

        </div>


        <div class="stat">

            <span>
                Коргарон
            </span>

            <b>
                {{ day.workers }}с
            </b>

        </div>

    </div>


    <!-- NIGHT -->

    <div class="card">

        <h2>
            🌙 Шабона — 12 соат
        </h2>


        <div class="stat">

            <span>
                Даромад
            </span>

            <b>
                {{ night.total }}с
            </b>

        </div>


        <div class="stat">

            <span>
                Соҳиб
            </span>

            <b>
                {{ night.owner }}с
            </b>

        </div>


        <div class="stat">

            <span>
                Налог
            </span>

            <b>
                {{ night.tax }}с
            </b>

        </div>


        <div class="stat">

            <span>
                Коргарон
            </span>

            <b>
                {{ night.workers }}с
            </b>

        </div>

    </div>


    <!-- TOTAL -->

    <div class="card">

        <h2>
            📊 ҲАМАГӢ — 24 СОАТ
        </h2>


        <div class="stat">

            <span>
                💰 Даромади умумӣ
            </span>

            <b class="big">
                {{ total.total }}с
            </b>

        </div>


        <div class="stat">

            <span>
                🏢 Соҳиби мойка
            </span>

            <b>
                {{ total.owner }}с
            </b>

        </div>


        <div class="stat">

            <span>
                🧾 Налог
            </span>

            <b>
                {{ total.tax }}с
            </b>

        </div>


        <div class="stat">

            <span>
                👷 Коргарон
            </span>

            <b>
                {{ total.workers }}с
            </b>

        </div>

    </div>


    <a
        class="back"
        href="/"
    >

        ← Бозгашт

    </a>


</div>

        """,
        day=day,
        night=night,
        total=total
    )


# =========================
# START
# =========================

if __name__ == "__main__":

    print("")
    print("================================")
    print("        БОХТАР СИТИ")
    print("        CAR WASH SYSTEM")
    print("================================")
    print("")
    print("Open: http://127.0.0.1:5050")
    print("")

    app.run(
        host="0.0.0.0",
        port=5050,
        debug=True
    )
