import requests
import json
from datetime import datetime
import time

class DiscordAlert:
    def __init__(self, webhook_url=None):
        # Your Discord webhook URL is now configured
        self.webhook_url = webhook_url or "https://discord.com/api/webhooks/1400302185673261216/QUbsg0Z0eELuPnFGEBxwxbdM_AOWtJvmPIn-plisyF7GvX_bEFIqh1OY67dEyel7rcvb"
        
        # Discord message limits
        self.max_message_length = 2000
        self.max_embeds = 10
        
    def send_message(self, content, embeds=None, username="Betting AI Bot"):
        """Send a message to Discord webhook"""
        try:
            payload = {
                "username": username,
                "content": content[:self.max_message_length] if content else None
            }
            
            if embeds and len(embeds) <= self.max_embeds:
                payload["embeds"] = embeds
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 204:
                print("Discord message sent successfully")
                return True
            else:
                print(f"Discord webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error sending Discord message: {str(e)}")
            return False

    def send_bovada_alert(self, games_message):
        """Send Bovada games alert"""
        if not games_message or games_message.strip() == "":
            return False
            
        # Split long messages
        messages = self.split_long_message(games_message)
        
        for i, msg in enumerate(messages):
            if i > 0:  # Add delay between multiple messages
                time.sleep(1)
            self.send_message(msg, username="Bovada Scanner")
        
        return True

    def send_prizepicks_alert(self, projections_message):
        """Send PrizePicks projections alert"""
        if not projections_message or projections_message.strip() == "":
            return False
            
        # Split long messages
        messages = self.split_long_message(projections_message)
        
        for i, msg in enumerate(messages):
            if i > 0:  # Add delay between multiple messages
                time.sleep(1)
            self.send_message(msg, username="PrizePicks Scanner")
        
        return True

    def send_combined_alert(self, bovada_data, prizepicks_data):
        """Send combined alert with both Bovada and PrizePicks data"""
        combined_message = "LIVE BETTING UPDATE\n\n"
        
        # Add Bovada section
        if bovada_data:
            combined_message += "BOVADA ODDS\n"
            combined_message += bovada_data + "\n\n"
        
        # Add PrizePicks section
        if prizepicks_data:
            combined_message += "PRIZEPICKS PROPS\n"
            combined_message += prizepicks_data + "\n"
        
        # Send the combined message
        messages = self.split_long_message(combined_message)
        
        for i, msg in enumerate(messages):
            if i > 0:
                time.sleep(1)
            self.send_message(msg, username="Betting AI Complete")
        
        return True

    def send_embed_alert(self, title, description, fields=None, color=0x00ff00):
        """Send rich embed alert"""
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Betting AI Scanner"
            }
        }
        
        if fields:
            embed["fields"] = fields[:25]  # Discord limit
        
        return self.send_message("", embeds=[embed])

    def send_bovada_embed(self, games):
        """Send Bovada data as rich embed"""
        if not games:
            return False
            
        title = f"Bovada Live Odds ({len(games)} games)"
        description = f"Updated: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}"
        
        fields = []
        
        # Group by sport
        sports_games = {}
        for game in games:
            sport = game.get('sport', 'Unknown')
            if sport not in sports_games:
                sports_games[sport] = []
            sports_games[sport].append(game)
        
        for sport, sport_games in sports_games.items():
            field_value = ""
            
            for game in sport_games[:3]:  # Limit to 3 games per sport in embed
                team1 = game.get('team1', 'Team 1')
                team2 = game.get('team2', 'Team 2')
                
                field_value += f"**{team1} vs {team2}**\n"
                
                # Add moneyline if available
                ml = game.get('moneyline', {})
                if ml.get('team1_odds') != 'N/A':
                    field_value += f"ML: {ml['team1_odds']} | {ml['team2_odds']}\n"
                
                field_value += "\n"
            
            if len(sport_games) > 3:
                field_value += f"... and {len(sport_games) - 3} more games"
            
            fields.append({
                "name": f"{sport} ({len(sport_games)})",
                "value": field_value or "No data available",
                "inline": True
            })
        
        return self.send_embed_alert(title, description, fields, color=0xff6b00)

    def send_prizepicks_embed(self, projections):
        """Send PrizePicks data as rich embed"""
        if not projections:
            return False
            
        # Categorize by sport
        sports_projs = {}
        for proj in projections:
            league = proj.get('league', 'Unknown').lower()
            sport = 'NFL' if 'nfl' in league else \
                   'CFB' if 'ncaaf' in league or 'college football' in league else \
                   'NBA' if 'nba' in league else \
                   'CBB' if 'ncaab' in league or 'college basketball' in league else \
                   'MLB' if 'mlb' in league else 'Other'
            
            if sport not in sports_projs:
                sports_projs[sport] = []
            sports_projs[sport].append(proj)
        
        title = f"PrizePicks Live Projections ({len(projections)} total)"
        description = f"Updated: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}"
        
        fields = []
        
        for sport, sport_projs in sports_projs.items():
            if sport == 'Other':
                continue
                
            field_value = ""
            
            for proj in sport_projs[:4]:  # Limit to 4 projections per sport
                player = proj.get('player_name', 'Unknown')
                stat = proj.get('stat_type', '')
                line = proj.get('line_score', 0)
                odds_type = proj.get('odds_type', '')
                
                direction = "Over" if odds_type.lower() == 'over' else \
                           "Under" if odds_type.lower() == 'under' else odds_type
                
                field_value += f"**{player}**\n{stat}: {direction} {line}\n\n"
            
            if len(sport_projs) > 4:
                field_value += f"... and {len(sport_projs) - 4} more"
            
            fields.append({
                "name": f"{sport} ({len(sport_projs)})",
                "value": field_value or "No data available",
                "inline": True
            })
        
        return self.send_embed_alert(title, description, fields, color=0x1e90ff)

    def split_long_message(self, message):
        """Split long messages into Discord-compatible chunks"""
        if len(message) <= self.max_message_length:
            return [message]
        
        messages = []
        current_message = ""
        
        lines = message.split('\n')
        
        for line in lines:
            # If adding this line would exceed limit, save current and start new
            if len(current_message + line + '\n') > self.max_message_length:
                if current_message:
                    messages.append(current_message.strip())
                    current_message = line + '\n'
                else:
                    # Single line is too long, truncate it
                    messages.append(line[:self.max_message_length-3] + "...")
            else:
                current_message += line + '\n'
        
        # Add remaining message
        if current_message:
            messages.append(current_message.strip())
        
        return messages

    def send_error_alert(self, error_message):
        """Send error notification"""
        embed = {
            "title": "Betting Scanner Error",
            "description": f"```{error_message}```",
            "color": 0xff0000,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Error Alert System"
            }
        }
        
        return self.send_message("ERROR DETECTED", embeds=[embed])

    def send_summary_alert(self, bovada_count, prizepicks_count, scan_time):
        """Send scan summary"""
        embed = {
            "title": "Scan Summary",
            "description": "Latest betting data scan completed",
            "color": 0x00ff00,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "Bovada Games",
                    "value": str(bovada_count),
                    "inline": True
                },
                {
                    "name": "PrizePicks Props",
                    "value": str(prizepicks_count),
                    "inline": True
                },
                {
                    "name": "Scan Time",
                    "value": f"{scan_time:.2f}s",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Betting AI Scanner"
            }
        }
        
        return self.send_message("", embeds=[embed])

    def test_webhook(self):
        """Test the Discord webhook connection"""
        if not self.webhook_url or "YOUR_DISCORD_WEBHOOK_URL_HERE" in self.webhook_url:
            print("Please set your Discord webhook URL before testing")
            print("Edit the webhook_url in the DiscordAlert class or pass it as parameter")
            return False
            
        test_message = "TEST MESSAGE\n"
        test_message += f"Webhook connection test at {datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n"
        test_message += "If you see this, your Discord alerts are working!"
        
        return self.send_message(test_message, username="Webhook Test")

if __name__ == "__main__":
    # Test the Discord webhook
    alert = DiscordAlert()
    
    if alert.webhook_url == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("Please set your Discord webhook URL before testing")
        print("Edit the webhook_url in the DiscordAlert class")
    else:
        print("Testing Discord webhook...")
        success = alert.test_webhook()
        if success:
            print("Discord webhook test successful!")
        else:
            print("Discord webhook test failed")