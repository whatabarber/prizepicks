# Add this method to your BettingAIAnalyzer class in ai_analyzer.py

def analyze_prizepicks_projections(self, projections):
    """Analyze PrizePicks projections for best props with improved variety"""
    if not projections:
        return []
    
    analyzed_props = []
    
    for proj in projections:
        try:
            analysis = self.analyze_single_projection(proj)
            if analysis:
                analyzed_props.append(analysis)
        except Exception as e:
            print(f"⚠️ Error analyzing projection: {str(e)}")
            continue
    
    # Sort by confidence first
    analyzed_props.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
    
    # NEW: Diversify by player to avoid repetition
    diversified_props = self.diversify_player_picks(analyzed_props)
    
    # Group by sport and limit
    sport_props = {}
    for prop in diversified_props:
        sport = self.map_league_to_sport(prop.get('league', ''))
        
        # FOCUS ON NFL AND CFB ONLY
        if sport not in ['NFL', 'CFB']:
            continue
            
        if sport not in sport_props:
            sport_props[sport] = []
        if len(sport_props[sport]) < self.max_picks_per_sport:
            sport_props[sport].append(prop)
    
    # Flatten and return
    top_props = []
    for sport_list in sport_props.values():
        top_props.extend(sport_list)
    
    return top_props

def diversify_player_picks(self, analyzed_props, max_per_player=2):
    """Ensure variety by limiting picks per player"""
    player_picks = {}
    diversified = []
    
    # Group by player
    for prop in analyzed_props:
        player = prop.get('player_name', 'Unknown')
        if player not in player_picks:
            player_picks[player] = []
        player_picks[player].append(prop)
    
    # Take top picks per player, prioritizing different stat types
    for player, picks in player_picks.items():
        # Sort by confidence
        picks.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # Group by stat type for this player
        stat_types_seen = set()
        player_selected = []
        
        for pick in picks:
            stat_type = pick.get('stat_type', '').lower()
            
            # Prioritize different stat types for variety
            if stat_type not in stat_types_seen or len(player_selected) == 0:
                player_selected.append(pick)
                stat_types_seen.add(stat_type)
                
                if len(player_selected) >= max_per_player:
                    break
        
        diversified.extend(player_selected)
    
    # Sort final list by confidence
    diversified.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
    
    return diversified

def map_league_to_sport(self, league):
    """Map league name to sport - UPDATED to focus on football only"""
    league_lower = league.lower()
    if 'nfl' in league_lower:
        return 'NFL'
    elif 'ncaaf' in league_lower or 'college football' in league_lower:
        return 'CFB'
    else:
        return 'Other'  # This will be filtered out