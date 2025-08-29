# Add to your update_all.py file

from github_deployer import GitHubDeployer

# Add this to your BettingAI class
class BettingAI:
    def __init__(self, discord_webhook=None):
        print("Initializing Betting AI Scanner...")
        
        # Initialize existing components
        self.bovada = BovadaScanner()
        self.prizepicks = PrizePicksScanner()
        self.discord = DiscordAlert(discord_webhook)
        self.analyzer = BettingAIAnalyzer()
        self.deployer = GitHubDeployer()  # NEW: GitHub deployer
        
        # Configuration
        self.send_discord_alerts = True
        self.save_data = True
        self.use_ai_analysis = True
        self.deploy_to_github = True  # NEW: Auto-deploy option
        self.min_games_threshold = 1
        self.min_projections_threshold = 1
        
        # Create data directory
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def run_full_scan(self):
        """Run complete scan with GitHub deployment"""
        print("\n" + "="*60)
        print("STARTING FULL BETTING SCAN WITH AUTO-DEPLOY")
        print("="*60)
        
        start_time = time.time()
        
        try:
            # Existing scan logic...
            bovada_games = self.scan_bovada()
            time.sleep(2)
            prizepicks_projections = self.scan_prizepicks()
            
            # AI Analysis
            bovada_analysis = []
            prizepicks_analysis = []
            
            if self.use_ai_analysis:
                print("\nRunning AI Analysis...")
                
                if bovada_games:
                    print(f"Analyzing {len(bovada_games)} Bovada games...")
                    bovada_analysis = self.analyzer.analyze_bovada_games(bovada_games)
                    print(f"Found {len(bovada_analysis)} high-value Bovada plays")
                
                if prizepicks_projections:
                    print(f"Analyzing {len(prizepicks_projections)} PrizePicks projections...")
                    prizepicks_analysis = self.analyzer.analyze_prizepicks_projections(prizepicks_projections)
                    print(f"Found {len(prizepicks_analysis)} high-confidence props")
                
                if self.save_data:
                    self.save_analysis_data(bovada_analysis, prizepicks_analysis)
            
            # NEW: Deploy to GitHub
            if self.deploy_to_github:
                print("\nDeploying to GitHub...")
                self.create_dashboard_file()
                if self.deployer.deploy_dashboard():
                    dashboard_url = "https://whatabarber.github.io/prizepicks/"
                    print(f"Dashboard live at: {dashboard_url}")
                else:
                    print("GitHub deployment failed")
            
            scan_time = time.time() - start_time
            
            # Send Discord alerts with dashboard link
            if self.send_discord_alerts:
                print("\nSending Discord alerts...")
                if self.use_ai_analysis:
                    self.send_enhanced_ai_alerts(bovada_analysis, prizepicks_analysis, scan_time)
                else:
                    self.send_alerts(bovada_games, prizepicks_projections, scan_time)
            
            self.print_final_summary(bovada_games, prizepicks_projections, bovada_analysis, prizepicks_analysis, scan_time)
            
            return {
                'bovada_games': bovada_games,
                'prizepicks_projections': prizepicks_projections,
                'bovada_analysis': bovada_analysis,
                'prizepicks_analysis': prizepicks_analysis,
                'scan_time': scan_time,
                'dashboard_url': 'https://whatabarber.github.io/prizepicks/' if self.deploy_to_github else None,
                'success': True
            }
            
        except Exception as e:
            error_msg = f"Critical error during scan: {str(e)}"
            print(f"Error: {error_msg}")
            
            if self.send_discord_alerts:
                self.discord.send_error_alert(error_msg)
            
            return {'error': error_msg, 'success': False}

    def create_dashboard_file(self):
        """Create the dashboard HTML file with current data"""
        dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrizePicks AI Dashboard</title>
    <!-- Include the CSS and HTML from the dashboard artifact above -->
</head>
<body>
    <!-- Include the HTML body from the dashboard artifact above -->
    
    <script>
        // Modified script to load from GitHub Pages
        async function loadPicks() {
            try {
                // Load from the deployed data files
                const analysisResponse = await fetch('./data/prizepicks_analysis.json');
                const bovadaResponse = await fetch('./data/bovada_analysis.json');
                
                let allPicks = [];
                
                if (analysisResponse.ok) {
                    const prizepicksData = await analysisResponse.json();
                    allPicks = allPicks.concat(prizepicksData || []);
                }
                
                if (bovadaResponse.ok) {
                    const bovadaData = await bovadaResponse.json();
                    // Convert Bovada format to display format if needed
                    allPicks = allPicks.concat(bovadaData || []);
                }
                
                if (allPicks.length === 0) {
                    loadDemoData();
                    return;
                }
                
                // Filter to only NFL and CFB
                allPicks = allPicks.filter(pick => {
                    const sport = pick.sport || pick.league;
                    return sport && (
                        sport.includes('NFL') || 
                        sport.includes('CFB') || 
                        sport.includes('NCAAF')
                    );
                });
                
                updateStats();
                displayPicks(allPicks);
                updateLastUpdateTime();
                
            } catch (error) {
                console.error('Error loading picks:', error);
                loadDemoData();
            }
        }
        
        // Rest of the JavaScript from the dashboard
        // ... (include all the dashboard JavaScript here)
    </script>
