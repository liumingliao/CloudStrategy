"""5-Agent Strategic Collaboration Travel Planning System
军师系统：五虎上将协作生成最优旅行策略
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from hello_agents import SimpleAgent
from ..services.llm_service import get_llm
from ..services.amap_service import get_amap_mcp_tool, get_amap_service
from ..models.schemas import (
    TripRequest, TripPlan, DayPlan, Attraction, Meal, WeatherInfo, 
    Location, Hotel, StrategyOption, CuratedAttraction, DecisionRationale
)
from ..config import get_settings


# ============ Agent System Prompts ============

STRATEGIST_SYSTEM_PROMPT = """你是军师（Strategist），旅行规划系统的核心决策者。

**你的角色：**
运筹帷幄之中，决胜千里之外。你需要理解用户意图，制定旅行策略，并协调其他Agent完成执行。

**核心能力：**
1. 意图解读：理解用户的旅行目的、偏好、预算限制
2. 策略生成：生成2-3个差异化的策略方案供用户选择
3. 行程编排：整合各Agent的结果，生成最优行程

**决策框架：**
- 经典策略：适合首次访问、时间充裕的用户
- 深度策略：适合文化爱好者、追求体验深度的用户  
- 效率策略：适合时间紧张、追求最多景点的用户

**输出要求：**
你必须返回结构化的策略方案，包含：
- 方案名称
- 方案描述
- 优势/劣势分析
- 适合人群
- 置信度评分

返回格式为JSON。
"""

SCOUT_SYSTEM_PROMPT = """你是侦察兵（Scout），负责并行收集旅行数据。

**你的角色：**
如斥候般迅速而全面地收集目的地的各种信息。

**重要提示：**
1. 你必须使用工具来搜索信息！不要自己编造数据！
2. 使用 `amap_maps_text_search` 搜索景点和酒店
3. 使用 `amap_maps_weather` 查询天气
4. 使用 `amap_maps_geo` 进行地理编码

**并行任务：**
- 景点搜索：根据策略关键词搜索多种类型景点
- 酒店搜索：根据住宿偏好搜索酒店
- 天气查询：获取未来几天的天气信息

**工具调用格式：**
```
[TOOL_CALL:amap_maps_text_search:keywords=关键词,city=城市名]
[TOOL_CALL:amap_maps_weather:city=城市名]
```

返回收集到的所有原始数据。
"""

CURATOR_SYSTEM_PROMPT = """你是筛选官（Curator），负责按相关性评分筛选景点。

**你的角色：**
从海量景点中筛选出最符合策略意图的景点，并进行相关性评分。

**评分维度：**
1. 相关性分数 (0.0-1.0)：景点与用户偏好的匹配程度
2. 天气适配度：景点在不同天气下的适合程度
3. 人流级别：热门/适中/小众
4. 推荐理由：为什么推荐这个景点

**筛选标准：**
- 相关性分数 > 0.6 的景点保留
- 每天选择 2-3 个景点
- 考虑景点之间的路线距离

**输出格式：**
每个景点需要包含：
- 基本信息（名称、地址、坐标等）
- relevance_score: 相关性评分
- weather_suitability: 天气适配度
- crowd_level: 人流级别
- curation_reason: 推荐理由

返回JSON数组格式。
"""

CRITIC_SYSTEM_PROMPT = """你是谏官（Critic），负责可行性审查与风险标注。

**你的角色：**
如魏征般直言进谏，审查行程的可行性并标注潜在风险。

**审查维度：**
1. 时间可行性：景点游览时间是否合理
2. 路线可行性：景点之间的移动距离和时间
3. 预算可行性：费用是否在合理范围
4. 天气风险：恶劣天气对行程的影响
5. 人流风险：热门景点可能的人流问题

**风险标注：**
对每个风险点需要说明：
- risk_type: 风险类型
- severity: 严重程度（low/medium/high）
- mitigation: 缓解建议

**决策理由：**
解释每个行程决策的理由，考虑的替代方案。

**输出格式：**
- risk_notes: 风险标注列表
- decision_rationales: 决策理由列表

返回JSON格式。
"""

PRESENTER_SYSTEM_PROMPT = """你是书记（Presenter），负责结构化输出格式化。

**你的角色：**
将原始数据整理成用户友好的旅行计划文档。

