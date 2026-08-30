package com.schoolagent.core.web;

public enum ErrorCode {
  INVALID_REQUEST("请求参数无效"),
  UPSTREAM_UNAVAILABLE("依赖服务暂时不可用"),
  INTERNAL_ERROR("服务内部错误");

  private final String message;

  ErrorCode(String message) {
    this.message = message;
  }

  public String getMessage() {
    return message;
  }
}
