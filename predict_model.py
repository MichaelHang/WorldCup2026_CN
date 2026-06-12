#!/usr/bin/env python3
"""
四层预测模型：Elo基线 → 贝叶斯更新 → 战术修正 → 蒙特卡洛模拟10万次
用于2026世界杯比赛预测
"""
import math
import random
from collections import Counter

random.seed(42)

# ============================================================
# 球队数据
# ============================================================
TEAMS = {
    "Canada": {
        "elo": 1793,
        "fifa_rank": 25,
        "flag": "🇨🇦",
        "name_cn": "加拿大",
        "style": "fast_counter",  # 快速反击
        "strength": "attack",
        "home": True,
    },
    "Bosnia": {
        "elo": 1591,
        "fifa_rank": 66,
        "flag": "🇧🇦",
        "name_cn": "波黑",
        "style": "physical_defense",
        "strength": "defense",
        "home": False,
    },
    "USA": {
        "elo": 1733,
        "fifa_rank": 37,
        "flag": "🇺🇸",
        "name_cn": "美国",
        "style": "high_press",
        "strength": "balanced",
        "home": True,
    },
    "Paraguay": {
        "elo": 1832,
        "fifa_rank": 22,
        "flag": "🇵🇾",
        "name_cn": "巴拉圭",
        "style": "compact_defense",
        "strength": "defense",
        "home": False,
    },
}

MATCHES = [
    {
        "home": "Canada",
        "away": "Bosnia",
        "time": "03:00",
        "venue": "多伦多体育场",
        "group": "B组",
        "home_advantage": 80,  # Elo points for home advantage (strong - Toronto)
    },
    {
        "home": "USA",
        "away": "Paraguay",
        "time": "09:00",
        "venue": "洛杉矶体育场",
        "group": "D组",
        "home_advantage": 60,  # Elo points for home advantage (moderate - LA)
    },
]


def elo_to_expected(home_elo, away_elo):
    """Layer 1: Elo baseline - convert Elo difference to win/draw/loss probabilities"""
    diff = home_elo - away_elo
    # Standard Elo expected score formula
    home_win_prob = 1.0 / (1.0 + 10 ** (-diff / 400.0))
    
    # Draw probability peaks when teams are evenly matched
    draw_factor = math.exp(-(diff ** 2) / (2 * 200 ** 2))
    draw_base = 0.28 * draw_factor  # Max draw ~28% when equal
    
    # Adjust win/loss to accommodate draw
    remaining = 1.0 - draw_base
    home_win = home_win_prob * remaining
    away_win = (1.0 - home_win_prob) * remaining
    
    return home_win, draw_base, away_win


def bayesian_update(home_win, draw, away_win, match_info):
    """Layer 2: Bayesian update with prior information"""
    home_adv = match_info.get("home_advantage", 0)
    home_elo = TEAMS[match_info["home"]]["elo"]
    away_elo = TEAMS[match_info["away"]]["elo"]
    
    # Prior: home advantage boost
    ha_factor = home_adv / 400.0  # Normalize
    ha_boost = 0.02 + ha_factor * 0.06  # 2-8% shift
    
    # Prior: FIFA ranking gap (confidence adjustment)
    home_rank = TEAMS[match_info["home"]]["fifa_rank"]
    away_rank = TEAMS[match_info["away"]]["fifa_rank"]
    rank_gap = abs(home_rank - away_rank)
    confidence_factor = min(rank_gap / 50.0, 0.3)  # Higher confidence when large gap
    
    # Bayesian-like adjustment: shift probability towards favorite
    if home_elo > away_elo:
        shift = ha_boost * (1 + confidence_factor)
        home_win = home_win * (1 + shift * 0.15)
        away_win = away_win * (1 - shift * 0.15)
        draw = draw * (1 - shift * 0.05)
    else:
        shift = ha_boost * (1 + confidence_factor)
        away_win = away_win * (1 + shift * 0.10)
        home_win = home_win * (1 - shift * 0.10)
        draw = draw * (1 - shift * 0.05)
    
    # Normalize
    total = home_win + draw + away_win
    return home_win / total, draw / total, away_win / total