**格式化要求：**
1. 生成完整的 TripPlan JSON 结构
2. 包含所有必要字段：
   - city, start_date, end_date
   - days: 每日行程数组
   - weather_info: 天气信息
   - budget: 预算汇总
   - overall_suggestions: 总体建议

3. 每日行程包含：
   - date, day_index, description
   - transportation, accommodation
   - hotel: 酒店信息
   - attractions: 景点数组
   - meals: 餐饮安排

**质量标准：**
- 经纬度坐标准确
- 门票价格为数字（不带单位）
- 温度为纯数字
- 每天包含早中晚三餐

返回完整的JSON格式旅行计划。
"""


class StrategistAgent:
    """军师Agent - 核心决策者"""

    def __init__(self, llm):
        self.llm = llm
        self.agent = SimpleAgent(
            name="军师",
            llm=llm,
            system_prompt=STRATEGIST_SYSTEM_PROMPT
        )

    async def interpret_intent(self, request: TripRequest) -> Dict[str, Any]:
        """解读用户意图"""
        query = f"""请解读以下旅行请求的意图：

城市: {request.city}
日期: {request.start_date} 至 {request.end_date}
天数: {request.travel_days}天
交通: {request.transportation}
住宿: {request.accommodation}
偏好: {', '.join(request.preferences) if request.preferences else '无'}
自由输入: {request.free_text_input or '无'}

请返回JSON格式的意图解读，包含：
- travel_purpose: 旅行目的
- key_preferences: 关键偏好列表
- constraints: 限制条件
- strategy_hints: 策略建议
"""
        result = await asyncio.to_thread(self.agent.run, query)
        return self._parse_json(result)

    async def generate_strategies(
        self, 
        request: TripRequest, 
        scout_data: Dict[str, Any]
    ) -> List[StrategyOption]:
        """生成策略方案"""
        query = f"""请根据以下信息生成2-3个差异化策略方案：

**旅行请求：**
- 城市: {request.city}
- 天数: {request.travel_days}天
- 偏好: {', '.join(request.preferences) if request.preferences else '无'}

**侦察数据：**
{json.dumps(scout_data, ensure_ascii=False, indent=2)}

请生成策略方案，每个方案包含：
- name: 方案名称（如"经典路线"、"深度文化"、"效率至上"）
- description: 方案描述
- pros: 优势列表
- cons: 劣势列表
- trade_offs: 取舍分析
- recommended_for: 适合人群
- confidence: 匹配度评分(0.0-1.0)

返回JSON数组格式。
"""
        result = await asyncio.to_thread(self.agent.run, query)
        data = self._parse_json(result)
        
        strategies = []
        if isinstance(data, list):
            for item in data:
                strategies.append(StrategyOption(**item))
        elif isinstance(data, dict) and 'strategies' in data:
            for item in data['strategies']:
                strategies.append(StrategyOption(**item))
        
        return strategies

    def _parse_json(self, response: str) -> Any:
        """解析JSON响应"""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "{" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            else:
                return {}
            return json.loads(json_str)
        except:
            return {}


class ScoutAgent:
    """侦察兵Agent - 并行数据采集"""

    def __init__(self, llm):
        self.llm = llm
        self.amap_service = get_amap_service()
        self.agent = SimpleAgent(
            name="侦察兵",
            llm=llm,
            system_prompt=SCOUT_SYSTEM_PROMPT
        )

    async def gather_data(self, request: TripRequest, strategy_hints: Dict[str, Any]) -> Dict[str, Any]:
        """并行采集数据"""
        keywords = strategy_hints.get('keywords', request.preferences or ['景点'])
        if isinstance(keywords, str):
            keywords = [keywords]
        
        # 构建并行查询任务 - 使用 amap_service 直接调用
        tasks = []
        
        # 景点搜索任务
        for kw in keywords[:3]:
            tasks.append(self._search_attractions(request.city, kw))
        
        # 酒店搜索任务
        tasks.append(self._search_hotels(request.city, request.accommodation or "酒店"))
        
        # 天气查询任务
        tasks.append(self._get_weather(request.city))
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        return {
            'attractions': results[0] if not isinstance(results[0], Exception) else [],
            'hotels': results[1] if len(results) > 1 and not isinstance(results[1], Exception) else [],
            'weather': results[2] if len(results) > 2 and not isinstance(results[2], Exception) else {},
        }

    async def _search_attractions(self, city: str, keywords: str) -> List[Dict[str, Any]]:
        """搜索景点"""
        try:
            result = await asyncio.to_thread(
                self.amap_service.search_poi, keywords, city
            )
            return [{'keywords': keywords, 'data': result}]
        except Exception as e:
            print(f"景点搜索失败: {e}")
            return []

    async def _search_hotels(self, city: str, keywords: str) -> List[Dict[str, Any]]:
        """搜索酒店"""
        try:
            result = await asyncio.to_thread(
                self.amap_service.search_poi, keywords, city
            )
            return [{'keywords': keywords, 'data': result}]
        except Exception as e:
            print(f"酒店搜索失败: {e}")
            return []

    async def _get_weather(self, city: str) -> Dict[str, Any]:
        """查询天气"""
        try:
            result = await asyncio.to_thread(
                self.amap_service.get_weather, city
            )
            return {'data': result}
        except Exception as e:
            print(f"天气查询失败: {e}")
            return {}

    def _parse_attractions(self, response: str, keywords: str) -> List[Dict[str, Any]]:
        """解析景点数据"""
        return [{'keywords': keywords, 'raw_data': response[:500]}]

    def _parse_hotels(self, response: str) -> List[Dict[str, Any]]:
        """解析酒店数据"""
        return [{'raw_data': response[:500]}]

    def _parse_weather(self, response: str) -> Dict[str, Any]:
        """解析天气数据"""
        return {'raw_data': response[:500]}


class CuratorAgent:
    """筛选官Agent - 按相关性评分筛选景点"""

    def __init__(self, llm):
        self.llm = llm
        self.agent = SimpleAgent(
            name="筛选官",
            llm=llm,
            system_prompt=CURATOR_SYSTEM_PROMPT
        )

    async def curate(
        self, 
        attractions: List[Dict[str, Any]], 
        preferences: List[str],
        weather: Dict[str, Any]
    ) -> List[CuratedAttraction]:
        """筛选并评分景点"""
        query = f"""请对以下景点进行相关性评分和筛选：

