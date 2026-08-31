package com.schoolagent.core.web;

import org.springframework.http.HttpStatus;

/** Expected business failure carrying a stable public error code and HTTP status. */
public class BusinessException extends RuntimeException {

  private final ErrorCode errorCode;
  private final HttpStatus status;

  public BusinessException(ErrorCode errorCode, HttpStatus status) {
    super(errorCode.getMessage());
    this.errorCode = errorCode;
    this.status = status;
  }

  public ErrorCode getErrorCode() {
    return errorCode;
  }

  public HttpStatus getStatus() {
    return status;
  }
}
