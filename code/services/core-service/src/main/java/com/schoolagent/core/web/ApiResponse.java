package com.schoolagent.core.web;

import java.time.ZoneId;
import java.time.ZonedDateTime;

/** Stable JSON envelope used by public core-service endpoints. */
public record ApiResponse<T>(
    boolean success, T data, ApiError error, String requestId, ZonedDateTime timestamp) {

  private static final ZoneId APPLICATION_ZONE = ZoneId.of("Asia/Shanghai");

  public static <T> ApiResponse<T> success(T data, String requestId) {
    return new ApiResponse<>(true, data, null, requestId, ZonedDateTime.now(APPLICATION_ZONE));
  }

  public static <T> ApiResponse<T> failure(ErrorCode errorCode, String requestId) {
    return new ApiResponse<>(
        false,
        null,
        new ApiError(errorCode.name(), errorCode.getMessage()),
        requestId,
        ZonedDateTime.now(APPLICATION_ZONE));
  }
}
