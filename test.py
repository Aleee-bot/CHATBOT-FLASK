from app import app
from chatbot import get_chat_response

with app.app_context():
    print("=" * 50)
    print("🌸 Flower Shop Chatbot")
    print("Type your question and press Enter")
    print("Type 'exit' to quit")
    print("=" * 50)

    while True:
        question = input("\nOwner: ").strip()

        if not question:
            print("Please type a question!")
            continue

        if question.lower() == "exit":
            print("Goodbye! 🌸")
            break

        try:
            response = get_chat_response(question)
            print(f"\nChatbot: {response}")
        except Exception as e:
            print(f"\nError: {e}")

        print("-" * 50)