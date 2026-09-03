export interface Food {
  id: string
  code: string
  name: string
  price: number
  category: string
  mealRole: string
  description: string
  imageUrl: string
  tastes: string[]
  ingredients: string[]
  energyLevel: string
  proteinLevel: string
  carbLevel: string
  oilLevel: string
  allergens: string[]
  spiceLevel: string
  portionSize: string
  suitableTags: string[]
  featured: boolean
}

export interface CartItem {
  id: string
  food: Food
  quantity: number
  subtotal: number
}
export interface Cart {
  items: CartItem[]
  totalQuantity: number
  totalAmount: number
}
export interface MealCombination {
  key: string
  title: string
  foodIds: string[]
  quantities: Record<string, number>
  totalPrice: number
  reason: string
  matchedRequirements: string[]
  limitations: string[]
}
export interface DemoOrder {
  id: string
  orderNumber: string
  status: 'PLACED'
  totalAmount: number
  createdAt: string
  items: Array<{ foodName: string; imageUrl: string; unitPrice: number; quantity: number }>
}
