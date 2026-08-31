package com.schoolagent.core.web;

import com.schoolagent.core.config.RequestIdFilter;
import jakarta.validation.ConstraintViolationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

/** Converts failures to the public envelope without exposing exception internals. */
@RestControllerAdvice
public class GlobalExceptionHandler {

  private static final Logger LOGGER = LoggerFactory.getLogger(GlobalExceptionHandler.class);

  @ExceptionHandler(BusinessException.class)
  public ResponseEntity<ApiResponse<Void>> handleBusiness(BusinessException exception) {
    return ResponseEntity.status(exception.getStatus())
        .body(ApiResponse.failure(exception.getErrorCode(), requestId()));
  }

  @ExceptionHandler(AccessDeniedException.class)
  public ResponseEntity<ApiResponse<Void>> handleAccessDenied(AccessDeniedException exception) {
    return ResponseEntity.status(HttpStatus.FORBIDDEN)
        .body(ApiResponse.failure(ErrorCode.FORBIDDEN, requestId()));
  }

  @ExceptionHandler({
    MethodArgumentNotValidException.class,
    ConstraintViolationException.class,
    MethodArgumentTypeMismatchException.class,
    HttpMessageNotReadableException.class
  })
  public ResponseEntity<ApiResponse<Void>> handleInvalidRequest(Exception exception) {
    LOGGER.warn("Request validation failed: {}", exception.getClass().getSimpleName());
    return ResponseEntity.badRequest()
        .body(ApiResponse.failure(ErrorCode.INVALID_REQUEST, requestId()));
  }

  @ExceptionHandler(Exception.class)
  public ResponseEntity<ApiResponse<Void>> handleUnexpected(Exception exception) {
    LOGGER.error("Unhandled request failure: {}", exception.getClass().getSimpleName());
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
        .body(ApiResponse.failure(ErrorCode.INTERNAL_ERROR, requestId()));
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
