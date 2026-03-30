// 类型定义

export interface Location {
  longitude: number
  latitude: number
}

export interface Attraction {
  name: string
  address: string
  location: Location
  visit_duration: number
  description: string
  category?: string
  rating?: number
  image_url?: string
  ticket_price?: number
}

export interface Meal {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  name: string
  address?: string
  location?: Location
  description?: string
  estimated_cost?: number
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price_range: string
  rating: string
  distance: string
  type: string
  estimated_cost?: number
}

export interface Budget {
  total_attractions: number
  total_hotels: number
  total_meals: number
  total_transportation: number
  total: number
}

export interface DayPlan {
  date: string
  day_index: number
  description: string
  transportation: string
  accommodation: string
  hotel?: Hotel
  attractions: Attraction[]
  meals: Meal[]
}

export interface WeatherInfo {
  date: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
  wind_power: string
}

export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
  strategy_options?: StrategyOption[]
  selected_strategy?: string
  decision_rationales?: DecisionRationale[]
  risk_notes?: string[]
}

export interface StrategyOption {
  name: string
  description: string
  pros: string[]
  cons: string[]
  trade_offs: string
  recommended_for: string
  confidence: number
}

export interface CuratedAttraction extends Attraction {
  relevance_score: number
  weather_suitability: string
  crowd_level: string
  curation_reason: string
}

export interface DecisionRationale {
  decision: string
  reason: string
  alternatives_considered: string[]
}

export interface TripFormData {
  city: string
  start_date: string
  end_date: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
}

export interface TripPlanResponse {
  success: boolean
  message: string
  data?: TripPlan
  graph_data?: KnowledgeGraphData
}

// ============ 知识图谱类型 ============

export interface GraphNode {
  id: string
  name: string
  category: number
  symbolSize: number
  itemStyle?: { color: string }
  value?: string
}

export interface GraphEdge {
  source: string
  target: string
  label?: string
}

export interface GraphCategory {
  name: string
}

export interface KnowledgeGraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  categories: GraphCategory[]
}

// ============ AI 行程问答类型 ============

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface TripChatRequest {
  message: string
  trip_plan: object
  history: ChatMessage[]
}

export interface TripChatResponse {
  success: boolean
  reply: string
}
