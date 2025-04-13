from flask import Flask
from flask import request, jsonify,g
import asyncio
from .check_api_key import require_api_key
from server_money import ServerMoney 
app = Flask(__name__)

@app.route("/api/money", methods=["GET"])
@require_api_key
def get_money():
    guild_id = g.guild_id
    user_id = request.args.get("user_id", type=int)

    if not guild_id or not user_id:
        return jsonify({"error": "guild_id and user_id are required"}), 400

    # 非同期関数を同期的に呼び出す
    balance = asyncio.run(ServerMoney().get_balance(guild_id, user_id))

    return jsonify({
        "guild_id": guild_id,
        "user_id": user_id,
        "balance": balance
    })

@app.route("/api/money/add", methods=["POST"])
@require_api_key
def add_money():
    data = request.json
    guild_id = g.guild_id
    user_id = data.get("user_id")
    amount = data.get("amount")
    reason = data.get("reason", "api_add")

    if not all([guild_id, user_id, amount]):
        return jsonify({"error": "guild_id, user_id, and amount are required"}), 400

    try:
        amount = int(amount)
    except ValueError:
        return jsonify({"error": "amount must be an integer"}), 400

    asyncio.run(ServerMoney().add_money(guild_id, user_id, amount, reason))

    return jsonify({
        "message": "Money added successfully",
        "guild_id": guild_id,
        "user_id": user_id,
        "amount": amount,
        "reason": reason
    }), 200


@app.route("/api/money/set", methods=["POST"])
@require_api_key
def set_money():
    data = request.json
    guild_id = g.guild_id
    user_id = data.get("user_id")
    amount = data.get("amount")
    reason = data.get("reason", "api_set")

    if guild_id is None or user_id is None or amount is None:
        return jsonify({"error": "guild_id, user_id, and amount are required"}), 400

    asyncio.run(ServerMoney().set_money(guild_id, user_id, int(amount), reason))
    return jsonify({"message": "Money set successfully"})


@app.route("/api/money/transfer", methods=["POST"])
@require_api_key
def transfer_money():
    data = request.json
    guild_id = g.guild_id
    from_user = data.get("from_user")
    to_user = data.get("to_user")
    amount = data.get("amount")

    if guild_id is None or from_user is None or to_user is None or amount is None:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        asyncio.run(ServerMoney().transfer_money(guild_id, int(from_user), int(to_user), int(amount)))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "Transfer complete"})

def api_run():
    print("api has launched")
    app.run(port=5002,host="0.0.0.0")