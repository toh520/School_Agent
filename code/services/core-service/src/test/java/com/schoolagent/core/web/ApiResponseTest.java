package com.schoolagent.core.web;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.ZoneId;
import org.junit.jupiter.api.Test;

class ApiResponseTest {

  @Test
  void createsSuccessEnvelopeInProjectTimezone() {
    ApiResponse<String> response = ApiResponse.success("ok", "request-1");

    assertThat(response.success()).isTrue();
    assertThat(response.data()).isEqualTo("ok");
    assertThat(response.requestId()).isEqualTo("request-1");
    assertThat(response.timestamp().getZone()).isEqualTo(ZoneId.of("Asia/Shanghai"));
  }
}
