"""
足球预测引擎 v1.1
模块: Elo评级 + 泊松回归 + 蒙特卡洛模拟 + 赔率分析 + Kelly仓位
v1.1修正: 单场决赛极端防守系数均值回归30%
"""

import math
import json
import os
from typing import Dict, List, Tuple, Optional

# ============================================
# 核心参数
# ============================================
LEAGUE_AVG_GOALS = 1.35
ELO_WEIGHT = 0.30
POISSON_WEIGHT = 0.70
DEFENSE_REGRESSION = 0.30
DEFENSE_EXTREME_THRESHOLD = 0.5


class FootballPredictionEngine:
    """足球比赛预测引擎"""
    
    def __init__(self, data_dir: str = None):
        self.elo_ratings = {}
        self.team_stats = {}
        self.prediction_log = []
        
        if data_dir:
            self.load_data(data_dir)
    
    def load_data(self, data_dir: str):
        """加载数据文件"""
        elo_path = os.path.join(data_dir, 'elo_ratings.json')
        stats_path = os.path.join(data_dir, 'team_stats.json')
        
        if os.path.exists(elo_path):
            with open(elo_path, 'r', encoding='utf-8') as f:
                self.elo_ratings = json.load(f)
        
        if os.path.exists(stats_path):
            with open(stats_path, 'r', encoding='utf-8') as f:
                self.team_stats = json.load(f)
    
    def elo_expected(self, elo_a: float, elo_b: float) -> float:
        return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
    
    @staticmethod
    def poisson_prob(lam: float, k: int) -> float:
        return (lam ** k) * math.exp(-lam) / math.factorial(k)
    
    def expected_goals(self, team_a: str, team_b: str, 
                       is_knockout: bool = False) -> Tuple[float, float]:
        stats_a = self.team_stats.get(team_a, {'avg_goals': LEAGUE_AVG_GOALS, 'avg_conceded': LEAGUE_AVG_GOALS})
        stats_b = self.team_stats.get(team_b, {'avg_goals': LEAGUE_AVG_GOALS, 'avg_conceded': LEAGUE_AVG_GOALS})
        
        attack_a = stats_a['avg_goals'] / LEAGUE_AVG_GOALS
        defense_a = stats_a['avg_conceded'] / LEAGUE_AVG_GOALS
        attack_b = stats_b['avg_goals'] / LEAGUE_AVG_GOALS
        defense_b = stats_b['avg_conceded'] / LEAGUE_AVG_GOALS
        
        # v1.1修正
        if is_knockout:
            if defense_b < DEFENSE_EXTREME_THRESHOLD:
                defense_b = defense_b * (1 - DEFENSE_REGRESSION) + 1.0 * DEFENSE_REGRESSION
            if defense_a < DEFENSE_EXTREME_THRESHOLD:
                defense_a = defense_a * (1 - DEFENSE_REGRESSION) + 1.0 * DEFENSE_REGRESSION
        
        xg_a = LEAGUE_AVG_GOALS * attack_a * defense_b
        xg_b = LEAGUE_AVG_GOALS * attack_b * defense_a
        return xg_a, xg_b
    
    def poisson_matrix(self, xg_a: float, xg_b: float, max_goals: int = 7) -> Dict:
        win_a = draw = win_b = 0.0
        score_probs = {}
        
        for ga in range(max_goals):
            for gb in range(max_goals):
                p = self.poisson_prob(xg_a, ga) * self.poisson_prob(xg_b, gb)
                score_probs[f"{ga}-{gb}"] = round(p * 100, 2)
                if ga > gb: win_a += p
                elif ga == ga: draw += p if ga == gb else 0
                else: win_b += p
        
        # 修复draw计算
        win_a = draw = win_b = 0.0
        for ga in range(max_goals):
            for gb in range(max_goals):
                p = self.poisson_prob(xg_a, ga) * self.poisson_prob(xg_b, gb)
                if ga > gb: win_a += p
                elif ga == gb: draw += p
                else: win_b += p
        
        return {'win_a': win_a, 'draw': draw, 'win_b': win_b, 'score_probs': score_probs}
    
    def predict(self, team_a: str, team_b: str,
                corrections: Dict = None, is_knockout: bool = False) -> Dict:
        corrections = corrections or {}
        
        elo_a = self.elo_ratings.get(team_a, 1500)
        elo_b = self.elo_ratings.get(team_b, 1500)
        elo_exp_a = self.elo_expected(elo_a, elo_b)
        
        xg_a, xg_b = self.expected_goals(team_a, team_b, is_knockout)
        poisson = self.poisson_matrix(xg_a, xg_b)
        
        combined_a = elo_exp_a * ELO_WEIGHT + poisson['win_a'] * POISSON_WEIGHT
        combined_draw = (1 - abs(elo_exp_a - 0.5)) * 0.15 + poisson['draw'] * POISSON_WEIGHT
        combined_b = (1 - elo_exp_a) * ELO_WEIGHT + poisson['win_b'] * POISSON_WEIGHT
        
        total = combined_a + combined_draw + combined_b
        combined_a /= total; combined_draw /= total; combined_b /= total
        
        adj_a = combined_a + corrections.get('a', 0)
        adj_draw = combined_draw + corrections.get('draw', 0)
        adj_b = combined_b + corrections.get('b', 0)
        
        total2 = adj_a + adj_draw + adj_b
        adj_a /= total2; adj_draw /= total2; adj_b /= total2
        
        top_scores = sorted(poisson['score_probs'].items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'team_a': team_a, 'team_b': team_b,
            'elo_a': elo_a, 'elo_b': elo_b,
            'elo_expected_a': round(elo_exp_a, 3),
            'xg_a': round(xg_a, 2), 'xg_b': round(xg_b, 2),
            'poisson': {
                'win_a': round(poisson['win_a'] * 100, 1),
                'draw': round(poisson['draw'] * 100, 1),
                'win_b': round(poisson['win_b'] * 100, 1)
            },
            'combined': {
                'win_a': round(combined_a * 100, 1),
                'draw': round(combined_draw * 100, 1),
                'win_b': round(combined_b * 100, 1)
            },
            'final': {
                'win_a': round(adj_a * 100, 1),
                'draw': round(adj_draw * 100, 1),
                'win_b': round(adj_b * 100, 1)
            },
            'top_scores': top_scores,
            'corrections': corrections,
            'is_knockout': is_knockout
        }
    
    def monte_carlo_path(self, team: str, stages: List[Dict], 
                         simulations: int = 100000) -> Dict:
        import random
        results = {i: 0 for i in range(len(stages) + 1)}
        results[0] = simulations
        
        for _ in range(simulations):
            current = True
            for stage_idx, stage in enumerate(stages):
                if not current: break
                if random.random() < stage['win_prob']:
                    results[stage_idx + 1] += 1
                else:
                    current = False
        
        return {
            'team': team,
            'simulations': simulations,
            'probabilities': {
                f'stage_{i}': round(results[i] / simulations * 100, 1)
                for i in range(len(stages) + 1)
            }
        }
    
    @staticmethod
    def odds_to_probability(odds_a: float, odds_draw: float, odds_b: float) -> Dict:
        raw_a = 1 / odds_a; raw_d = 1 / odds_draw; raw_b = 1 / odds_b
        total = raw_a + raw_d + raw_b
        vig = total - 1
        return {
            'prob_a': round(raw_a / total * 100, 1),
            'prob_draw': round(raw_d / total * 100, 1),
            'prob_b': round(raw_b / total * 100, 1),
            'vig': round(vig * 100, 1)
        }
    
    def value_detection(self, model_prob: Dict, market_prob: Dict, 
                        threshold: float = 3.0) -> Dict:
        edges = {}
        for key in ['win_a', 'draw', 'win_b']:
            model = model_prob.get(key, 0)
            market = market_prob.get(key, 0)
            edge = model - market
            edges[key] = {
                'model': model, 'market': market,
                'edge': round(edge, 1),
                'is_value': abs(edge) >= threshold
            }
        return edges
    
    @staticmethod
    def kelly(prob: float, odds: float, fraction: float = 0.5) -> float:
        full_kelly = (prob * odds - 1) / (odds - 1)
        return max(0, full_kelly * fraction)


    def upset_analysis(self, team_a: str, team_b: str,
                       match_context: Dict = None) -> Dict:
        """爆冷分析模块 v1.0 (2026世界杯)

        基于三层判据：风格克制、状态变量、赛制红利
        返回爆冷概率和关键因素
        """
        match_context = match_context or {}

        # 确定强队和弱队（基于Elo）
        elo_a = self.elo_ratings.get(team_a, 1500)
        elo_b = self.elo_ratings.get(team_b, 1500)
        favorite = team_a if elo_a >= elo_b else team_b
        underdog = team_b if favorite == team_a else team_a
        elo_gap = abs(elo_a - elo_b)

        # 基础预测（final字段已是百分比0-100，转为0-1概率）
        base_pred = self.predict(team_a, team_b)
        underdog_key = 'win_b' if favorite == team_a else 'win_a'
        draw_key = 'draw'
        base_upset_prob = base_pred['final'][underdog_key] / 100.0
        base_draw_prob = base_pred['final'][draw_key] / 100.0

        # 三层爆冷修正
        corrections = {'style': 0, 'status': 0, 'format': 0}

        # 1. 风格克制修正
        stats_fav = self.team_stats.get(favorite, {'avg_goals': LEAGUE_AVG_GOALS, 'avg_conceded': LEAGUE_AVG_GOALS})
        stats_und = self.team_stats.get(underdog, {'avg_goals': LEAGUE_AVG_GOALS, 'avg_conceded': LEAGUE_AVG_GOALS})

        # 攻强守弱（场均进球>1.8且失球>0.9）遇铁桶（弱队失球<0.9）
        if stats_fav['avg_goals'] > 1.8 and stats_fav['avg_conceded'] > 0.9 and stats_und['avg_conceded'] < 0.9:
            corrections['style'] += 0.04  # 铁桶克攻强守弱

        # 弱队反击型（进球>1.3且失球<1.0）vs 控球型强队
        if stats_und['avg_goals'] > 1.3 and stats_und['avg_conceded'] < 1.0 and stats_fav['avg_goals'] > 2.0:
            corrections['style'] += 0.03  # 反击克控球

        # 2. 状态变量修正
        if match_context.get('internal_strife'):
            corrections['status'] -= 0.04  # 强队内讧
        if match_context.get('key_injury'):
            corrections['status'] -= 0.03  # 强队核心伤缺
        if match_context.get('slow_starter'):
            corrections['status'] += 0.02  # 强队历来小组赛慢热

        # 3. 赛制红利修正
        if match_context.get('is_first_match'):
            corrections['format'] += 0.03  # 首轮不确定性
        if match_context.get('rotation_risk'):
            corrections['format'] += 0.06  # 末轮轮换
        if match_context.get('is_last_group_match'):
            corrections['format'] += 0.02  # 末轮算分
        if match_context.get('expansion_format'):
            corrections['format'] += 0.03  # 48队扩军红利

        total_correction = corrections['style'] + corrections['status'] + corrections['format']

        adjusted_upset = min(0.95, base_upset_prob + total_correction)
        adjusted_draw = min(0.50, base_draw_prob + abs(corrections['status']) * 0.3)

        # 爆冷等级判定
        upset_combined = adjusted_upset + adjusted_draw * 0.5
        if upset_combined >= 0.40:
            tier = "Tier 1 - 高概率爆冷"
        elif upset_combined >= 0.30:
            tier = "Tier 2 - 中概率爆冷"
        elif upset_combined >= 0.20:
            tier = "Tier 3 - 值得盯的暗冷"
        else:
            tier = "常规 - 爆冷概率低"

        return {
            'favorite': favorite,
            'underdog': underdog,
            'elo_gap': elo_gap,
            'base_upset_prob': round(base_upset_prob * 100, 1),
            'base_draw_prob': round(base_draw_prob * 100, 1),
            'corrections': {k: round(v * 100, 1) for k, v in corrections.items()},
            'total_correction': round(total_correction * 100, 1),
            'adjusted_upset_prob': round(adjusted_upset * 100, 1),
            'adjusted_draw_prob': round(adjusted_draw * 100, 1),
            'upset_combined': round(upset_combined * 100, 1),
            'tier': tier,
            'key_factors': [
                f for f, v in corrections.items() if abs(v) >= 0.01
            ]
        }