</body>
</html>"""
        
        # Save to docs folder for GitHub Pages
        os.makedirs("docs", exist_ok=True)
        with open("docs/index.html", "w") as f:
            f.write(dashboard_html)

    def send_enhanced_ai_alerts(self, bovada_analysis, prizepicks_analysis, scan_time):
        """Send enhanced Discord alerts with dashboard link"""
        try:
            dashboard_url = "https://whatabarber.github.io/prizepicks/"
            
            # Create enhanced message
            message = f"AI BETTING ANALYSIS UPDATE\n\n"
            message += f"Full Dashboard: {dashboard_url}\n\n"
            
            # Bovada summary
            if bovada_analysis:
                message += f"BOVADA TOP PICKS ({len(bovada_analysis)} games):\n"
                for i, analysis in enumerate(bovada_analysis[:3], 1):
                    message += f"{i}. {analysis['matchup']} - {analysis['confidence_score']:.1f}/10\n"
                    for rec in analysis['recommendations'][:1]:
                        message += f"   • {rec['bet_type']}: {rec['recommendation']}\n"
                
                if len(bovada_analysis) > 3:
                    message += f"... +{len(bovada_analysis) - 3} more on dashboard\n"
                message += "\n"
            
            # PrizePicks summary with variety
            if prizepicks_analysis:
                # Group by player to show variety
                players_shown = set()
                unique_picks = []
                
                for pick in prizepicks_analysis:
                    player = pick['player_name']
                    if player not in players_shown or len(unique_picks) < 5:
                        unique_picks.append(pick)
                        players_shown.add(player)
                        if len(unique_picks) >= 8:  # Limit to 8 diverse picks
                            break
                
                message += f"PRIZEPICKS TOP PROPS ({len(prizepicks_analysis)} total, showing diverse picks):\n"
                for i, pick in enumerate(unique_picks[:5], 1):
                    rec_parts = pick['recommendation'].split()
                    stat_line = ' '.join(rec_parts[-3:])  # Get "Over/Under X.X StatType"
                    message += f"{i}. {pick['player_name']}: {stat_line} ({pick['confidence_score']:.1f}/10)\n"
                
                remaining = len(prizepicks_analysis) - len(unique_picks)
                if remaining > 0:
                    message += f"... +{remaining} more players on dashboard\n"
            
            message += f"\nScan Time: {scan_time:.1f}s"
            message += f"\nAuto-updated every scan | View all picks: {dashboard_url}"
            
            # Send via Discord
            self.discord.send_message(message, username="AI Betting Dashboard")
            print("Enhanced Discord alert sent successfully")
            
        except Exception as e:
            print(f"Failed to send enhanced Discord alerts: {str(e)}")

    def print_final_summary(self, bovada_games, prizepicks_projections, bovada_analysis, prizepicks_analysis, scan_time):
        """Print comprehensive summary"""
        print("\n" + "="*70)
        print("BETTING AI SCAN COMPLETE")
        print("="*70)
        print(f"Raw Data:")
        print(f"  • Bovada Games: {len(bovada_games)}")
        print(f"  • PrizePicks Projections: {len(prizepicks_projections)}")
        
        if self.use_ai_analysis:
            print(f"\nAI-Filtered Results:")
            print(f"  • High-Value Bovada Plays: {len(bovada_analysis)}")
            print(f"  • High-Confidence Props: {len(prizepicks_analysis)}")
            
            # Show variety stats
            if prizepicks_analysis:
                unique_players = len(set(p['player_name'] for p in prizepicks_analysis))
                print(f"  • Unique Players: {unique_players}")
                
                stat_types = set(p.get('stat_type', '') for p in prizepicks_analysis)
                print(f"  • Stat Types: {', '.join(list(stat_types)[:5])}")
        
        print(f"\nSystem Status:")
        print(f"  • Scan Time: {scan_time:.2f} seconds")
        print(f"  • Discord Alerts: {'Sent' if self.send_discord_alerts else 'Disabled'}")
        print(f"  • GitHub Deploy: {'Success' if self.deploy_to_github else 'Disabled'}")
        
        if self.deploy_to_github:
            print(f"  • Dashboard: https://whatabarber.github.io/prizepicks/")
        
        print("="*70)


# Update main function to support new features
def main():
    print("BETTING AI: REAL-TIME SCANNER WITH AUTO-DEPLOY")
    print("=" * 55)
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    ai = BettingAI(webhook_url)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'no-deploy':
            ai.deploy_to_github = False
            ai.run_full_scan()
        elif command == 'deploy-only':
            ai.create_dashboard_file()
            ai.deployer.deploy_dashboard()
        elif command == 'football-only':
            # This is now default behavior
            ai.run_full_scan()
        # ... other existing commands
    else:
        result = ai.run_full_scan()
        
        if result['success']:
            if result.get('dashboard_url'):
                print(f"\nDashboard available at: {result['dashboard_url']}")
            print("\nTips:")
            print("  • Dashboard auto-refreshes every 5 minutes")
            print("  • Run 'python update_all.py continuous' for auto-updates")
            print("  • Run 'python update_all.py no-deploy' to skip GitHub upload")


if __name__ == "__main__":
    main()