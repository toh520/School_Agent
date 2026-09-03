package com.schoolagent.core.canteen;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.schoolagent.core.canteen.CanteenDtos.CartItemResponse;
import com.schoolagent.core.canteen.CanteenDtos.CartResponse;
import com.schoolagent.core.canteen.CanteenDtos.FoodResponse;
import com.schoolagent.core.canteen.CanteenDtos.OrderItemResponse;
import com.schoolagent.core.canteen.CanteenDtos.OrderResponse;
import java.math.BigDecimal;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** JDBC persistence for menu reads, each student's cart, and demo order snapshots. */
@Repository
class CanteenRepository {
  private static final TypeReference<LinkedHashMap<String, Object>> MAP_TYPE =
      new TypeReference<>() {};
  private final JdbcTemplate jdbc;
  private final ObjectMapper objectMapper;

  CanteenRepository(JdbcTemplate jdbc, ObjectMapper objectMapper) {
    this.jdbc = jdbc;
    this.objectMapper = objectMapper;
  }

  List<FoodResponse> foods(boolean onlyAvailable) {
    String availability = onlyAvailable ? " AND payload->>'availabilityStatus' = 'AVAILABLE'" : "";
    return jdbc.query(
        "SELECT id, code, name, payload FROM dish WHERE deleted_at IS NULL"
            + availability
            + " ORDER BY CASE WHEN payload->>'featured' = 'YES' THEN 0 ELSE 1 END, name",
        this::mapFood);
  }

  Optional<FoodResponse> food(UUID id) {
    return jdbc
        .query(
            "SELECT id, code, name, payload FROM dish WHERE id = ? AND deleted_at IS NULL",
            this::mapFood,
            id)
        .stream()
        .findFirst();
  }

  List<String> allergens(UUID userId) {
    String json =
        jdbc.queryForObject(
            "SELECT allergens::text FROM user_preference WHERE user_id = ?", String.class, userId);
    try {
      return objectMapper.readValue(json == null ? "[]" : json, new TypeReference<>() {});
    } catch (JsonProcessingException exception) {
      throw new IllegalStateException("Invalid allergen profile", exception);
    }
  }

  void addCart(UUID userId, UUID foodId, int quantity) {
    jdbc.update(
        """
        INSERT INTO canteen_cart_item(id, user_id, dish_id, quantity)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, dish_id) DO UPDATE
        SET quantity = LEAST(20, canteen_cart_item.quantity + EXCLUDED.quantity),
            updated_at = CURRENT_TIMESTAMP
        """,
        UUID.randomUUID(),
        userId,
        foodId,
        quantity);
  }

  void updateCart(UUID userId, UUID itemId, int quantity) {
    jdbc.update(
        "UPDATE canteen_cart_item SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        quantity,
        itemId,
        userId);
  }

  void deleteCart(UUID userId, UUID itemId) {
    jdbc.update("DELETE FROM canteen_cart_item WHERE id = ? AND user_id = ?", itemId, userId);
  }

  CartResponse cart(UUID userId) {
    List<CartItemResponse> items =
        jdbc.query(
            """
        SELECT cart.id AS cart_id, cart.quantity, dish.id, dish.code, dish.name, dish.payload
        FROM canteen_cart_item cart JOIN dish ON dish.id = cart.dish_id
        WHERE cart.user_id = ? AND dish.deleted_at IS NULL
        ORDER BY cart.updated_at DESC
        """,
            (resultSet, row) -> {
              FoodResponse food = mapFood(resultSet, row);
              return new CartItemResponse(
                  resultSet.getObject("cart_id", UUID.class),
                  food,
                  resultSet.getInt("quantity"),
                  food.price().multiply(BigDecimal.valueOf(resultSet.getInt("quantity"))));
            },
            userId);
    int count = items.stream().mapToInt(CartItemResponse::quantity).sum();
    BigDecimal total =
        items.stream().map(CartItemResponse::subtotal).reduce(BigDecimal.ZERO, BigDecimal::add);
    return new CartResponse(items, count, total);
  }