def tactical_correction(home_win, draw, away_win, match_info):
    """Layer 3: Tactical correction based on playing styles"""
    home_style = TEAMS[match_info["home"]]["style"]
    away_style = TEAMS[match_info["away"]]["style"]
    home_strength = TEAMS[match_info["home"]]["strength"]
    away_strength = TEAMS[match_info["away"]]["strength"]
    
    home_elo = TEAMS[match_info["home"]]["elo"]
    away_elo = TEAMS[match_info["away"]]["elo"]
    
    # Tactical adjustments
    adj_draw = 0
    adj_home = 0
    adj_away = 0
    
    # Fast counter-attack vs physical defense -> slightly more home wins, fewer draws
    if home_style == "fast_counter" and away_style == "physical_defense":
        adj_home += 0.015
        adj_draw -= 0.010
        adj_away -= 0.005
    
    # High press vs compact defense -> more draws (attrition)
    if home_style == "high_press" and away_style == "compact_defense":
        adj_draw += 0.020
        adj_home -= 0.010
        adj_away -= 0.010
    
    # Strength differential: attack vs defense -> fewer draws
    if home_strength == "attack" and away_strength == "defense":
        adj_draw -= 0.015
        if home_elo > away_elo:
            adj_home += 0.010
        else:
            adj_away += 0.005
    
    # Balanced vs defense -> slight underdog boost
    if home_strength == "balanced" and away_strength == "defense":
        adj_draw += 0.010
    
    home_win += adj_home
    draw += adj_draw
    away_win += adj_away
    
    # Normalize
    total = home_win + draw + away_win
    return max(0, home_win / total), max(0, draw / total), max(0, away_win / total)


def poisson_goal_distribution(expected_goals):
    """Generate random goals from Poisson distribution"""
    L = math.exp(-expected_goals)
    p = 1.0
    k = 0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def monte_carlo_simulation(home_win_prob, draw_prob, away_win_prob, match_info, n=100000):
    """Layer 4: Monte Carlo simulation with 100,000 iterations"""
    home_elo = TEAMS[match_info["home"]]["elo"]
    away_elo = TEAMS[match_info["away"]]["elo"]
    home_adv = match_info.get("home_advantage", 0)
    
    # Calculate expected goals based on Elo difference
    # Baseline: average goals in international football ~1.3 per team
    elo_diff = (home_elo + home_adv) - away_elo
    
    # Expected goals for home team
    home_xg_base = 1.35
    away_xg_base = 1.20
    
    # Adjust for Elo difference
    elo_factor = elo_diff / 200.0  # Every 200 Elo points ~ 0.25 goals difference
    home_xg = home_xg_base + elo_factor * 0.25
    away_xg = away_xg_base - elo_factor * 0.25
    
    # Floor at 0.3
    home_xg = max(0.3, home_xg)
    away_xg = max(0.3, away_xg)
    
    # Home advantage in goals
    home_xg += home_adv / 400.0 * 0.3
    
    # Style adjustments
    home_style = TEAMS[match_info["home"]]["style"]
    away_style = TEAMS[match_info["away"]]["style"]
    
    if home_style == "high_press":
        home_xg += 0.1
    if away_style == "compact_defense":
        home_xg -= 0.08
        away_xg += 0.05
    if home_style == "fast_counter":
        home_xg += 0.05
        away_xg -= 0.03
    
    # Ensure positive
    home_xg = max(0.3, home_xg)
    away_xg = max(0.3, away_xg)
    
    results = {"home_win": 0, "draw": 0, "away_win": 0}
    score_counts = Counter()
    
    for _ in range(n):
        home_goals = poisson_goal_distribution(home_xg)
        away_goals = poisson_goal_distribution(away_xg)
        
        score = (home_goals, away_goals)
        score_counts[score] += 1
        
        if home_goals > away_goals:
            results["home_win"] += 1
        elif home_goals == away_goals:
            results["draw"] += 1
        else:
            results["away_win"] += 1
    
    # Convert to percentages
    total = sum(results.values())
    probs = {k: v / total * 100 for k, v in results.items()}
    
    # Top scorelines
    top_scores = score_counts.most_common(8)
    score_probs = [(f"{h}-{a}", count / n * 100) for (h, a), count in top_scores]
    
    return probs, score_probs, home_xg, away_xg


def run_full_model():
    """Run the complete 4-layer model for all matches"""
    results = []
    
    for match in MATCHES:
        home_team = TEAMS[match["home"]]
        away_team = TEAMS[match["away"]]
        
        # Adjust Elo for home advantage
        home_elo_adj = home_team["elo"] + match["home_advantage"]
        away_elo = away_team["elo"]
        
        # Layer 1: Elo baseline
        h1, d1, a1 = elo_to_expected(home_elo_adj, away_elo)
        
        # Layer 2: Bayesian update
        h2, d2, a2 = bayesian_update(h1, d1, a1, match)
        
        # Layer 3: Tactical correction
        h3, d3, a3 = tactical_correction(h2, d2, a2, match)
        
        # Layer 4: Monte Carlo
        probs, score_probs, home_xg, away_xg = monte_carlo_simulation(h3, d3, a3, match, n=100000)
        
        # Format best scoreline with highest probability
        best_score, best_score_prob = score_probs[0] if score_probs else ("1-0", 15.0)
        
        result = {
            "home_flag": home_team["flag"],
            "home_name": home_team["name_cn"],
            "away_flag": away_team["flag"],
            "away_name": away_team["name_cn"],
            "time": match["time"],
            "venue": match["venue"],
            "group": match["group"],
            "home_win": round(probs["home_win"], 1),
            "draw": round(probs["draw"], 1),
            "away_win": round(probs["away_win"], 1),
            "best_score": best_score,
            "score_probs": [(s, round(p, 1)) for s, p in score_probs[:5]],
            "home_xg": round(home_xg, 2),
            "away_xg": round(away_xg, 2),
            # Raw layer outputs for debugging
            "layer1": (round(h1*100,1), round(d1*100,1), round(a1*100,1)),
            "layer2": (round(h2*100,1), round(d2*100,1), round(a2*100,1)),
            "layer3": (round(h3*100,1), round(d3*100,1), round(a3*100,1)),
            "elo_home": home_team["elo"],
            "elo_away": away_team["elo"],
            "home_advantage": match["home_advantage"],
            # Tactical factors
            "key_factors": get_key_factors(match),
            "scripts": get_scripts(match),
        }
        
        results.append(result)
    
    return results


