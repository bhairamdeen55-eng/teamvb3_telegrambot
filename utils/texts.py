# utils/texts.py
START_TEXT = (
    "👋 <b>Welcome to TeamVB3 Educational Bot!</b>\n\n"
    "I'm your AI-powered learning assistant. Here's what I can do:\n\n"
    "📝 <b>Quizzes</b> — Test your knowledge with topic-wise quizzes\n"
    "📚 <b>DPP</b> — Daily Practice Problems for consistent learning\n"
    "📸 <b>Photo Test</b> — Upload handwritten answers for AI evaluation\n"
    "📊 <b>Scores</b> — Track your progress and performance\n"
    "🎯 <b>Personalized</b> — AI-powered adaptive learning\n\n"
    "Use /menu to explore all features or just send me a message!"
)

MENU_TEXT = (
    "📌 <b>Main Menu</b>\n\n"
    "Choose what you'd like to do:"
)

QUIZ_INTRO = (
    "🧠 <b>Smart Quiz Mode</b>\n\n"
    "I'll ask you questions one by one. "
    "Select a topic to get started, or try a random quiz!"
)

DPP_INTRO = (
    "📚 <b>Daily Practice Problems</b>\n\n"
    "Practice makes perfect! Select a topic to get problems."
)

PHOTO_TEST_INTRO = (
    "📸 <b>Photo Test</b>\n\n"
    "Upload a photo of your handwritten answers or notes, "
    "and I'll evaluate them using AI!\n\n"
    "Supported formats: JPG, PNG\n"
    "Max size: 20MB"
)

HELP_TEXT = (
    "❓ <b>Help & Support</b>\n\n"
    "<b>Commands:</b>\n"
    "/start — Start the bot\n"
    "/menu — Main menu\n"
    "/quiz — Start a quiz\n"
    "/dpp — Daily practice problems\n"
    "/test — Upload photo for evaluation\n"
    "/score — Check your scores\n"
    "/help — This message\n"
    "/admin — Admin panel (admins only)\n\n"
    "<b>Need help?</b>\n"
    "Contact @admin for support"
)

SCORE_TEXT = (
    "📊 <b>Your Performance</b>\n\n"
    "Total Quizzes: {total_attempts}\n"
    "Average Score: {avg_percentage}%\n"
    "Correct Answers: {total_correct}\n"
    "Wrong Answers: {total_wrong}\n\n"
    "Keep practicing to improve!"
)

ERROR_TEXT = "⚠️ Something went wrong. Please try again later."
UNAUTHORIZED = "⛔ You don't have permission to use this command."
LIMIT_REACHED = "⚠️ You've reached your daily limit. Upgrade to premium for unlimited access!"
