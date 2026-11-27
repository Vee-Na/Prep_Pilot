def evaluate_answer(question_text, answer_text):
    # temp py file before LLM integration
    words = len(answer_text.split())
    score = min(10.0, round(words / 5, 1))
    feedback = 'Placeholder feedback: LLM scoring is not connected yet.'
    return score, feedback