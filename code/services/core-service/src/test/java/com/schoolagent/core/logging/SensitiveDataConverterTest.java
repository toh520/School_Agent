package com.schoolagent.core.logging;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class SensitiveDataConverterTest {

  @Test
  void masksCommonSecretAssignments() {
    String message = "password=demo token:abc api_key=key123 action=health";

    assertThat(SensitiveDataConverter.mask(message))
        .isEqualTo("password=*** token:*** api_key=*** action=health");
  }
}
