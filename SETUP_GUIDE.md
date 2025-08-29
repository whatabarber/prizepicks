# 🎰 BETTING AI: REAL-TIME SETUP GUIDE

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Discord Webhook
1. Go to your Discord server settings
2. Navigate to Integrations → Webhooks
3. Create a new webhook
4. Copy the webhook URL
5. Edit `discord_alert.py` and replace `YOUR_DISCORD_WEBHOOK_URL_HERE` with your actual webhook URL

### 3. Run the Scanner
```bash
python update_all.py
```

## 🤖 AI Analysis Features

### Smart Filtering
- **Bovada**: Analyzes odds for value bets, provides AI commentary
- **PrizePicks**: Filters 2500+ props down to 5-10 best per sport
- **Confidence Scoring**: Each pick gets a 1-10 confidence rating
- **Edge Calculation**: Shows estimated percentage edge for value bets

### AI Commentary
- Explains reasoning behind each recommendation
- Identifies line movement and market inefficiencies  
- Provides confidence levels and value edges
- Gives sport-specific insights

## 🔧 Configuration Options

### Discord Setup
In `discord_alert.py`, replace:
```python
self.webhook_url = "YOUR_DISCORD_WEBHOOK_URL_HERE"
```
With your actual Discord webhook URL:
```python
self.webhook_url = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
```

### Environment Variable (Alternative)
Set webhook URL as environment variable:
```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
```

### AI Analysis Settings
Edit `ai_analyzer.py` to customize:
- `confidence_threshold = 7.0` - Minimum confidence (1-10)
- `max_picks_per_sport = 8` - Max recommendations per sport
- `value_thresholds` - Minimum edge percentages for different bet types

## 🎯 Usage Commands

### AI-Powered Analysis (Default)
```bash
python update_all.py
```

### Continuous AI Mode (Auto-updates every 15 minutes)
```bash
python update_all.py continuous
```

### Custom Interval (e.g., every 5 minutes)
```bash
python update_all.py continuous 5
```

### Raw Data Mode (No AI filtering)
```bash
python update_all.py no-ai
```

### Silent Raw Mode (No AI, no Discord)
```bash
python update_all.py raw
```

### Test Connections
```bash
python update_all.py test
```

### Scan Only Bovada
```bash
python update_all.py bovada
```

### Scan Only PrizePicks
```bash
python update_all.py prizepicks
```

### Run Without Discord Alerts
```bash
python update_all.py no-discord
```

## 📊 Data Output

### JSON Files (saved to `/data` folder)
- `bovada_current.json` - Latest Bovada odds
- `prizepicks_current.json` - Latest PrizePicks projections
- `bovada_YYYYMMDD_HHMMSS.json` - Timestamped backups
- `prizepicks_YYYYMMDD_HHMMSS.json` - Timestamped backups

### Discord Alerts
- Real-time notifications sent to your Discord channel
- Separate alerts for Bovada odds and PrizePicks projections
- Summary reports with scan statistics

## 🏈 Supported Sports

### Bovada
- NFL (Football)
- College Football (CFB)
- NBA (Basketball)
- College Basketball (CBB)
- MLB (Baseball)

### PrizePicks
- NFL player props
- College Football player props
- NBA player props
- College Basketball player props
- MLB player props

## 🛠 Troubleshooting

### Common Issues

#### "Discord webhook failed"
- Verify your webhook URL is correct
- Check Discord server permissions
- Test with: `python update_all.py test`

#### "No data found"
- Sports may be out of season
- API endpoints may be temporarily unavailable
- Check your internet connection

#### "Import errors"
- Run: `pip install -r requirements.txt`
- Ensure Python 3.7+ is installed

### Rate Limiting
- Built-in delays between API calls
- Bovada: 1 second between sports
- PrizePicks: Automatic retry with backoff
- Discord: 1 second between messages

### Legal Compliance
- Ensure sports betting is legal in your jurisdiction
- Respect terms of service for all platforms
- Use for informational purposes only

## 🔄 Automation Options

### Cron Job (Linux/Mac)
Add to crontab for automatic runs:
```bash
# Run every 15 minutes
*/15 * * * * cd /path/to/betting-ai && python update_all.py

# Run every hour
0 * * * * cd /path/to/betting-ai && python update_all.py
```

### Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., every 15 minutes)
4. Action: Start a program
5. Program: `python`
6. Arguments: `update_all.py`
7. Start in: Your project directory

### Background Service
Keep running continuously:
```bash
nohup python update_all.py continuous &
```

## 📈 Performance Tips

### Optimize Scan Speed
- Reduce number of sports in scanner configs
- Increase intervals for continuous mode
- Use `no-discord` mode for faster scanning

### Data Management
- Old backup files in `/data` can be deleted
- Consider rotating logs for long-term usage
- Monitor disk space for continuous operation

## 🔐 Security Notes

- Keep your Discord webhook URL private
- Don't commit webhook URLs to version control
- Use environment variables for sensitive data
- Regular security updates for dependencies

## 💡 Advanced Usage

### Custom Filters
Edit scanners to add custom filtering:
- Minimum odds thresholds
- Specific teams only
- High-value projections only

### Integration
- Import modules into other Python scripts
- Build custom dashboards using JSON data
- Create additional alert channels (email, SMS, etc.)

### Monitoring
- Add logging for production use
- Set up health checks
- Monitor API rate limits

## 🆘 Support

If you encounter issues:
1. Check this guide first
2. Test individual components: `python update_all.py test`
3. Review error messages in console output
4. Ensure all dependencies are properly installed

Remember: This is for informational purposes only. Always comply with local laws and platform terms of service.