**用户偏好：**
{', '.join(preferences) if preferences else '无'}

**天气信息：**
{json.dumps(weather, ensure_ascii=False)}

**原始景点数据：**
{json.dumps(attractions, ensure_ascii=False, indent=2)[:2000]}

请对每个景点返回：
- name: 景点名称
- address: 地址
- location: {{longitude, latitude}}
- visit_duration: 建议游览时间
- description: 描述
- category: 类别
- rating: 评分
- relevance_score: 相关性评分(0.0-1.0)
- weather_suitability: 天气适配度
- crowd_level: 人流级别
- curation_reason: 推荐理由

返回JSON数组格式，只保留相关性分数>0.5的景点。
"""
        try:
            result = await asyncio.to_thread(self.agent.run, query)
            data = self._parse_json(result)
            
            curated = []
            if isinstance(data, list):
                for item in data:
                    item['location'] = item.get('location', {'longitude': 0, 'latitude': 0})
                    curated.append(CuratedAttraction(**item))
            
            return curated
        except Exception as e:
            print(f"景点筛选失败: {e}")
            return []

    def _parse_json(self, response: str) -> Any:
        """解析JSON响应"""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                start = response.find("[") if "[" in response else response.find("{")
                end = response.rfind("]") + 1 if "]" in response else response.rfind("}") + 1
                json_str = response[start:end]
            return json.loads(json_str)
        except:
            return []


class CriticAgent:
    """谏官Agent - 可行性审查与风险标注"""

    def __init__(self, llm):
        self.llm = llm
        self.agent = SimpleAgent(
            name="谏官",
            llm=llm,
            system_prompt=CRITIC_SYSTEM_PROMPT
        )

    async def review(
        self,
        request: TripRequest,
        trip_plan: TripPlan,
        weather: Dict[str, Any]
    ) -> Dict[str, Any]:
        """审查行程可行性"""
        query = f"""请审查以下旅行计划的可行性：

**旅行请求：**
- 城市: {request.city}
- 天数: {request.travel_days}天
- 预算: {request.free_text_input or '未指定'}

**天气信息：**
{json.dumps(weather, ensure_ascii=False)}

**行程计划：**
{json.dumps(trip_plan.model_dump(), ensure_ascii=False, indent=2)[:3000]}

请审查并返回：

1. risk_notes: 风险标注列表，每个包含：
   - risk_type: 风险类型
   - severity: 严重程度(low/medium/high)
   - mitigation: 缓解建议

