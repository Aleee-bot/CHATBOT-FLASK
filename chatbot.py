from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from database import db
from sqlalchemy import text


print("Loading Text-to-SQL model...")
model_path = 'gaussalgo/T5-LM-Large-text2sql-spider'
sql_model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
sql_tokenizer = AutoTokenizer.from_pretrained(model_path)


print("Loading Flan-T5 model...")
flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
flan_model     = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
flan_model.eval()


SCHEMA = """
CREATE TABLE flowers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    quantity INTEGER NOT NULL,
    price FLOAT NOT NULL
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    flower_id INTEGER REFERENCES flowers(id),
    quantity INTEGER NOT NULL,
    total_price FLOAT NOT NULL,
    order_date TIMESTAMP DEFAULT NOW()
);
"""


def generate_sql(user_question):
    """Convert owner's question to SQL query."""

    prompt = f"tables:\n{SCHEMA}\nquery for: {user_question}"

    inputs = sql_tokenizer(
        prompt,
        padding=True,
        truncation=True,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = sql_model.generate(
            **inputs,
            max_length=256,
            num_beams=4,
            early_stopping=True
        )

    sql = sql_tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Generated SQL: {sql}")
    return sql.strip()


def run_sql(sql):
    """Run the generated SQL on PostgreSQL."""
    try:
        if not sql.strip().lower().startswith("select"):
            return None, "Only SELECT queries are allowed."

        result  = db.session.execute(text(sql))
        rows    = result.fetchall()
        columns = list(result.keys())
        data    = [dict(zip(columns, row)) for row in rows]
        return data, None

    except Exception as e:
        db.session.rollback()
        print(f"SQL Error: {e}")
        return None, str(e)


def generate_text(prompt):
    inputs = flan_tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True
    )
    with torch.no_grad():
        outputs = flan_model.generate(
            **inputs,
            max_length=200,
            num_beams=4,
            early_stopping=True
        )
    return flan_tokenizer.decode(outputs[0], skip_special_tokens=True)



def generate_description(user_question, data):
    """Use Flan-T5 to describe the result and give suggestions."""


    data_str = "\n".join(
        [", ".join(f"{k}: {v}" for k, v in row.items()) for row in data]
    )


    description_prompt = f"""
    You are a friendly flower shop assistant reporting to the owner.
    The owner asked: "{user_question}"
    The database returned this data:
    {data_str}

    Write a brief and clear description of this result in 2-3 sentences.
    """
    description = generate_text(description_prompt)

    return description 


def get_chat_response(user_question):
    """Main function called from app.py."""

    sql = generate_sql(user_question)

    data, error = run_sql(sql)

    if error or not data:
        data_str = "No data found."
    else:
        data_str = "\n".join(
            [", ".join(f"{k}: {v}" for k, v in row.items()) for row in data]
        )

    description = generate_text(f"""
    You are a friendly flower shop assistant reporting to the owner.
    Reply in a friendly and professional way.
    Keep it short and mention you can help with
    shop reports like sales, stock, orders and customers.
    The owner asked: "{user_question}"
    The database returned this data:
    {data_str}

    Write a brief and clear description of this result in 2-3 sentences.
    """)

    return description


