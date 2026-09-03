import type { ApiResponse } from '../types/api'
import type { Cart, DemoOrder, Food, MealCombination } from '../types/canteen'
import { agentHttp, authenticatedHttp } from './http'

function dataOrThrow<T>(response: { data: ApiResponse<T> }, message: string): T {
  if (response.data.data === null) throw new Error(message)
  return response.data.data
}

export async function fetchFoods(): Promise<Food[]> {
  return dataOrThrow(
    await authenticatedHttp.get<ApiResponse<Food[]>>('/canteen/foods'),
    '餐品加载失败',
  )
}
export async function fetchCart(): Promise<Cart> {
  return dataOrThrow(
    await authenticatedHttp.get<ApiResponse<Cart>>('/canteen/cart'),
    '购物车加载失败',
  )
}
export async function addCartItem(
  foodId: string,
  quantity = 1,
  allergenConfirmed = false,
): Promise<Cart> {
  return dataOrThrow(
    await authenticatedHttp.post<ApiResponse<Cart>>('/canteen/cart/items', {
      foodId,
      quantity,
      allergenConfirmed,
    }),
    '加入购物车失败',
  )
}
export async function updateCartItem(itemId: string, quantity: number): Promise<Cart> {
  return dataOrThrow(
    await authenticatedHttp.patch<ApiResponse<Cart>>(`/canteen/cart/items/${itemId}`, { quantity }),
    '购物车更新失败',
  )
}
export async function deleteCartItem(itemId: string): Promise<Cart> {
  return dataOrThrow(
    await authenticatedHttp.delete<ApiResponse<Cart>>(`/canteen/cart/items/${itemId}`),
    '购物车更新失败',
  )
}
export async function placeDemoOrder(): Promise<DemoOrder> {
  return dataOrThrow(
    await authenticatedHttp.post<ApiResponse<DemoOrder>>('/canteen/orders'),
    '下单失败',
  )
}
export async function fetchOrders(): Promise<DemoOrder[]> {
  return dataOrThrow(
    await authenticatedHttp.get<ApiResponse<DemoOrder[]>>('/canteen/orders'),
    '订单记录加载失败',
  )
}
export async function recommendMeals(payload: Record<string, unknown>): Promise<MealCombination[]> {
  return dataOrThrow(
    await agentHttp.post<ApiResponse<MealCombination[]>>('/canteen/recommendations', payload, {
      timeout: 0,
    }),
    '推荐生成失败',
  )
}