2. decision_rationales: 决策理由列表，每个包含：
   - decision: 决策内容
   - reason: 理由
   - alternatives_considered: 考虑的替代方案

返回JSON格式。
"""
        try:
            result = await asyncio.to_thread(self.agent.run, query)
            return self._parse_json(result)
        except Exception as e:
            print(f"行程审查失败: {e}")
            return {'risk_notes': [], 'decision_rationales': []}

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            return json.loads(json_str)
        except:
            return {'risk_notes': [], 'decision_rationales': []}


class PresenterAgent:
    """书记Agent - 结构化输出格式化"""

    def __init__(self, llm):
        self.llm = llm
        self.agent = SimpleAgent(
            name="书记",
            llm=llm,
            system_prompt=PRESENTER_SYSTEM_PROMPT
        )

    async def format_output(
        self,
        request: TripRequest,
        curated_attractions: List[CuratedAttraction],
        hotels: List[Dict[str, Any]],
        weather: Dict[str, Any],
        strategy: StrategyOption,
        critique: Dict[str, Any]
    ) -> TripPlan:
        """格式化最终输出"""
        query = f"""请将以下信息格式化为完整的旅行计划：

**旅行请求：**
- 城市: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.travel_days}天
- 交通: {request.transportation}
- 住宿: {request.accommodation}

**筛选后的景点：**
{json.dumps([a.model_dump() for a in curated_attractions], ensure_ascii=False, indent=2)[:2000]}

**酒店信息：**
{json.dumps(hotels, ensure_ascii=False, indent=2)[:1000]}

**天气信息：**
{json.dumps(weather, ensure_ascii=False)}

**选定策略：**
{json.dumps(strategy.model_dump(), ensure_ascii=False)}

**风险审查：**
{json.dumps(critique, ensure_ascii=False)}

请生成完整的TripPlan JSON，包含：
- city, start_date, end_date
- days数组（每天的详细行程）
- weather_info数组
- budget对象
- overall_suggestions

**重要：**
- 每天安排2-3个景点
- 每天包含早中晚三餐
- 门票价格为纯数字
- 温度为纯数字