  OrderResponse placeOrder(UUID userId, String orderNumber) {
    CartResponse cart = cart(userId);
    UUID orderId = UUID.randomUUID();
    jdbc.update(
        "INSERT INTO canteen_order(id, order_number, user_id, total_amount) VALUES (?, ?, ?, ?)",
        orderId,
        orderNumber,
        userId,
        cart.totalAmount());
    for (CartItemResponse item : cart.items()) {
      jdbc.update(
          "INSERT INTO canteen_order_item(id, order_id, dish_id, dish_name, image_url, unit_price, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)",
          UUID.randomUUID(),
          orderId,
          item.food().id(),
          item.food().name(),
          item.food().imageUrl(),
          item.food().price(),
          item.quantity());
    }
    jdbc.update("DELETE FROM canteen_cart_item WHERE user_id = ?", userId);
    return order(userId, orderId).orElseThrow();
  }

  Optional<OrderResponse> order(UUID userId, UUID orderId) {
    return jdbc
        .query(
            "SELECT id, order_number, status, total_amount, created_at FROM canteen_order WHERE id = ? AND user_id = ?",
            (resultSet, row) ->
                new OrderResponse(
                    resultSet.getObject("id", UUID.class),
                    resultSet.getString("order_number"),
                    resultSet.getString("status"),
                    resultSet.getBigDecimal("total_amount"),
                    resultSet.getObject("created_at", OffsetDateTime.class).toInstant(),
                    orderItems(orderId)),
            orderId,
            userId)
        .stream()
        .findFirst();
  }

  List<OrderResponse> orders(UUID userId) {
    return jdbc.query(
        """
        SELECT id, order_number, status, total_amount, created_at
        FROM canteen_order
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (resultSet, row) -> {
          UUID orderId = resultSet.getObject("id", UUID.class);
          return new OrderResponse(
              orderId,
              resultSet.getString("order_number"),
              resultSet.getString("status"),
              resultSet.getBigDecimal("total_amount"),
              resultSet.getObject("created_at", OffsetDateTime.class).toInstant(),
              orderItems(orderId));
        },
        userId);
  }

  private List<OrderItemResponse> orderItems(UUID orderId) {
    return jdbc.query(
        "SELECT dish_name, image_url, unit_price, quantity FROM canteen_order_item WHERE order_id = ? ORDER BY id",
        (resultSet, row) ->
            new OrderItemResponse(
                resultSet.getString("dish_name"),
                resultSet.getString("image_url"),
                resultSet.getBigDecimal("unit_price"),
                resultSet.getInt("quantity")),
        orderId);
  }

  @SuppressWarnings("unchecked")
  private FoodResponse mapFood(ResultSet resultSet, int row) throws SQLException {
    try {
      Map<String, Object> payload =
          objectMapper.readValue(resultSet.getString("payload"), MAP_TYPE);
      return new FoodResponse(
          resultSet.getObject("id", UUID.class),
          resultSet.getString("code"),
          resultSet.getString("name"),
          decimal(payload.get("price")),
          string(payload.get("category")),
          string(payload.get("mealRole")),
          string(payload.get("description")),
          string(payload.get("imageUrl")),
          list(payload.get("tastes")),
          list(payload.get("ingredients")),
          string(payload.getOrDefault("energyLevel", "UNKNOWN")),
          string(payload.getOrDefault("proteinLevel", "UNKNOWN")),
          string(payload.getOrDefault("carbLevel", "UNKNOWN")),
          string(payload.getOrDefault("oilLevel", "UNKNOWN")),
          list(payload.get("allergens")),
          string(payload.get("spiceLevel")),
          string(payload.get("portionSize")),
          list(payload.get("suitableTags")),
          "YES".equals(payload.get("featured")));
    } catch (JsonProcessingException exception) {
      throw new SQLException("Invalid dish payload", exception);
    }
  }

  private BigDecimal decimal(Object value) {
    return value == null ? BigDecimal.ZERO : new BigDecimal(String.valueOf(value));
  }

  private String string(Object value) {
    return value == null ? "" : String.valueOf(value);
  }

  private List<String> list(Object value) {
    return value instanceof List<?> items
        ? items.stream().map(String::valueOf).toList()
        : List.of();
  }
}
