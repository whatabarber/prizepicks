# Create this file: test_imports.py
try:
    from bovada_scanner import BovadaScanner
    print("BovadaScanner imported successfully")
except Exception as e:
    print(f"BovadaScanner import failed: {e}")

try:
    from prizepicks_scanner import PrizePicksScanner
    print("PrizePicksScanner imported successfully")
except Exception as e:
    print(f"PrizePicksScanner import failed: {e}")

try:
    from discord_alert import DiscordAlert
    print("DiscordAlert imported successfully")
except Exception as e:
    print(f"DiscordAlert import failed: {e}")

try:
    from ai_analyzer import BettingAIAnalyzer
    print("BettingAIAnalyzer imported successfully")
except Exception as e:
    print(f"BettingAIAnalyzer import failed: {e}")