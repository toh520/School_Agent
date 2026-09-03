package com.schoolagent.core.canteen;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

/** Public contracts for the single-canteen student demo. */
public final class CanteenDtos {
  private CanteenDtos() {}

  public record FoodResponse(
      UUID id,
      String code,
      String name,
      BigDecimal price,
      String category,
      String mealRole,
      String description,
      String imageUrl,
      List<String> tastes,
      List<String> ingredients,
      String energyLevel,
      String proteinLevel,
      String carbLevel,
      String oilLevel,
      List<String> allergens,
      String spiceLevel,
      String portionSize,
      List<String> suitableTags,
      boolean featured) {}

  public record CartMutationRequest(
      @NotNull UUID foodId, @Min(1) @Max(20) int quantity, boolean allergenConfirmed) {}

  public record CartQuantityRequest(@Min(1) @Max(20) int quantity) {}

  public record CartItemResponse(UUID id, FoodResponse food, int quantity, BigDecimal subtotal) {}

  public record CartResponse(
      List<CartItemResponse> items, int totalQuantity, BigDecimal totalAmount) {}

  public record OrderItemResponse(
      String foodName, String imageUrl, BigDecimal unitPrice, int quantity) {}

  public record OrderResponse(
      UUID id,
      String orderNumber,
      String status,
      BigDecimal totalAmount,
      Instant createdAt,
      List<OrderItemResponse> items) {}
}
