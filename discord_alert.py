# Add this method to your DiscordAlert class in discord_alert.py

def send_combined_alert_with_dashboard(self, bovada_data, prizepicks_data):
    """Send combined alert with dashboard link"""
    combined_message = "🚨 **LIVE BETTING UPDATE** 🚨\n\n"
    
    # Add dashboard link at the top
    combined_message += "📊 **FULL DASHBOARD**: https://whatabarber.github.io/prizepicks/\n\n"
    
    # Add Bovada section (shortened for Discord)
    if bovada_data and len(bovada_data) > 0:
        combined_message += f"🏈 **BOVADA TOP PICKS** ({len(bovada_data)} games)\n"
        # Show only top 3 to save space
        for analysis in bovada_data[:3]:
            combined_message += f"• **{analysis['matchup']}**\n"
            for rec in analysis['recommendations'][:1]:  # Only show top rec
                combined_message += f"  {rec['bet_type']}: {rec['recommendation']} ({rec['confidence']:.1f}/10)\n"
        
        if len(bovada_data) > 3:
            combined_message += f"... and {len(bovada_data) - 3} more games on dashboard\n"
        combined_message += "\n"
    
    # Add PrizePicks section (shortened)
    if prizepicks_data and len(prizepicks_data) > 0:
        combined_message += f"🎯 **PRIZEPICKS TOP PROPS** ({len(prizepicks_data)} total)\n"
        
        # Group by sport and show limited picks
        sports_props = {}
        for prop in prizepicks_data:
            sport = prop['sport']
            if sport not in sports_props:
                sports_props[sport] = []
            sports_props[sport].append(prop)
        
        for sport, props in sports_props.items():
            if sport == 'Other':
                continue
            combined_message += f"**{sport}** - Top {min(3, len(props))} picks:\n"
            for prop in props[:3]:  # Show only top 3 per sport
                combined_message += f"• {prop['player_name']}: {prop['recommendation'].split()[-3:]} ({prop['confidence_score']:.1f}/10)\n"
            
            if len(props) > 3:
                combined_message += f"  ... +{len(props) - 3} more on dashboard\n"
            combined_message += "\n"
    
    combined_message += "📊 **VIEW ALL PICKS**: https://whatabarber.github.io/prizepicks/\n"
    combined_message += "🔄 Dashboard auto-refreshes every 5 minutes"
    
    # Send the message
    messages = self.split_long_message(combined_message)
    
    for i, msg in enumerate(messages):
        if i > 0:
            time.sleep(1)
        self.send_message(msg, username="AI Betting Dashboard")
    
    return True