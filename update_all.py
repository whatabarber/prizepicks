#!/usr/bin/env python3
"""
BETTING AI: REAL-TIME DATA SCANNER
Fetches live odds from Bovada and projections from PrizePicks
Sends alerts to Discord and saves data locally
"""

import os
import sys
import time
import json
from datetime import datetime
import traceback

# Import our custom modules
from bovada_scanner import BovadaScanner
from prizepicks_scanner import PrizePicksScanner
from discord_alert import DiscordAlert
from ai_analyzer import BettingAIAnalyzer

# GitHub deployment with actual git commands
def deploy_to_github():
    """Deploy data files to GitHub repository"""
    try:
        import subprocess
        import os
        import shutil
        
        print("Starting GitHub deployment...")
        
        # First, check if we're in a git repository
        if not os.path.exists('.git'):
            print("Error: Not in a git repository. Run 'git init' first.")
            return False
        
        # Copy JSON files to root directory (where Vercel can access them)
        data_files = [
            "prizepicks_analysis.json",
            "bovada_analysis.json", 
            "prizepicks_current.json",
            "bovada_current.json"
        ]
        
        files_copied = []
        for file in data_files:
            src = os.path.join("data", file)
            dst = file  # Copy to root directory
            
            if os.path.exists(src):
                shutil.copy2(src, dst)
                files_copied.append(file)
                print(f"Copied {file} to root directory")
        
        if not files_copied:
            print("No data files to deploy")
            return False
        
        # Git commands to commit and push
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_message = f"Auto-update betting data - {timestamp}"
        
        # Add files
        add_result = subprocess.run(
            ["git", "add"] + files_copied,
            capture_output=True, 
            text=True
        )
        
        if add_result.returncode != 0:
            print(f"Git add failed: {add_result.stderr}")
            return False
        
        # Commit files
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True
        )
        
        if commit_result.returncode != 0:
            if "nothing to commit" in commit_result.stdout:
                print("No changes to commit")
                return True
            else:
                print(f"Git commit failed: {commit_result.stderr}")
                return False
        
        # FIXED: Try main first, then master
        push_result = subprocess.run(
            ["git", "push", "origin", "main"],
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            print("Failed to push to 'main', trying 'master'...")
            push_result = subprocess.run(
                ["git", "push", "origin", "master"],
                capture_output=True,
                text=True
            )
            
            if push_result.returncode != 0:
                print(f"Git push failed on both branches: {push_result.stderr}")
                print("Try running: git push origin main --force")
                return False
        
        print(f"Successfully pushed to GitHub: {commit_message}")
        print("Vercel should auto-deploy in ~30 seconds")
        return True
        
    except Exception as e:
        print(f"GitHub deployment failed: {str(e)}")
        return False


class BettingAI:
    def __init__(self, discord_webhook=None):
        print("Initializing Betting AI Scanner...")
        
        # Initialize scanners
        self.bovada = BovadaScanner()
        self.prizepicks = PrizePicksScanner()
        self.discord = DiscordAlert(discord_webhook)
        self.analyzer = BettingAIAnalyzer()
        
        # Configuration
        self.send_discord_alerts = True
        self.save_data = True
        self.use_ai_analysis = True
        self.deploy_to_github = True
        self.min_games_threshold = 1
        self.min_projections_threshold = 1
        
        # Create data directory
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"Created data directory: {self.data_dir}")

    def run_full_scan(self):
        """Run complete scan of both Bovada and PrizePicks"""
        print("\n" + "="*60)
        print("STARTING FULL BETTING SCAN")
        print("="*60)
        
        start_time = time.time()
        
        try:
            # Scan Bovada
            print("\nSCANNING BOVADA...")
            bovada_games = self.scan_bovada()
            
            # Small delay between scans
            time.sleep(2)
            
            # Scan PrizePicks
            print("\nSCANNING PRIZEPICKS...")
            prizepicks_projections = self.scan_prizepicks()
            
            # AI Analysis
            bovada_analysis = []
            prizepicks_analysis = []
            
            if self.use_ai_analysis:
                print("\nRUNNING AI ANALYSIS...")
                
                # Analyze Bovada games
                if bovada_games:
                    print(f"Analyzing {len(bovada_games)} Bovada games...")
                    bovada_analysis = self.analyzer.analyze_bovada_games(bovada_games)
                    print(f"Found {len(bovada_analysis)} high-value Bovada plays")
                
                # Analyze PrizePicks projections
                if prizepicks_projections:
                    print(f"Analyzing {len(prizepicks_projections)} PrizePicks projections...")
                    prizepicks_analysis = self.analyzer.analyze_prizepicks_projections(prizepicks_projections)
                    print(f"Found {len(prizepicks_analysis)} high-confidence props")
                
                # Save analysis results
                if self.save_data:
                    self.save_analysis_data(bovada_analysis, prizepicks_analysis)
            
            # Deploy to GitHub Pages
            if self.deploy_to_github:
                print("\nPREPARING GITHUB PAGES DEPLOYMENT...")
                deploy_to_github()
            
            # Calculate scan time
            scan_time = time.time() - start_time
            
            # Send alerts if enabled
            if self.send_discord_alerts:
                print("\nSENDING DISCORD ALERTS...")
                if self.use_ai_analysis:
                    self.send_enhanced_ai_alerts(bovada_analysis, prizepicks_analysis, scan_time)
                else:
                    self.send_alerts(bovada_games, prizepicks_projections, scan_time)
            
            # Print summary
            if self.use_ai_analysis:
                self.print_ai_summary(bovada_games, prizepicks_projections, bovada_analysis, prizepicks_analysis, scan_time)
            else:
                self.print_summary(bovada_games, prizepicks_projections, scan_time)
            
            return {
                'bovada_games': bovada_games,
                'prizepicks_projections': prizepicks_projections,
                'bovada_analysis': bovada_analysis if self.use_ai_analysis else [],
                'prizepicks_analysis': prizepicks_analysis if self.use_ai_analysis else [],
                'scan_time': scan_time,
                'success': True
            }
            
        except Exception as e:
            error_msg = f"Critical error during scan: {str(e)}"
            print(f"Error: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Send error alert
            if self.send_discord_alerts:
                self.discord.send_error_alert(error_msg)
            
            return {
                'error': error_msg,
                'success': False
            }

    def scan_bovada(self):
        """Scan Bovada for live odds"""
        try:
            games = self.bovada.scan_all_sports()
            
            if self.save_data:
                self.save_bovada_data(games)
            
            print(f"Bovada scan complete: {len(games)} games found")
            return games
            
        except Exception as e:
            error_msg = f"Bovada scan failed: {str(e)}"
            print(f"Error: {error_msg}")
            return []

    def scan_prizepicks(self):
        """Scan PrizePicks for live projections"""
        try:
            projections = self.prizepicks.scan_all_projections()
            
            if self.save_data:
                self.save_prizepicks_data(projections)
            
            print(f"PrizePicks scan complete: {len(projections)} projections found")
            return projections
            
        except Exception as e:
            error_msg = f"PrizePicks scan failed: {str(e)}"
            print(f"Error: {error_msg}")
            return []

    def send_enhanced_ai_alerts(self, bovada_analysis, prizepicks_analysis, scan_time):
        """Send enhanced Discord alerts with dashboard link and variety"""
        try:
            dashboard_url = "https://prizepicks-one.vercel.app/"
            
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
                # Show diverse players instead of repetitive picks
                players_shown = set()
                unique_picks = []
                
                for pick in prizepicks_analysis:
                    player = pick['player_name']
                    if player not in players_shown or len(unique_picks) < 5:
                        unique_picks.append(pick)
                        players_shown.add(player)
                        if len(unique_picks) >= 8:
                            break
                
                message += f"PRIZEPICKS TOP PROPS ({len(prizepicks_analysis)} total, showing diverse picks):\n"
                for i, pick in enumerate(unique_picks[:5], 1):
                    rec_parts = pick['recommendation'].split()
                    stat_line = ' '.join(rec_parts[-3:])
                    message += f"{i}. {pick['player_name']}: {stat_line} ({pick['confidence_score']:.1f}/10)\n"
                
                remaining = len(prizepicks_analysis) - len(unique_picks)
                if remaining > 0:
                    message += f"... +{remaining} more players on dashboard\n"
            
            message += f"\nScan Time: {scan_time:.1f}s"
            message += f"\nView all picks: {dashboard_url}"
            
            # Send via Discord
            self.discord.send_message(message, username="AI Betting Dashboard")
            print("Enhanced Discord alert sent successfully")
            
        except Exception as e:
            print(f"Failed to send enhanced Discord alerts: {str(e)}")

    def send_alerts(self, bovada_games, prizepicks_projections, scan_time):
        """Send Discord alerts with scan results"""
        try:
            send_bovada = len(bovada_games) >= self.min_games_threshold
            send_prizepicks = len(prizepicks_projections) >= self.min_projections_threshold
            
            if not send_bovada and not send_prizepicks:
                print("Not enough data to send alerts")
                return
            
            if send_bovada:
                bovada_message = self.bovada.format_for_discord(bovada_games)
                self.discord.send_bovada_alert(bovada_message)
                time.sleep(1)
            
            if send_prizepicks:
                prizepicks_message = self.prizepicks.format_for_discord(prizepicks_projections)
                self.discord.send_prizepicks_alert(prizepicks_message)
                time.sleep(1)
            
            self.discord.send_summary_alert(len(bovada_games), len(prizepicks_projections), scan_time)
            
            print("Discord alerts sent successfully")
            
        except Exception as e:
            print(f"Failed to send Discord alerts: {str(e)}")

    def save_analysis_data(self, bovada_analysis, prizepicks_analysis):
        """Save AI analysis results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if bovada_analysis:
                bovada_file = os.path.join(self.data_dir, 'bovada_analysis.json')
                with open(bovada_file, 'w') as f:
                    json.dump(bovada_analysis, f, indent=2)
                
                backup_file = os.path.join(self.data_dir, f'bovada_analysis_{timestamp}.json')
                with open(backup_file, 'w') as f:
                    json.dump(bovada_analysis, f, indent=2)
            
            if prizepicks_analysis:
                prizepicks_file = os.path.join(self.data_dir, 'prizepicks_analysis.json')
                with open(prizepicks_file, 'w') as f:
                    json.dump(prizepicks_analysis, f, indent=2)
                
                backup_file = os.path.join(self.data_dir, f'prizepicks_analysis_{timestamp}.json')
                with open(backup_file, 'w') as f:
                    json.dump(prizepicks_analysis, f, indent=2)
            
            print("AI analysis data saved")
            
        except Exception as e:
            print(f"Failed to save analysis data: {str(e)}")

    def save_bovada_data(self, games):
        """Save Bovada data to files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            current_file = os.path.join(self.data_dir, 'bovada_current.json')
            with open(current_file, 'w') as f:
                json.dump(games, f, indent=2)
            
            backup_file = os.path.join(self.data_dir, f'bovada_{timestamp}.json')
            with open(backup_file, 'w') as f:
                json.dump(games, f, indent=2)
            
            print(f"Bovada data saved to {current_file}")
            
        except Exception as e:
            print(f"Failed to save Bovada data: {str(e)}")

    def save_prizepicks_data(self, projections):
        """Save PrizePicks data to files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            current_file = os.path.join(self.data_dir, 'prizepicks_current.json')
            with open(current_file, 'w') as f:
                json.dump(projections, f, indent=2)
            
            backup_file = os.path.join(self.data_dir, f'prizepicks_{timestamp}.json')
            with open(backup_file, 'w') as f:
                json.dump(projections, f, indent=2)
            
            print(f"PrizePicks data saved to {current_file}")
            
        except Exception as e:
            print(f"Failed to save PrizePicks data: {str(e)}")

    def print_ai_summary(self, bovada_games, prizepicks_projections, bovada_analysis, prizepicks_analysis, scan_time):
        """Print AI analysis summary"""
        print("\n" + "="*60)
        print("AI BETTING ANALYSIS SUMMARY")
        print("="*60)
        print(f"Raw Data Collected:")
        print(f"   Bovada Games: {len(bovada_games)}")
        print(f"   PrizePicks Projections: {len(prizepicks_projections)}")
        print(f"")
        print(f"AI-Filtered Recommendations:")
        print(f"   High-Value Bovada Plays: {len(bovada_analysis)}")
        print(f"   High-Confidence Props: {len(prizepicks_analysis)}")
        print(f"")
        
        if bovada_analysis:
            print("TOP BOVADA RECOMMENDATIONS:")
            for i, analysis in enumerate(bovada_analysis[:3], 1):
                print(f"   {i}. {analysis['matchup']} - Confidence: {analysis['confidence_score']:.1f}/10")
                for rec in analysis['recommendations']:
                    print(f"      • {rec['bet_type']}: {rec['recommendation']} ({rec['odds']})")
        
        if prizepicks_analysis:
            print("TOP PRIZEPICKS RECOMMENDATIONS:")
            # Show variety of players
            shown_players = set()
            count = 1
            for prop in prizepicks_analysis:
                if prop['player_name'] not in shown_players and count <= 5:
                    print(f"   {count}. {prop['recommendation']} - Confidence: {prop['confidence_score']:.1f}/10")
                    shown_players.add(prop['player_name'])
                    count += 1
        
        print(f"")
        print(f"Total Scan Time: {scan_time:.2f} seconds")
        print(f"Dashboard: https://whatabarber.github.io/prizepicks/")
        print(f"Completed At: {datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}")
        print("="*60)

    def print_summary(self, bovada_games, prizepicks_projections, scan_time):
        """Print scan summary"""
        print("\n" + "="*60)
        print("SCAN SUMMARY")
        print("="*60)
        print(f"Bovada Games Found: {len(bovada_games)}")
        print(f"PrizePicks Projections Found: {len(prizepicks_projections)}")
        print(f"Total Scan Time: {scan_time:.2f} seconds")
        print(f"Discord Alerts: {'Enabled' if self.send_discord_alerts else 'Disabled'}")
        print(f"Data Saving: {'Enabled' if self.save_data else 'Disabled'}")
        print(f"Completed At: {datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}")
        print("="*60)

    def run_continuous(self, interval_minutes=15):
        """Run scanner continuously at specified interval"""
        print(f"Starting continuous mode (every {interval_minutes} minutes)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_full_scan()
                print(f"\nWaiting {interval_minutes} minutes until next scan...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\nContinuous mode stopped by user")
        except Exception as e:
            print(f"\nContinuous mode error: {str(e)}")

    def test_connections(self):
        """Test all connections"""
        print("Testing connections...")
        
        if self.discord.webhook_url != "YOUR_DISCORD_WEBHOOK_URL_HERE":
            print("Testing Discord webhook...")
            discord_success = self.discord.test_webhook()
            print(f"Discord: {'Success' if discord_success else 'Failed'}")
        else:
            print("Discord webhook not configured")
        
        print("Testing Bovada connection...")
        try:
            test_games = self.bovada.fetch_sport_data('NFL', 'football')
            bovada_success = isinstance(test_games, list)
            print(f"Bovada: {'Success' if bovada_success else 'Failed'}")
        except:
            print("Bovada: Failed")
        
        print("Testing PrizePicks connection...")
        try:
            test_leagues = self.prizepicks.get_active_leagues()
            prizepicks_success = isinstance(test_leagues, list)
            print(f"PrizePicks: {'Success' if prizepicks_success else 'Failed'}")
        except:
            print("PrizePicks: Failed")

def main():
    """Main function"""
    print("BETTING AI: REAL-TIME SCANNER")
    print("=" * 50)
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    ai = BettingAI(webhook_url)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            ai.test_connections()
        elif command == 'continuous':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 15
            ai.run_continuous(interval)
        elif command == 'bovada':
            ai.scan_bovada()
        elif command == 'prizepicks':
            ai.scan_prizepicks()
        elif command == 'no-discord':
            ai.send_discord_alerts = False
            ai.run_full_scan()
        elif command == 'no-ai':
            ai.use_ai_analysis = False
            ai.run_full_scan()
        elif command == 'raw':
            ai.use_ai_analysis = False
            ai.send_discord_alerts = False
            ai.run_full_scan()
        elif command == 'no-deploy':
            ai.deploy_to_github = False
            ai.run_full_scan()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, continuous, bovada, prizepicks, no-discord, no-ai, raw, no-deploy")
    else:
        result = ai.run_full_scan()
        
        if result['success']:
            if ai.use_ai_analysis:
                bovada_count = len(result.get('bovada_analysis', []))
                props_count = len(result.get('prizepicks_analysis', []))
                print(f"\nAI Analysis complete! Found {bovada_count} high-value plays and {props_count} top props!")
            else:
                bovada_count = len(result.get('bovada_games', []))
                props_count = len(result.get('prizepicks_projections', []))
                print(f"\nRaw scan complete! Found {bovada_count} games and {props_count} projections!")
            
            print("Tips:")
            print("  • Run 'python update_all.py continuous' for auto-updates")
            print("  • Run 'python update_all.py no-ai' for raw data without filtering")
            print("  • Dashboard: https://whatabarber.github.io/prizepicks/")
        else:
            print("\nScan completed with errors")

if __name__ == "__main__":
    main()