def get_key_factors(match):
    """Generate key tactical factors for display"""
    home = TEAMS[match["home"]]
    away = TEAMS[match["away"]]
    
    factors = []
    
    if match["home"] == "Canada":
        factors.append("多伦多主场优势：加拿大首次世界杯主场作战，全国士气高涨")
        factors.append(f"Elo差距+{home['elo'] + match['home_advantage'] - away['elo']}：加拿大纸面实力明显占优")
        factors.append("阿方索·戴维斯左路突破 vs 波黑老迈防线：速度差是关键")
        factors.append("波黑哲科高龄（40岁）体能存疑，下半场可能崩盘")
    
    elif match["home"] == "USA":
        factors.append("洛杉矶主场氛围：美国队熟悉的场地和气候条件")
        factors.append(f"巴拉圭Elo更高（{away['elo']} vs {home['elo']}）：南美劲旅经验丰富")
        factors.append("普利西奇中场创造力 vs 巴拉圭铁桶阵：破密集防守能力受考验")
        factors.append("巴拉圭南美世预赛失球最少之一，防守纪律性极强")
    
    return factors


def get_scripts(match):
    """Generate match scripts"""
    if match["home"] == "Canada":
        return [
            ("剧本A", "加拿大开场高压，戴维斯左路连续突破制造机会，上半场1-0领先；波黑下半场体能下降，加拿大70分钟后锁定胜局"),
            ("剧本B", "波黑利用哲科支点作用稳守反击，加拿大久攻不下心态急躁，波黑定位球破门后全线退守"),
        ]
    elif match["home"] == "USA":
        return [
            ("剧本A", "美国利用主场气势开场猛攻，普利西奇灵光一闪破僵；巴拉圭被迫压出后防线漏洞增加"),
            ("剧本B", "巴拉圭教科书式低位防守+反击，美国控球占优但威胁寥寥，0-0闷平或巴拉圭偷袭得手"),
        ]


if __name__ == "__main__":
    results = run_full_model()
    
    for i, r in enumerate(results):
        print(f"\n{'='*60}")
        print(f"比赛 {i+1}: {r['home_flag']} {r['home_name']} vs {r['away_flag']} {r['away_name']}")
        print(f"时间: {r['time']} | 场地: {r['venue']} | {r['group']}")
        print(f"Elo: {r['home_name']} {r['elo_home']}(+{r['home_advantage']}主场) vs {r['away_name']} {r['elo_away']}")
        print(f"\nLayer 1 (Elo):   主{r['layer1'][0]}% 平{r['layer1'][1]}% 客{r['layer1'][2]}%")
        print(f"Layer 2 (Bayes): 主{r['layer2'][0]}% 平{r['layer2'][1]}% 客{r['layer2'][2]}%")
        print(f"Layer 3 (Tact):  主{r['layer3'][0]}% 平{r['layer3'][1]}% 客{r['layer3'][2]}%")
        print(f"Layer 4 (MC 10万): 主{r['home_win']}% 平{r['draw']}% 客{r['away_win']}%")
        print(f"Expected Goals: {r['home_name']} {r['home_xg']} - {r['away_xg']} {r['away_name']}")
        print(f"\nTop 5 Scorelines:")
        for s, p in r['score_probs']:
            print(f"  {s}: {p}%")
        print(f"\nKey Factors:")
        for f in r['key_factors']:
            print(f"  ▸ {f}")
        print(f"\nScripts:")
        for label, desc in r['scripts']:
            print(f"  [{label}] {desc}")
    
    # Output JSON for use in HTML generation
    import json
    print("\n\n=== JSON OUTPUT ===")
    print(json.dumps(results, ensure_ascii=False, indent=2))
