"""高德地图服务封装"""

import json
import subprocess
from typing import List, Dict, Any, Optional
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo

# 全局服务实例
_amap_service = None


def get_amap_mcp_tool():
    """
    获取高德地图MCP工具（简化版本）
    
    由于hello-agents版本变化，返回一个兼容对象
    """
    return _get_amap_service()


def _run_amap_command(args: List[str]) -> str:
    """运行amap-mcp-server命令"""
    try:
        result = subprocess.run(
            ["uvx", "amap-mcp-server"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        print(f"执行amap命令失败: {e}")
        return "{}"


class AmapService:
    """高德地图服务封装类"""
    
    def __init__(self):
        """初始化服务"""
        settings = get_settings()
        if not settings.vite_amap_web_key:
            print("⚠️ 高德地图API Key未配置")
        self.api_key = settings.vite_amap_web_key
    
    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[Dict[str, Any]]:
        """
        搜索POI
        
        Args:
            keywords: 搜索关键词
            city: 城市
            citylimit: 是否限制在城市范围内
            
        Returns:
            POI信息列表
        """
        # 使用高德Web API直接搜索
        import urllib.request
        import urllib.parse
        
        try:
            base_url = "https://restapi.amap.com/v3/place/text"
            params = {
                "key": self.api_key,
                "keywords": keywords,
                "city": city,
                "citylimit": "true" if citylimit else "false",
                "output": "json",
                "types": "风景名胜|公园|广场|博物馆|寺庙|教堂|大学|体育场馆"
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            pois = []
            if data.get("status") == "1" and data.get("pois"):
                for poi in data["pois"][:10]:  # 限制返回数量
                    location = poi.get("location", "").split(",")
                    pois.append({
                        "name": poi.get("name", ""),
                        "address": poi.get("address", ""),
                        "location": {
                            "longitude": float(location[0]) if len(location) >= 1 else 0,
                            "latitude": float(location[1]) if len(location) >= 2 else 0
                        } if location and len(location) >= 2 else {"longitude": 0, "latitude": 0},
                        "type": poi.get("type", ""),
                        "rating": None,
                        "photos": []
                    })
            
            return pois
            
        except Exception as e:
            print(f"POI搜索失败: {str(e)}")
            return self._get_mock_pois(keywords, city)
    
    def _get_mock_pois(self, keywords: str, city: str) -> List[Dict[str, Any]]:
        """返回模拟POI数据（当API调用失败时）"""
        return [
            {
                "name": f"{city}{keywords}景点1",
                "address": f"{city}市景区路1号",
                "location": {"longitude": 116.4, "latitude": 39.9},
                "type": "风景名胜",
                "rating": 4.5,
                "photos": []
            },
            {
                "name": f"{city}{keywords}景点2",
                "address": f"{city}市景区路2号",
                "location": {"longitude": 116.41, "latitude": 39.91},
                "type": "公园",
                "rating": 4.3,
                "photos": []
            },
            {
                "name": f"{city}{keywords}景点3",
                "address": f"{city}市景区路3号",
                "location": {"longitude": 116.42, "latitude": 39.92},
                "type": "博物馆",
                "rating": 4.6,
                "photos": []
            }
        ]
    
    def get_weather(self, city: str) -> List[WeatherInfo]:
        """
        查询天气
        
        Args:
            city: 城市名称
            
        Returns:
            天气信息列表
        """
        import urllib.request
        import urllib.parse
        from datetime import datetime, timedelta
        
        try:
            base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
            params = {
                "key": self.api_key,
                "city": city,
                "extensions": "all"
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            weather_list = []
            if data.get("status") == "1" and data.get("forecasts") and data["forecasts"].get("forecast"):
                for day_weather in data["forecasts"]["forecast"][:7]:  # 7天天气
                    weather_list.append(WeatherInfo(
                        date=day_weather.get("date", ""),
                        day_weather=day_weather.get("dayWeather", ""),
                        night_weather=day_weather.get("nightWeather", ""),
                        day_temp=int(day_weather.get("dayTemp", 20)),
                        night_temp=int(day_weather.get("nightTemp", 10)),
                        wind_direction=day_weather.get("windDir", ""),
                        wind_power=day_weather.get("windPower", "")
                    ))
            
            return weather_list if weather_list else self._get_mock_weather(city)
            
        except Exception as e:
            print(f"天气查询失败: {str(e)}")
            return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> List[WeatherInfo]:
        """返回模拟天气数据"""
        from datetime import datetime, timedelta
        
        weather_list = []
        base_date = datetime.now()
        conditions = ["晴", "多云", "晴", "多云", "晴"]
        
        for i in range(5):
            date = base_date + timedelta(days=i)
            weather_list.append(WeatherInfo(
                date=date.strftime("%Y-%m-%d"),
                day_weather=conditions[i % len(conditions)],
                night_weather="多云" if conditions[i % len(conditions)] == "晴" else "晴",
                day_temp=20 + i,
                night_temp=12 + i,
                wind_direction="南风",
                wind_power="1-3级"
            ))
        
        return weather_list
    
    def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking"
    ) -> Dict[str, Any]:
        """
        规划路线
        
        Args:
            origin_address: 起点地址
            destination_address: 终点地址
            origin_city: 起点城市
            destination_city: 终点城市
            route_type: 路线类型 (walking/driving/transit)
            
        Returns:
            路线信息
        """
        import urllib.request
        import urllib.parse
        
        try:
            base_url = f"https://restapi.amap.com/v3/direction/{route_type}"
            params = {
                "key": self.api_key,
                "origin": origin_address,
                "destination": destination_address,
                "city": origin_city or destination_city
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data.get("status") == "1" and data.get("route"):
                route = data["route"]
                paths = route.get("paths", [])
                if paths:
                    path = paths[0]
                    return {
                        "distance": float(path.get("distance", 0)),
                        "duration": int(path.get("duration", 0)),
                        "route_type": route_type,
                        "description": path.get("strategy", "")
                    }
            
            return {"distance": 0, "duration": 0, "route_type": route_type, "description": ""}
            
        except Exception as e:
            print(f"路线规划失败: {str(e)}")
            return {"distance": 0, "duration": 0, "route_type": route_type, "description": ""}
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """
        地理编码(地址转坐标)

        Args:
            address: 地址
            city: 城市

        Returns:
            经纬度坐标
        """
        import urllib.request
        import urllib.parse
        
        try:
            base_url = "https://restapi.amap.com/v3/geocode/geo"
            params = {
                "key": self.api_key,
                "address": address,
                "city": city or ""
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data.get("status") == "1" and data.get("geocodes"):
                geocode = data["geocodes"][0]
                location = geocode.get("location", "").split(",")
                if len(location) >= 2:
                    return Location(
                        longitude=float(location[0]),
                        latitude=float(location[1])
                    )
            
            return None
            
        except Exception as e:
            print(f"地理编码失败: {str(e)}")
            return None
    
    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """
        获取POI详情

        Args:
            poi_id: POI ID

        Returns:
            POI详情信息
        """
        # 高德Web API不提供此功能，返回空
        return {}


def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service
    
    if _amap_service is None:
        _amap_service = AmapService()
    
    return _amap_service