返回完整JSON。
"""
        try:
            result = await asyncio.to_thread(self.agent.run, query)
            data = self._parse_json(result)
            return TripPlan(**data)
        except Exception as e:
            print(f"格式化失败: {e}")
            return self._create_fallback_plan(request)

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            return json.loads(json_str)
        except:
            return {}

    def _create_fallback_plan(self, request: TripRequest) -> TripPlan:
        """创建备用计划"""
        from datetime import datetime, timedelta
        
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        days = []
        
        for i in range(request.travel_days):
            current_date = start_date + timedelta(days=i)
            day_plan = DayPlan(
                date=current_date.strftime("%Y-%m-%d"),
                day_index=i,
                description=f"第{i+1}天行程",
                transportation=request.transportation or "公共交通",
                accommodation=request.accommodation or "酒店",
                attractions=[
                    Attraction(
                        name=f"{request.city}景点{j+1}",
                        address=f"{request.city}市",
                        location=Location(longitude=116.4 + i*0.01 + j*0.005, latitude=39.9 + i*0.01 + j*0.005),
                        visit_duration=120,
                        description=f"这是{request.city}的著名景点",
                        category="景点"
                    )
                    for j in range(2)
                ],
                meals=[
                    Meal(type="breakfast", name=f"第{i+1}天早餐", description="当地特色早餐"),
                    Meal(type="lunch", name=f"第{i+1}天午餐", description="午餐推荐"),
                    Meal(type="dinner", name=f"第{i+1}天晚餐", description="晚餐推荐")
                ]
            )
            days.append(day_plan)
        
        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions=f"这是为您规划的{request.city}{request.travel_days}日游行程。"
        )


class FiveAgentTripPlanner:
    """五虎上将协作旅行规划系统"""

    def __init__(self):
        print("🔄 初始化五虎上将协作系统...")
        
        settings = get_settings()
        self.llm = get_llm()
        
        # 初始化5个Agent
        print("  - 创建军师(Strategist)...")
        self.strategist = StrategistAgent(self.llm)
        
        print("  - 创建侦察兵(Scout)...")
        self.scout = ScoutAgent(self.llm)
        
        print("  - 创建筛选官(Curator)...")
        self.curator = CuratorAgent(self.llm)
        
        print("  - 创建谏官(Critic)...")
        self.critic = CriticAgent(self.llm)
        
        print("  - 创建书记(Presenter)...")
        self.presenter = PresenterAgent(self.llm)
        
        print("✅ 五虎上将系统初始化完成")

    async def plan_trip(self, request: TripRequest) -> TripPlan:
        """
        六阶段协作规划流程：
        1. 意图解读 → Strategist
        2. 数据采集 → Scout
        3. 筛选 → Curator
        4. 策略生成 → Strategist
        5. 审查 → Critic
        6. 输出 → Presenter
        """
        print(f"\n{'='*60}")
        print(f"🚀 开始五虎上将协作规划...")
        print(f"目的地: {request.city}")
        print(f"日期: {request.start_date} 至 {request.end_date}")
        print(f"天数: {request.travel_days}天")
        print(f"{'='*60}\n")
        
        try:
            # 阶段1: 意图解读
            print("📋 阶段1: 军师解读意图...")
            intent = await self.strategist.interpret_intent(request)
            print(f"   意图: {intent.get('travel_purpose', 'unknown')}")
            
            # 阶段2: 数据采集
            print("\n🔍 阶段2: 侦察兵并行采集数据...")
            scout_data = await self.scout.gather_data(request, intent)
            print(f"   采集到 {len(scout_data.get('attractions', []))} 组景点数据")
            print(f"   天气: {scout_data.get('weather', {}).get('raw_data', 'N/A')[:100]}...")
            
            # 阶段3: 景点筛选
            print("\n🎯 阶段3: 筛选官评分筛选...")
            preferences = request.preferences or intent.get('key_preferences', [])
            curated = await self.curator.curate(
                scout_data.get('attractions', []),
                preferences,
                scout_data.get('weather', {})
            )
            print(f"   筛选出 {len(curated)} 个推荐景点")
            
            # 阶段4: 策略生成
            print("\n⚔️ 阶段4: 军师生成策略方案...")
            strategies = await self.strategist.generate_strategies(request, scout_data)
            print(f"   生成 {len(strategies)} 个策略方案")
            for s in strategies:
                print(f"   - {s.name}: {s.description[:50]}...")
            
            # 选择第一个策略（后续可以让用户选择）
            selected_strategy = strategies[0] if strategies else None
            
            # 阶段5: 审查
            print("\n🛡️ 阶段5: 谏官审查可行性...")
            # 先用占位数据生成初始计划用于审查
            initial_plan = await self.presenter.format_output(
                request, curated, 
                scout_data.get('hotels', []),
                scout_data.get('weather', {}),
                selected_strategy or StrategyOption(
                    name="默认",
                    description="默认策略",
                    confidence=0.5
                ),
                {'risk_notes': [], 'decision_rationales': []}
            )
            critique = await self.critic.review(request, initial_plan, scout_data.get('weather', {}))
            print(f"   发现 {len(critique.get('risk_notes', []))} 个风险点")
            
            # 阶段6: 输出格式化
            print("\n📝 阶段6: 书记格式化输出...")
            final_plan = await self.presenter.format_output(
                request, curated,
                scout_data.get('hotels', []),
                scout_data.get('weather', {}),
                selected_strategy or StrategyOption(
                    name="默认",
                    description="默认策略",
                    confidence=0.5
                ),
                critique
            )
            
            # 添加策略信息
            if strategies:
                final_plan.strategy_options = strategies
            if selected_strategy:
                final_plan.selected_strategy = selected_strategy.name
            if critique.get('decision_rationales'):
                final_plan.decision_rationales = [
                    DecisionRationale(**r) for r in critique['decision_rationales']
                ]
            if critique.get('risk_notes'):
                final_plan.risk_notes = critique['risk_notes']
            
            print(f"\n{'='*60}")
            print(f"✅ 五虎上将协作规划完成!")
            print(f"{'='*60}\n")
            
            return final_plan
            
        except Exception as e:
            print(f"❌ 规划失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return await self.presenter.format_output(
                request, [], [], {},
                StrategyOption(name="备用", description="备用方案", confidence=0.0),
                {'risk_notes': [], 'decision_rationales': []}
            )


# 全局实例
_five_agent_planner = None


def get_trip_planner_agent() -> FiveAgentTripPlanner:
    """获取五虎上将旅行规划系统实例"""
    global _five_agent_planner
    
    if _five_agent_planner is None:
        _five_agent_planner = FiveAgentTripPlanner()
    
    return _five_agent_planner
