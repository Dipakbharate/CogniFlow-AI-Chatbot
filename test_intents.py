from app.intent_detector import detect_intent

test_queries = [
    "hello there",
    "see you later",
    "generate an image of a dragon",
    "create a pdf document",
    "what is machine learning",
    "do you remember what I told you earlier"
]

print("--- Intent Detection Test ---")
for q in test_queries:
    print(f"Query: '{q}'\nDetected Intent: {detect_intent(q)}\n")
