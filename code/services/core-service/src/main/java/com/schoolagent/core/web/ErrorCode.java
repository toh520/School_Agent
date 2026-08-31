package com.schoolagent.core.web;

public enum ErrorCode {
  INVALID_REQUEST("请求参数无效"),
  INVALID_CREDENTIALS("账号或密码错误"),
  PASSWORD_MISMATCH("两次输入的密码不一致"),
  USERNAME_ALREADY_EXISTS("登录账号已被使用"),
  STUDENT_NUMBER_ALREADY_EXISTS("学号已注册"),
  PHONE_ALREADY_EXISTS("手机号已注册"),
  ACCOUNT_DISABLED("账号已被禁用"),
  UNAUTHENTICATED("请先登录或刷新会话"),
  FORBIDDEN("无权访问该资源"),
  RESOURCE_NOT_FOUND("请求的资源不存在"),
  RESOURCE_IN_USE("资料仍被其他有效记录引用，不能停用"),
  SELF_STATUS_CHANGE_FORBIDDEN("不能修改当前登录账号的状态"),
  CONFLICT("请求与当前数据状态冲突"),
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
