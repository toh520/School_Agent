package com.schoolagent.core.canteen;

import com.schoolagent.core.canteen.CanteenDtos.CartResponse;
import com.schoolagent.core.canteen.CanteenDtos.FoodResponse;
import com.schoolagent.core.canteen.CanteenDtos.OrderResponse;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Enforces availability and allergy confirmation before cart or order mutation. */
@Service
class CanteenService {
  private final CanteenRepository repository;

  CanteenService(CanteenRepository repository) {
    this.repository = repository;
  }

  List<FoodResponse> foods() {
    return repository.foods(true);
  }

  CartResponse cart(UUID userId) {
    return repository.cart(userId);
  }

  List<OrderResponse> orders(UUID userId) {
    return repository.orders(userId);
  }

  @Transactional
  CartResponse add(UUID userId, UUID foodId, int quantity, boolean allergenConfirmed) {
    FoodResponse food =
        repository
            .food(foodId)
            .orElseThrow(
                () -> new BusinessException(ErrorCode.RESOURCE_NOT_FOUND, HttpStatus.NOT_FOUND));
    Set<String> profile = new HashSet<>(repository.allergens(userId));
    profile.retainAll(food.allergens());
    if (!profile.isEmpty() && !allergenConfirmed) {
      throw new BusinessException(ErrorCode.CONFLICT, HttpStatus.CONFLICT);
    }
    repository.addCart(userId, foodId, quantity);
    return repository.cart(userId);
  }

  CartResponse update(UUID userId, UUID itemId, int quantity) {
    repository.updateCart(userId, itemId, quantity);
    return repository.cart(userId);
  }

  CartResponse delete(UUID userId, UUID itemId) {
    repository.deleteCart(userId, itemId);
    return repository.cart(userId);
  }

  @Transactional
  OrderResponse placeOrder(UUID userId) {
    if (repository.cart(userId).items().isEmpty())
      throw new BusinessException(ErrorCode.CONFLICT, HttpStatus.CONFLICT);
    String number =
        "DEMO" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
    return repository.placeOrder(userId, number);
  }
}