if __name__ == "__main__":
    engine = FootballPredictionEngine(data_dir=os.path.join(os.path.dirname(__file__), '..', 'data'))
    print(f"已加载 {len(engine.elo_ratings)} 支球队Elo数据")
    print(f"已加载 {len(engine.team_stats)} 支球队攻防数据")

    # 爆冷分析快速测试
    test_matches = [
        ("巴西", "摩洛哥", {"is_first_match": True, "expansion_format": True}),
        ("荷兰", "日本", {"is_first_match": True, "expansion_format": True}),
        ("法国", "塞内加尔", {"is_first_match": True, "expansion_format": True, "slow_starter": True}),
        ("比利时", "伊朗", {"expansion_format": True}),
        ("挪威", "法国", {"is_last_group_match": True, "rotation_risk": True, "expansion_format": True}),
        ("乌拉圭", "西班牙", {"is_last_group_match": True, "expansion_format": True}),
        ("英格兰", "加纳", {"expansion_format": True, "slow_starter": True}),
        ("德国", "厄瓜多尔", {"is_last_group_match": True, "expansion_format": True}),
        ("美国", "土耳其", {"is_last_group_match": True, "expansion_format": True}),
        ("葡萄牙", "哥伦比亚", {"is_last_group_match": True, "expansion_format": True}),
    ]
    print("\n=== 2026世界杯爆冷分析测试 ===\n")
    for fav, und, ctx in test_matches:
        result = engine.upset_analysis(fav, und, ctx)
        print(f"{result['favorite']} vs {result['underdog']} | Elo差{result['elo_gap']} | "
              f"基础爆冷{result['base_upset_prob']}% → 调整后{result['adjusted_upset_prob']}% | "
              f"修正: 风格{result['corrections']['style']}% 状态{result['corrections']['status']}% 赛制{result['corrections']['format']}% | "
              f"{result['tier']}")
