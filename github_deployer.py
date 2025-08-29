# Create a new file: github_deployer.py

import os
import subprocess
import shutil
from datetime import datetime

class GitHubDeployer:
    def __init__(self, repo_path=".", docs_folder="docs"):
        self.repo_path = repo_path
        self.docs_folder = docs_folder
        self.data_folder = os.path.join(docs_folder, "data")
        
        # Create necessary folders
        os.makedirs(self.docs_folder, exist_ok=True)
        os.makedirs(self.data_folder, exist_ok=True)
    
    def copy_dashboard_files(self):
        """Copy dashboard HTML and data files to docs folder"""
        try:
            # Copy the dashboard HTML file to docs/index.html
            dashboard_content = """<!-- Your dashboard HTML content here -->"""
            
            with open(os.path.join(self.docs_folder, "index.html"), "w") as f:
                f.write(dashboard_content)
            
            # Copy JSON data files
            data_files = [
                "prizepicks_analysis.json",
                "bovada_analysis.json", 
                "prizepicks_current.json",
                "bovada_current.json"
            ]
            
            for file in data_files:
                src = os.path.join("data", file)
                dst = os.path.join(self.data_folder, file)
                
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    print(f"Copied {file} to docs/data/")
            
            return True
            
        except Exception as e:
            print(f"Error copying files: {str(e)}")
            return False
    
    def commit_and_push(self, commit_message=None):
        """Commit changes and push to GitHub"""
        try:
            if not commit_message:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"Auto-update betting data - {timestamp}"
            
            # Git commands
            commands = [
                ["git", "add", "docs/"],
                ["git", "commit", "-m", commit_message],
                ["git", "push", "origin", "main"]
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
                if result.returncode != 0:
                    print(f"Git command failed: {' '.join(cmd)}")
                    print(f"Error: {result.stderr}")
                    return False
            
            print(f"Successfully pushed to GitHub: {commit_message}")
            return True
            
        except Exception as e:
            print(f"Error during git operations: {str(e)}")
            return False
    
    def deploy_dashboard(self):
        """Full deploy process"""
        print("Starting GitHub deployment...")
        
        if self.copy_dashboard_files():
            if self.commit_and_push():
                print("Dashboard deployed successfully!")
                print("Available at: https://whatabarber.github.io/prizepicks/")
                return True
        
        print("Deployment failed!")
        return False