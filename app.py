from flask import Flask, request
import json
from datetime import datetime
import matplotlib.pyplot as plt
from flask import Response
from collections import defaultdict
import io


app = Flask(__name__)

# Load existing data (if file exists)
try:
    with open("data.json", "r") as file:
        expenses = json.load(file)
except:
    expenses = []

@app.route("/")
def home():
    expense_list = "<br>".join([f"{e['amount']} - {e.get('category','No Category')} - {e['time']}" for e in expenses[-5:]])
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Expense Tracker</title>

    <style>
        body {{
            font-family: Arial;
            background-color: #f5f7fa;
            text-align: center;
        }}

        .container {{
            width: 400px;
            margin: auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
        }}

        input, select {{
            width: 90%;
            padding: 10px;
            margin: 5px;
        }}

        button {{
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }}

        a {{
            display: block;
            margin: 5px;
            color: blue;
            text-decoration: none;
        }}

        .expense {{
            background: #f1f1f1;
            margin: 5px;
            padding: 5px;
            border-radius: 5px;
        }}
    </style>
</head>

<body>

<div class="container">
    <h1>Expense Tracker</h1>

    <form action="/add" method="post">
        <input name="amount" placeholder="Enter amount">

        <select name="category">
            <option value="Food">Food</option>
            <option value="Groceries">Groceries</option>
            <option value="Shopping">Shopping</option>
            <option value="Rent">Rent</option>
            <option value="Entertainment">Entertainment</option>
            <option value="Health">Health</option>
            <option value="Travel">Travel</option>
            <option value="Other">Other</option>
        </select>

        <input name="custom_category" placeholder="Custom category (only if Other)">

        <button type="submit">Add Expense</button>
    </form>

    <hr>

    <a href="/chart">View Chart</a>
    <a href="/summary">View Summary</a>
    <a href="/total">Show Total</a>
    <a href="/all">Show All Expenses</a>
    <a href="/delete">Delete Last Expense</a>
    <a href="/clear">Clear All</a>

    <hr>

    <h3>Recent Expenses</h3>
    {''.join([f"<div class='expense'>{e['amount']} - {e.get('category','No Category')} - {e['time']}</div>" for e in expenses[-5:]])}

</div>

</body>
</html>
"""

@app.route("/add", methods=["POST"])
def add():
    amount = request.form["amount"]
    category = request.form["category"]
    custom = request.form["custom_category"]

    # ✅ Hybrid category logic
    allowed_categories = [
        "Food", "Groceries", "Shopping",
        "Rent", "Entertainment", "Health", "Travel"
    ]

    if category == "Other":
        if not custom:
            return "<h3>Enter custom category</h3><a href='/'>Go Back</a>"

        custom = custom.strip()

        if not custom.isalpha():
            return "<h3>Invalid category (letters only)</h3><a href='/'>Go Back</a>"

        if len(custom) < 3:
            return "<h3>Category too short</h3><a href='/'>Go Back</a>"

        category = custom.capitalize()

    elif category not in allowed_categories:
        return "<h3>Invalid category</h3><a href='/'>Go Back</a>"

    # ✅ Amount validation
    if not amount.isdigit():
        return "<h3>Invalid input (numbers only)</h3><a href='/'>Go Back</a>"

    amount = int(amount)

    if amount <= 0:
        return "<h3>Amount must be positive</h3><a href='/'>Go Back</a>"

    # ✅ Store data
    expenses.append({
        "amount": amount,
        "category": category,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # ✅ Save file
    with open("data.json", "w") as file:
        json.dump(expenses, file)

    return "<h3>Expense Added</h3><a href='/'>Go Back</a>"

@app.route("/total")
def total():
    return f"<h3>Total Expense: {sum(item["amount"] for item in expenses)}</h3><a href='/'>Go Back</a>"

@app.route("/all")
def all_expenses():
    return "<br>".join([f"{e['amount']} - {e.get('category','No Category')} - {e['time']}" for e in expenses]) + "<br><a href='/'>Go Back</a>"

@app.route("/clear")
def clear():
    expenses.clear()

    # also clear file
    with open("data.json", "w") as file:
        json.dump(expenses, file)

    return "<br>".join([f"{e['amount']} - {e['time']}" for e in expenses]) + "<br><a href='/'>Go Back</a>"

@app.route("/delete")
def delete():
    if expenses:
        expenses.pop()

        with open("data.json", "w") as file:
            json.dump(expenses, file)

    return "<h3>Last expense deleted</h3><a href='/'>Go Back</a>"

@app.route("/chart")
def chart():
    category_totals = defaultdict(int)

    # group data
    for e in expenses:
        category_totals[e["category"]] += e["amount"]

    labels = list(category_totals.keys())
    values = list(category_totals.values())

    # create chart
    plt.figure(figsize=(6,6))
    plt.pie(values, labels=labels, autopct='%1.1f%%')
    plt.title("Expense Distribution")

    # convert to image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return Response(img.getvalue(), mimetype='image/png')

@app.route("/summary")
def summary():
    category_totals = {}

    for e in expenses:
        cat = e["category"]
        category_totals[cat] = category_totals.get(cat, 0) + e["amount"]

    total = sum(category_totals.values())

    if total == 0:
        return "<h3>No data available</h3><a href='/'>Go Back</a>"

    result = "<h2>Expense Analysis</h2><br>"

    # 🔹 Sort categories (highest first)
    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

    # 🔹 Top 3 categories
    result += "<b>Top Spending Categories:</b><br>"
    for k, v in sorted_cats[:3]:
        percent = (v / total) * 100
        result += f"{k}: ₹{v} ({percent:.1f}%)<br>"
    
    result += "<br>"

    # 🔹 Detailed insights
    for k, v in category_totals.items():
        percent = (v / total) * 100

        if percent > 40:
            comment = f"⚠️ You are overspending on {k}. Try reducing it."
        elif percent > 20:
            comment = f"Moderate spending on {k}"
        else:
            comment = f"Low spending on {k} 👍"

        result += f"{k}: ₹{v} ({percent:.1f}%) → {comment}<br><br>"

    # 🔹 Daily average (basic logic)
    days = len(expenses) if len(expenses) > 0 else 1
    avg = total / days

    result += f"<b>Average spending per entry:</b> ₹{avg:.1f}<br><br>"

    # 🔹 Highest spending category
    max_cat = sorted_cats[0][0]
    result += f"<b>Biggest expense category:</b> {max_cat}<br>"

    return result + "<br><a href='/'>Go Back</a>"

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
