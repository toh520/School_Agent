package com.schoolagent.core.web;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import org.junit.jupiter.api.Test;

class PageResponseTest {

  @Test
  void rejectsInvalidPageSize() {
    assertThatThrownBy(() -> new PageResponse<>(List.of(), 0, 0, 0, 0))
        .isInstanceOf(IllegalArgumentException.class);
  }
}
