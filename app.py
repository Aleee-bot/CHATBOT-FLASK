import os
from dotenv import load_dotenv
import torch
from flask import Flask , render_template , jsonify , request
from transformers import AutoModelForCausalLM, AutoTokenizer
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")

db = SQLAlchemy(app)

class Flower(db.Model):
    __tablename__ = 'flowers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.String(80), nullable=False)
    sold_quantity = db.Column(db.String(80), nullable=False)
    sale_price = db.Column(db.String(80), nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    reply = get_chat_response(user_message) #"this is bot reply" 
    return jsonify({"reply": reply})

def get_chat_response(text):
    chat_history_ids = None
    # Let's chat for 5 lines
    for step in range(5):
        # encode the new user input, add the eos_token and return a tensor in Pytorch
        new_user_input_ids = tokenizer.encode(str(text) + tokenizer.eos_token, return_tensors='pt')

        # append the new user input tokens to the chat history
        bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if step > 0 else new_user_input_ids

        # generated a response while limiting the total chat history to 1000 tokens, 
        chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)

        # pretty print last ouput tokens from bot
        return tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)

@app.route("/flowers")
def flowers():
    flowers = Flower.query.all()
    flower_list = []
    for flower in flowers:
        flower_list.append({
            "id": flower.id,
            "name": flower.name,
            "price": flower.price,
            "sold_quantity": flower.sold_quantity,
            "sale_price": flower.sale_price
        })
    return jsonify(flower_list)

@app.route("/add_flower", methods=["POST"])
def add_flower():
    data = request.get_json()
    new_flower = Flower(
        name=data["name"],
        price=data["price"],
        sold_quantity=data["sold_quantity"],
        sale_price=data["sale_price"]
    )
    db.session.add(new_flower)
    db.session.commit()
    return jsonify({"message": "Flower added successfully!"}) , 201

if __name__ == "__main__":
    app.run(debug=True)