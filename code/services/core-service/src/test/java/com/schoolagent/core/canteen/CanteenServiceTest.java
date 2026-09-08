package com.schoolagent.core.canteen;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.inOrder;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.schoolagent.core.canteen.CanteenDtos.CartResponse;
import com.schoolagent.core.web.BusinessException;
import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InOrder;
import org.springframework.http.HttpStatus;

class CanteenServiceTest {

  private CanteenRepository repository;
  private CanteenService service;

  @BeforeEach
  void setUp() {
    repository = mock(CanteenRepository.class);
    service = new CanteenService(repository);
  }

  @Test
  void checkoutLocksTheOwnerBeforeReadingAnEmptyCart() {
    UUID userId = UUID.randomUUID();
    when(repository.cart(userId)).thenReturn(new CartResponse(List.of(), 0, BigDecimal.ZERO));

    BusinessException error =
        assertThrows(BusinessException.class, () -> service.placeOrder(userId));

    assertEquals(HttpStatus.CONFLICT, error.getStatus());
    InOrder calls = inOrder(repository);
    calls.verify(repository).lockUserForOrder(userId);
    calls.verify(repository).cart(userId);
  }

  @Test
  void checkoutUsesAUniqueBoundedOrderNumber() {
    UUID userId = UUID.randomUUID();
    CartResponse cart =
        new CartResponse(
            List.of(mock(CanteenDtos.CartItemResponse.class)), 1, new BigDecimal("3.00"));
    when(repository.cart(userId)).thenReturn(cart);
    when(repository.placeOrder(
            org.mockito.ArgumentMatchers.eq(userId), org.mockito.ArgumentMatchers.anyString()))
        .thenReturn(mock(CanteenDtos.OrderResponse.class));

    service.placeOrder(userId);

    verify(repository)
        .placeOrder(
            org.mockito.ArgumentMatchers.eq(userId),
            org.mockito.ArgumentMatchers.matches("DEMO\\d{14}-[A-F0-9]{8}"));
  }
}
