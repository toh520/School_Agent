package com.schoolagent.core.canteen;

import com.schoolagent.core.canteen.CanteenDtos.CartMutationRequest;
import com.schoolagent.core.canteen.CanteenDtos.CartQuantityRequest;
import com.schoolagent.core.canteen.CanteenDtos.CartResponse;
import com.schoolagent.core.canteen.CanteenDtos.FoodResponse;
import com.schoolagent.core.canteen.CanteenDtos.OrderResponse;
import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.identity.CurrentIdentity;
import com.schoolagent.core.web.ApiResponse;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Student API for browsing the single canteen, managing a cart, and placing demo orders. */
@RestController
@RequestMapping("/api/v1/canteen")
@PreAuthorize("hasRole('STUDENT')")
public class CanteenController {
  private final CanteenService service;

  public CanteenController(CanteenService service) {
    this.service = service;
  }

  @GetMapping("/foods")
  public ApiResponse<List<FoodResponse>> foods() {
    return ApiResponse.success(service.foods(), requestId());
  }

  @GetMapping("/cart")
  public ApiResponse<CartResponse> cart(Authentication auth) {
    return ApiResponse.success(service.cart(id(auth)), requestId());
  }

  @PostMapping("/cart/items")
  public ApiResponse<CartResponse> add(
      Authentication auth, @Valid @RequestBody CartMutationRequest request) {
    return ApiResponse.success(
        service.add(id(auth), request.foodId(), request.quantity(), request.allergenConfirmed()),
        requestId());
  }

  @PatchMapping("/cart/items/{itemId}")
  public ApiResponse<CartResponse> update(
      Authentication auth,
      @PathVariable UUID itemId,
      @Valid @RequestBody CartQuantityRequest request) {
    return ApiResponse.success(service.update(id(auth), itemId, request.quantity()), requestId());
  }

  @DeleteMapping("/cart/items/{itemId}")
  public ApiResponse<CartResponse> delete(Authentication auth, @PathVariable UUID itemId) {
    return ApiResponse.success(service.delete(id(auth), itemId), requestId());
  }

  @PostMapping("/orders")
  public ApiResponse<OrderResponse> order(Authentication auth) {
    return ApiResponse.success(service.placeOrder(id(auth)), requestId());
  }

  @GetMapping("/orders")
  public ApiResponse<List<OrderResponse>> orders(Authentication auth) {
    return ApiResponse.success(service.orders(id(auth)), requestId());
  }

  private UUID id(Authentication auth) {
    return CurrentIdentity.from(auth).userId();
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
