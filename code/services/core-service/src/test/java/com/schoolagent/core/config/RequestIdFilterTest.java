package com.schoolagent.core.config;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class RequestIdFilterTest {

  @Test
  void keepsSafeCallerRequestId() {
    assertThat(RequestIdFilter.normalizedRequestId("web-request_123")).isEqualTo("web-request_123");
  }

  @Test
  void replacesUnsafeCallerRequestId() {
    assertThat(RequestIdFilter.normalizedRequestId("unsafe request\nvalue"))
        .matches("[0-9a-f-]{36}");
  }
}
